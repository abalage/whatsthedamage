import { createGettext } from 'vue3-gettext'
import translations from '../locales/translations.json'

export default createGettext({
  defaultLanguage: 'en',
  availableLanguages: {
    en: 'English',
    hu: 'Magyar'
  },
  translations,
  silent: import.meta.env.PROD // Silent in production
})
