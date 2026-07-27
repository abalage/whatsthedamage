import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useGettext } from 'vue3-gettext'

export const useLocaleStore = defineStore('locale', () => {
  const gettext = useGettext()
  const locale = ref<string>(gettext.current)

  const setLocale = (newLocale: string): void => {
    locale.value = newLocale
    gettext.current = newLocale
    localStorage.setItem('locale', newLocale)
  }

  const loadLocale = (): void => {
    const savedLocale = localStorage.getItem('locale')
    if (savedLocale) {
      locale.value = savedLocale
      gettext.current = savedLocale
    }
  }

  /**
   * Translate a string using gettext's $gettext function
   * @param text - The text to translate
   * @returns The translated text
   */
  const translate = (text: string): string => {
    return gettext.$gettext(text)
  }

  return {
    locale,
    setLocale,
    loadLocale,
    translate
  }
})
