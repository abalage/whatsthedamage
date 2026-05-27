// Vue module shim for TypeScript
declare module '*.vue' {
  import { DefineComponent } from 'vue'
  const component: DefineComponent<unknown, unknown, unknown>
  export default component
}

declare module '*.css' {
  const content: string
  export default content
}

// Type for translation keys used with vue3-gettext
export type TranslationKeys = string

// Extend ImportMeta to include custom environment variables
declare global {
  interface ImportMeta {
    env: ImportMetaEnv
  }
}

export interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string | undefined
  readonly PROD: boolean | undefined
  // Add other VITE_* variables as needed
}