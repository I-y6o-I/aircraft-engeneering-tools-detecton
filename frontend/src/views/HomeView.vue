<template>
  <div class="home-container">
    <!-- Navigation -->
    <nav class="navbar">
      <div class="nav-content">
        <Logo />
        <router-link to="/auth" class="login-btn">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
            <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4" stroke="currentColor" stroke-width="2"/>
            <polyline points="10,17 15,12 10,7" stroke="currentColor" stroke-width="2"/>
            <line x1="15" y1="12" x2="3" y2="12" stroke="currentColor" stroke-width="2"/>
          </svg>
          Вход
        </router-link>
      </div>
    </nav>

    <!-- Main Content -->
    <main class="main-content">
      <div class="hero-section">
        <div class="hero-text">
          <h1 class="hero-title">
            Автоматизация приёма и выдачи
            <span class="gradient-text">авиационных инструментов</span>
          </h1>
          <p class="hero-subtitle">

          </p>
        </div>

        <!-- Photo Upload Section -->
        <div class="upload-section">
          <div class="upload-area" :class="{ 'drag-over': isDragOver }" 
               @drop="handleDrop" 
               @dragover="handleDragOver" 
               @dragenter="handleDragEnter"
               @dragleave="handleDragLeave"
               @click="triggerFileInput">
            
            <input ref="fileInput" 
                   type="file" 
                   accept="image/*" 
                   @change="handleFileSelect" 
                   class="file-input">

            <div v-if="!selectedFiles.length" class="upload-placeholder">
              <div class="upload-icon">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" stroke="currentColor" stroke-width="2"/>
                  <polyline points="17,8 12,3 7,8" stroke="currentColor" stroke-width="2"/>
                  <line x1="12" y1="3" x2="12" y2="15" stroke="currentColor" stroke-width="2"/>
                </svg>
              </div>
              <h3 class="upload-title">Загрузите фотографию комплекта инструментов</h3>
              <p class="upload-text">
                Выберите или перетащите фотографию для <span class="upload-link">автоматической идентификации</span>
              </p>
              <p class="upload-formats">PNG, JPG, JPEG до 10MB</p>
            </div>

            <div v-else class="uploaded-files">
              <h3 class="files-title">Загруженный файл</h3>
              <div class="single-file">
                <div class="file-preview">
                  <img :src="selectedFiles[0].preview" :alt="selectedFiles[0].name" class="preview-image">
                  <button @click.stop="removeFile(0)" class="remove-btn">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                      <line x1="18" y1="6" x2="6" y2="18" stroke="currentColor" stroke-width="2"/>
                      <line x1="6" y1="6" x2="18" y2="18" stroke="currentColor" stroke-width="2"/>
                    </svg>
                  </button>
                </div>
                <div class="file-info">
                  <p class="file-name">{{ selectedFiles[0].name }}</p>
                  <p class="file-size">{{ formatFileSize(selectedFiles[0].size) }}</p>
                </div>
              </div>
              
              <!-- Confidence Threshold Section -->
              <div class="confidence-section" @click.stop>
                <h4 class="confidence-title">Калибровка порога уверенности</h4>
                <div class="confidence-controls">
                  <div class="confidence-slider-container">
                    <label for="confidenceSlider" class="confidence-label">
                      Порог уверенности: <span class="confidence-value">{{ confidenceThreshold }}%</span>
                    </label>
                    <input 
                      id="confidenceSlider"
                      v-model="confidenceThreshold" 
                      type="range" 
                      min="1" 
                      max="100" 
                      step="1" 
                      class="confidence-slider"
                      @click.stop
                    />
                    <div class="confidence-marks">
                      <span class="mark-label">10%</span>
                      <span class="mark-label">25%</span>
                      <span class="mark-label">50%</span>
                      <span class="mark-label">75%</span>
                      <span class="mark-label">99%</span>
                    </div>
                  </div>
                  <div class="confidence-info">
                    <div class="confidence-description">
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" class="info-icon">
                        <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                        <path d="M9,9h0a3,3,0,0,1,6,0c0,2-3,3-3,3" stroke="currentColor" stroke-width="2"/>
                        <path d="M12,17h.01" stroke="currentColor" stroke-width="2"/>
                      </svg>
                      <span v-if="confidenceThreshold >= 80" class="confidence-text">
                        Высокий порог: будут показаны только инструменты с очень высокой уверенностью
                      </span>
                      <span v-else-if="confidenceThreshold >= 50" class="confidence-text">
                        Средний порог: баланс между точностью и количеством найденных инструментов
                      </span>
                      <span v-else class="confidence-text">
                        Низкий порог: будут показаны все возможные инструменты, включая сомнительные
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div v-if="selectedFiles.length" class="action-section">
            <button class="analyze-btn" @click="handleAnalyze">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                <path d="M9 12l2 2 4-4" stroke="currentColor" stroke-width="2"/>
                <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
              </svg>
              Провести распознавание
            </button>
            <p class="analyze-note">
              Система автоматически распознает инструменты на фотографии и покажет их список
            </p>
          </div>
        </div>
      </div>

      <!-- Tools Showcase -->
      <div class="tools-showcase-section">
        <h2 class="tools-showcase-title">Всего 11 типов/классов инструментов</h2>
        <div class="tools-scroll-container">
          <div class="tools-list">
            <div v-for="tool in tools" :key="tool.name" class="tool-card">
              <div class="tool-image-container">
                <img :src="tool.image" :alt="tool.name" class="tool-image" />
              </div>
              <p class="tool-name">{{ tool.name }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Features Section -->
      <!-- <div class="features-section">
        <div class="features-grid">
          <div class="feature-card">
            <div class="feature-icon">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none">
                <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z" stroke="currentColor" stroke-width="2"/>
              </svg>
            </div>
            <h3>Распознавание инструментов</h3>
            <p>Автоматическая идентификация гаечных ключей, отвёрток, насадок и другого авиационного оборудования</p>
          </div>

          <div class="feature-card">
            <div class="feature-icon">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none">
                <path d="M22 12h-4l-3 9L9 3l-3 9H2" stroke="currentColor" stroke-width="2"/>
              </svg>
            </div>
            <h3>Контроль качества</h3>
            <p>Автоматический запуск ручной проверки при расхождениях свыше допустимого порога</p>
          </div>

          <div class="feature-card">
            <div class="feature-icon">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none">
                <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2" stroke="currentColor" stroke-width="2"/>
                <rect x="8" y="2" width="8" height="4" rx="1" ry="1" stroke="currentColor" stroke-width="2"/>
                <path d="M9 12l2 2 4-4" stroke="currentColor" stroke-width="2"/>
              </svg>
            </div>
            <h3>Сверка с складом</h3>
            <p>Автоматическое сравнение полученного комплекта с выданным или заказанным на складе</p>
          </div>
        </div>
      </div> -->
    </main>

    <footer class="footer">
      <div class="footer-content">
        <p class="footer-text">Партнёры и организаторы проекта</p>
        <div class="footer-logos">
          <img src="/footer/departament_moscow.png" alt="Департамент транспорта и развития дорожно-транспортной инфраструктуры города Москвы" class="footer-logo">
          <img src="/footer/lct_fest.png" alt="Leaders of digital transformation" class="footer-logo">
          <img src="/footer/aeroflot.png" alt="Аэрофлот" class="footer-logo">
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useNotificationStore } from '@/stores/notifications'
import { useRecognitionStore } from '@/stores/recognition'
import Logo from '@/components/Logo.vue';

const tools = ref([
  { name: 'Отвертка минусовая', image: '/instruments/отвертка_минусовая.png' },
  { name: 'Отвертка плюсовая', image: '/instruments/отвертка_плюсовая.png' },
  { name: 'Отвертка со смещенным крестом', image: '/instruments/отвертка_со_смещенным_крестом.png' },
  { name: 'Пассатижи', image: '/instruments/пассатижи.png' },
  { name: 'Пассатижи контровочные', image: '/instruments/пассатижи_контровочные.png' },
  { name: 'Шерница', image: '/instruments/шерница.png' },
  { name: 'Разводной ключ', image: '/instruments/разводной_ключ.png' },
  { name: 'Ключ рожковый накидной 3/4', image: '/instruments/ключ_рожковый_накидной_3_на_4.png' },
  { name: 'Коловорот', image: '/instruments/коловорот.png' },
  { name: 'Бокорезы', image: '/instruments/бокорезы.png' },
  { name: 'Открывашка для банок с маслом', image: '/instruments/открывашка_для_банок_с_маслом.png' },
])

const router = useRouter()
const notifications = useNotificationStore()
const recognitionStore = useRecognitionStore()

interface FileWithPreview extends File {
  preview: string
}

const fileInput = ref<HTMLInputElement | null>(null)
const selectedFiles = ref<FileWithPreview[]>([])
const isDragOver = ref(false)
const confidenceThreshold = ref(98)

const triggerFileInput = () => {
  fileInput.value?.click()
}

const handleFileSelect = (event: Event) => {
  const target = event.target as HTMLInputElement
  if (target.files && target.files[0]) {
    addFile(target.files[0])
  }
}

const handleDrop = (event: DragEvent) => {
  event.preventDefault()
  isDragOver.value = false
  
  if (event.dataTransfer?.files && event.dataTransfer.files[0]) {
    addFile(event.dataTransfer.files[0])
  }
}

const handleDragOver = (event: DragEvent) => {
  event.preventDefault()
}

const handleDragEnter = (event: DragEvent) => {
  event.preventDefault()
  isDragOver.value = true
}

const handleDragLeave = (event: DragEvent) => {
  event.preventDefault()
  // Only set to false if we're leaving the upload area completely
  const currentTarget = event.currentTarget as HTMLElement
  const relatedTarget = event.relatedTarget as Node
  if (currentTarget && !currentTarget.contains(relatedTarget)) {
    isDragOver.value = false
  }
}

const addFile = (file: File) => {
  // Check if it's an image
  if (!file.type.startsWith('image/')) {
    notifications.warning('Пожалуйста, выберите изображение в формате PNG, JPG или JPEG.', {
      title: 'Неподдерживаемый формат файла'
    })
    return
  }

  // Create preview
  const reader = new FileReader()
  reader.onload = (e) => {
    const fileWithPreview = file as FileWithPreview
    fileWithPreview.preview = e.target?.result as string
    selectedFiles.value = [fileWithPreview] // Replace any existing file
  }
  reader.readAsDataURL(file)

  // Reset file input
  if (fileInput.value) {
    fileInput.value.value = ''
  }
}

const removeFile = (index: number) => {
  selectedFiles.value = []
}

const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const handleAnalyze = () => {
  if (!selectedFiles.value.length) {
    notifications.info('Пожалуйста, выберите изображение для анализа.', {
      title: 'Файл не выбран'
    })
    return
  }

  const file = selectedFiles.value[0]
  const imageData = file.preview
  const threshold = confidenceThreshold.value

  // Store image data in sessionStorage to avoid URL length limits
  const recognitionData = {
    image: imageData,
    threshold: threshold,
    fileName: file.name,
    fileSize: file.size,
    timestamp: Date.now()
  }
  
  recognitionStore.setRecognitionData(recognitionData)
  // sessionStorage.setItem('aero-kit-recognition-data', JSON.stringify(recognitionData))

  // Navigate to recognition page
  router.push('/recognition')
}

// Cleanup object URLs when component unmounts
onUnmounted(() => {
  selectedFiles.value.forEach(file => {
    URL.revokeObjectURL(file.preview)
  })
})
</script>

<style scoped>
.home-container {
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
  max-width: 1200px;
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
  font-size: 24px;
  font-weight: 700;
  color: #f1f5f9;
}

.logo svg {
  color: #3b82f6;
}

.login-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(59, 130, 246, 0.1);
  color: #3b82f6;
  border: 1px solid rgba(59, 130, 246, 0.3);
  border-radius: 8px;
  padding: 10px 20px;
  text-decoration: none;
  font-weight: 600;
  transition: all 0.2s;
}

.login-btn:hover {
  background: rgba(59, 130, 246, 0.2);
  transform: translateY(-1px);
}

/* Main Content */
.main-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 24px;
}

.hero-section {
  padding: 80px 0;
  text-align: center;
}

.hero-text {
  margin-bottom: 60px;
}

.hero-title {
  font-size: 3.5rem;
  font-weight: 800;
  color: #f1f5f9;
  line-height: 1.1;
  margin-bottom: 24px;
}

.gradient-text {
  background: linear-gradient(135deg, #3b82f6 0%, #06b6d4 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero-subtitle {
  font-size: 1.25rem;
  color: #94a3b8;
  line-height: 1.6;
  max-width: 600px;
  margin: 0 auto;
}

/* Upload Section */
.upload-section {
  max-width: 800px;
  margin: 0 auto;
}

.upload-area {
  background: rgba(30, 41, 59, 0.6);
  backdrop-filter: blur(20px);
  border: 2px dashed rgba(71, 85, 105, 0.5);
  border-radius: 16px;
  padding: 60px 40px;
  cursor: pointer;
  transition: all 0.3s;
  position: relative;
}

.upload-area:hover,
.upload-area.drag-over {
  border-color: #3b82f6;
  background: rgba(59, 130, 246, 0.05);
}

.file-input {
  display: none;
}

.upload-placeholder {
  text-align: center;
}

.upload-icon {
  color: #64748b;
  margin-bottom: 24px;
}

.upload-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: #f1f5f9;
  margin-bottom: 12px;
}

.upload-text {
  color: #94a3b8;
  font-size: 1rem;
  margin-bottom: 8px;
}

.upload-link {
  color: #3b82f6;
  font-weight: 600;
}

.upload-formats {
  color: #64748b;
  font-size: 0.875rem;
}

/* Uploaded Files */
.uploaded-files {
  text-align: center;
}

.files-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: #f1f5f9;
  margin-bottom: 24px;
}

.single-file {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 20px;
  background: rgba(30, 41, 59, 0.6);
  border-radius: 12px;
  border: 1px solid rgba(71, 85, 105, 0.3);
}

.file-preview {
  position: relative;
  flex-shrink: 0;
}

.preview-image {
  width: 120px;
  height: 120px;
  object-fit: cover;
  border-radius: 8px;
  border: 1px solid rgba(71, 85, 105, 0.3);
}

.remove-btn {
  position: absolute;
  top: 4px;
  right: 4px;
  background: rgba(239, 68, 68, 0.9);
  color: white;
  border: none;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
}

.remove-btn:hover {
  background: #ef4444;
}

.file-info {
  flex: 1;
  text-align: left;
}

.file-name {
  color: #f1f5f9;
  font-size: 1rem;
  font-weight: 500;
  margin-bottom: 8px;
  word-break: break-word;
}

.file-size {
  color: #64748b;
  font-size: 0.875rem;
}

/* Confidence Threshold Section */
.confidence-section {
  margin-top: 24px;
  padding: 20px;
  background: rgba(15, 23, 42, 0.6);
  border-radius: 12px;
  border: 1px solid rgba(71, 85, 105, 0.3);
}

.confidence-title {
  color: #f1f5f9;
  font-size: 1.125rem;
  font-weight: 600;
  margin-bottom: 16px;
  text-align: center;
}

.confidence-controls {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.confidence-slider-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.confidence-label {
  color: #cbd5e1;
  font-size: 0.875rem;
  font-weight: 500;
  text-align: center;
}

.confidence-value {
  color: #3b82f6;
  font-weight: 700;
}

.confidence-slider {
  width: 100%;
  height: 6px;
  background: rgba(71, 85, 105, 0.3);
  border-radius: 3px;
  outline: none;
  cursor: pointer;
  -webkit-appearance: none;
  appearance: none;
}

.confidence-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 20px;
  height: 20px;
  background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
  border-radius: 50%;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3);
  transition: all 0.2s;
}

.confidence-slider::-webkit-slider-thumb:hover {
  transform: scale(1.1);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
}

.confidence-slider::-moz-range-thumb {
  width: 20px;
  height: 20px;
  background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
  border-radius: 50%;
  cursor: pointer;
  border: none;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3);
}

.confidence-marks {
  display: flex;
  justify-content: space-between;
  padding: 0 10px;
}

.mark-label {
  color: #64748b;
  font-size: 0.75rem;
  font-weight: 500;
}

.confidence-info {
  display: flex;
  justify-content: center;
}

.confidence-description {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: rgba(30, 41, 59, 0.6);
  border-radius: 8px;
  border: 1px solid rgba(71, 85, 105, 0.3);
  max-width: 400px;
}

.info-icon {
  color: #3b82f6;
  flex-shrink: 0;
}

.confidence-text {
  color: #cbd5e1;
  font-size: 0.875rem;
  line-height: 1.4;
}

/* Action Section */
.action-section {
  margin-top: 32px;
  text-align: center;
}

.analyze-btn {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
  color: white;
  border: none;
  border-radius: 12px;
  padding: 16px 32px;
  font-size: 1.125rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  margin-bottom: 12px;
}

.analyze-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 20px 40px -12px rgba(59, 130, 246, 0.4);
}

.analyze-note {
  color: #64748b;
  font-size: 0.875rem;
}

/* Tools Showcase Section */
.tools-showcase-section {
  padding-bottom: 80px;
  text-align: center;
}

.tools-showcase-title {
  font-size: 2rem;
  font-weight: 700;
  color: #f1f5f9;
  margin-bottom: 40px;
}

.tools-scroll-container {
  position: relative;
}

.tools-scroll-container::before,
.tools-scroll-container::after {
  content: '';
  position: absolute;
  top: 0;
  bottom: 0;
  width: 100px;
  z-index: 2;
  pointer-events: none;
}

.tools-scroll-container::before {
  left: -24px;
  background: linear-gradient(to right, #1e293b 20%, transparent);
}

.tools-scroll-container::after {
  right: -24px;
  background: linear-gradient(to left, #1e293b 20%, transparent);
}


.tools-list {
  display: flex;
  overflow-x: auto;
  padding: 20px 0;
  gap: 24px;
  -ms-overflow-style: none;
  scrollbar-width: none;
  -webkit-overflow-scrolling: touch;
}

.tools-list::-webkit-scrollbar {
  display: none;
}

.tool-card {
  flex: 0 0 auto;
  width: 200px;
  background: rgba(30, 41, 59, 0.6);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(71, 85, 105, 0.3);
  border-radius: 16px;
  padding: 24px;
  text-align: center;
  transition: all 0.3s;
}

.tool-card:hover {
  transform: translateY(-8px);
  border-color: rgba(59, 130, 246, 0.4);
  box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2);
}

.tool-image-container {
  height: 120px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 20px;
}

.tool-image {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
  -webkit-user-drag: none;
  user-select: none;
}

.tool-name {
  color: #cbd5e1;
  font-size: 0.9rem;
  font-weight: 500;
  line-height: 1.4;
  height: 40px; /* To align names even if they wrap to 2 lines */
  display: flex;
  align-items: center;
  justify-content: center;
}

/* Footer */
.footer {
  padding: 60px 0;
  border-top: 1px solid rgba(71, 85, 105, 0.3);
}

.footer-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 24px;
  text-align: center;
}

.footer-text {
  font-size: 1.25rem;
  font-weight: 600;
  color: #cbd5e1;
  margin-bottom: 32px;
}

.footer-logos {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 60px;
  flex-wrap: wrap;
}

.footer-logo {
  max-height: 50px;
  opacity: 0.9;
  transition: all 0.3s;
  filter: grayscale(50%);
}

.footer-logo:hover {
  opacity: 1;
  filter: grayscale(0%);
  transform: scale(1.05);
}

/* Features Section */
.features-section {
  padding: 80px 0;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 32px;
}

.feature-card {
  background: rgba(30, 41, 59, 0.6);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(71, 85, 105, 0.3);
  border-radius: 16px;
  padding: 32px;
  text-align: center;
  transition: all 0.3s;
}

.feature-card:hover {
  transform: translateY(-4px);
  border-color: rgba(59, 130, 246, 0.3);
}

.feature-icon {
  color: #3b82f6;
  margin-bottom: 20px;
}

.feature-card h3 {
  font-size: 1.25rem;
  font-weight: 600;
  color: #f1f5f9;
  margin-bottom: 12px;
}

.feature-card p {
  color: #94a3b8;
  line-height: 1.6;
}

/* Responsive Design */
@media (max-width: 768px) {
  .nav-content {
    padding: 12px 16px;
  }
  
  .logo {
    font-size: 20px;
  }
  
  .main-content {
    padding: 0 16px;
  }
  
  .hero-section {
    padding: 60px 0;
  }
  
  .hero-title {
    font-size: 2.5rem;
  }
  
  .hero-subtitle {
    font-size: 1.125rem;
  }
  
  .upload-area {
    padding: 40px 20px;
  }
  
  .single-file {
    flex-direction: column;
    text-align: center;
    gap: 16px;
  }
  
  .file-info {
    text-align: center;
  }
  
  .confidence-section {
    margin-top: 20px;
    padding: 16px;
  }
  
  .confidence-title {
    font-size: 1rem;
    margin-bottom: 12px;
  }
  
  .confidence-description {
    padding: 10px 12px;
    max-width: 100%;
  }
  
  .confidence-text {
    font-size: 0.8125rem;
  }

  .tools-showcase-section {
    padding-bottom: 60px;
  }

  .tools-showcase-title {
    font-size: 1.5rem;
  }

  .tool-card {
    width: 160px;
    padding: 16px;
  }

  .tools-scroll-container::before {
    left: -16px;
  }

  .tools-scroll-container::after {
    right: -16px;
  }
  
  .features-section {
    padding: 60px 0;
  }
  
  .features-grid {
    grid-template-columns: 1fr;
    gap: 24px;
  }
  
  .feature-card {
    padding: 24px;
  }
  
  .footer {
    padding: 40px 0;
  }

  .footer-text {
    font-size: 1.125rem;
    margin-bottom: 24px;
  }

  .footer-logos {
    gap: 40px;
  }

  .footer-logo {
    max-height: 40px;
  }
}

@media (max-width: 480px) {
  .hero-title {
    font-size: 2rem;
  }
  
  .upload-area {
    padding: 30px 16px;
  }
  
  .analyze-btn {
    padding: 14px 24px;
    font-size: 1rem;
  }
  
  .tools-showcase-title {
    font-size: 1.25rem;
  }

  .tool-card {
    width: 140px;
  }

  .tool-image-container {
    height: 100px;
  }
  
  .tool-name {
    font-size: 0.8rem;
  }
  
  .footer-logo {
    max-height: 35px;
  }
}
</style>
