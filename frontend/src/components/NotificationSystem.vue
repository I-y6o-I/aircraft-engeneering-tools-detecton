<template>
  <Teleport to="body">
    <div class="notification-container">
      <TransitionGroup name="notification" tag="div">
        <div
          v-for="notification in notifications"
          :key="notification.id"
          :class="[
            'notification',
            `notification--${notification.type}`,
            { 'notification--dismissible': notification.dismissible }
          ]"
          @click="notification.dismissible && dismiss(notification.id)"
        >
          <div class="notification__icon">
            <svg v-if="notification.type === 'success'" width="20" height="20" viewBox="0 0 24 24" fill="none">
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" stroke="currentColor" stroke-width="2"/>
              <polyline points="22,4 12,14.01 9,11.01" stroke="currentColor" stroke-width="2"/>
            </svg>
            <svg v-else-if="notification.type === 'error'" width="20" height="20" viewBox="0 0 24 24" fill="none">
              <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
              <line x1="15" y1="9" x2="9" y2="15" stroke="currentColor" stroke-width="2"/>
              <line x1="9" y1="9" x2="15" y2="15" stroke="currentColor" stroke-width="2"/>
            </svg>
            <svg v-else-if="notification.type === 'warning'" width="20" height="20" viewBox="0 0 24 24" fill="none">
              <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" stroke="currentColor" stroke-width="2"/>
              <line x1="12" y1="9" x2="12" y2="13" stroke="currentColor" stroke-width="2"/>
              <circle cx="12" cy="17" r="1" fill="currentColor"/>
            </svg>
            <svg v-else-if="notification.type === 'info'" width="20" height="20" viewBox="0 0 24 24" fill="none">
              <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
              <path d="M12 16v-4" stroke="currentColor" stroke-width="2"/>
              <circle cx="12" cy="8" r="1" fill="currentColor"/>
            </svg>
          </div>
          
          <div class="notification__content">
            <div v-if="notification.title" class="notification__title">
              {{ notification.title }}
            </div>
            <div class="notification__message">
              {{ notification.message }}
            </div>
            
            <!-- Action buttons -->
            <div v-if="notification.actions && notification.actions.length > 0" class="notification__actions">
              <button
                v-for="action in notification.actions"
                :key="action.label"
                @click.stop="handleAction(notification.id, action)"
                :class="[
                  'notification__action-btn',
                  `notification__action-btn--${action.style || 'secondary'}`
                ]"
              >
                {{ action.label }}
              </button>
            </div>
          </div>
          
          <button
            v-if="notification.dismissible"
            @click.stop="dismiss(notification.id)"
            class="notification__close"
            aria-label="Закрыть уведомление"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
              <line x1="18" y1="6" x2="6" y2="18" stroke="currentColor" stroke-width="2"/>
              <line x1="6" y1="6" x2="18" y2="18" stroke="currentColor" stroke-width="2"/>
            </svg>
          </button>
          
          <!-- Progress bar for auto-dismiss -->
          <div 
            v-if="notification.duration && notification.duration > 0"
            class="notification__progress"
            :style="{ animationDuration: `${notification.duration}ms` }"
          ></div>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useNotificationStore } from '../stores/notifications'

const notificationStore = useNotificationStore()

const notifications = computed(() => notificationStore.notifications)

const dismiss = (id: string) => {
  notificationStore.dismiss(id)
}

const handleAction = (notificationId: string, action: any) => {
  action.action()
  dismiss(notificationId)
}
</script>

<style scoped>
.notification-container {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 9999;
  pointer-events: none;
  max-width: 400px;
  width: 100%;
}

.notification {
  position: relative;
  display: flex;
  align-items: flex-start;
  gap: 12px;
  background: rgba(30, 41, 59, 0.95);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(71, 85, 105, 0.3);
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 12px;
  box-shadow: 0 20px 40px -12px rgba(0, 0, 0, 0.4);
  pointer-events: auto;
  overflow: hidden;
  min-height: 60px;
  transition: all 0.2s ease;
}

.notification:hover {
  transform: translateX(-4px);
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
}

.notification--dismissible {
  cursor: pointer;
}

.notification--success {
  border-left: 4px solid #10b981;
}

.notification--error {
  border-left: 4px solid #ef4444;
}

.notification--warning {
  border-left: 4px solid #f59e0b;
}

.notification--info {
  border-left: 4px solid #3b82f6;
}

.notification__icon {
  flex-shrink: 0;
  width: 20px;
  height: 20px;
  margin-top: 2px;
}

.notification--success .notification__icon {
  color: #10b981;
}

.notification--error .notification__icon {
  color: #ef4444;
}

.notification--warning .notification__icon {
  color: #f59e0b;
}

.notification--info .notification__icon {
  color: #3b82f6;
}

.notification__content {
  flex: 1;
  min-width: 0;
}

.notification__title {
  font-weight: 600;
  font-size: 0.875rem;
  color: #f1f5f9;
  margin-bottom: 4px;
  line-height: 1.4;
}

.notification__message {
  font-size: 0.875rem;
  color: #cbd5e1;
  line-height: 1.5;
  white-space: pre-line;
}

.notification__actions {
  display: flex;
  gap: 8px;
  margin-top: 12px;
}

.notification__action-btn {
  border: none;
  border-radius: 6px;
  padding: 6px 12px;
  font-size: 0.75rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  flex-shrink: 0;
}

.notification__action-btn--primary {
  background: #3b82f6;
  color: white;
}

.notification__action-btn--primary:hover {
  background: #2563eb;
}

.notification__action-btn--secondary {
  background: rgba(71, 85, 105, 0.3);
  color: #cbd5e1;
  border: 1px solid rgba(71, 85, 105, 0.4);
}

.notification__action-btn--secondary:hover {
  background: rgba(71, 85, 105, 0.4);
  color: #f1f5f9;
}

.notification__close {
  flex-shrink: 0;
  background: none;
  border: none;
  color: #94a3b8;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  transition: all 0.2s;
  margin-top: -2px;
}

.notification__close:hover {
  background: rgba(71, 85, 105, 0.3);
  color: #f1f5f9;
}

.notification__progress {
  position: absolute;
  bottom: 0;
  left: 0;
  height: 2px;
  background: linear-gradient(90deg, transparent 0%, currentColor 100%);
  animation: progress-shrink linear forwards;
  opacity: 0.6;
}

.notification--success .notification__progress {
  color: #10b981;
}

.notification--error .notification__progress {
  color: #ef4444;
}

.notification--warning .notification__progress {
  color: #f59e0b;
}

.notification--info .notification__progress {
  color: #3b82f6;
}

@keyframes progress-shrink {
  from {
    width: 100%;
  }
  to {
    width: 0%;
  }
}

/* Transition animations */
.notification-enter-active {
  transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

.notification-leave-active {
  transition: all 0.3s cubic-bezier(0.55, 0.085, 0.68, 0.53);
}

.notification-enter-from {
  opacity: 0;
  transform: translateX(100%) scale(0.8);
}

.notification-leave-to {
  opacity: 0;
  transform: translateX(100%) scale(0.9);
}

.notification-move {
  transition: transform 0.3s ease;
}

/* Responsive design */
@media (max-width: 640px) {
  .notification-container {
    top: 10px;
    right: 10px;
    left: 10px;
    max-width: none;
  }
  
  .notification {
    margin-bottom: 8px;
    padding: 12px;
  }
  
  .notification__title {
    font-size: 0.8125rem;
  }
  
  .notification__message {
    font-size: 0.8125rem;
  }
}
</style>
