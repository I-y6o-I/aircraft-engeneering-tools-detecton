<template>
  <div class="dashboard-container">
    <div class="dashboard-header">
      <Logo />
      <div class="user-info">
        <span>Добро пожаловать, {{ user?.employeeId }}</span>
        <button @click="handleLogout" class="logout-btn">Выйти</button>
      </div>
    </div>
    
    <div class="dashboard-content">
      <!-- Welcome Section -->
      <div class="welcome-section">
        <div class="welcome-card">
          <h1>Панель управления сессиями</h1>
          <p>Табельный номер: {{ user?.employeeId }}</p>
          <div class="status">
            <span class="status-indicator"></span>
            Авторизация успешна
          </div>
        </div>

        <!-- Quick Actions -->
        <div class="quick-actions">
          <button @click="openCreateModal" class="create-session-btn">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
              <line x1="12" y1="5" x2="12" y2="19" stroke="currentColor" stroke-width="2"/>
              <line x1="5" y1="12" x2="19" y2="12" stroke="currentColor" stroke-width="2"/>
            </svg>
            Новая сессия
          </button>
          <!-- <button @click="refreshSessions" class="refresh-btn" :disabled="isLoading">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" :class="{ 'spinning': isLoading }">
              <polyline points="23,4 23,10 17,10" stroke="currentColor" stroke-width="2"/>
              <polyline points="1,20 1,14 7,14" stroke="currentColor" stroke-width="2"/>
              <path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4-4.64 4.36A9 9 0 0 1 3.51 15" stroke="currentColor" stroke-width="2"/>
            </svg>
            Обновить
          </button> -->
        </div>
      </div>

      <!-- Sessions Overview -->
      <div class="sessions-overview">
        <div class="overview-stats">
          <div class="stat-card">
            <div class="stat-icon draft">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" stroke="currentColor" stroke-width="2"/>
                <polyline points="14,2 14,8 20,8" stroke="currentColor" stroke-width="2"/>
              </svg>
            </div>
            <div class="stat-content">
              <div class="stat-number">{{ draftSessions.length }}</div>
              <div class="stat-label">Черновики</div>
            </div>
          </div>

          <div class="stat-card">
            <div class="stat-icon active">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                <polyline points="12,6 12,12 16,14" stroke="currentColor" stroke-width="2"/>
              </svg>
            </div>
            <div class="stat-content">
              <div class="stat-number">{{ activeSessions.length }}</div>
              <div class="stat-label">Активные</div>
            </div>
          </div>

          <div class="stat-card">
            <div class="stat-icon completed">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" stroke="currentColor" stroke-width="2"/>
                <polyline points="22,4 12,14.01 9,11.01" stroke="currentColor" stroke-width="2"/>
              </svg>
            </div>
            <div class="stat-content">
              <div class="stat-number">{{ completedSessions.length }}</div>
              <div class="stat-label">Завершённые</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Sessions List -->
      <div class="sessions-section">
        <div class="section-header">
          <h2>Сессии</h2>
          <div class="section-actions">
            <span class="sessions-count">Всего: {{ sessionsCount }}</span>
          </div>
        </div>

        <!-- Loading State -->
        <div v-if="isLoading && sessions.length === 0" class="loading-state">
          <div class="loading-spinner"></div>
          <p>Загрузка сессий...</p>
        </div>

        <!-- Sessions List -->
        <div v-else-if="sessions.length > 0" class="sessions-list">
          <div 
            v-for="session in sessions" 
            :key="session.id"
            class="session-card"
            @click="navigateToSession(session.id)"
          >
            <div class="session-header">
              <div class="session-info">
                <h3 class="session-title">{{ session.notes || 'Без названия' }}</h3>
                <div class="session-meta">
                  <span class="session-id">ID: {{ session.id.split('-')[1] }}</span>
                  <span class="session-date">{{ formatDate(session.created_at) }}</span>
                </div>
              </div>
              <div class="session-status" :class="getSessionStatusColor(session.status)">
                <span class="status-dot"></span>
                {{ getSessionStatusText(session.status) }}
              </div>
            </div>

            <div class="session-footer">
              <div class="session-timestamps">
                <span class="timestamp">Создана: {{ formatDateTime(session.created_at) }}</span>
                <span class="timestamp">Обновлена: {{ formatDateTime(session.updated_at) }}</span>
              </div>
              <div class="session-actions" @click.stop>
                <button class="session-btn" @click="navigateToSession(session.id)">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                    <path d="M9 18l6-6-6-6" stroke="currentColor" stroke-width="2"/>
                  </svg>
                  Открыть
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Empty State -->
        <div v-else class="empty-state">
          <div class="empty-icon">
            <svg width="64" height="64" viewBox="0 0 24 24" fill="none">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" stroke="currentColor" stroke-width="1.5"/>
              <polyline points="14,2 14,8 20,8" stroke="currentColor" stroke-width="1.5"/>
              <line x1="16" y1="13" x2="8" y2="13" stroke="currentColor" stroke-width="1.5"/>
              <line x1="16" y1="17" x2="8" y2="17" stroke="currentColor" stroke-width="1.5"/>
              <polyline points="10,9 9,9 8,9" stroke="currentColor" stroke-width="1.5"/>
            </svg>
          </div>
          <h3>Нет сессий</h3>
          <p>Создайте первую сессию для начала работы с системой</p>
          <button @click="openCreateModal" class="primary-button">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
              <line x1="12" y1="5" x2="12" y2="19" stroke="currentColor" stroke-width="2"/>
              <line x1="5" y1="12" x2="19" y2="12" stroke="currentColor" stroke-width="2"/>
            </svg>
            Создать сессию
          </button>
        </div>
      </div>
    </div>

    <!-- Create Session Modal -->
    <CreateSessionModal 
      :is-open="showCreateModal"
      @close="closeCreateModal"
      @created="handleSessionCreated"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useSessionStore } from '@/stores/sessions'
import CreateSessionModal from '@/components/CreateSessionModal.vue'
import Logo from '@/components/Logo.vue';

const router = useRouter()
const authStore = useAuthStore()
const sessionStore = useSessionStore()

const showCreateModal = ref(false)

const user = computed(() => authStore.user)
const sessions = computed(() => sessionStore.sessions)
const isLoading = computed(() => sessionStore.isLoading)
const sessionsCount = computed(() => sessionStore.sessionsCount)
const draftSessions = computed(() => sessionStore.draftSessions)
const activeSessions = computed(() => sessionStore.activeSessions)
const completedSessions = computed(() => sessionStore.completedSessions)

// Auto-refresh sessions every 30 seconds
let refreshInterval: NodeJS.Timeout | null = null

onMounted(async () => {
  await loadSessions()
  
  // Set up auto-refresh (disabled for better UX during active work)
  // refreshInterval = setInterval(() => {
  //   if (!showCreateModal.value) {
  //     loadSessions()
  //   }
  // }, 30000)
})

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
})

const loadSessions = async () => {
  try {
    await sessionStore.fetchSessions()
  } catch (error) {
    console.error('Failed to load sessions:', error)
  }
}

const refreshSessions = async () => {
  await loadSessions()
}

const openCreateModal = () => {
  showCreateModal.value = true
}

const closeCreateModal = () => {
  showCreateModal.value = false
}

const handleSessionCreated = (sessionId: string) => {
  // Modal will handle navigation, just refresh the list
  loadSessions()
}

const navigateToSession = (sessionId: string) => {
  router.push(`/sessions/${sessionId}`)
}

const handleLogout = () => {
  authStore.logout()
  router.push('/auth')
}

// Helper methods
const getSessionStatusText = (status: string): string => {
  return sessionStore.getSessionStatusText(status)
}

const getSessionStatusColor = (status: string): string => {
  const baseColor = sessionStore.getSessionStatusColor(status)
  // Remove 'text-' prefix and convert to CSS class
  return baseColor.replace('text-', '')
}

const formatDate = (dateString: string): string => {
  const date = new Date(dateString)
  return date.toLocaleDateString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric'
  })
}

const formatDateTime = (dateString: string): string => {
  const date = new Date(dateString)
  return date.toLocaleString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}
</script>

<style scoped>
.dashboard-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 40px;
  border-bottom: 1px solid rgba(71, 85, 105, 0.3);
  background: rgba(30, 41, 59, 0.8);
  backdrop-filter: blur(20px);
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 20px;
  font-weight: 600;
  color: #f1f5f9;
}

.logo svg {
  color: #3b82f6;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 16px;
  color: #cbd5e1;
}

.logout-btn {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 6px;
  padding: 8px 16px;
  cursor: pointer;
  transition: all 0.2s;
}

.logout-btn:hover {
  background: rgba(239, 68, 68, 0.2);
}

.dashboard-content {
  padding: 32px 40px;
  max-width: 1400px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 32px;
}

/* Welcome Section */
.welcome-section {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 24px;
  align-items: center;
}

.welcome-card {
  background: rgba(30, 41, 59, 0.8);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(71, 85, 105, 0.3);
  border-radius: 16px;
  padding: 32px;
}

.welcome-card h1 {
  color: #f1f5f9;
  font-size: 1.875rem;
  font-weight: 700;
  margin-bottom: 12px;
}

.welcome-card p {
  color: #94a3b8;
  font-size: 1rem;
  margin-bottom: 16px;
}

.status {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #10b981;
  font-weight: 500;
  font-size: 0.875rem;
}

.status-indicator {
  width: 8px;
  height: 8px;
  background: #10b981;
  border-radius: 50%;
  animation: pulse 2s infinite;
}

.quick-actions {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.create-session-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
  color: white;
  border: none;
  border-radius: 12px;
  padding: 16px 24px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.create-session-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 20px 40px -12px rgba(59, 130, 246, 0.4);
}

.refresh-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  background: rgba(71, 85, 105, 0.2);
  color: #cbd5e1;
  border: 1px solid rgba(71, 85, 105, 0.3);
  border-radius: 8px;
  padding: 12px 16px;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s;
}

.refresh-btn:hover:not(:disabled) {
  background: rgba(71, 85, 105, 0.3);
}

.refresh-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.spinning {
  animation: spin 1s linear infinite;
}

/* Sessions Overview */
.sessions-overview {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.overview-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
  background: rgba(30, 41, 59, 0.6);
  border: 1px solid rgba(71, 85, 105, 0.3);
  border-radius: 12px;
  padding: 24px;
}

.stat-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  border-radius: 12px;
  flex-shrink: 0;
}

.stat-icon.draft {
  background: rgba(100, 116, 139, 0.1);
  color: #64748b;
}

.stat-icon.active {
  background: rgba(59, 130, 246, 0.1);
  color: #3b82f6;
}

.stat-icon.completed {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
}

.stat-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stat-number {
  font-size: 2rem;
  font-weight: 700;
  color: #f1f5f9;
}

.stat-label {
  font-size: 0.875rem;
  color: #94a3b8;
}

/* Sessions Section */
.sessions-section {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.section-header h2 {
  font-size: 1.5rem;
  font-weight: 600;
  color: #f1f5f9;
  margin: 0;
}

.sessions-count {
  color: #94a3b8;
  font-size: 0.875rem;
}

/* Loading and Empty States */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: #94a3b8;
  text-align: center;
}

.loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid rgba(59, 130, 246, 0.3);
  border-top: 3px solid #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 16px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
}

.empty-icon {
  color: #475569;
  margin-bottom: 24px;
}

.empty-state h3 {
  color: #f1f5f9;
  font-size: 1.25rem;
  font-weight: 600;
  margin-bottom: 8px;
}

.empty-state p {
  color: #94a3b8;
  margin-bottom: 24px;
}

.primary-button {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
  color: white;
  border: none;
  border-radius: 8px;
  padding: 12px 24px;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.primary-button:hover {
  transform: translateY(-1px);
  box-shadow: 0 10px 20px -8px rgba(59, 130, 246, 0.4);
}

/* Sessions List */
.sessions-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.session-card {
  background: rgba(30, 41, 59, 0.6);
  border: 1px solid rgba(71, 85, 105, 0.3);
  border-radius: 12px;
  padding: 24px;
  cursor: pointer;
  transition: all 0.2s;
}

.session-card:hover {
  background: rgba(30, 41, 59, 0.8);
  transform: translateY(-1px);
  box-shadow: 0 10px 20px -8px rgba(0, 0, 0, 0.3);
}

.session-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.session-info {
  flex: 1;
}

.session-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: #f1f5f9;
  margin: 0 0 8px 0;
}

.session-meta {
  display: flex;
  align-items: center;
  gap: 16px;
}

.session-id {
  color: #64748b;
  font-size: 0.75rem;
  font-family: monospace;
}

.session-date {
  color: #94a3b8;
  font-size: 0.875rem;
}

.session-status {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.875rem;
  font-weight: 500;
  padding: 6px 12px;
  border-radius: 6px;
  border: 1px solid;
  white-space: nowrap;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: currentColor;
}

.session-status.gray-400 {
  color: #9ca3af;
  background: rgba(156, 163, 175, 0.1);
  border-color: rgba(156, 163, 175, 0.3);
}

.session-status.blue-400 {
  color: #60a5fa;
  background: rgba(96, 165, 250, 0.1);
  border-color: rgba(96, 165, 250, 0.3);
}

.session-status.yellow-400 {
  color: #fbbf24;
  background: rgba(251, 191, 36, 0.1);
  border-color: rgba(251, 191, 36, 0.3);
}

.session-status.green-400 {
  color: #34d399;
  background: rgba(52, 211, 153, 0.1);
  border-color: rgba(52, 211, 153, 0.3);
}

.session-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.session-timestamps {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.timestamp {
  color: #64748b;
  font-size: 0.75rem;
}

.session-actions {
  display: flex;
  gap: 8px;
}

.session-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  background: rgba(59, 130, 246, 0.1);
  color: #3b82f6;
  border: 1px solid rgba(59, 130, 246, 0.3);
  border-radius: 6px;
  padding: 8px 12px;
  font-size: 0.75rem;
  cursor: pointer;
  transition: all 0.2s;
}

.session-btn:hover {
  background: rgba(59, 130, 246, 0.2);
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

/* Responsive */
@media (max-width: 1024px) {
  .welcome-section {
    grid-template-columns: 1fr;
    gap: 20px;
  }
  
  .quick-actions {
    flex-direction: row;
    justify-content: center;
  }
  
  .overview-stats {
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  }
}

@media (max-width: 768px) {
  .dashboard-header {
    padding: 16px 20px;
    flex-direction: column;
    gap: 16px;
  }
  
  .dashboard-content {
    padding: 20px;
  }
  
  .welcome-card {
    padding: 24px;
  }
  
  .welcome-card h1 {
    font-size: 1.5rem;
  }
  
  .quick-actions {
    flex-direction: column;
  }
  
  .session-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  
  .session-footer {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  
  .session-meta {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
}
</style>
