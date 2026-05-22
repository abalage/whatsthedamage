import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useGettext } from 'vue3-gettext'

export const useLocaleStore = defineStore('locale', () => {
  const locale = ref<string>('en')
  const gettext = useGettext()

  const setLocale = (newLocale: string): void => {
    locale.value = newLocale
    gettext.current = newLocale
    localStorage.setItem('locale', locale.value)
  }

  const loadLocale = (): void => {
    const savedLocale = localStorage.getItem('locale')
    if (savedLocale) {
      locale.value = savedLocale
      gettext.current = savedLocale
    }
  }

  return {
    locale,
    setLocale,
    loadLocale
  }
})
