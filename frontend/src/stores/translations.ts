import { ref } from 'vue'
import enTranslations from '../translations/en.json'
import huTranslations from '../translations/hu.json'

interface Translations {
  [key: string]: Record<string, string>
}

export const translations = ref<Translations>({})

export const loadTranslations = async (): Promise<void> => {
  translations.value = {
    en: enTranslations,
    hu: huTranslations
  }
}

export const getTranslation = (key: string, locale: string = 'en'): string => {
  return translations.value[locale]?.[key] ?? key
}