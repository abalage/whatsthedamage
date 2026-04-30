import { ref } from 'vue'
import enTranslations from '../translations/en.json'
import huTranslations from '../translations/hu.json'

export const translations = ref<Record<string, any>>({})

export const loadTranslations = async () => {
  translations.value = {
    en: enTranslations,
    hu: huTranslations
  }
}

export const getTranslation = (key: string, locale: string = 'en'): string => {
  return translations.value[locale]?.[key] || key
}