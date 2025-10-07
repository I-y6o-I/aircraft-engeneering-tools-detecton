import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { 
  apiService,
  type LoginRequest,
  type RegisterRequest,
  type UserProfile,
  type LoginResponse,
} from '@/services/api'

// User interface for local state
export interface User {
  id: string
  employeeId: string
  role: string
}

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const isLoading = ref(false)

  const isAuthenticated = computed(() => !!user.value)

  // Login function
  const login = async (loginData: LoginRequest): Promise<void> => {
    isLoading.value = true
    try {
      const response = await apiService.login(loginData)
      
      // Store token
      localStorage.setItem('aero-kit-token', response.access_token)
      localStorage.setItem('aero-kit-token-type', response.token_type)
      const expiresIn = response.expires_in * 1000 // Convert seconds to milliseconds
      const expirationTime = Date.now() + expiresIn
      localStorage.setItem('aero-kit-token-expires', expirationTime.toString())

      // Get user profile after successful login
      await fetchUserProfile()
    } catch (error) {
      logout() // Clear any partial login state
      throw error
    } finally {
      isLoading.value = false
    }
  }

  // Register function
  const register = async (registerData: RegisterRequest): Promise<void> => {
    isLoading.value = true
    try {
      await apiService.register(registerData)
      // Auto-login after successful registration
      await login({
        employee_id: registerData.employee_id,
        password: registerData.password,
      })
    } catch (error) {
      throw error
    } finally {
      isLoading.value = false
    }
  }

  // Fetch user profile from API
  const fetchUserProfile = async (): Promise<void> => {
    const token = localStorage.getItem('aero-kit-token')
    if (!token) {
      return
    }

    try {
      const profile: UserProfile = await apiService.getMe()
      
      // Map API response to local user state
      user.value = {
        id: profile.user_id,
        employeeId: profile.employee_id,
        role: profile.role,
      }
    } catch (error) {
      console.error('Failed to fetch user profile:', error)
      // If fetching profile fails (e.g., token expired), log out the user
      logout()
    }
  }

  // Logout function
  const logout = (): void => {
    user.value = null
    localStorage.removeItem('aero-kit-token')
    localStorage.removeItem('aero-kit-token-type')
    localStorage.removeItem('aero-kit-token-expires')
  }

  // Initialize auth state from localStorage
  const initializeAuth = async (): Promise<void> => {
    const storedToken = localStorage.getItem('aero-kit-token')
    const tokenExpires = localStorage.getItem('aero-kit-token-expires')
    
    if (storedToken && tokenExpires) {
      const expirationTime = parseInt(tokenExpires)
      if (Date.now() > expirationTime) {
        logout()
        return
      }
      
      // Try to fetch user profile if we have a valid token
      await fetchUserProfile()
    }
  }

  // Check if user has valid session
  const checkAuth = (): boolean => {
    const token = localStorage.getItem('aero-kit-token')
    const tokenExpires = localStorage.getItem('aero-kit-token-expires')
    
    if (!token || !tokenExpires) {
      logout()
      return false
    }
    
    const expirationTime = parseInt(tokenExpires)
    if (Date.now() > expirationTime) {
      logout()
      return false
    }
    
    return isAuthenticated.value
  }

  return {
    user,
    isLoading,
    isAuthenticated,
    login,
    register,
    logout,
    initializeAuth,
    checkAuth,
    fetchUserProfile
  }
})
