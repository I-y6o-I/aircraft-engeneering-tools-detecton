<template>
  <div class="diff-container">
    <!-- Loading State -->
    <div v-if="isLoading" class="loading-state">
      <div class="loading-spinner"></div>
      <p>Анализ различий между выдачей и сдачей...</p>
    </div>

    <!-- Diff Results -->
    <div v-else-if="diffData" class="diff-content">
      <!-- Summary Header -->
      <div class="diff-header">
        <div class="diff-summary">
          <div class="summary-card" :class="{ 'has-issues': hasDiscrepancies }">
            <div class="summary-icon" :class="{ 'success': !hasDiscrepancies, 'warning': hasDiscrepancies }">
              <svg v-if="!hasDiscrepancies" width="32" height="32" viewBox="0 0 24 24" fill="none">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" stroke="currentColor" stroke-width="2"/>
                <polyline points="22,4 12,14.01 9,11.01" stroke="currentColor" stroke-width="2"/>
              </svg>
              <svg v-else width="32" height="32" viewBox="0 0 24 24" fill="none">
                <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" stroke="currentColor" stroke-width="2"/>
                <line x1="12" y1="9" x2="12" y2="13" stroke="currentColor" stroke-width="2"/>
                <circle cx="12" cy="17" r="1" fill="currentColor"/>
              </svg>
            </div>
            <div class="summary-content">
              <h2 v-if="!hasDiscrepancies">Все инструменты сданы</h2>
              <h2 v-else>Обнаружены расхождения</h2>
              <p v-if="!hasDiscrepancies">
                Все 11 инструментов были успешно возвращены
              </p>
              <p v-else>
                {{ diffData.missing.length }} {{ getInstrumentWord(diffData.missing.length) }} 
                {{ diffData.missing.length === 1 ? 'не был сдан' : 'не было сдано' }}
              </p>
            </div>
          </div>
        </div>

        <div class="action-section">
          <button @click="router.push('/dashboard')" class="finalize-btn back-btn">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
              <path d="M19 12H5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M12 19l-7-7 7-7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            Вернуться к списку сессий
          </button>
        </div>
      </div>
      
      <!-- Image Comparison -->
      <div class="image-comparison-section" v-if="handoutImage || handoverImage">
        <div v-if="handoutImage" class="image-display">
          <h3 class="section-title image-title">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="17 8 12 3 7 8"></polyline><line x1="12" y1="3" x2="12" y2="15"></line></svg>
            Изображение выдачи
          </h3>
          <div class="image-wrapper">
             <v-stage ref="stageHandout" :config="stageConfigHandout">
              <v-layer>
                <v-image :config="imageConfigHandout" />
              </v-layer>
              <v-layer>
                <v-group v-for="(anno, index) in handoutAnnotations" :key="`handout-anno-${index}`">
                  <v-rect :config="getAnnotationBoxConfig(anno, stageConfigHandout)" />
                  <v-text :config="getAnnotationLabelConfig(anno, index, stageConfigHandout)" />
                </v-group>
              </v-layer>
            </v-stage>
          </div>
        </div>
        <div v-if="handoverImage" class="image-display">
          <h3 class="section-title image-title">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
            Изображение сдачи
          </h3>
           <div class="image-wrapper">
             <v-stage ref="stageHandover" :config="stageConfigHandover">
              <v-layer>
                <v-image :config="imageConfigHandover" />
              </v-layer>
              <v-layer>
                <v-group v-for="(anno, index) in handoverAnnotations" :key="`handover-anno-${index}`">
                  <v-rect :config="getAnnotationBoxConfig(anno, stageConfigHandover)" />
                  <v-text :config="getAnnotationLabelConfig(anno, index, stageConfigHandover)" />
                </v-group>
              </v-layer>
            </v-stage>
          </div>
        </div>
      </div>

      <!-- Detailed Comparison -->
      <div class="comparison-grid">
        <!-- Missing Instruments (if any) -->
        <!-- <div v-if="diffData.missing.length > 0" class="comparison-section missing">
          <h3 class="section-title">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
              <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
              <line x1="15" y1="9" x2="9" y2="15" stroke="currentColor" stroke-width="2"/>
              <line x1="9" y1="9" x2="15" y2="15" stroke="currentColor" stroke-width="2"/>
            </svg>
            Недостающие инструменты ({{ diffData.missing.length }})
          </h3>
          <div class="instrument-list">
            <div 
              v-for="instrument in diffData.missing" 
              :key="`missing-${instrument}`"
              class="instrument-item missing"
            >
              <div class="instrument-info">
                <span class="instrument-name">{{ formatClassName(instrument) }}</span>
                <span class="instrument-status">Выдан, но не сдан</span>
              </div>
              <div class="status-indicator missing">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                  <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                  <line x1="15" y1="9" x2="9" y2="15" stroke="currentColor" stroke-width="2"/>
                  <line x1="9" y1="9" x2="15" y2="15" stroke="currentColor" stroke-width="2"/>
                </svg>
              </div>
            </div>
          </div>
        </div> -->

        <!-- Returned Instruments -->
        <!-- <div class="comparison-section returned">
          <h3 class="section-title">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" stroke="currentColor" stroke-width="2"/>
              <polyline points="22,4 12,14.01 9,11.01" stroke="currentColor" stroke-width="2"/>
            </svg>
            Сданные инструменты ({{ returnedInstruments.length }})
          </h3>
          <div class="instrument-list">
            <div 
              v-for="instrument in returnedInstruments" 
              :key="`returned-${instrument}`"
              class="instrument-item returned"
            >
              <div class="instrument-info">
                <span class="instrument-name">{{ formatClassName(instrument) }}</span>
                <span class="instrument-status">Успешно сдан</span>
              </div>
              <div class="status-indicator returned">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                  <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" stroke="currentColor" stroke-width="2"/>
                  <polyline points="22,4 12,14.01 9,11.01" stroke="currentColor" stroke-width="2"/>
                </svg>
              </div>
            </div>
          </div>
        </div> -->

        <!-- Extra Instruments (if any) -->
        <!-- <div v-if="diffData.extra && diffData.extra.length > 0" class="comparison-section extra">
          <h3 class="section-title">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
              <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
              <line x1="12" y1="8" x2="12" y2="12" stroke="currentColor" stroke-width="2"/>
              <line x1="12" y1="16" x2="12.01" y2="16" stroke="currentColor" stroke-width="2"/>
            </svg>
            Дополнительные инструменты ({{ diffData.extra.length }})
          </h3>
          <div class="instrument-list">
            <div 
              v-for="instrument in diffData.extra" 
              :key="`extra-${instrument}`"
              class="instrument-item extra"
            >
              <div class="instrument-info">
                <span class="instrument-name">{{ formatClassName(instrument) }}</span>
                <span class="instrument-status">Сдан, но не был выдан</span>
              </div>
              <div class="status-indicator extra">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                  <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                  <line x1="12" y1="8" x2="12" y2="12" stroke="currentColor" stroke-width="2"/>
                  <line x1="12" y1="16" x2="12.01" y2="16" stroke="currentColor" stroke-width="2"/>
                </svg>
              </div>
            </div>
          </div>
        </div> -->
      </div>

      <!-- Session Timeline -->
      <!-- <div class="timeline-section">
        <h3 class="section-title">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
            <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
            <polyline points="12,6 12,12 16,14" stroke="currentColor" stroke-width="2"/>
          </svg>
          История сессии
        </h3>
        <div class="timeline">
          <div class="timeline-item">
            <div class="timeline-marker handout"></div>
            <div class="timeline-content">
              <h4>Выдача завершена</h4>
              <p>{{ totalInstruments }} {{ getInstrumentWord(totalInstruments) }} {{ totalInstruments === 1 ? 'выдан' : 'выдано' }}</p>
              <span class="timeline-time">{{ formatSessionTime('handout') }}</span>
            </div>
          </div>
          <div class="timeline-item">
            <div class="timeline-marker handover"></div>
            <div class="timeline-content">
              <h4>Сдача завершена</h4>
              <p>{{ returnedInstruments.length }} {{ getInstrumentWord(returnedInstruments.length) }} {{ returnedInstruments.length === 1 ? 'сдан' : 'сдано' }}</p>
              <span class="timeline-time">{{ formatSessionTime('handover') }}</span>
            </div>
          </div>
        </div>
      </div> -->
    </div>

    <!-- Error State -->
    <div v-else class="error-state">
      <div class="error-icon">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none">
          <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
          <line x1="15" y1="9" x2="9" y2="15" stroke="currentColor" stroke-width="2"/>
          <line x1="9" y1="9" x2="15" y2="15" stroke="currentColor" stroke-width="2"/>
        </svg>
      </div>
      <h3>Не удалось загрузить сравнение</h3>
      <p>Попробуйте обновить страницу или обратитесь к администратору</p>
      <button @click="loadDiff" class="retry-btn">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
          <polyline points="23,4 23,10 17,10" stroke="currentColor" stroke-width="2"/>
          <polyline points="1,20 1,14 7,14" stroke="currentColor" stroke-width="2"/>
          <path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4-4.64 4.36A9 9 0 0 1 3.51 15" stroke="currentColor" stroke-width="2"/>
        </svg>
        Повторить попытку
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, reactive, nextTick } from 'vue';
import { useRouter } from 'vue-router';
import { useSessionStore } from '@/stores/sessions'
import { useNotificationStore } from '@/stores/notifications'
import { type SessionDiff, type FinalAnnotation } from '@/services/api'
import Konva from 'konva'

interface Props {
  sessionId: string
}

const props = defineProps<Props>()

const sessionStore = useSessionStore()
const notifications = useNotificationStore()
const router = useRouter()

const isLoading = ref(true)

const diffData = computed(() => sessionStore.sessionDiff)
const currentSession = computed(() => sessionStore.currentSession)

// Konva state for handout
const stageHandout = ref(null)
const stageConfigHandout = reactive({ width: 600, height: 450 })
const imageConfigHandout = reactive({ 
  image: null as HTMLImageElement | null,
  width: 600,
  height: 450
})
const originalImageHandout = ref<HTMLImageElement | null>(null)

// Konva state for handover
const stageHandover = ref(null)
const stageConfigHandover = reactive({ width: 600, height: 450 })
const imageConfigHandover = reactive({
  image: null as HTMLImageElement | null,
  width: 600,
  height: 450
})
const originalImageHandover = ref<HTMLImageElement | null>(null)


const handoutImage = computed(() => currentSession.value?.handout?.image)
const handoverImage = computed(() => currentSession.value?.handover?.image)
const handoutAnnotations = computed(() => currentSession.value?.handout?.final?.annotations || [])
const handoverAnnotations = computed(() => currentSession.value?.handover?.final?.annotations || [])


const hasDiscrepancies = computed(() => {
  if (!diffData.value) return false
  return diffData.value.missing.length > 0
})

const returnedInstruments = computed(() => {
  if (!diffData.value) return []
  
  // Get all instruments that were found in handover (successfully returned)
  const allExpectedInstruments = Object.keys(diffData.value.expected)
  return allExpectedInstruments.filter(instrument => 
    !diffData.value.missing.includes(instrument)
  )
})

const totalInstruments = computed(() => {
  return diffData.value ? Object.keys(diffData.value.expected).length : 0
})

// Load diff data when component mounts
onMounted(async () => {
  await loadDiff()
  // Load images after diff data is loaded
  if (handoutImage.value) {
    await loadImage(
      handoutImage.value, 
      originalImageHandout, 
      stageConfigHandout, 
      imageConfigHandout
    )
  }
  if (handoverImage.value) {
    await loadImage(
      handoverImage.value, 
      originalImageHandover, 
      stageConfigHandover, 
      imageConfigHandover
    )
  }
})

const loadDiff = async () => {
  isLoading.value = true
  try {
    await sessionStore.fetchSessionDiff(props.sessionId)
  } catch (error) {
    console.error('Failed to load session diff:', error)
  } finally {
    isLoading.value = false
  }
}

// Image and Konva Methods
const loadImage = async (
  imageData: string,
  originalImage: typeof originalImageHandout,
  stageConfig: typeof stageConfigHandout,
  imageConfig: typeof imageConfigHandout
) => {
  if (!imageData) return;

  const img = new Image()
  img.src = imageData
  img.onload = async () => {
    originalImage.value = img
    
    const containerMaxWidth = 600
    const containerMaxHeight = 450
    const aspectRatio = img.height / img.width
    const containerAspectRatio = containerMaxHeight / containerMaxWidth
    
    let finalWidth, finalHeight

    if (aspectRatio > containerAspectRatio) {
      finalHeight = containerMaxHeight
      finalWidth = finalHeight / aspectRatio
    } else {
      finalWidth = containerMaxWidth
      finalHeight = finalWidth * aspectRatio
    }

    stageConfig.width = Math.round(finalWidth)
    stageConfig.height = Math.round(finalHeight)
    
    imageConfig.width = stageConfig.width
    imageConfig.height = stageConfig.height
    imageConfig.image = img
    
    await nextTick()
  }
  img.onerror = () => {
    console.error('Failed to load image for Konva canvas')
  }
}

const getAnnotationBoxConfig = (annotation: FinalAnnotation, stageConfig: typeof stageConfigHandout) => {
  const [xCenter, yCenter, width, height] = annotation.box
  const x = (xCenter - width / 2) * stageConfig.width
  const y = (yCenter - height / 2) * stageConfig.height
  const w = width * stageConfig.width
  const h = height * stageConfig.height
  
  return {
    x,
    y,
    width: w,
    height: h,
    fill: 'rgba(59, 130, 246, 0.2)',
    stroke: '#3b82f6',
    strokeWidth: 2,
    listening: false,
  }
}

const getAnnotationLabelConfig = (annotation: FinalAnnotation, index: number, stageConfig: typeof stageConfigHandout) => {
  const [xCenter, yCenter, width, height] = annotation.box
  const x = (xCenter - width / 2) * stageConfig.width
  const y = (yCenter - height / 2) * stageConfig.height - 20

  const className = annotation.class_ || annotation.class || 'Unknown'
  
  return {
    x,
    y,
    text: `${index + 1}. ${formatClassName(className)}`,
    fontSize: 14,
    fontFamily: 'Arial, sans-serif',
    fill: '#ffffff',
    padding: 4,
    background: 'rgba(0,0,0,0.5)',
    listening: false,
  }
}


// Helper methods
const formatClassName = (className: string): string => {
  const nameMap: Record<string, string> = {
    'screwdriver_plus': 'Отвертка плюсовая',
    'screwdriver_minus': 'Отвертка минусовая',
    'wrench_adjustable': 'Разводной ключ',
    'offset_cross': 'Отвертка со смещенным крестом',
    'ring_wrench_3_4': 'Ключ рожковый накидной 3/4',
    'nippers': 'Бокорезы',
    'brace': 'Коловорот',
    'lock_pliers': 'Пассатижи контровочные',
    'pliers': 'Пассатижи',
    'shernitsa': 'Шерница',
    'oil_can_opener': 'Открывашка для банок с маслом'
  }
  return nameMap[className] || className
}

const getInstrumentWord = (count: number): string => {
  if (count % 10 === 1 && count % 100 !== 11) {
    return 'инструмент'
  } else if ([2, 3, 4].includes(count % 10) && ![12, 13, 14].includes(count % 100)) {
    return 'инструмента'
  } else {
    return 'инструментов'
  }
}

const formatSessionTime = (phase: 'handout' | 'handover'): string => {
  const session = sessionStore.currentSession
  if (!session) return ''
  
  let timestamp: string | undefined
  if (phase === 'handout' && session.handout?.issued_at) {
    timestamp = session.handout.issued_at
  } else if (phase === 'handover' && session.handover?.returned_at) {
    timestamp = session.handover.returned_at
  }
  
  if (timestamp) {
    const date = new Date(timestamp)
    return date.toLocaleString('ru-RU', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }
  
  return 'Время не указано'
}
</script>

<style scoped>
.diff-container {
  display: flex;
  flex-direction: column;
  gap: 32px;
}

/* New Image Comparison Styles */
.image-comparison-section {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 24px;
  background: rgba(30, 41, 59, 0.6);
  border: 1px solid rgba(71, 85, 105, 0.3);
  border-radius: 12px;
  padding: 24px;
}

.image-display {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.image-title {
  color: #cbd5e1;
  border-bottom: 1px solid rgba(71, 85, 105, 0.3);
  padding-bottom: 12px;
  margin: 0;
}

.image-title svg {
  color: #3b82f6;
}

.image-wrapper {
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(71, 85, 105, 0.3);
  border-radius: 8px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 300px;
}

/* Loading State */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
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

.loading-state p {
  color: #94a3b8;
  font-size: 1rem;
}

.diff-content {
  display: flex;
  flex-direction: column;
  gap: 32px;
}

/* Diff Header */
.diff-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 24px;
}

.diff-summary {
  flex: 1;
}

.summary-card {
  display: flex;
  align-items: center;
  gap: 20px;
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(71, 85, 105, 0.3);
  border-radius: 12px;
  padding: 24px;
  transition: all 0.2s;
}

.summary-card.has-issues {
  border-color: rgba(245, 158, 11, 0.5);
  background: rgba(245, 158, 11, 0.05);
}

.summary-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 64px;
  height: 64px;
  border-radius: 16px;
  flex-shrink: 0;
}

.summary-icon.success {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
}

.summary-icon.warning {
  background: rgba(245, 158, 11, 0.1);
  color: #f59e0b;
}

.summary-content h2 {
  color: #f1f5f9;
  font-size: 1.5rem;
  font-weight: 600;
  margin-bottom: 8px;
}

.summary-content p {
  color: #94a3b8;
  font-size: 1rem;
  margin: 0;
}

.action-section {
  flex-shrink: 0;
}

.finalize-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  border: none;
  border-radius: 8px;
  padding: 16px 24px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  min-width: 200px;
  justify-content: center;
}

.back-btn {
  background: #374151;
  color: #f3f4f6;
}

.back-btn:hover:not(:disabled) {
  background: #4b5563;
  transform: translateY(-2px);
  box-shadow: 0 10px 20px -10px rgba(0,0,0,0.2);
}

.finalize-btn.success {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
}

.finalize-btn.success:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 20px 40px -12px rgba(16, 185, 129, 0.4);
}

.finalize-btn.warning {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  color: white;
}

.finalize-btn.warning:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 20px 40px -12px rgba(245, 158, 11, 0.4);
}

.finalize-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

/* Comparison Grid */
.comparison-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: 24px;
}

.comparison-section {
  background: rgba(30, 41, 59, 0.6);
  border: 1px solid rgba(71, 85, 105, 0.3);
  border-radius: 12px;
  padding: 20px;
}

.comparison-section.missing {
  border-left: 4px solid #ef4444;
}

.comparison-section.returned {
  border-left: 4px solid #10b981;
}

.comparison-section.extra {
  border-left: 4px solid #f59e0b;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 1.125rem;
  font-weight: 600;
  color: #f1f5f9;
  margin-bottom: 16px;
}

.section-title svg {
  color: #3b82f6;
}

.missing .section-title svg {
  color: #ef4444;
}

.returned .section-title svg {
  color: #10b981;
}

.extra .section-title svg {
  color: #f59e0b;
}

.instrument-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.instrument-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(71, 85, 105, 0.3);
  border-radius: 8px;
  padding: 16px;
}

.instrument-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.instrument-name {
  color: #f1f5f9;
  font-weight: 600;
  font-size: 0.875rem;
}

.instrument-status {
  color: #64748b;
  font-size: 0.75rem;
}

.instrument-item.missing .instrument-status {
  color: #ef4444;
}

.instrument-item.returned .instrument-status {
  color: #10b981;
}

.instrument-item.extra .instrument-status {
  color: #f59e0b;
}

.status-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  flex-shrink: 0;
}

.status-indicator.missing {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

.status-indicator.returned {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
}

.status-indicator.extra {
  background: rgba(245, 158, 11, 0.1);
  color: #f59e0b;
}

/* Timeline Section */
.timeline-section {
  background: rgba(30, 41, 59, 0.6);
  border: 1px solid rgba(71, 85, 105, 0.3);
  border-radius: 12px;
  padding: 24px;
}

.timeline {
  display: flex;
  flex-direction: column;
  gap: 20px;
  margin-top: 20px;
}

.timeline-item {
  display: flex;
  align-items: center;
  gap: 16px;
}

.timeline-marker {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  flex-shrink: 0;
}

.timeline-marker.handout {
  background: #3b82f6;
}

.timeline-marker.handover {
  background: #f59e0b;
}

.timeline-content h4 {
  color: #f1f5f9;
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: 4px;
}

.timeline-content p {
  color: #94a3b8;
  font-size: 0.875rem;
  margin-bottom: 8px;
}

.timeline-time {
  color: #64748b;
  font-size: 0.75rem;
}

/* Warning Notice */
.warning-notice {
  background: rgba(245, 158, 11, 0.1);
  border: 1px solid rgba(245, 158, 11, 0.3);
  border-radius: 12px;
  padding: 20px;
}

.warning-content {
  display: flex;
  gap: 16px;
}

.warning-content svg {
  color: #f59e0b;
  flex-shrink: 0;
  margin-top: 2px;
}

.warning-text h4 {
  color: #f59e0b;
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: 8px;
}

.warning-text p {
  color: #94a3b8;
  font-size: 0.875rem;
  line-height: 1.5;
  margin: 0;
}

/* Error State */
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
}

.error-icon {
  color: #ef4444;
  margin-bottom: 24px;
}

.error-state h3 {
  color: #f1f5f9;
  font-size: 1.25rem;
  font-weight: 600;
  margin-bottom: 12px;
}

.error-state p {
  color: #94a3b8;
  margin-bottom: 24px;
}

.retry-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(59, 130, 246, 0.1);
  color: #3b82f6;
  border: 1px solid rgba(59, 130, 246, 0.3);
  border-radius: 8px;
  padding: 12px 24px;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.retry-btn:hover {
  background: rgba(59, 130, 246, 0.2);
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* Responsive */
@media (max-width: 768px) {
  .diff-header {
    flex-direction: column;
    align-items: stretch;
  }

  .summary-card {
    flex-direction: column;
    text-align: center;
    gap: 16px;
  }

  .comparison-grid {
    grid-template-columns: 1fr;
  }

  .timeline-item {
    align-items: flex-start;
  }

  .timeline-marker {
    margin-top: 4px;
  }

  .warning-content {
    flex-direction: column;
    text-align: center;
  }

  .warning-content svg {
    align-self: center;
    margin-top: 0;
  }
}
</style>
