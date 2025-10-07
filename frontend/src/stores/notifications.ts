import { defineStore } from 'pinia'
import { ref } from 'vue'

export type NotificationType = 'success' | 'error' | 'warning' | 'info'

export interface Notification {
  id: string
  type: NotificationType
  title?: string
  message: string
  duration?: number // в миллисекундах, 0 = не исчезает автоматически
  dismissible?: boolean
  actions?: NotificationAction[]
}

export interface NotificationAction {
  label: string
  action: () => void
  style?: 'primary' | 'secondary'
}

export interface NotificationOptions {
  type?: NotificationType
  title?: string
  duration?: number
  dismissible?: boolean
  actions?: NotificationAction[]
}

export const useNotificationStore = defineStore('notifications', () => {
  const notifications = ref<Notification[]>([])
  const timeouts = new Map<string, NodeJS.Timeout>()

  // Генерация уникального ID
  const generateId = (): string => {
    return `notification-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
  }

  // Добавление уведомления
  const add = (message: string, options: NotificationOptions = {}): string => {
    const id = generateId()
    
    const notification: Notification = {
      id,
      type: options.type || 'info',
      title: options.title,
      message,
      duration: options.duration !== undefined ? options.duration : getDefaultDuration(options.type || 'info'),
      dismissible: options.dismissible !== undefined ? options.dismissible : true,
      actions: options.actions
    }

    notifications.value.push(notification)

    // Автоматическое удаление через указанное время
    if (notification.duration && notification.duration > 0) {
      const timeout = setTimeout(() => {
        dismiss(id)
      }, notification.duration)
      
      timeouts.set(id, timeout)
    }

    return id
  }

  // Удаление уведомления
  const dismiss = (id: string): void => {
    const index = notifications.value.findIndex(n => n.id === id)
    if (index !== -1) {
      notifications.value.splice(index, 1)
    }

    // Очистка таймера
    const timeout = timeouts.get(id)
    if (timeout) {
      clearTimeout(timeout)
      timeouts.delete(id)
    }
  }

  // Удаление всех уведомлений
  const clear = (): void => {
    notifications.value = []
    
    // Очистка всех таймеров
    timeouts.forEach(timeout => clearTimeout(timeout))
    timeouts.clear()
  }

  // Получение времени по умолчанию для разных типов
  const getDefaultDuration = (type: NotificationType): number => {
    switch (type) {
      case 'success':
        return 3000
      case 'info':
        return 3000
      case 'warning':
        return 3000
      case 'error':
        return 3000
      default:
        return 3000
    }
  }

  // Удобные методы для разных типов уведомлений
  const success = (message: string, options: Omit<NotificationOptions, 'type'> = {}): string => {
    return add(message, { ...options, type: 'success' })
  }

  const error = (message: string, options: Omit<NotificationOptions, 'type'> = {}): string => {
    return add(message, { ...options, type: 'error' })
  }

  const warning = (message: string, options: Omit<NotificationOptions, 'type'> = {}): string => {
    return add(message, { ...options, type: 'warning' })
  }

  const info = (message: string, options: Omit<NotificationOptions, 'type'> = {}): string => {
    return add(message, { ...options, type: 'info' })
  }

  // Специальные методы для частых случаев
  const confirmAction = (
    message: string, 
    onConfirm: () => void, 
    options: Omit<NotificationOptions, 'type' | 'actions' | 'duration'> = {}
  ): string => {
    return add(message, {
      ...options,
      type: 'warning',
      duration: 0,
      actions: [
        {
          label: 'Отмена',
          action: () => {}, // Просто закроется
          style: 'secondary'
        },
        {
          label: 'Подтвердить',
          action: onConfirm,
          style: 'primary'
        }
      ]
    })
  }

  const loadingAction = (message: string, options: Omit<NotificationOptions, 'type'> = {}): string => {
    return add(message, {
      ...options,
      type: 'info',
      duration: 0,
      dismissible: false
    })
  }

  return {
    notifications,
    add,
    dismiss,
    clear,
    success,
    error,
    warning,
    info,
    confirmAction,
    loadingAction
  }
})
