/// <reference types="vite/client" />

// Vue module shim for TypeScript
declare module '*.vue' {
  import { DefineComponent } from 'vue'
  const component: DefineComponent<unknown, unknown, unknown>
  export default component
}

// CSS module shim
declare module '*.css' {
  const content: string
  export default content
}
