<template>
  <div class="auth-container">
    <div class="auth-card">
      <div class="auth-header">
        <router-link to="/" class="logo">
          <svg
            class="arrow-icon"
            xmlns="http://www.w3.org/2000/svg"
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <line x1="19" y1="12" x2="5" y2="12"></line>
            <polyline points="12 19 5 12 12 5"></polyline>
          </svg>
          <Logo />
        </router-link>
      </div>

      <!-- Login Form -->
      <div v-if="!isRegisterMode" class="auth-form">
        <h2 class="form-title">Добро пожаловать</h2>
        <p class="form-subtitle">Войдите для продолжения</p>

        <form @submit.prevent="handleLogin" class="form">
          <div class="form-group">
            <label for="loginId" class="form-label">Табельный номер</label>
            <input
              id="loginId"
              v-model="loginForm.employee_id"
              type="text"
              class="form-input"
              placeholder="Введите ваш табельный номер"
              required
            />
          </div>

          <div class="form-group">
            <label for="password" class="form-label">Пароль</label>
            <input
              id="password"
              v-model="loginForm.password"
              type="password"
              class="form-input"
              placeholder="••••••••••"
              required
            />
          </div>

          <button type="submit" class="submit-btn" :disabled="isLoading">
            {{ isLoading ? 'Вход в систему...' : 'Войти' }}
          </button>
        </form>

        <p class="auth-switch">
          Нет аккаунта? 
          <button @click="toggleMode" class="link-btn">Зарегистрироваться</button>
        </p>
      </div>

      <!-- Register Form -->
      <div v-else class="auth-form">
        <h2 class="form-title">Создать аккаунт</h2>
        <p class="form-subtitle">Присоединяйтесь для управления инструментами</p>

        <form @submit.prevent="handleRegister" class="form">
          <div class="form-group">
            <label for="employeeId" class="form-label">Табельный номер</label>
            <input
              id="employeeId"
              v-model="registerForm.employee_id"
              type="text"
              class="form-input"
              placeholder="Введите уникальный табельный номер"
              required
            />
          </div>

          <div class="form-group">
            <label for="registerPassword" class="form-label">Пароль</label>
            <input
              id="registerPassword"
              v-model="registerForm.password"
              type="password"
              class="form-input"
              placeholder="Создайте надёжный пароль"
              required
            />
          </div>

          <div class="form-group">
            <label for="confirmPassword" class="form-label">Повторите пароль</label>
            <input
              id="confirmPassword"
              v-model="registerForm.confirmPassword"
              type="password"
              class="form-input"
              :class="{ 'password-mismatch': !passwordsMatch }"
              placeholder="Повторите пароль"
              required
            />
            <div v-if="registerForm.confirmPassword && !passwordsMatch" class="password-error">
              Пароли не совпадают
            </div>
          </div>

          <div class="form-group">
            <label for="role" class="form-label">Роль (тестирование)</label>
            <select id="role" v-model="registerForm.role" class="form-input">
              <option value="simple">Пользователь</option>
              <option value="admin">Администратор</option>
            </select>
          </div>

          <button type="submit" class="submit-btn" :disabled="isLoading">
            {{ isLoading ? 'Создание аккаунта...' : 'Создать аккаунт' }}
          </button>
        </form>

        <p class="auth-switch">
          Уже есть аккаунт? 
          <button @click="toggleMode" class="link-btn">Войти</button>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useNotificationStore } from '@/stores/notifications'
import Logo from '@/components/Logo.vue'

const router = useRouter()
const authStore = useAuthStore()
const notifications = useNotificationStore()

const isRegisterMode = ref(false)
const isLoading = ref(false)

const loginForm = reactive({
  employee_id: '',
  password: ''
})

const registerForm = reactive({
  employee_id: '',
  password: '',
  confirmPassword: '',
  role: 'simple' as 'simple' | 'admin'
})

// Check if passwords match
const passwordsMatch = computed(() => {
  if (!registerForm.password || !registerForm.confirmPassword) return true
  return registerForm.password === registerForm.confirmPassword
})

const toggleMode = () => {
  isRegisterMode.value = !isRegisterMode.value
  // Reset forms
  Object.assign(loginForm, { employee_id: '', password: '' })
  Object.assign(registerForm, { 
    employee_id: '', 
    password: '',
    confirmPassword: '',
    role: 'simple'
  })
}

const handleLogin = async () => {
  isLoading.value = true
  try {
    await authStore.login({
      employee_id: loginForm.employee_id,
      password: loginForm.password
    })
    router.push('/dashboard') // Redirect to dashboard after successful login
  } catch (error: any) {
    console.error('Login failed:', error)
    notifications.error(error.message || 'Неверный логин или пароль. Проверьте введённые данные и попробуйте ещё раз.', {
      title: 'Ошибка входа'
    })
  } finally {
    isLoading.value = false
  }
}

const handleRegister = async () => {
  // Validate password confirmation
  if (registerForm.password !== registerForm.confirmPassword) {
    notifications.warning('Пароли не совпадают. Пожалуйста, проверьте введённые данные.', {
      title: 'Ошибка валидации'
    })
    return
  }

  isLoading.value = true
  try {
    // Pass data in API format
    await authStore.register({
      employee_id: registerForm.employee_id,
      password: registerForm.password,
      role: registerForm.role
    })
    router.push('/dashboard') // Redirect to dashboard after successful registration
  } catch (error: any) {
    console.error('Registration failed:', error)
    notifications.error(error.message || 'Не удалось создать аккаунт. Возможно, пользователь с таким логином уже существует.', {
      title: 'Ошибка регистрации'
    })
  } finally {
    isLoading.value = false
  }
}
</script>

<style scoped>
.auth-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.auth-card {
  background: rgba(30, 41, 59, 0.8);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(71, 85, 105, 0.3);
  border-radius: 16px;
  padding: 40px;
  width: 100%;
  max-width: 480px;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
}

.auth-header {
  text-align: center;
  margin-bottom: 32px;
}

.logo {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  font-size: 24px;
  font-weight: 600;
  color: #f1f5f9;
  margin-bottom: 8px;
  text-decoration: none;
  transition: opacity 0.2s;
}

.logo:hover {
  opacity: 0.8;
}

.logo .arrow-icon {
  width: 22px;
  height: 22px;
  color: #94a3b8;
  transition:
    color 0.2s ease-in-out,
    transform 0.2s ease-in-out;
}

.logo:hover .arrow-icon {
  color: #f1f5f9;
  transform: translateX(-4px);
}

.logo svg {
  color: #3b82f6;
}

.auth-form {
  width: 100%;
}

.form-title {
  font-size: 28px;
  font-weight: 700;
  color: #f1f5f9;
  text-align: center;
  margin-bottom: 8px;
}

.form-subtitle {
  color: #94a3b8;
  text-align: center;
  margin-bottom: 32px;
  font-size: 16px;
}

.form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-label {
  color: #cbd5e1;
  font-size: 14px;
  font-weight: 500;
}

.form-input, select.form-input {
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(71, 85, 105, 0.4);
  border-radius: 8px;
  padding: 12px 16px;
  color: #f1f5f9;
  font-size: 16px;
  transition: all 0.2s;
}

.form-input:focus, select.form-input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.form-input::placeholder {
  color: #64748b;
}

.form-input.password-mismatch {
  border-color: #ef4444;
  box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.1);
}

.password-error {
  color: #ef4444;
  font-size: 12px;
  margin-top: 4px;
  font-weight: 500;
}

.submit-btn {
  background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
  color: white;
  border: none;
  border-radius: 8px;
  padding: 14px 24px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  margin-top: 8px;
}

.submit-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 10px 25px -5px rgba(59, 130, 246, 0.4);
}

.submit-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.auth-switch {
  text-align: center;
  margin-top: 24px;
  color: #94a3b8;
  font-size: 14px;
}

.link-btn {
  color: #3b82f6;
  background: none;
  border: none;
  cursor: pointer;
  font-weight: 600;
  text-decoration: underline;
}

.link-btn:hover {
  color: #60a5fa;
}

@media (max-width: 640px) {
  .auth-card {
    padding: 24px;
  }
  
  .form-row {
    grid-template-columns: 1fr;
  }
}
</style>
