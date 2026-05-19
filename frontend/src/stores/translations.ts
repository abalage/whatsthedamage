import { defineStore } from 'pinia'
import { ref } from 'vue'
import enTranslations from '../translations/en.json'
import huTranslations from '../translations/hu.json'
import { useLocaleStore } from './locale'

/**
 * Type representing all available locales
 */
export type Locale = 'en' | 'hu'

/**
 * Type representing translation key - must match keys in translation JSON files
 * This is inferred from the English translation file structure
 */
export type TranslationKeys = keyof typeof enTranslations

/**
 * Type representing all translations
 */
export interface Translations {
  en: typeof enTranslations
  hu: typeof huTranslations
}

/**
 * Translations store using Pinia
 *
 * This store manages translation data and provides type-safe access to translations.
 * It loads translations for all locales and provides a function to get translations
 * based on the current locale.
 */
export const useTranslationsStore = defineStore('translations', () => {
  // Internal state for translations
  const translations = ref<Translations>({
    en: enTranslations,
    hu: huTranslations
  })

  /**
   * Load translations (they're already loaded at module level via imports)
   * This function is kept for backward compatibility
   */
  const loadTranslations = (): void => {
    // Translations are loaded via static imports above
    translations.value = {
      en: enTranslations,
      hu: huTranslations
    }
  }

  /**
   * Get translation with type-safe key
   * @param key - Translation key (must exist in translation files)
   * @param localeParam - Locale (defaults to current locale from locale store)
   * @returns Translated string or the key if not found
   */
  const getTranslation = (key: TranslationKeys, localeParam?: Locale): string => {
    const localeStore = useLocaleStore()
    // Pinia automatically unwraps refs, so localeStore.locale is already a string
    const targetLocale: Locale = localeParam ?? (localeStore.locale as Locale)
    return translations.value[targetLocale]?.[key] ?? key
  }

  /**
   * Check if a translation key exists
   * @param key - Translation key to check
   * @param targetLocale - Locale to check in (defaults to 'en')
   * @returns Whether the key exists
   */
  const hasTranslation = (key: string, targetLocale: Locale = 'en'): boolean => {
    return key in translations.value[targetLocale]
  }

  /**
   * Get all translations for a specific locale
   * @param targetLocale - Locale to get translations for
   * @returns Translation object for the locale
   */
  const getLocaleTranslations = (targetLocale: Locale): Record<string, string> => {
    return translations.value[targetLocale]
  }

  return {
    translations,
    loadTranslations,
    getTranslation,
    hasTranslation,
    getLocaleTranslations
  }
})

/**
 * Standalone getTranslation function for backward compatibility
 * Uses the translations store internally
 * @param key - Translation key
 * @param locale - Locale (optional, defaults to current locale)
 * @returns Translated string or the key if not found
 */
export const getTranslation = (key: TranslationKeys, locale?: Locale): string => {
  const store = useTranslationsStore()
  return store.getTranslation(key, locale)
}

/**
 * Standalone loadTranslations function for backward compatibility
 */
export const loadTranslations = (): void => {
  const store = useTranslationsStore()
  store.loadTranslations()
}

// Export type
export type TranslationsStore = ReturnType<typeof useTranslationsStore>
