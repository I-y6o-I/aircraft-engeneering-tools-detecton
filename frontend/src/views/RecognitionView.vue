<template>
  <div class="recognition-container">
    <!-- Navigation -->
    <nav class="navbar">
      <div class="nav-content">
        <router-link to="/" class="logo">
          <Logo />
        </router-link>
      </div>
    </nav>

    <!-- Main Content -->
    <main class="main-content">
      <!-- Loading State -->
      <div v-if="isLoading" class="loading-section">
        <div class="loading-spinner"></div>
        <h2>{{ loadingText }}</h2>
        <p>{{ loadingSubtext }}</p>
      </div>

      <!-- Recognition Results -->
      <div v-else-if="recognitionData" class="recognition-section">
        <div class="results-header">
          <h1 class="results-title">Результаты распознавания</h1>
          <div class="header-info">
            <div class="file-info">
              <span class="file-label">Файл: </span>
              <span class="file-name">{{ recognitionSessionData?.fileName || 'Неизвестный файл' }}</span>
            </div>
            <div class="threshold-info">
              <span class="threshold-label">Порог уверенности: </span>
              <span class="threshold-value">{{ Math.round((recognitionData?.threshold || threshold) * 100) }}%</span>
            </div>
            <button @click="resetRecognition" class="header-action-btn">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                <polyline points="23,4 23,10 17,10" stroke="currentColor" stroke-width="2"/>
                <polyline points="1,20 1,14 7,14" stroke="currentColor" stroke-width="2"/>
                <path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4-4.64 4.36A9 9 0 0 1 3.51 15" stroke="currentColor" stroke-width="2"/>
              </svg>
              Переснять
            </button>
          </div>
        </div>

        <div class="results-content">
          <!-- Left Column: Image + Actions -->
          <div class="left-column">
            <div class="image-section">
              <div class="image-container">
              <v-stage 
                ref="stage"
                :config="stageConfig" 
                @mousedown="handleStageMouseDown"
                @mousemove="handleStageMouseMove"
                @mouseup="handleStageMouseUp">
                <v-layer ref="imageLayer">
                  <v-image 
                    v-if="imageConfig.image"
                    ref="konvaImage"
                    :config="{
                      x: imageConfig.x,
                      y: imageConfig.y,
                      width: imageConfig.width,
                      height: imageConfig.height,
                      image: imageConfig.image
                    }"
                  />
                  <!-- Fallback rect for debugging when image is not loaded -->
                  <v-rect 
                    v-else-if="originalImage && !imageConfig.image"
                    :config="{
                      x: 0,
                      y: 0,
                      width: stageConfig.width,
                      height: stageConfig.height,
                      fill: '#1f2937',
                      stroke: '#f59e0b',
                      strokeWidth: 2
                    }"
                  />
                  <v-text
                    v-if="originalImage && !imageConfig.image"
                    :config="{
                      x: stageConfig.width / 2,
                      y: stageConfig.height / 2,
                      text: 'Ошибка загрузки изображения в Konva',
                      fontSize: 16,
                      fontFamily: 'Arial',
                      fill: '#f59e0b',
                      align: 'center',
                      offsetX: 150,
                      offsetY: 8
                    }"
                  />
                </v-layer>
                <v-layer ref="annotationLayer">
                  <!-- Existing Detections -->
                  <v-group 
                    v-for="(detection, index) in allDetections" 
                    :key="`detection-${detection.detection_id || index}`">
                    <v-rect 
                      :config="getDetectionBoxConfig(detection, index)"
                      @dragmove="(e) => handleDetectionDragMove(detection, e)"
                      @dragend="() => handleDetectionDragEnd(detection)"
                    />
                    <v-text :config="getDetectionLabelConfig(detection, index)" />
                    <!-- Edit handles for editing detection -->
                    <template v-if="editingDetectionId === detection.detection_id">
                      <v-circle 
                        v-for="(handle, handleIndex) in getEditHandles(detection)"
                        :key="`handle-${handleIndex}`"
                        :config="handle"
                        @dragstart="(e) => handleResizeStart(detection, handle.handleType, e)"
                        @dragmove="(e) => handleResizeDrag(detection, e)"
                        @dragend="() => handleResizeEnd(detection)"
                      />
                    </template>
                  </v-group>
                  <!-- New annotation being drawn -->
                  <v-rect 
                    v-if="newAnnotation"
                    :config="newAnnotationConfig"
                  />
                </v-layer>
              </v-stage>
            </div>
          </div>

          <!-- Action Buttons -->
          <div class="actions-section">
            <div class="summary-info">
              <div class="summary-item">
                <span class="summary-label">Найдено:</span>
                <span class="summary-value">{{ recognitionData.summary.found_candidates }}</span>
              </div>
              <div class="summary-item">
                <span class="summary-label">Прошло порог:</span>
                <span class="summary-value">{{ recognitionData.summary.passed_above_threshold }}</span>
              </div>
              <div class="summary-item">
                <span class="summary-label">Требует проверки:</span>
                <span class="summary-value">{{ recognitionData.summary.requires_manual_count }}</span>
              </div>
              <div class="summary-item">
                <span class="summary-label">Не найдено:</span>
                <span class="summary-value">{{ recognitionData.summary.not_found_count }}</span>
              </div>
            </div>
            
            <div class="action-buttons">
              <button 
                @click="saveAnnotations" 
                class="primary-btn" 
                :disabled="isSaveDisabled"
                :title="saveDisabledReason"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                  <polyline points="20,6 9,17 4,12" stroke="currentColor" stroke-width="2"/>
                </svg>
                {{ isSaving ? 'Сохранение...' : 'Завершить разметку' }}
              </button>
            </div>
          </div>

          <!-- Save validation message -->
          <div v-if="saveDisabledReason" class="save-validation-notice">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
              <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
              <line x1="12" y1="8" x2="12" y2="12" stroke="currentColor" stroke-width="2"/>
              <line x1="12" y1="16" x2="12.01" y2="16" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
            <p>{{ saveDisabledReason }}</p>
          </div>
        </div>

        <!-- Right Column: Detection Lists -->
        <div class="lists-section">
            <!-- Found Detections -->
            <div class="detections-list">
              <h3 class="list-title">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                  <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" stroke="currentColor" stroke-width="2"/>
                  <polyline points="22,4 12,14.01 9,11.01" stroke="currentColor" stroke-width="2"/>
                </svg>
                Обнаруженные инструменты ({{ allDetections.length }})
              </h3>
              <div class="detection-items">
                <div 
                  v-for="(detection, index) in allDetections" 
                  :key="`detection-item-${detection.detection_id || index}`"
                  class="detection-item" 
                  :class="{ 
                    'passed-threshold': detection.is_passed_conf_treshold,
                    'failed-threshold': !detection.is_passed_conf_treshold,
                    'selected': selectedDetection?.detection_id === detection.detection_id
                  }"
                  @click="selectDetection(detection, index)">
                  <div class="detection-header">
                    <span class="detection-number">{{ index + 1 }}</span>
                    <span class="detection-status">
                      <svg v-if="detection.is_passed_conf_treshold" width="16" height="16" viewBox="0 0 24 24" fill="none">
                        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" stroke="currentColor" stroke-width="2"/>
                        <polyline points="22,4 12,14.01 9,11.01" stroke="currentColor" stroke-width="2"/>
                      </svg>
                      <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none">
                        <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                        <line x1="15" y1="9" x2="9" y2="15" stroke="currentColor" stroke-width="2"/>
                        <line x1="9" y1="9" x2="15" y2="15" stroke="currentColor" stroke-width="2"/>
                      </svg>
                    </span>
                  </div>
                  <div class="detection-info">
                    <div class="info-item">
                      <span class="info-label">Инструмент:</span>
                      <span class="info-value">{{ getDetectionDisplayName(detection) }}</span>
                    </div>
                    <div class="confidence-info">
                      <span class="confidence-label">Уверенность:</span>
                      <span class="confidence-value" :class="{ 
                        'high-confidence': detection.confidence >= 0.8,
                        'medium-confidence': detection.confidence >= 0.5 && detection.confidence < 0.8,
                        'low-confidence': detection.confidence < 0.5
                      }">
                        {{ Math.round(detection.confidence * 100) }}%
                      </span>
                    </div>
                    <div class="class-editor">
                        <label>Изменить на:</label>
                        <select 
                          :value="detection.class"
                          @change="handleClassChange(detection, $event)"
                          class="class-select"
                          @click.stop>
                          <option v-for="className in getAvailableClasses(detection)" :key="className" :value="className">
                            {{ formatClassName(className) }}
                          </option>
                        </select>
                    </div>
                  </div>
                  <div class="detection-actions">
                    <button 
                      @click.stop="editDetectionPosition(detection)" 
                      class="action-btn edit-btn"
                      :class="{ 
                        'active': editingDetectionId === detection.detection_id,
                        'has-changes': editingDetectionId === detection.detection_id && hasUnsavedChanges
                      }">
                      <svg v-if="editingDetectionId === detection.detection_id" width="14" height="14" viewBox="0 0 24 24" fill="none">
                        <polyline points="20,6 9,17 4,12" stroke="currentColor" stroke-width="2"/>
                      </svg>
                      <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none">
                        <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" stroke="currentColor" stroke-width="2"/>
                        <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" stroke="currentColor" stroke-width="2"/>
                      </svg>
                      {{ editingDetectionId === detection.detection_id ? 'Сохранить' : 'Править позицию' }}
                      <span v-if="editingDetectionId === detection.detection_id && hasUnsavedChanges" class="changes-indicator">•</span>
                    </button>
                    <button @click.stop="removeDetection(detection)" class="action-btn remove-btn">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
                        <polyline points="3,6 5,6 21,6" stroke="currentColor" stroke-width="2"/>
                        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" stroke="currentColor" stroke-width="2"/>
                      </svg>
                      Удалить
                    </button>
                  </div>
                </div>
              </div>
            </div>

            <!-- Not Found Instruments -->
            <div class="not-found-list">
              <h3 class="list-title">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                  <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                  <line x1="15" y1="9" x2="9" y2="15" stroke="currentColor" stroke-width="2"/>
                  <line x1="9" y1="9" x2="15" y2="15" stroke="currentColor" stroke-width="2"/>
                </svg>
                Ненайденные инструменты ({{ notFoundInstruments.length }})
              </h3>
              <div class="not-found-items">
                <div 
                  v-for="instrument in notFoundInstruments" 
                  :key="`not-found-${instrument}`"
                  class="not-found-item">
                  <span class="instrument-name">{{ formatClassName(instrument) }}</span>
                  <button @click="addManualAnnotation(instrument)" class="action-btn add-btn">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
                      <line x1="12" y1="5" x2="12" y2="19" stroke="currentColor" stroke-width="2"/>
                      <line x1="5" y1="12" x2="19" y2="12" stroke="currentColor" stroke-width="2"/>
                    </svg>
                    Добавить вручную
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { apiService, type PredictResponse, type Detection, type Annotation, type AdjustRequest, type AdjustResponse } from '@/services/api'
import { useNotificationStore } from '@/stores/notifications'
import { useRecognitionStore, type RecognitionData } from '@/stores/recognition'
import Konva from 'konva'
import Logo from '@/components/Logo.vue';

type UIDetection = Detection & { isDuplicate?: boolean };

const router = useRouter()
const route = useRoute()
const notifications = useNotificationStore()
const recognitionStore = useRecognitionStore()

// Component state
const isLoading = ref(true)
const isSaving = ref(false)
const loadingText = ref('Инициализация системы распознавания...')
const loadingSubtext = ref('Подготовка нейронной сети для анализа изображений')
const recognitionData = ref<PredictResponse | null>(null)
const allDetections = ref<UIDetection[]>([])
const selectedDetection = ref<UIDetection | null>(null)
const selectedDetectionIndex = ref<number | null>(null)
  const isEditingPosition = ref(false)
  const editingDetectionId = ref<string | null>(null)
  const hasUnsavedChanges = ref(false)

// Konva references
const stage = ref<any>(null)
const imageLayer = ref<any>(null)
const annotationLayer = ref<any>(null)
const konvaImage = ref<any>(null)

// Image and annotation state
const originalImage = ref<HTMLImageElement | null>(null)
const stageConfig = reactive({
  width: 800,
  height: 600,
  scaleX: 1,
  scaleY: 1,
  x: 0,
  y: 0
})

const imageConfig = reactive({
  x: 0,
  y: 0,
  width: 800,
  height: 600,
  image: null as HTMLImageElement | null
})

// Manual annotation drawing
const isDrawing = ref(false)
const newAnnotation = ref<any>(null)
const drawingClass = ref<string>('')

// Recognition data from sessionStorage
const recognitionSessionData = ref<RecognitionData | null>(null)

const imageData = computed(() => recognitionSessionData.value?.image || '')
const threshold = computed(() => recognitionSessionData.value?.threshold || 75)

// Computed properties
const notFoundInstruments = computed(() => {
  if (!recognitionData.value) return []
  const foundClasses = allDetections.value.map(d => d.class)
  return recognitionData.value.not_found.filter(cls => !foundClasses.includes(cls))
})

// Get available classes for a specific detection (all from catalog)
const getAvailableClasses = (_currentDetection: UIDetection) => {
  if (!recognitionData.value) return []
  return recognitionData.value.classes_catalog
}

const newAnnotationConfig = computed(() => {
  if (!newAnnotation.value) return {}
  return {
    x: newAnnotation.value.x,
    y: newAnnotation.value.y,
    width: newAnnotation.value.width,
    height: newAnnotation.value.height,
    fill: 'rgba(59, 130, 246, 0.3)',
    stroke: '#3b82f6',
    strokeWidth: 2,
    dash: [5, 5]
  }
})

const isSaveDisabled = computed(() => {
  if (isSaving.value) return true
  if (!recognitionData.value) return true

  const hasDuplicates = allDetections.value.some(d => d.isDuplicate)
  const isCountInvalid = allDetections.value.length !== 11

  return hasDuplicates || isCountInvalid
})

const saveDisabledReason = computed(() => {
  if (isSaving.value || !recognitionData.value) return ''

  const hasDuplicates = allDetections.value.some(d => d.isDuplicate)
  const toolCount = allDetections.value.length
  const isCountInvalid = toolCount !== 11
  
  const reasons = []
  if (isCountInvalid) {
    reasons.push(`требуется 11 инструментов (сейчас ${toolCount})`)
  }
  if (hasDuplicates) {
    reasons.push('обнаружены дубликаты инструментов')
  }

  if (reasons.length > 0) {
    const reasonText = reasons.join(' и ')
    return `Невозможно сохранить: ${reasonText}.`
  }

  return ''
})

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

// Recalculate duplicate flags for a specific class
const recalculateDuplicatesForClass = (className: string) => {
  const detectionsOfClass = allDetections.value.filter(d => d.class === className);
  detectionsOfClass.forEach((detection, index) => {
    detection.isDuplicate = index > 0;
  });
}

// Get display name for a detection, including duplicate status
const getDetectionDisplayName = (detection: UIDetection) => {
  const baseName = formatClassName(detection.class);
  if (detection.isDuplicate) {
    return `${baseName} (дупликат)`;
  }
  return baseName;
}

// Konva helper methods
const getDetectionBoxConfig = (detection: Detection, index: number) => {
  const [xCenter, yCenter, width, height] = detection.box
  const x = (xCenter - width / 2) * stageConfig.width
  const y = (yCenter - height / 2) * stageConfig.height
  const w = width * stageConfig.width
  const h = height * stageConfig.height

  const color = detection.is_passed_conf_treshold ? '#10b981' : '#ef4444'
  const isSelected = selectedDetection.value?.detection_id === detection.detection_id
  const isEditing = editingDetectionId.value === detection.detection_id

  return {
    x,
    y,
    width: w,
    height: h,
    fill: isSelected ? `${color}40` : `${color}20`,
    stroke: isEditing ? '#3b82f6' : color,
    strokeWidth: isEditing ? 4 : isSelected ? 3 : 2,
    listening: true,
    draggable: isEditing,
    name: `detection-${detection.detection_id}`,
    id: `detection-${detection.detection_id}`, // Add ID for easier finding
    // Add event listeners for dragging
    ...(isEditing && {
      dragBoundFunc: (pos: any) => {
        // Keep the rectangle within bounds
        return {
          x: Math.max(0, Math.min(pos.x, stageConfig.width - w)),
          y: Math.max(0, Math.min(pos.y, stageConfig.height - h))
        }
      }
    })
  }
}

const getDetectionLabelConfig = (detection: UIDetection, index: number) => {
  const [xCenter, yCenter, width, height] = detection.box
  const x = (xCenter - width / 2) * stageConfig.width
  const y = (yCenter - height / 2) * stageConfig.height - 25

  return {
    x,
    y,
    text: `${index + 1}. ${getDetectionDisplayName(detection)}`,
    fontSize: 14,
    fontFamily: 'Arial',
    fill: '#ffffff',
    align: 'left',
    listening: false,
    shadowColor: 'black',
    shadowBlur: 2,
    shadowOffsetX: 1,
    shadowOffsetY: 1
  }
}

const getEditHandles = (detection: UIDetection) => {
  const [xCenter, yCenter, width, height] = detection.box
  const x1 = (xCenter - width / 2) * stageConfig.width
  const y1 = (yCenter - height / 2) * stageConfig.height
  const x2 = (xCenter + width / 2) * stageConfig.width
  const y2 = (yCenter + height / 2) * stageConfig.height
  const xMid = xCenter * stageConfig.width
  const yMid = yCenter * stageConfig.height

  return [
    // Corner handles
    { 
      x: x1, y: y1, radius: 6, fill: '#3b82f6', stroke: '#ffffff', strokeWidth: 2, 
      draggable: true, name: 'resize-handle-nw', cursor: 'nw-resize', handleType: 'nw'
    },
    { 
      x: x2, y: y1, radius: 6, fill: '#3b82f6', stroke: '#ffffff', strokeWidth: 2, 
      draggable: true, name: 'resize-handle-ne', cursor: 'ne-resize', handleType: 'ne'
    },
    { 
      x: x2, y: y2, radius: 6, fill: '#3b82f6', stroke: '#ffffff', strokeWidth: 2, 
      draggable: true, name: 'resize-handle-se', cursor: 'se-resize', handleType: 'se'
    },
    { 
      x: x1, y: y2, radius: 6, fill: '#3b82f6', stroke: '#ffffff', strokeWidth: 2, 
      draggable: true, name: 'resize-handle-sw', cursor: 'sw-resize', handleType: 'sw'
    },
    // Edge handles
    { 
      x: xMid, y: y1, radius: 5, fill: '#3b82f6', stroke: '#ffffff', strokeWidth: 2, 
      draggable: true, name: 'resize-handle-n', cursor: 'n-resize', handleType: 'n'
    },
    { 
      x: x2, y: yMid, radius: 5, fill: '#3b82f6', stroke: '#ffffff', strokeWidth: 2, 
      draggable: true, name: 'resize-handle-e', cursor: 'e-resize', handleType: 'e'
    },
    { 
      x: xMid, y: y2, radius: 5, fill: '#3b82f6', stroke: '#ffffff', strokeWidth: 2, 
      draggable: true, name: 'resize-handle-s', cursor: 's-resize', handleType: 's'
    },
    { 
      x: x1, y: yMid, radius: 5, fill: '#3b82f6', stroke: '#ffffff', strokeWidth: 2, 
      draggable: true, name: 'resize-handle-w', cursor: 'w-resize', handleType: 'w'
    }
  ]
}

// Event handlers
const selectDetection = (detection: UIDetection, index: number) => {
  selectedDetection.value = detection
  selectedDetectionIndex.value = index
}

const editDetectionPosition = (detection: Detection) => {
  console.log('editDetectionPosition called:', detection.detection_id, 'isEditing:', isEditingPosition.value)
  
  if (isEditingPosition.value && editingDetectionId.value === detection.detection_id) {
    // Save changes and exit editing mode
    console.log('Saving position changes for:', detection.detection_id)
    savePositionChanges(detection)
  } else {
    // Enter editing mode
    console.log('Entering editing mode for:', detection.detection_id)
    selectedDetection.value = detection
    isEditingPosition.value = true
    editingDetectionId.value = detection.detection_id
    hasUnsavedChanges.value = false
  }
}

const removeDetection = (detection: UIDetection) => {
  const index = allDetections.value.findIndex(d => d.detection_id === detection.detection_id)
  if (index !== -1) {
    const removedClass = detection.class
    const wasDuplicate = detection.isDuplicate
    
    // Remove detection from list
    allDetections.value.splice(index, 1)

    // Recalculate duplicates for the affected class
    recalculateDuplicatesForClass(removedClass);
    
    // Check if there are still other detections of the same class
    const hasOtherDetectionsOfSameClass = allDetections.value.some(d => d.class === removedClass)
    
    // If this was the last detection of this class AND it was not a duplicate, move it to not_found
    if (!wasDuplicate && !hasOtherDetectionsOfSameClass && recognitionData.value) {
      // Add to not_found if not already there
      if (!recognitionData.value.not_found.includes(removedClass)) {
        recognitionData.value.not_found.push(removedClass)
        console.log(`Added "${removedClass}" to not_found after removal`)
      }
      
      // Update summary statistics
      recognitionData.value.summary.found_candidates = allDetections.value.length
      recognitionData.value.summary.not_found_count = recognitionData.value.not_found.length
      recognitionData.value.summary.passed_above_threshold = allDetections.value.filter(d => d.is_passed_conf_treshold).length
      recognitionData.value.summary.requires_manual_count = allDetections.value.filter(d => !d.is_passed_conf_treshold).length
    }
    
    // Clear selection if removed detection was selected
    if (selectedDetection.value?.detection_id === detection.detection_id) {
      selectedDetection.value = null
      selectedDetectionIndex.value = null
    }
    
    // Exit editing mode if removed detection was being edited
    if (editingDetectionId.value === detection.detection_id) {
      isEditingPosition.value = false
      editingDetectionId.value = null
      hasUnsavedChanges.value = false
    }
  }
}

const handleClassChange = (detection: UIDetection, event: Event) => {
  const target = event.target as HTMLSelectElement
  const newClass = target.value
  const oldClass = detection.class
  const wasDuplicate = detection.isDuplicate ?? false
  
  if (newClass === oldClass) return // No change
  
  console.log(`Changing class from "${oldClass}" to "${newClass}"`)
  
  // Update the detection class
  detection.class = newClass

  // Recalculate duplicates for both old and new classes
  recalculateDuplicatesForClass(oldClass)
  recalculateDuplicatesForClass(newClass)
  
  // Check if old class should be moved to not_found
  const hasOtherDetectionsOfOldClass = allDetections.value.some(d => 
    d.detection_id !== detection.detection_id && d.class === oldClass
  )
  
  if (!wasDuplicate && !hasOtherDetectionsOfOldClass && recognitionData.value) {
    // Add old class to not_found if not already there
    if (!recognitionData.value.not_found.includes(oldClass)) {
      recognitionData.value.not_found.push(oldClass)
      console.log(`Added "${oldClass}" to not_found`)
    }
  }
  
  // Remove new class from not_found if it's there
  if (recognitionData.value && recognitionData.value.not_found.includes(newClass)) {
    const notFoundIndex = recognitionData.value.not_found.indexOf(newClass)
    recognitionData.value.not_found.splice(notFoundIndex, 1)
    console.log(`Removed "${newClass}" from not_found`)
  }
  
  // Update summary statistics
  if (recognitionData.value) {
    recognitionData.value.summary.found_candidates = allDetections.value.length
    recognitionData.value.summary.not_found_count = recognitionData.value.not_found.length
    recognitionData.value.summary.passed_above_threshold = allDetections.value.filter(d => d.is_passed_conf_treshold).length
    recognitionData.value.summary.requires_manual_count = allDetections.value.filter(d => !d.is_passed_conf_treshold).length
  }
}

const addManualAnnotation = (className: string) => {
  // Allow adding duplicates without warning
  drawingClass.value = className
  isDrawing.value = false
  // Enable drawing mode
  notifications.info(
    `Нарисуйте прямоугольник на изображении, чтобы отметить расположение инструмента.`,
    { 
      title: `Режим рисования: ${formatClassName(className)}`,
      duration: 3000
    }
  )
}

// Stage event handlers
const handleStageMouseDown = (e: any) => {
  if (drawingClass.value && !isDrawing.value) {
    isDrawing.value = true
    const pos = stage.value.getNode().getPointerPosition()
    newAnnotation.value = {
      x: pos.x,
      y: pos.y,
      width: 0,
      height: 0
    }
  }
}

const handleStageMouseMove = (e: any) => {
  if (isDrawing.value && newAnnotation.value) {
    const pos = stage.value.getNode().getPointerPosition()
    newAnnotation.value.width = pos.x - newAnnotation.value.x
    newAnnotation.value.height = pos.y - newAnnotation.value.y
  }
}

const handleStageMouseUp = (e: any) => {
  if (isDrawing.value && newAnnotation.value && drawingClass.value) {
    // Convert to normalized coordinates
    const box: [number, number, number, number] = [
      (newAnnotation.value.x + newAnnotation.value.width / 2) / stageConfig.width,
      (newAnnotation.value.y + newAnnotation.value.height / 2) / stageConfig.height,
      Math.abs(newAnnotation.value.width) / stageConfig.width,
      Math.abs(newAnnotation.value.height) / stageConfig.height
    ]

    // Create new detection
    const newDetection: Detection = {
      detection_id: `manual-${Date.now()}`,
      class: drawingClass.value,
      confidence: 1.0,
      is_passed_conf_treshold: true,
      box
    }
    
    const isDuplicate = allDetections.value.some(d => d.class === drawingClass.value);

    const newUIDetection: UIDetection = {
      ...newDetection,
      isDuplicate: isDuplicate
    }

      allDetections.value.push(newUIDetection)
      
      // Remove from not_found list since we just added it manually
      if (recognitionData.value && recognitionData.value.not_found.includes(drawingClass.value)) {
        const notFoundIndex = recognitionData.value.not_found.indexOf(drawingClass.value)
        recognitionData.value.not_found.splice(notFoundIndex, 1)
        console.log(`Removed "${drawingClass.value}" from not_found after manual annotation`)
        
        // Update summary statistics
        recognitionData.value.summary.found_candidates = allDetections.value.length
        recognitionData.value.summary.not_found_count = recognitionData.value.not_found.length
        recognitionData.value.summary.passed_above_threshold = allDetections.value.filter(d => d.is_passed_conf_treshold).length
        recognitionData.value.summary.requires_manual_count = allDetections.value.filter(d => !d.is_passed_conf_treshold).length
      }
      
      // Reset drawing state
    isDrawing.value = false
    newAnnotation.value = null
    drawingClass.value = ''
  }
}

const savePositionChanges = (detection: Detection) => {
  try {
    // Find the rect node through the stage reference
    const stageNode = stage.value?.getNode()
    if (!stageNode) {
      console.error('Stage not found')
      return
    }

    // Try multiple ways to find the node
    let rectNode = stageNode.findOne(`#detection-${detection.detection_id}`) || 
                   stageNode.findOne(`[name=detection-${detection.detection_id}]`)
    
    if (!rectNode) {
      console.error(`Rect node not found for detection: ${detection.detection_id}`)
      console.log('Available nodes:', stageNode.find('Rect').map((n: any) => ({ name: n.name(), id: n.id() })))
      return
    }

    const x = rectNode.x()
    const y = rectNode.y()
    const width = rectNode.width()
    const height = rectNode.height()

    console.log('Current position:', { x, y, width, height })
    console.log('Stage dimensions:', { width: stageConfig.width, height: stageConfig.height })

    // Convert back to normalized coordinates
    const normalizedBox: [number, number, number, number] = [
      (x + width / 2) / stageConfig.width,  // x center
      (y + height / 2) / stageConfig.height, // y center
      width / stageConfig.width,             // width
      height / stageConfig.height            // height
    ]

    console.log('Normalized box:', normalizedBox)

    // Update the detection in the array
    const detectionIndex = allDetections.value.findIndex(d => d.detection_id === detection.detection_id)
    if (detectionIndex !== -1) {
      // Update the box coordinates
      allDetections.value[detectionIndex].box = normalizedBox
      
      // Mark as edited if it wasn't manual
      let newDetectionId = detection.detection_id
      if (!detection.detection_id?.startsWith('manual-') && !detection.detection_id?.startsWith('edited-')) {
        newDetectionId = `edited-${detection.detection_id}`
        allDetections.value[detectionIndex].detection_id = newDetectionId
      }
      
      // Update the selectedDetection reference
      if (selectedDetection.value?.detection_id === detection.detection_id) {
        selectedDetection.value = { ...allDetections.value[detectionIndex] }
      }
      
      console.log('Updated detection:', allDetections.value[detectionIndex])
    } else {
      console.error('Detection not found in array')
      return
    }

    // Exit editing mode
    isEditingPosition.value = false
    editingDetectionId.value = null
    hasUnsavedChanges.value = false
    
    // Show success message
    notifications.success('Позиция инструмента успешно обновлена!', { 
      title: 'Изменения сохранены' 
    })
    
    // Force re-render of the stage
    nextTick(() => {
      if (annotationLayer.value) {
        annotationLayer.value.getNode().batchDraw()
      }
    })
  } catch (error) {
    console.error('Error saving position changes:', error)
    notifications.error('Не удалось сохранить изменения позиции. Попробуйте ещё раз.', {
      title: 'Ошибка сохранения'
    })
  }
}

const handleDetectionDragEnd = (detection: Detection) => {
  console.log('handleDetectionDragEnd called for:', detection.detection_id)
  // Mark that there are unsaved changes
  if (editingDetectionId.value === detection.detection_id) {
    hasUnsavedChanges.value = true
  }
}

const handleDetectionDragMove = (detection: Detection, e: any) => {
  if (editingDetectionId.value === detection.detection_id) {
    // Update the detection box coordinates in real-time during drag
    const rectNode = e.target
    const x = rectNode.x()
    const y = rectNode.y()
    const width = rectNode.width()
    const height = rectNode.height()

    // Convert to normalized coordinates
    const normalizedBox: [number, number, number, number] = [
      (x + width / 2) / stageConfig.width,  // x center
      (y + height / 2) / stageConfig.height, // y center
      width / stageConfig.width,             // width
      height / stageConfig.height            // height
    ]

    // Update the detection box in real-time
    const detectionIndex = allDetections.value.findIndex(d => d.detection_id === detection.detection_id)
    if (detectionIndex !== -1) {
      allDetections.value[detectionIndex].box = normalizedBox
    }
  }
}

// Resize state
const resizingDetection = ref<Detection | null>(null)
const resizeHandleType = ref<string | null>(null)
const initialResizeState = ref<{
  startPointerX: number
  startPointerY: number
  originalBox: number[]
} | null>(null)

const handleResizeStart = (detection: Detection, handleType: string, e: any) => {
  console.log(`Starting resize for detection ${detection.detection_id} with handle ${handleType}`)
  
  resizingDetection.value = detection
  resizeHandleType.value = handleType
  
  const stage = e.target.getStage()
  const pointer = stage.getPointerPosition()
  
  initialResizeState.value = {
    startPointerX: pointer.x,
    startPointerY: pointer.y,
    originalBox: [...detection.box]
  }
}

const handleResizeDrag = (detection: Detection, e: any) => {
  if (!resizingDetection.value || !resizeHandleType.value || !initialResizeState.value) return
  if (resizingDetection.value.detection_id !== detection.detection_id) return

  const stage = e.target.getStage()
  const pointer = stage.getPointerPosition()
  const handleType = resizeHandleType.value
  const initial = initialResizeState.value
  
  // Calculate deltas
  const deltaX = pointer.x - initial.startPointerX
  const deltaY = pointer.y - initial.startPointerY

  // Get original box in pixel coordinates
  const [origCenterX, origCenterY, origWidth, origHeight] = initial.originalBox
  const origX1 = (origCenterX - origWidth / 2) * stageConfig.width
  const origY1 = (origCenterY - origHeight / 2) * stageConfig.height
  const origX2 = (origCenterX + origWidth / 2) * stageConfig.width
  const origY2 = (origCenterY + origHeight / 2) * stageConfig.height

  let newX1 = origX1
  let newY1 = origY1
  let newX2 = origX2
  let newY2 = origY2

  // Apply resize based on handle type
  switch (handleType) {
    case 'nw':
      newX1 += deltaX
      newY1 += deltaY
      break
    case 'ne':
      newX2 += deltaX
      newY1 += deltaY
      break
    case 'se':
      newX2 += deltaX
      newY2 += deltaY
      break
    case 'sw':
      newX1 += deltaX
      newY2 += deltaY
      break
    case 'n':
      newY1 += deltaY
      break
    case 'e':
      newX2 += deltaX
      break
    case 's':
      newY2 += deltaY
      break
    case 'w':
      newX1 += deltaX
      break
  }

  // Enforce minimum size (20px)
  const minSize = 20
  if (newX2 - newX1 < minSize) {
    if (handleType.includes('w')) newX1 = newX2 - minSize
    else newX2 = newX1 + minSize
  }
  if (newY2 - newY1 < minSize) {
    if (handleType.includes('n')) newY1 = newY2 - minSize
    else newY2 = newY1 + minSize
  }

  // Enforce stage boundaries
  newX1 = Math.max(0, Math.min(newX1, stageConfig.width - minSize))
  newY1 = Math.max(0, Math.min(newY1, stageConfig.height - minSize))
  newX2 = Math.max(minSize, Math.min(newX2, stageConfig.width))
  newY2 = Math.max(minSize, Math.min(newY2, stageConfig.height))

  // Convert back to normalized coordinates
  const newCenterX = (newX1 + newX2) / 2 / stageConfig.width
  const newCenterY = (newY1 + newY2) / 2 / stageConfig.height
  const newWidth = (newX2 - newX1) / stageConfig.width
  const newHeight = (newY2 - newY1) / stageConfig.height

  // Update detection box
  detection.box = [newCenterX, newCenterY, newWidth, newHeight]
  hasUnsavedChanges.value = true
}

const handleResizeEnd = (detection: Detection) => {
  console.log('handleResizeEnd called for:', detection.detection_id)
  
  // Clear resize state
  resizingDetection.value = null
  resizeHandleType.value = null
  initialResizeState.value = null
  
  // Mark that there are unsaved changes
  if (editingDetectionId.value === detection.detection_id) {
    hasUnsavedChanges.value = true
  }
}




// Main actions
const resetRecognition = () => {
  // Clean up sessionStorage
  // sessionStorage.removeItem('aero-kit-recognition-data')
  recognitionStore.clearRecognitionData()
  router.push('/')
}

const saveAnnotations = async () => {
  isSaving.value = true
  try {
    const annotations: Annotation[] = allDetections.value.map((detection) => ({
      class: detection.class,
      box: detection.box,
      source: detection.detection_id?.startsWith('manual-') ? 'manual' : 
               detection.detection_id?.startsWith('edited-') ? 'edited' : 'model',
      from_detection_id: detection.detection_id?.startsWith('manual-') ? undefined : detection.detection_id
    }))

    const request: AdjustRequest = {
      threshold: threshold.value / 100,
      annotations
    }

    const result: AdjustResponse = await apiService.adjustPredictions(request)

    if (result.ok) {
      notifications.success(
        `Все ${result.count} инструментов найдены и размечены.`,
        { 
          title: 'Разметка завершена!',
          duration: 3000
        }
      )
      // Clean up sessionStorage
      // sessionStorage.removeItem('aero-kit-recognition-data')
      recognitionStore.clearRecognitionData()
      router.push('/')
    } else {
      const warnings = result.issues.join('\n')
      notifications.error(
        `Найдены следующие ошибки:\n\n${warnings}\n\nПожалуйста, исправьте ошибки перед сохранением.`,
        { 
          title: 'Ошибки в разметке',
          duration: 0 // Не исчезает автоматически
        }
      )
    }
  } catch (error: any) {
    console.error('Error saving annotations:', error)
    notifications.error(error.message || 'Не удалось сохранить разметку. Проверьте подключение к интернету и попробуйте ещё раз.', {
      title: 'Ошибка сохранения'
    })
  } finally {
    isSaving.value = false
  }
}

// Lifecycle
onMounted(async () => {
  // Load recognition data from sessionStorage
  // const storedData = sessionStorage.getItem('aero-kit-recognition-data')
  const storedData = recognitionStore.recognitionData

  if (!storedData) {
    notifications.error('Данные для распознавания не найдены. Пожалуйста, загрузите изображение заново.', {
      title: 'Сессия истекла'
    })
    router.push('/')
    return
  }

  try {
    // recognitionSessionData.value = JSON.parse(storedData)
    recognitionSessionData.value = storedData
  } catch (error) {
    console.error('Error parsing recognition data:', error)
    notifications.error('Не удалось загрузить данные распознавания. Попробуйте загрузить изображение заново.', {
      title: 'Ошибка загрузки данных'
    })
    router.push('/')
    return
  }

  if (!imageData.value) {
    notifications.error('Изображение не найдено в данных сессии. Пожалуйста, загрузите изображение заново.', {
      title: 'Изображение отсутствует'
    })
    router.push('/')
    return
  }

  try {
    // Simulate loading phases
    loadingText.value = 'Загрузка изображения...'
    loadingSubtext.value = 'Обработка загруженного файла'
    await new Promise(resolve => setTimeout(resolve, 1000))

    // Load image
    loadingText.value = 'Загрузка изображения...'
    loadingSubtext.value = 'Подготовка изображения для анализа'
    
    const img = new Image()
    img.crossOrigin = 'anonymous'
    img.onload = async () => {
      console.log('Image loaded successfully:', img.width, 'x', img.height)
      originalImage.value = img
      
      // Calculate optimal dimensions that fit in container and maintain aspect ratio
      const containerMaxWidth = 800
      const containerMaxHeight = 600
      const aspectRatio = img.height / img.width
      
      let finalWidth, finalHeight
      
      // Calculate dimensions that fit perfectly in container while maintaining aspect ratio
      const containerAspectRatio = containerMaxHeight / containerMaxWidth
      
      if (aspectRatio > containerAspectRatio) {
        // Image is taller relative to container - constrain by height
        finalHeight = containerMaxHeight
        finalWidth = finalHeight / aspectRatio
      } else {
        // Image is wider relative to container - constrain by width  
        finalWidth = containerMaxWidth
        finalHeight = finalWidth * aspectRatio
      }
      
      stageConfig.width = Math.round(finalWidth)
      stageConfig.height = Math.round(finalHeight)
      
      imageConfig.width = stageConfig.width
      imageConfig.height = stageConfig.height
      imageConfig.image = img
      
      console.log('Stage config:', stageConfig)
      console.log('Image config:', imageConfig)
      
      await nextTick()
      
      // Wait a bit more for Vue to update the DOM
      await new Promise(resolve => setTimeout(resolve, 100))
      
      // Check if Konva stage is available
      console.log('Stage reference:', stage.value)
      console.log('Image layer reference:', imageLayer.value)
      console.log('Konva image reference:', konvaImage.value)
      
      // Force redraw
      if (imageLayer.value) {
        console.log('Force redraw image layer')
        imageLayer.value.getNode().batchDraw()
      }
      
      // Double check if image is set correctly
      if (konvaImage.value) {
        const imageNode = konvaImage.value.getNode()
        console.log('Konva image node:', imageNode)
        console.log('Image in node:', imageNode.image())
      }

      // Start recognition
      loadingText.value = 'Анализ изображения нейронной сетью...'
      loadingSubtext.value = 'Поиск и классификация авиационных инструментов'
      
      const recognitionResult = await apiService.predict({
        image: imageData.value,
        threshold: threshold.value / 100
      })

      console.log('Recognition result:', recognitionResult)
      recognitionData.value = recognitionResult
      
      // Process detections to identify duplicates
      const seenClasses = new Set<string>();
      allDetections.value = recognitionResult.detections.map(detection => {
        const isDuplicate = seenClasses.has(detection.class);
        seenClasses.add(detection.class);
        return {
          ...detection,
          isDuplicate: isDuplicate,
        };
      });
      
      isLoading.value = false
    }
    
    img.onerror = (error) => {
      console.error('Failed to load image:', error)
      notifications.error('Не удалось загрузить изображение. Проверьте формат файла и попробуйте ещё раз.', {
        title: 'Ошибка загрузки изображения'
      })
      router.push('/')
    }
    
    console.log('Loading image from:', imageData.value.substring(0, 50) + '...')
    img.src = imageData.value
  } catch (error: any) {
    console.error('Error during recognition:', error)
    notifications.error(error.message || 'Произошла ошибка при анализе изображения. Попробуйте загрузить изображение заново.', {
      title: 'Ошибка распознавания'
    })
    router.push('/')
  }
})

onUnmounted(() => {
  if (originalImage.value) {
    originalImage.value = null
  }
  // Optional: Clean up sessionStorage when leaving the component
  // sessionStorage.removeItem('aero-kit-recognition-data')
  // recognitionStore.clearRecognitionData() // This might be too aggressive if user just navigates away
})
</script>

<style scoped>
.recognition-container {
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
  justify-content: flex-start;
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
  text-decoration: none;
  transition: all 0.2s;
  cursor: pointer;
}

.logo:hover {
  color: #e2e8f0;
  transform: translateY(-1px);
}

.logo svg {
  color: #3b82f6;
  transition: all 0.2s;
}

.logo:hover svg {
  color: #60a5fa;
}

/* Main Content */
.main-content {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 24px;
  width: 100%;
  box-sizing: border-box;
}

/* Loading */
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
  font-size: 1rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* Recognition Results */
.recognition-section {
  padding: 40px 0;
}

.results-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32px;
  padding-bottom: 20px;
  border-bottom: 1px solid rgba(71, 85, 105, 0.3);
}

.results-title {
  font-size: 2rem;
  font-weight: 700;
  color: #f1f5f9;
}

.header-info {
  display: flex;
  align-items: center;
  gap: 16px;
}

.file-info {
  background: rgba(30, 41, 59, 0.6);
  border: 1px solid rgba(71, 85, 105, 0.3);
  border-radius: 8px;
  padding: 12px 16px;
}

.file-label {
  color: #94a3b8;
  font-size: 0.875rem;
}

.file-name {
  color: #f1f5f9;
  font-weight: 600;
  font-size: 0.875rem;
}

.threshold-info {
  background: rgba(30, 41, 59, 0.6);
  border: 1px solid rgba(71, 85, 105, 0.3);
  border-radius: 8px;
  padding: 12px 16px;
}

.threshold-label {
  color: #94a3b8;
  font-size: 0.875rem;
}

.threshold-value {
  color: #3b82f6;
  font-weight: 600;
  font-size: 1rem;
}

.header-action-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(71, 85, 105, 0.2);
  color: #cbd5e1;
  border: 1px solid rgba(71, 85, 105, 0.3);
  border-radius: 8px;
  padding: 16px 16px;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
  height: fit-content;
}

.header-action-btn:hover {
  background: rgba(71, 85, 105, 0.3);
  transform: translateY(-1px);
}

.results-content {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(350px, 400px);
  gap: 32px;
  align-items: start;
  width: 100%;
  max-width: 1400px;
  margin: 0 auto;
}

/* Left Column */
.left-column {
  display: flex;
  flex-direction: column;
  gap: 24px;
  min-width: 0; /* Allow shrinking */
}

/* Image Section */
.image-section {
  background: rgba(30, 41, 59, 0.6);
  border: 1px solid rgba(71, 85, 105, 0.3);
  border-radius: 16px;
  padding: 24px;
  display: flex;
  flex-direction: column;
  height: fit-content;
}

.image-container {

  border-radius: 8px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  max-height: 600px;
}

.image-container canvas {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}


/* Lists Section */
.lists-section {
  display: flex;
  flex-direction: column;
  gap: 24px;
  min-width: 0; /* Allow shrinking */
}

.list-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 1.125rem;
  font-weight: 600;
  color: #f1f5f9;
  margin-bottom: 16px;
}

.list-title svg {
  color: #3b82f6;
}

/* Detection Items */
.detections-list {
  background: rgba(30, 41, 59, 0.6);
  border: 1px solid rgba(71, 85, 105, 0.3);
  border-radius: 12px;
  padding: 20px;
  min-width: 0; /* Allow content to shrink */
}

.detection-items {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: 400px;
  overflow-y: auto;
}

.detection-item {
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(71, 85, 105, 0.3);
  border-radius: 8px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.2s;
}

.detection-item:hover {
  background: rgba(15, 23, 42, 0.8);
}

.detection-item.selected {
  border-color: #3b82f6;
  background: rgba(59, 130, 246, 0.1);
}

.detection-item.passed-threshold {
  border-left: 4px solid #10b981;
}

.detection-item.failed-threshold {
  border-left: 4px solid #ef4444;
}

.detection-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.detection-number {
  background: #3b82f6;
  color: white;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.875rem;
  font-weight: 600;
}

.detection-status svg {
  color: #10b981;
}

.failed-threshold .detection-status svg {
  color: #ef4444;
}

.detection-info {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 12px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.info-label {
  color: #94a3b8;
  font-size: 0.875rem;
}

.info-value {
  color: #f1f5f9;
  font-weight: 600;
  font-size: 0.875rem;
  text-align: right;
}

.class-editor {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.class-editor label {
  color: #94a3b8;
  font-size: 0.875rem;
  font-weight: 500;
}

.class-select {
  background: rgba(30, 41, 59, 0.8);
  border: 1px solid rgba(71, 85, 105, 0.4);
  border-radius: 6px;
  padding: 8px 12px;
  color: #f1f5f9;
  font-size: 0.875rem;
}

.class-note {
  color: #64748b;
  font-size: 0.75rem;
  margin-top: 4px;
  font-style: italic;
}

.confidence-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.confidence-label {
  color: #94a3b8;
  font-size: 0.875rem;
}

.confidence-value {
  font-weight: 600;
}

.high-confidence {
  color: #10b981;
}

.medium-confidence {
  color: #f59e0b;
}

.low-confidence {
  color: #ef4444;
}

.detection-actions {
  display: flex;
  gap: 8px;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  border: none;
  border-radius: 6px;
  padding: 6px 12px;
  font-size: 0.75rem;
  cursor: pointer;
  transition: all 0.2s;
}

.edit-btn {
  background: rgba(59, 130, 246, 0.1);
  color: #3b82f6;
}

.edit-btn:hover {
  background: rgba(59, 130, 246, 0.2);
}

.remove-btn {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

.remove-btn:hover {
  background: rgba(239, 68, 68, 0.2);
}

.add-btn {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
}

.add-btn:hover {
  background: rgba(16, 185, 129, 0.2);
}

.edit-btn.active {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
  border: 1px solid rgba(16, 185, 129, 0.3);
}

.edit-btn.active:hover {
  background: rgba(16, 185, 129, 0.2);
}

.edit-btn.has-changes {
  background: rgba(251, 191, 36, 0.1);
  color: #f59e0b;
  border: 1px solid rgba(251, 191, 36, 0.3);
}

.edit-btn.has-changes:hover {
  background: rgba(251, 191, 36, 0.2);
}

.changes-indicator {
  color: #f59e0b;
  font-weight: 900;
  font-size: 1.2rem;
  margin-left: 4px;
}

/* Not Found Items */
.not-found-list {
  background: rgba(30, 41, 59, 0.6);
  border: 1px solid rgba(71, 85, 105, 0.3);
  border-radius: 12px;
  padding: 20px;
}

.not-found-items {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.not-found-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(71, 85, 105, 0.3);
  border-radius: 6px;
  padding: 12px 16px;
}

.instrument-name {
  color: #f1f5f9;
  font-size: 0.875rem;
}


/* Actions Section */
.actions-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: rgba(30, 41, 59, 0.6);
  border: 1px solid rgba(71, 85, 105, 0.3);
  border-radius: 12px;
  padding: 24px;
}

.summary-info {
  display: flex;
  gap: 24px;
}

.summary-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.summary-label {
  color: #94a3b8;
  font-size: 0.875rem;
}

.summary-value {
  color: #f1f5f9;
  font-size: 1.25rem;
  font-weight: 600;
}

.action-buttons {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.save-action-wrapper {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.save-disabled-reason {
  margin-top: 8px;
  padding: 8px 12px;
  background: rgba(251, 191, 36, 0.1);
  border: 1px solid rgba(251, 191, 36, 0.3);
  border-radius: 6px;
  color: #f59e0b;
  font-size: 0.875rem;
  max-width: 350px;
  text-align: right;
  font-weight: 500;
}

.primary-btn, .secondary-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  border: none;
  border-radius: 8px;
  padding: 12px 24px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.primary-btn {
  background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
  color: white;
}

.primary-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 20px 40px -12px rgba(59, 130, 246, 0.4);
}

.primary-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.secondary-btn {
  background: rgba(71, 85, 105, 0.2);
  color: #cbd5e1;
  border: 1px solid rgba(71, 85, 105, 0.3);
}

.secondary-btn:hover {
  background: rgba(71, 85, 105, 0.3);
  transform: translateY(-1px);
}

/* Responsive Design */
@media (max-width: 1200px) {
  .results-content {
    grid-template-columns: 1fr;
    gap: 24px;
    max-width: 800px;
  }
  
  .lists-section {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 24px;
  }
}

@media (max-width: 768px) {
  .nav-content {
    padding: 12px 16px;
  }
  
  .main-content {
    padding: 0 16px;
    max-width: none;
  }
  
  .results-content {
    max-width: none;
  }
  
  .results-header {
    flex-direction: column;
    gap: 16px;
    align-items: flex-start;
  }
  
  .results-title {
    font-size: 1.5rem;
  }

  .header-info {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
    width: 100%;
  }
  
  .lists-section {
    grid-template-columns: 1fr;
  }

  
  .actions-section {
    flex-direction: column;
    gap: 20px;
    text-align: center;
  }
  
  .summary-info {
    justify-content: center;
    flex-wrap: wrap;
    gap: 16px;
  }
}

.save-validation-notice {
  background: rgba(251, 191, 36, 0.1);
  border: 1px solid rgba(251, 191, 36, 0.3);
  border-radius: 12px;
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 12px;
  color: #f59e0b;
}

.save-validation-notice p {
  margin: 0;
  font-size: 0.875rem;
  font-weight: 500;
  line-height: 1.5;
}

.save-validation-notice svg {
  flex-shrink: 0;
}
</style>
