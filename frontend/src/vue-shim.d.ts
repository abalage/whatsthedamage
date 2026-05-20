declare module '*.vue' {
  import { DefineComponent } from 'vue'
  const component: DefineComponent<unknown, unknown, unknown>
  export default component
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string | undefined
  // Add other VITE_* variables as needed
}