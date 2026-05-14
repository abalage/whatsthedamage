import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useLocaleStore = defineStore('locale', () => {
  const locale = ref<string>('en')

  const setLocale = (newLocale: string): void => {
    locale.value = newLocale
    localStorage.setItem('locale', locale.value)
  }

  const loadLocale = (): void => {
    const savedLocale = localStorage.getItem('locale')
    if (savedLocale) {
      locale.value = savedLocale
    }
  }

  return {
    locale,
    setLocale,
    loadLocale
  }
})

export type LocaleStore = ReturnType<typeof useLocaleStore>