import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface RecognitionData {
  image: string
  threshold: number
  fileName: string
  fileSize: number
  timestamp: number
}

export const useRecognitionStore = defineStore('recognition', () => {
  const recognitionData = ref<RecognitionData | null>(null)

  const setRecognitionData = (data: RecognitionData) => {
    recognitionData.value = data
  }

  const clearRecognitionData = () => {
    recognitionData.value = null
  }

  return {
    recognitionData,
    setRecognitionData,
    clearRecognitionData,
  }
})
