<template>
  <div class="session-container">
    <!-- Navigation -->
    <nav class="navbar">
      <div class="nav-content">
        <router-link to="/dashboard" class="logo">
          <Logo />
        </router-link>
        <div class="nav-session-info" v-if="currentSession">
          <span class="session-name">{{ currentSession.notes || 'Без названия' }}</span>
          <div class="session-status" :class="getSessionStatusColor(currentSession.status)">
            <span class="status-dot"></span>
            {{ getSessionStatusText(currentSession.status) }}
          </div>
        </div>
      </div>
    </nav>

    <!-- Loading State -->
    <div v-if="isLoading && !currentSession" class="loading-section">
      <div class="loading-spinner"></div>
      <h2>Загрузка сессии...</h2>
      <p>Получение информации о сессии {{ $route.params.id }}</p>
    </div>

    <!-- Session Content -->
    <div v-else-if="currentSession" class="session-content">
      
      <!-- Session Header -->
      <div class="session-header">
        <div class="session-info">
          <h1 class="session-title">{{ currentSession.notes || 'Сессия без названия' }}</h1>
          <div class="session-meta">
            <span class="session-id">ID: {{ currentSession.id.split('-')[1] }}</span>
            <span class="session-employee">Сотрудник: {{ currentSession.employee_id }}</span>
            <span class="session-threshold">Порог: {{ Math.round(currentSession.threshold_used * 100) }}%</span>
          </div>
        </div>
      </div>

      <!-- Session Progress -->
      <div class="session-progress">
        <div class="progress-steps">
          <div class="step" :class="getStepClass('draft')">
            <div class="step-number">1</div>
            <div class="step-info">
              <span class="step-title">Создание</span>
              <span class="step-description">Настройка сессии</span>
            </div>
          </div>
          
          <div class="step-connector" :class="{ 'completed': isStepCompleted('draft') }"></div>
          
          <div class="step" :class="getStepClass('handout')">
            <div class="step-number">2</div>
            <div class="step-info">
              <span class="step-title">Выдача</span>
              <span class="step-description">Распознавание и разметка</span>
            </div>
          </div>
          
          <div class="step-connector" :class="{ 'completed': isStepCompleted('handout') }"></div>
          
          <div class="step" :class="getStepClass('issued')">
            <div class="step-number">3</div>
            <div class="step-info">
              <span class="step-title">Выдано</span>
              <span class="step-description">Инструменты выданы</span>
            </div>
          </div>
          
          <div class="step-connector" :class="{ 'completed': isStepCompleted('issued') }"></div>
          
          <div class="step" :class="getStepClass('handover')">
            <div class="step-number">4</div>
            <div class="step-info">
              <span class="step-title">Сдача</span>
              <span class="step-description">Проверка возврата</span>
            </div>
          </div>
          
          <div class="step-connector" :class="{ 'completed': isStepCompleted('handover') }"></div>
          
          <div class="step" :class="getStepClass('returned')">
            <div class="step-number">5</div>
            <div class="step-info">
              <span class="step-title">Сдано</span>
              <span class="step-description">Проверка инструментов</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Dynamic Content Based on Session Status -->
      
      <!-- Draft State: Upload for Handout -->
      <div v-if="currentSession.status === 'draft'" class="stage-content">
        <div class="stage-header">
          <h2>Выдача инструментов</h2>
          <p>Загрузите изображение с инструментами для начала процедуры выдачи</p>
        </div>
        
        <div class="upload-section">
          <div class="upload-area" @click="triggerFileInput" @drop="handleDrop" @dragover="handleDragOver" :class="{ 'processing': isProcessing }">
            <input
              ref="fileInput"
              type="file"
              accept="image/*"
              @change="handleFileSelect"
              class="file-input"
              :disabled="isProcessing"
            />
            <div v-if="isProcessing" class="upload-processing">
              <div class="loading-spinner"></div>
              <p>Идет обработка изображения...</p>
              <small>Это может занять некоторое время</small>
            </div>
            <div v-else class="upload-content">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" class="upload-icon">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" stroke="currentColor" stroke-width="2"/>
                <polyline points="17,8 12,3 7,8" stroke="currentColor" stroke-width="2"/>
                <line x1="12" y1="3" x2="12" y2="15" stroke="currentColor" stroke-width="2"/>
              </svg>
              <h3>Выберите изображение</h3>
              <p>Нажмите или перетащите файл изображения сюда</p>
              <small>Поддерживаемые форматы: JPG, PNG, WebP</small>
            </div>
          </div>
        </div>
      </div>

      <!-- Handout Processing/Manual State -->
      <div v-else-if="['handout_auto', 'handout_needs_manual'].includes(currentSession.status)" class="stage-content">
        <HandoutRecognition 
          :session="currentSession"
          @complete="handleHandoutComplete"
        />
      </div>

      <!-- Issued State: Ready for Handover -->
      <div v-else-if="currentSession.status === 'issued'" class="stage-content">
        <div class="stage-header">
          <h2>Инструменты выданы</h2>
          <p>Процедура выдачи завершена. Готовность к началу процедуры сдачи</p>
        </div>
        
        <div class="issued-summary">
          <div class="summary-card">
            <div class="summary-icon completed">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" stroke="currentColor" stroke-width="2"/>
                <polyline points="22,4 12,14.01 9,11.01" stroke="currentColor" stroke-width="2"/>
              </svg>
            </div>
            <div class="summary-content">
              <h3>Выдача завершена</h3>
              <p>Все 11 инструментов размечены и выданы</p>
              <div class="summary-meta" v-if="currentSession.handout?.issued_at">
                <span>Выдано: {{ formatDateTime(currentSession.handout.issued_at) }}</span>
              </div>
            </div>
          </div>
        </div>

        <div class="stage-actions">
          <h3>Начать процедуру сдачи</h3>
          <p>Загрузите изображение возвращаемых инструментов</p>
          
          <div class="upload-section">
            <div class="upload-area" @click="triggerHandoverFileInput" @drop="handleHandoverDrop" @dragover="handleDragOver" :class="{ 'processing': isProcessing }">
              <input
                ref="handoverFileInput"
                type="file"
                accept="image/*"
                @change="handleHandoverFileSelect"
                class="file-input"
                :disabled="isProcessing"
              />
              <div v-if="isProcessing" class="upload-processing">
                <div class="loading-spinner"></div>
                <p>Идет обработка изображения...</p>
                <small>Это может занять некоторое время</small>
              </div>
              <div v-else class="upload-content">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" class="upload-icon">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" stroke="currentColor" stroke-width="2"/>
                  <polyline points="7,10 12,15 17,10" stroke="currentColor" stroke-width="2"/>
                  <line x1="12" y1="15" x2="12" y2="3" stroke="currentColor" stroke-width="2"/>
                </svg>
                <h3>Выберите изображение для сдачи</h3>
                <p>Нажмите или перетащите файл изображения с возвращаемыми инструментами</p>
                <small>Поддерживаемые форматы: JPG, PNG, WebP</small>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Handover Processing/Manual State -->
      <div v-else-if="['handover_auto', 'handover_needs_manual'].includes(currentSession.status)" class="stage-content">
        <HandoverRecognition 
          :session="currentSession"
          @complete="handleHandoverComplete"
        />
      </div>

      <!-- Returned State: Show Differences -->
      <div v-else-if="currentSession.status === 'returned'" class="stage-content">
        <div class="stage-header">
          <h2>Инструменты сданы</h2>
          <p>Сравнение выданных и сданных инструментов для завершения сессии</p>
        </div>

        <SessionDiff 
          :session-id="currentSession.id"
        />
      </div>

    </div>

    <!-- Error State -->
    <div v-else class="error-section">
      <div class="error-icon">
        <svg width="64" height="64" viewBox="0 0 24 24" fill="none">
          <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
          <line x1="15" y1="9" x2="9" y2="15" stroke="currentColor" stroke-width="2"/>
          <line x1="9" y1="9" x2="15" y2="15" stroke="currentColor" stroke-width="2"/>
        </svg>
      </div>
      <h2>Сессия не найдена</h2>
      <p>Сессия с ID {{ $route.params.id }} не существует или недоступна</p>
      <button @click="$router.push('/dashboard')" class="primary-button">
        Вернуться к списку сессий
      </button>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useSessionStore } from '@/stores/sessions'
import { useNotificationStore } from '@/stores/notifications'
import { useRecognitionStore } from '@/stores/recognition'
import HandoutRecognition from '@/components/HandoutRecognition.vue'
import HandoverRecognition from '@/components/HandoverRecognition.vue'
import SessionDiff from '@/components/SessionDiff.vue'
import Logo from '@/components/Logo.vue'

const route = useRoute()
const router = useRouter()
const sessionStore = useSessionStore()
const notifications = useNotificationStore()
const recognitionStore = useRecognitionStore()

const fileInput = ref<HTMLInputElement | null>(null)
const handoverFileInput = ref<HTMLInputElement | null>(null)
const isProcessing = ref(false)

const sessionId = computed(() => route.params.id as string)
const currentSession = computed(() => sessionStore.currentSession)
const isLoading = computed(() => sessionStore.isLoading)

onMounted(async () => {
  await loadSession()
})

onUnmounted(() => {
  sessionStore.clearCurrentSession()
})

const loadSession = async () => {
  try {
    await sessionStore.fetchSession(sessionId.value)
  } catch (error) {
    console.error('Failed to load session:', error)
  }
}

// Step progress helpers
const isStepCompleted = (step: string): boolean => {
  if (!currentSession.value) return false
  
  const status = currentSession.value.status
  switch (step) {
    case 'draft': return status !== 'draft'
    case 'handout': return ['issued', 'handover_auto', 'handover_needs_manual', 'returned'].includes(status)
    case 'issued': return ['handover_auto', 'handover_needs_manual', 'returned'].includes(status)
    case 'handover': return status === 'returned'
    case 'returned': return status === 'returned'
    default: return false
  }
}

const getStepClass = (step: string): string => {
  if (!currentSession.value) return ''
  
  const status = currentSession.value.status
  if (step === 'draft' && status === 'draft') return 'current'
  if (step === 'handout' && ['handout_auto', 'handout_needs_manual'].includes(status)) return 'current'
  if (step === 'issued' && status === 'issued') return 'current'
  if (step === 'handover' && ['handover_auto', 'handover_needs_manual'].includes(status)) return 'current'
  
  if (isStepCompleted(step)) return 'completed'
  
  return ''
}

// File upload handlers for handout
const triggerFileInput = () => {
  if (!isProcessing.value) {
    fileInput.value?.click()
  }
}

const handleFileSelect = async (event: Event) => {
  const target = event.target as HTMLInputElement
  if (target.files && target.files[0]) {
    await processHandoutImage(target.files[0])
  }
}

const handleDrop = async (event: DragEvent) => {
  event.preventDefault()
  if (isProcessing.value) return
  
  const files = event.dataTransfer?.files
  if (files && files[0]) {
    await processHandoutImage(files[0])
  }
}

const handleDragOver = (event: DragEvent) => {
  event.preventDefault()
}

// File upload handlers for handover
const triggerHandoverFileInput = () => {
  if (!isProcessing.value) {
    handoverFileInput.value?.click()
  }
}

const handleHandoverFileSelect = async (event: Event) => {
  const target = event.target as HTMLInputElement
  if (target.files && target.files[0]) {
    await processHandoverImage(target.files[0])
  }
}

const handleHandoverDrop = async (event: DragEvent) => {
  event.preventDefault()
  if (isProcessing.value) return
  
  const files = event.dataTransfer?.files
  if (files && files[0]) {
    await processHandoverImage(files[0])
  }
}

// Image processing
const processHandoutImage = async (file: File) => {
  if (!currentSession.value) return
  
  isProcessing.value = true
  try {
    const base64Image = await fileToBase64(file)
    
    // Store handout image data for the HandoutRecognition component
    recognitionStore.setRecognitionData({
      image: base64Image,
      threshold: currentSession.value.threshold_used * 100,
      fileName: file.name,
      fileSize: file.size,
      timestamp: Date.now()
    })
    
    await sessionStore.handoutPredict(sessionId.value, {
      image: base64Image,
      threshold: currentSession.value.threshold_used
    })
  } catch (error) {
    console.error('Failed to process handout image:', error)
  } finally {
    isProcessing.value = false
  }
}

const processHandoverImage = async (file: File) => {
  if (!currentSession.value) return
  
  isProcessing.value = true
  try {
    const base64Image = await fileToBase64(file)
    
    // Store handover image data for the HandoverRecognition component
    recognitionStore.setRecognitionData({
      image: base64Image,
      threshold: currentSession.value.threshold_used * 100,
      fileName: file.name,
      fileSize: file.size,
      timestamp: Date.now()
    })
    
    await sessionStore.handoverPredict(sessionId.value, {
      image: base64Image,
      threshold: currentSession.value.threshold_used
    })
  } catch (error) {
    console.error('Failed to process handover image:', error)
  } finally {
    isProcessing.value = false
  }
}

const fileToBase64 = (file: File): Promise<string> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => {
      const result = reader.result as string
      resolve(result)
    }
    reader.onerror = reject
    reader.readAsDataURL(file)
  })
}

// Event handlers
const handleHandoutComplete = () => {
  loadSession()
}

const handleHandoverComplete = () => {
  loadSession()
}

// Helper methods
const getSessionStatusText = (status: string): string => {
  return sessionStore.getSessionStatusText(status)
}

const getSessionStatusColor = (status: string): string => {
  const baseColor = sessionStore.getSessionStatusColor(status)
  return baseColor.replace('text-', '')
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
.session-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

/* Navigation */
.navbar {
  position: sticky;
  top: 0;
  z-index: 100;
  background: rgba(30, 41, 59, 0.95);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(71, 85, 105, 0.3);
}

.nav-content {
  max-width: 1400px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 20px;
  font-weight: 700;
  color: #f1f5f9;
  text-decoration: none;
  transition: all 0.2s;
}

.logo:hover {
  color: #e2e8f0;
  transform: translateY(-1px);
}

.logo svg {
  color: #3b82f6;
}

.nav-session-info {
  display: flex;
  align-items: center;
  gap: 16px;
}

.session-name {
  color: #f1f5f9;
  font-weight: 600;
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
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: currentColor;
}

/* Status colors */
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

/* Loading State */
.loading-section {
  padding: 120px 0;
  text-align: center;
  color: #f1f5f9;
}

.loading-spinner {
  width: 48px;
  height: 48px;
  border: 4px solid rgba(59, 130, 246, 0.3);
  border-top: 4px solid #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 32px;
}

.loading-section h2 {
  font-size: 1.5rem;
  font-weight: 600;
  margin-bottom: 12px;
}

.loading-section p {
  color: #94a3b8;
}

/* Session Content */
.session-content {
  max-width: 1400px;
  margin: 0 auto;
  padding: 32px 24px;
}

/* Session Header */
.session-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32px;
  padding-bottom: 24px;
  border-bottom: 1px solid rgba(71, 85, 105, 0.3);
}

.session-title {
  font-size: 2rem;
  font-weight: 700;
  color: #f1f5f9;
  margin-bottom: 8px;
}

.session-meta {
  display: flex;
  gap: 24px;
  color: #94a3b8;
  font-size: 0.875rem;
}

.session-id {
  font-family: monospace;
}

/* Session Progress */
.session-progress {
  margin-bottom: 40px;
}

.progress-steps {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px 0;
}

.step {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  position: relative;
}

.step-number {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  margin-bottom: 12px;
  background: rgba(71, 85, 105, 0.3);
  color: #94a3b8;
  border: 2px solid rgba(71, 85, 105, 0.3);
}

.step-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.step-title {
  font-weight: 600;
  color: #cbd5e1;
  font-size: 0.875rem;
}

.step-description {
  color: #64748b;
  font-size: 0.75rem;
}

.step.current .step-number {
  background: #3b82f6;
  color: white;
  border-color: #3b82f6;
}

.step.current .step-title {
  color: #3b82f6;
}

.step.completed .step-number {
  background: #10b981;
  color: white;
  border-color: #10b981;
}

.step.completed .step-title {
  color: #10b981;
}

.step-connector {
  width: 60px;
  height: 2px;
  background: rgba(71, 85, 105, 0.3);
  margin: 0 16px;
}

.step-connector.completed {
  background: #10b981;
}

/* Stage Content */
.stage-content {
  background: rgba(30, 41, 59, 0.6);
  border: 1px solid rgba(71, 85, 105, 0.3);
  border-radius: 16px;
  padding: 32px;
}

.stage-header {
  text-align: center;
  margin-bottom: 32px;
}

.stage-header h2 {
  font-size: 1.75rem;
  font-weight: 600;
  color: #f1f5f9;
  margin-bottom: 8px;
}

.stage-header p {
  color: #94a3b8;
  font-size: 1rem;
}

/* Upload Section */
.upload-section {
  max-width: 600px;
  margin: 0 auto;
}

.upload-area {
  border: 2px dashed rgba(71, 85, 105, 0.5);
  border-radius: 12px;
  padding: 48px 24px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
}

.upload-area:not(.processing):hover {
  border-color: #3b82f6;
  background: rgba(59, 130, 246, 0.05);
}

.upload-area.processing {
  cursor: wait;
  border-color: #3b82f6;
}

.file-input {
  display: none;
}

.upload-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.upload-icon {
  color: #64748b;
}

.upload-area:not(.processing):hover .upload-icon {
  color: #3b82f6;
}

.upload-content h3 {
  color: #f1f5f9;
  font-size: 1.25rem;
  font-weight: 600;
  margin: 0;
}

.upload-content p {
  color: #94a3b8;
  margin: 0;
}

.upload-content small {
  color: #64748b;
  font-size: 0.75rem;
}

.upload-processing {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: #94a3b8;
}

.upload-processing .loading-spinner {
  margin: 0;
  width: 32px;
  height: 32px;
  border-width: 3px;
}

.upload-processing p {
  font-size: 1rem;
  font-weight: 500;
  color: #cbd5e1;
  margin: 0;
}

.upload-processing small {
  color: #64748b;
  font-size: 0.875rem;
}

/* Issued Summary */
.issued-summary {
  max-width: 600px;
  margin: 0 auto 32px;
}

.summary-card {
  display: flex;
  align-items: center;
  gap: 20px;
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(71, 85, 105, 0.3);
  border-radius: 12px;
  padding: 24px;
}

.summary-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 56px;
  height: 56px;
  border-radius: 12px;
  flex-shrink: 0;
}

.summary-icon.completed {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
}

.summary-content h3 {
  color: #f1f5f9;
  font-size: 1.25rem;
  font-weight: 600;
  margin-bottom: 8px;
}

.summary-content p {
  color: #94a3b8;
  margin-bottom: 12px;
}

.summary-meta {
  color: #64748b;
  font-size: 0.875rem;
}

/* Stage Actions */
.stage-actions {
  margin-top: 32px;
  text-align: center;
}

.stage-actions h3 {
  color: #f1f5f9;
  font-size: 1.25rem;
  font-weight: 600;
  margin-bottom: 8px;
}

.stage-actions p {
  color: #94a3b8;
  margin-bottom: 24px;
}

/* Error State */
.error-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 120px 20px;
  text-align: center;
}

.error-icon {
  color: #ef4444;
  margin-bottom: 24px;
}

.error-section h2 {
  color: #f1f5f9;
  font-size: 1.5rem;
  font-weight: 600;
  margin-bottom: 12px;
}

.error-section p {
  color: #94a3b8;
  margin-bottom: 32px;
}

.primary-button {
  display: inline-flex;
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

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* Responsive */
@media (max-width: 768px) {
  .nav-content {
    padding: 12px 16px;
  }
  
  .session-content {
    padding: 20px 16px;
  }
  
  .session-header {
    flex-direction: column;
    gap: 16px;
    align-items: flex-start;
  }
  
  .session-meta {
    flex-direction: column;
    gap: 8px;
  }
  
  .progress-steps {
    flex-wrap: wrap;
    gap: 16px;
  }
  
  .step-connector {
    display: none;
  }
  
  .stage-content {
    padding: 24px 20px;
  }
  
  .upload-area {
    padding: 32px 20px;
  }
  
  .summary-card {
    flex-direction: column;
    text-align: center;
  }
}
</style>
