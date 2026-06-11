import { defineStore } from 'pinia'
import { ref, inject } from 'vue'
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

  /**
   * Translate a string using gettext's $gettext function
   * @param text - The text to translate
   * @returns The translated text
   */
  const translate = (text: string): string => {
    // The $gettext function is available globally from the vue3-gettext plugin
    // We need to access it through the injected gettext object
    return gettext.$gettext(text)
  }

  return {
    locale,
    setLocale,
    loadLocale,
    translate
  }
})
