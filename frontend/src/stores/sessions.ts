import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { 
  apiService, 
  type SessionListItem, 
  type SessionDetail, 
  type CreateSessionRequest, 
  type SessionDiff,
  type PredictRequest,
  type PredictResponse,
  type AdjustRequest,
  type AdjustResponse
} from '@/services/api'
import { useNotificationStore } from '@/stores/notifications'

export const useSessionStore = defineStore('sessions', () => {
  // State
  const sessions = ref<SessionListItem[]>([])
  const currentSession = ref<SessionDetail | null>(null)
  const sessionDiff = ref<SessionDiff | null>(null)
  const isLoading = ref(false)
  const isCreating = ref(false)
  const isProcessing = ref(false)
  
  // Computed
  const sessionsCount = computed(() => sessions.value.length)
  const draftSessions = computed(() => 
    sessions.value.filter(s => s.status === 'draft')
  )
  const activeSessions = computed(() => 
    sessions.value.filter(s => ['handout_auto', 'handout_needs_manual', 'issued', 'handover_auto', 'handover_needs_manual'].includes(s.status))
  )
  const completedSessions = computed(() => 
    sessions.value.filter(s => ['returned', 'completed'].includes(s.status))
  )

  // Actions
  const fetchSessions = async () => {
    isLoading.value = true
    try {
      const response = await apiService.getSessions()
      // The backend returns a flat list of items, not a paginated object.
      // Let's check if response is an array before assigning.
      if (Array.isArray(response)) {
        sessions.value = response
      } else if (response.items && Array.isArray(response.items)) {
        // Handle paginated response if backend adds it later
        sessions.value = response.items
      } else {
        console.warn('Unexpected response format for sessions:', response)
        sessions.value = []
      }
    } catch (error) {
      const notifications = useNotificationStore()
      notifications.error('Не удалось загрузить список сессий', {
        title: 'Ошибка загрузки'
      })
      throw error
    } finally {
      isLoading.value = false
    }
  }

  const createSession = async (request: CreateSessionRequest) => {
    isCreating.value = true
    try {
      const response = await apiService.createSession(request)
      
      // After creating, fetch the full list to get all details correctly
      await fetchSessions()
      
      const notifications = useNotificationStore()
      notifications.success('Сессия успешно создана', {
        title: 'Успех'
      })
      
      return response
    } catch (error) {
      const notifications = useNotificationStore()
      notifications.error('Не удалось создать сессию', {
        title: 'Ошибка создания'
      })
      throw error
    } finally {
      isCreating.value = false
    }
  }

  const fetchSession = async (sessionId: string) => {
    isLoading.value = true
    try {
      const session = await apiService.getSession(sessionId)
      currentSession.value = session
      return session
    } catch (error) {
      const notifications = useNotificationStore()
      notifications.error('Не удалось загрузить данные сессии', {
        title: 'Ошибка загрузки'
      })
      throw error
    } finally {
      isLoading.value = false
    }
  }

  const handoutPredict = async (sessionId: string, request: PredictRequest): Promise<PredictResponse> => {
    isProcessing.value = true
    try {
      const result = await apiService.sessionHandoutPredict(sessionId, request)
      
      // Update current session with predict data
      if (currentSession.value && currentSession.value.id === sessionId) {
        if (!currentSession.value.handout) {
          currentSession.value.handout = {}
        }
        currentSession.value.handout.predict = result
        currentSession.value.handout.image = request.image
        currentSession.value.status = 'handout_needs_manual'
      }
      
      return result
    } catch (error) {
      const notifications = useNotificationStore()
      notifications.error('Ошибка при распознавании изображения', {
        title: 'Ошибка распознавания'
      })
      throw error
    } finally {
      isProcessing.value = false
    }
  }

  const handoutAdjust = async (sessionId: string, request: AdjustRequest): Promise<AdjustResponse> => {
    isProcessing.value = true
    try {
      const result = await apiService.sessionHandoutAdjust(sessionId, request)
      
      // Update current session with final data by re-fetching
      if (result.ok) {
        await fetchSession(sessionId)
      }
      
      return result
    } catch (error) {
      throw error
    } finally {
      isProcessing.value = false
    }
  }

  const issueSession = async (sessionId: string) => {
    isProcessing.value = true
    try {
      const result = await apiService.issueSession(sessionId)
      
      // Update session status by re-fetching the session and the list
      await fetchSession(sessionId)
      await fetchSessions()
      
      const notifications = useNotificationStore()
      notifications.success('Инструменты успешно выданы', {
        title: 'Выдача завершена'
      })
      
      return result
    } catch (error) {
      throw error
    } finally {
      isProcessing.value = false
    }
  }

  const handoverPredict = async (sessionId: string, request: PredictRequest): Promise<PredictResponse> => {
    isProcessing.value = true
    try {
      const result = await apiService.sessionHandoverPredict(sessionId, request)
      
      // Update current session with predict data
      if (currentSession.value && currentSession.value.id === sessionId) {
        if (!currentSession.value.handover) {
          currentSession.value.handover = {}
        }
        currentSession.value.handover.predict = result
        currentSession.value.handover.image = request.image
        currentSession.value.status = 'handover_needs_manual'
      }
      
      return result
    } catch (error) {
      const notifications = useNotificationStore()
      notifications.error('Ошибка при распознавании изображения сдачи', {
        title: 'Ошибка распознавания'
      })
      throw error
    } finally {
      isProcessing.value = false
    }
  }

  const handoverAdjust = async (sessionId: string, request: AdjustRequest): Promise<AdjustResponse> => {
    isProcessing.value = true
    try {
      const result = await apiService.sessionHandoverAdjust(sessionId, request)
      
      // Update current session with final data by re-fetching
      if (result.ok) {
        await fetchSession(sessionId)
        await fetchSessions() // also update list for status change
      } else {
     }
      
      return result
    } catch (error) {
      const notifications = useNotificationStore()
      throw error
    } finally {
      isProcessing.value = false
    }
  }

  const fetchSessionDiff = async (sessionId: string) => {
    isLoading.value = true
    try {
      const diff = await apiService.getSessionDiff(sessionId)
      sessionDiff.value = diff
      return diff
    } catch (error) {
      const notifications = useNotificationStore()
      notifications.error('Ошибка при получении сравнения', {
        title: 'Ошибка загрузки'
      })
      throw error
    } finally {
      isLoading.value = false
    }
  }

  const finalizeSession = async (sessionId: string) => {
    isProcessing.value = true
    try {
      const result = await apiService.finalizeSession(sessionId)
      
      // Update session status by re-fetching
      await fetchSession(sessionId)
      await fetchSessions()
      
      const notifications = useNotificationStore()
      notifications.success('Сессия успешно завершена', {
        title: 'Сдача завершена'
      })
      
      return result
    } catch (error) {
      const notifications = useNotificationStore()
      notifications.error('Ошибка при завершении сессии', {
        title: 'Ошибка завершения'
      })
      throw error
    } finally {
      isProcessing.value = false
    }
  }

  const clearCurrentSession = () => {
    currentSession.value = null
    sessionDiff.value = null
  }

  const clearSessionDiff = () => {
    sessionDiff.value = null
  }

  // Helper method to get session status in Russian
  const getSessionStatusText = (status: string): string => {
    const statusMap: Record<string, string> = {
      'draft': 'Черновик',
      'handout_auto': 'Выдача (авто)',
      'handout_needs_manual': 'Выдача (ручная правка)',
      'issued': 'Выдано',
      'handover_auto': 'Сдача (авто)',
      'handover_needs_manual': 'Сдача (ручная правка)',
      'returned': 'Сдано (проверено)',
      'completed': 'Завершено'
    }
    return statusMap[status] || status
  }

  const getSessionStatusColor = (status: string): string => {
    const colorMap: Record<string, string> = {
      'draft': 'text-gray-400',
      'handout_auto': 'text-blue-400',
      'handout_needs_manual': 'text-yellow-400',
      'issued': 'text-green-400',
      'handover_auto': 'text-blue-400',
      'handover_needs_manual': 'text-yellow-400',
      'returned': 'text-green-400',
    }
    return colorMap[status] || 'text-gray-400'
  }

  return {
    // State
    sessions,
    currentSession,
    sessionDiff,
    isLoading,
    isCreating,
    isProcessing,
    
    // Computed
    sessionsCount,
    draftSessions,
    activeSessions,
    completedSessions,
    
    // Actions
    fetchSessions,
    createSession,
    fetchSession,
    handoutPredict,
    handoutAdjust,
    issueSession,
    handoverPredict,
    handoverAdjust,
    fetchSessionDiff,
    finalizeSession,
    clearCurrentSession,
    clearSessionDiff,
    
    // Helpers
    getSessionStatusText,
    getSessionStatusColor
  }
})
