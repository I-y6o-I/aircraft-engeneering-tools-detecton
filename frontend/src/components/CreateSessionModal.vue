<template>
  <div v-if="isOpen" class="modal-overlay" @click="handleOverlayClick">
    <div class="modal-content" @click.stop>
      <div class="modal-header">
        <h2 class="modal-title">Создание новой сессии</h2>
        <button @click="closeModal" class="close-button">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
            <line x1="18" y1="6" x2="6" y2="18" stroke="currentColor" stroke-width="2"/>
            <line x1="6" y1="6" x2="18" y2="18" stroke="currentColor" stroke-width="2"/>
          </svg>
        </button>
      </div>

      <form @submit.prevent="handleSubmit" class="modal-form">
        <!-- Session Notes -->
        <div class="form-group">
          <label for="session-notes" class="form-label">
            Название смены <span class="required">*</span>
          </label>
          <input
            id="session-notes"
            v-model="formData.notes"
            type="text"
            class="form-input"
            placeholder="Введите название смены (например: Смена А)"
            required
            :disabled="isLoading"
          />
          <p class="form-help">Укажите название или описание рабочей смены</p>
        </div>

        <!-- Confidence Threshold -->
        <div class="form-group">
          <label for="threshold-slider" class="form-label">
            Порог уверенности: <span class="threshold-value">{{ formData.threshold }}%</span>
          </label>
          <div class="threshold-container">
            <input
              id="threshold-slider"
              v-model.number="formData.threshold"
              type="range"
              min="1"
              max="100"
              step="1"
              class="threshold-slider"
              :disabled="isLoading"
            />
            <div class="threshold-labels">
              <span class="threshold-label">10%</span>
              <span class="threshold-label">25%</span>
              <span class="threshold-label">50%</span>
              <span class="threshold-label">75%</span>
              <span class="threshold-label">99%</span>
            </div>
          </div>
          <p class="form-help">
            Минимальный уровень уверенности для автоматического принятия детекций. 
            Чем выше порог, тем больше инструментов потребует ручной проверки.
          </p>
        </div>

        <!-- Threshold Recommendations -->
        <div class="threshold-info">
          <div class="info-item">
            <div class="info-icon warning" v-if="formData.threshold >= 80">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z" stroke="currentColor" stroke-width="2"/>
                <path d="M12 9v4" stroke="currentColor" stroke-width="2"/>
                <path d="m12 17 .01 0" stroke="currentColor" stroke-width="2"/>
              </svg>
            </div>
            <div class="info-icon recommended" v-else-if="formData.threshold >= 50">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" stroke="currentColor" stroke-width="2"/>
                <polyline points="22,4 12,14.01 9,11.01" stroke="currentColor" stroke-width="2"/>
              </svg>
            </div>
            <div class="info-icon caution" v-else>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                <path d="M12,17h.01" stroke="currentColor" stroke-width="2"/>
                <path d="M9,9h0a3,3,0,0,1,6,0c0,2-3,3-3,3" stroke="currentColor" stroke-width="2"/>
              </svg>
            </div>
            <div class="info-text">
              <span v-if="formData.threshold >= 80" class="warning">
                Высокий порог - больше инструментов потребует ручной разметки
              </span>
              <span v-else-if="formData.threshold >= 50" class="recommended">
                Средний порог: баланс между точностью и количеством найденных инструментов
              </span>
              <span v-else class="caution">
                Низкий порог: будут показаны все возможные инструменты, включая сомнительные
              </span>
            </div>
          </div>
        </div>

        <!-- Action Buttons -->
        <div class="form-actions">
          <button
            type="button"
            @click="closeModal"
            class="secondary-button"
            :disabled="isLoading"
          >
            Отмена
          </button>
          <button
            type="submit"
            class="primary-button"
            :disabled="isLoading || !formData.notes.trim()"
          >
            <div v-if="isLoading" class="loading-spinner"></div>
            <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none">
              <line x1="12" y1="5" x2="12" y2="19" stroke="currentColor" stroke-width="2"/>
              <line x1="5" y1="12" x2="19" y2="12" stroke="currentColor" stroke-width="2"/>
            </svg>
            {{ isLoading ? 'Создание...' : 'Создать сессию' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useSessionStore } from '@/stores/sessions'
import { useNotificationStore } from '@/stores/notifications'

interface Props {
  isOpen: boolean
}

interface Emits {
  (e: 'close'): void
  (e: 'created', sessionId: string): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const router = useRouter()
const sessionStore = useSessionStore()
const notifications = useNotificationStore()

const isLoading = ref(false)

const formData = reactive({
  notes: '',
  threshold: 98
})

// Reset form data when modal opens
watch(() => props.isOpen, (isOpen) => {
  if (isOpen) {
    formData.notes = ''
    formData.threshold = 98
  }
})

const closeModal = () => {
  if (!isLoading.value) {
    emit('close')
  }
}

const handleOverlayClick = (event: MouseEvent) => {
  closeModal()
}

const handleSubmit = async () => {
  if (isLoading.value || !formData.notes.trim()) return

  isLoading.value = true
  try {
    const response = await sessionStore.createSession({
      threshold: formData.threshold / 100,
      notes: formData.notes.trim()
    })

    emit('created', response.session_id)
    
    // Navigate to the new session
    router.push(`/sessions/${response.session_id}`)
    
    // Close modal
    closeModal()
  } catch (error) {
    console.error('Failed to create session:', error)
    // Error handling is done in the store
  } finally {
    isLoading.value = false
  }
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.75);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.modal-content {
  background: rgba(30, 41, 59, 0.95);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(71, 85, 105, 0.3);
  border-radius: 16px;
  padding: 0;
  width: 100%;
  max-width: 500px;
  max-height: 90vh;
  overflow: hidden;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24px 24px 20px;
  border-bottom: 1px solid rgba(71, 85, 105, 0.3);
}

.modal-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: #f1f5f9;
  margin: 0;
}

.close-button {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border: none;
  background: rgba(71, 85, 105, 0.2);
  color: #94a3b8;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.close-button:hover {
  background: rgba(71, 85, 105, 0.3);
  color: #f1f5f9;
}

.modal-form {
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-label {
  color: #f1f5f9;
  font-size: 0.875rem;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 8px;
}

.required {
  color: #ef4444;
}

.threshold-value {
  color: #3b82f6;
  font-weight: 600;
}

.form-input {
  background: rgba(15, 23, 42, 0.8);
  border: 1px solid rgba(71, 85, 105, 0.4);
  border-radius: 8px;
  padding: 12px 16px;
  color: #f1f5f9;
  font-size: 0.875rem;
  transition: all 0.2s;
}

.form-input:focus {
  outline: none;
  border-color: #3b82f6;
  background: rgba(15, 23, 42, 0.9);
}

.form-input:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.form-help {
  color: #64748b;
  font-size: 0.75rem;
  line-height: 1.4;
  margin: 0;
}

.threshold-container {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.threshold-slider {
  width: 100%;
  height: 6px;
  background: rgba(71, 85, 105, 0.4);
  border-radius: 3px;
  outline: none;
  -webkit-appearance: none;
  appearance: none;
  cursor: pointer;
}

.threshold-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 20px;
  height: 20px;
  background: #3b82f6;
  border-radius: 50%;
  cursor: pointer;
  transition: all 0.2s;
}

.threshold-slider::-webkit-slider-thumb:hover {
  background: #60a5fa;
  transform: scale(1.1);
}

.threshold-slider:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.threshold-slider:disabled::-webkit-slider-thumb {
  cursor: not-allowed;
  transform: none;
}

.threshold-labels {
  display: flex;
  justify-content: space-between;
  padding: 0 10px;
}

.threshold-label {
  color: #64748b;
  font-size: 0.75rem;
}

.threshold-info {
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(71, 85, 105, 0.3);
  border-radius: 8px;
  padding: 16px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.info-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  flex-shrink: 0;
}

.info-icon.recommended {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
}

.info-icon.warning {
  background: rgba(251, 191, 36, 0.1);
  color: #f59e0b;
}

.info-icon.caution {
  background: rgba(96, 165, 250, 0.1);
  color: #60a5fa;
}

.info-text {
  color: #cbd5e1;
  font-size: 0.875rem;
  line-height: 1.4;
}

.info-text .recommended {
  color: #10b981;
}

.info-text .warning {
  color: #f59e0b;
}

.info-text .caution {
  color: #60a5fa;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 8px;
}

.primary-button,
.secondary-button {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px 24px;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  min-width: 120px;
  height: 44px;
}

.primary-button {
  background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
  color: white;
  border: none;
}

.primary-button:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 10px 20px -8px rgba(59, 130, 246, 0.4);
}

.primary-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.secondary-button {
  background: rgba(71, 85, 105, 0.2);
  color: #cbd5e1;
  border: 1px solid rgba(71, 85, 105, 0.3);
}

.secondary-button:hover:not(:disabled) {
  background: rgba(71, 85, 105, 0.3);
  transform: translateY(-1px);
}

.secondary-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.loading-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top: 2px solid white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* Responsive */
@media (max-width: 640px) {
  .modal-overlay {
    padding: 16px;
  }

  .modal-content {
    max-width: 100%;
  }

  .modal-header {
    padding: 20px 20px 16px;
  }

  .modal-form {
    padding: 20px;
  }

  .modal-title {
    font-size: 1.25rem;
  }

  .form-actions {
    flex-direction: column-reverse;
  }

  .primary-button,
  .secondary-button {
    width: 100%;
  }
}
</style>
