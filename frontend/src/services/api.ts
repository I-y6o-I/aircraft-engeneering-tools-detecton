// API service for handling HTTP requests
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

// Types for API responses
export interface ApiResponse<T = any> {
  data: T
  message?: string
  status: number
}

export interface ApiError {
  message: string
  status: number
  details?: any
}

// Recognition API Types
export interface PredictRequest {
  image: string // base64-строка изображения
  threshold: number
}

export interface Detection {
  detection_id: string
  class: string
  confidence: number
  is_passed_conf_treshold: boolean
  box: [number, number, number, number] // [x_center, y_center, width, height] в нормализованных координатах (0..1)
}

export interface PredictResponse {
  threshold: number
  classes_catalog: string[]
  detections: Detection[]
  not_found: string[]
  summary: {
    expected_total: number
    found_candidates: number
    passed_above_threshold: number
    requires_manual_count: number
    not_found_count: number
  }
}

export interface Annotation {
  class: string
  box: [number, number, number, number]
  source: 'model' | 'edited' | 'manual'
  from_detection_id?: string
}

export interface AdjustRequest {
  threshold: number
  annotations: Annotation[]
}

export interface FinalClass {
  present: boolean
  box: [number, number, number, number]
  source: 'model' | 'edited' | 'manual'
  from_detection_id?: string
}

export interface AdjustResponse {
  ok: boolean
  issues: string[]
  count: number
  passed?: boolean
  validation?: {
    warnings: string[]
    errors?: string[]
  }
}

// Session Types
export type SessionStatus = 'draft' | 'handout_auto' | 'handout_needs_manual' | 'issued' | 'handover_auto' | 'handover_needs_manual' | 'returned' | 'completed' // Added 'completed' based on session store logic

export interface CreateSessionRequest {
  threshold: number
  notes: string
}

export interface CreateSessionResponse {
  session_id: string
  status: SessionStatus
  threshold_used: number
  created_at: string
}

export interface SessionListItem {
  id: string
  employee_id: string
  status: SessionStatus
  notes?: string
  created_at: string
  updated_at: string
}

export interface SessionListResponse {
  page: number
  limit: number
  total: number
  items: SessionListItem[]
}

export interface FinalAnnotation {
  class?: string
  class_?: string
  box: [number, number, number, number]
  source: 'model' | 'edited' | 'manual'
  from_detection_id?: string
}

export interface SessionPhase {
  predict?: PredictResponse
  final?: {
    annotations: FinalAnnotation[]
    validation?: AdjustResponse['validation']
  }
  image?: string | null
  issued_at?: string
  returned_at?: string
}

export interface SessionDetail {
  id: string
  employee_id: string
  status: SessionStatus
  threshold_used: number
  notes?: string
  handout?: SessionPhase
  handover?: SessionPhase
  created_at: string
  updated_at: string
}

export interface SessionDiff {
  expected: Record<string, number>
  handout_final: Record<string, FinalClass>
  handover_final: Record<string, FinalClass>
  missing: string[]
  extra?: string[]
}

export interface StatusChangeResponse {
  status: SessionStatus
  issued_at?: string
  returned_at?: string
}

// Auth Types from auth.ts - moving them here for colocation
export interface LoginRequest {
  employee_id: string
  password: string
}

export interface LoginResponse {
  access_token: string
  token_type: string
  expires_in: number
}

export interface RegisterRequest {
  employee_id: string
  password: string
  role: 'simple' | 'admin' // Added role as per backend README
}

export interface RegisterResponse {
  user_id: string
  employee_id: string
  role: string
  created_at: string
}

export interface UserProfile {
  user_id: string
  employee_id: string
  role: string
}


class ApiService {
  private baseURL: string

  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`
    
    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    }

    // Add authorization header if token exists
    const token = localStorage.getItem('aero-kit-token')
    if (token) {
      config.headers = {
        ...config.headers,
        Authorization: `Bearer ${token}`,
      }
    }

    try {
      const response = await fetch(url, config)

      if (response.status === 204) {
        // Handle no content response
        return {} as T
      }
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        // Use `detail` field from FastAPI errors if available
        let errorMessage = `HTTP error! status: ${response.status}`

        if (errorData.detail) {
          if (Array.isArray(errorData.detail)) {
            // Handle array of validation errors from FastAPI
            errorMessage = errorData.detail
              .map((err: any) => err.msg || JSON.stringify(err))
              .join('\n')
          } else if (typeof errorData.detail === 'string') {
            // Handle simple string detail
            errorMessage = errorData.detail
          } else {
            // Handle other object-like details
            errorMessage = JSON.stringify(errorData.detail)
          }
        } else if (errorData.message) {
          // Fallback to a generic message property
          errorMessage = errorData.message
        }
        
        throw new Error(errorMessage)
      }

      return await response.json()
    } catch (error) {
      console.error('API request failed:', error)
      throw error
    }
  }

  // GET request
  async get<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'GET' })
  }

  // POST request
  async post<T>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    })
  }

  // PUT request
  async put<T>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    })
  }

  // DELETE request
  async delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'DELETE' })
  }

  // PATCH request
  async patch<T>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PATCH',
      body: data ? JSON.stringify(data) : undefined,
    })
  }

  // --- Auth API Methods ---
  async login(request: LoginRequest): Promise<LoginResponse> {
    return this.post<LoginResponse>('/auth/login', request)
  }

  async register(request: RegisterRequest): Promise<RegisterResponse> {
    return this.post<RegisterResponse>('/auth/register', request)
  }

  async getMe(): Promise<UserProfile> {
    return this.get<UserProfile>('/auth/me')
  }


  // --- Recognition API Methods ---
  async predict(request: PredictRequest): Promise<PredictResponse> {
    return this.post<PredictResponse>('/predict', request)
  }

  async adjustPredictions(request: AdjustRequest): Promise<AdjustResponse> {
    return this.post<AdjustResponse>('/predict/adjust', request)
  }

  // --- Session Management Methods ---
  async createSession(request: CreateSessionRequest): Promise<CreateSessionResponse> {
    return this.post<CreateSessionResponse>('/sessions/handout', request)
  }

  async getSession(sessionId: string): Promise<SessionDetail> {
    return this.get<SessionDetail>(`/sessions/${sessionId}`)
  }

  async getSessions(page: number = 1, limit: number = 20): Promise<SessionListResponse> {
    // Note: Backend doesn't seem to support pagination yet, but we keep the params for future use
    return this.get<SessionListResponse>('/sessions')
  }

  async sessionHandoutPredict(sessionId: string, request: PredictRequest): Promise<PredictResponse> {
    return this.post<PredictResponse>(`/sessions/${sessionId}/handout/predict`, request)
  }

  async sessionHandoutAdjust(sessionId: string, request: AdjustRequest): Promise<AdjustResponse> {
    return this.post<AdjustResponse>(`/sessions/${sessionId}/handout/adjust`, request)
  }

  async issueSession(sessionId: string): Promise<StatusChangeResponse> {
    return this.post<StatusChangeResponse>(`/sessions/${sessionId}/issue`, {})
  }

  async sessionHandoverPredict(sessionId: string, request: PredictRequest): Promise<PredictResponse> {
    return this.post<PredictResponse>(`/sessions/${sessionId}/handover/predict`, request)
  }

  async sessionHandoverAdjust(sessionId: string, request: AdjustRequest): Promise<AdjustResponse> {
    return this.post<AdjustResponse>(`/sessions/${sessionId}/handover/adjust`, request)
  }

  async getSessionDiff(sessionId: string): Promise<SessionDiff> {
    return this.get<SessionDiff>(`/sessions/${sessionId}/diff`)
  }

  async finalizeSession(sessionId: string): Promise<StatusChangeResponse> {
    return this.post<StatusChangeResponse>(`/sessions/${sessionId}/finalize`, {})
  }
}

// Export singleton instance
export const apiService = new ApiService()
export default apiService
