/**
 * Global frontend error handlers.
 *
 * Captures otherwise-unobserved Vue errors and unhandled promise
 * rejections and routes them to the console logger. There is
 * deliberately no reporting endpoint: stack traces and messages can
 * contain user data, and the backend already logs unexpected /api/*
 * failures server-side (api/error_handlers.py). Log the error
 * message and component info only, never payloads.
 * @module utils/errorHandling
 */

import type { App, ComponentPublicInstance } from 'vue'
import { logger } from './logger'

/**
 * Install the global error handlers on a Vue app instance.
 *
 * @param app - Vue application instance
 */
export function installGlobalErrorHandlers(app: App): void {
  app.config.errorHandler = (err: unknown, _instance: ComponentPublicInstance | null, info: string): void => {
    const message = err instanceof Error ? err.message : String(err)
    logger.error(`Unhandled Vue error: ${message} (${info})`)
  }

  window.addEventListener('unhandledrejection', (event: PromiseRejectionEvent): void => {
    const reason = event.reason
    const message = reason instanceof Error ? reason.message : String(reason)
    logger.error(`Unhandled promise rejection: ${message}`)
  })
}
