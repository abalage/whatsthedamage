import { defineStore } from 'pinia'
import { useGettext } from 'vue3-gettext'
import { usePersistentRef } from '../composables/usePersistentRef'

const LOCALE_KEY = 'locale'

export const useLocaleStore = defineStore('locale', () => {
  const gettext = useGettext()
  const locale = usePersistentRef<string>(
    LOCALE_KEY,
    gettext.current,
    (value): value is string => typeof value === 'string' && value in gettext.available
  )

  const setLocale = (newLocale: string): void => {
    locale.value = newLocale
    gettext.current = newLocale
  }

  const loadLocale = (): void => {
    gettext.current = locale.value
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
