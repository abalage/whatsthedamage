import { ref } from 'vue'

export const useLocaleStore = () => {
  const locale = ref<string>('en')

  const setLocale = (newLocale: string) => {
    locale.value = newLocale
    localStorage.setItem('locale', locale.value)
  }

  const loadLocale = () => {
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
}

export type LocaleStore = ReturnType<typeof useLocaleStore>