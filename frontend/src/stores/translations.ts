import { ref } from 'vue'
import enTranslations from '../translations/en.json'
import huTranslations from '../translations/hu.json'

// Note: This module uses plain reactive refs instead of Pinia because:
// 1. Translations need to be accessed at module load time (before Pinia is installed)
// 2. The getTranslation function is imported directly in many components
// 3. Pinia stores cannot be accessed outside of component setup
// This is an intentional architectural decision for backward compatibility.

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

// Internal state - can be accessed at module level since it's not a Pinia store
const translations = ref<Translations>({})

const loadTranslations = async (): Promise<void> => {
  translations.value = {
    en: enTranslations,
    hu: huTranslations
  }
}

/**
 * Get translation with type-safe key
 * @param key - Translation key (must exist in translation files)
 * @param locale - Locale (defaults to 'en')
 * @returns Translated string or the key if not found
 */
const getTranslation = (key: TranslationKeys, locale: Locale = 'en'): string => {
  return translations.value[locale]?.[key] ?? key
}

// Export as factory function for consistency with other stores
export const useTranslationsStore = (): {
  translations: typeof translations
  loadTranslations: () => Promise<void>
  getTranslation: (key: TranslationKeys, locale?: Locale) => string
} => {
  return {
    translations,
    loadTranslations,
    getTranslation
  }
}

// Export individual properties for backward compatibility
// These can be accessed at module level (not Pinia stores)
export { translations, loadTranslations, getTranslation }