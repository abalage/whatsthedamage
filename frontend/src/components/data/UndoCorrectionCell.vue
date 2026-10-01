<script setup lang="ts">
/**
 * UndoCorrectionCell - Undo button for VueDataTable cells.
 *
 * Renders nothing until the row's transaction carries corrections.
 * Clicking the button restores the original values through the
 * injected `undo` prop, which also refreshes the row.
 */

import { ref } from 'vue'
import { useGettext } from 'vue3-gettext'

interface Props {
  /** Whether the row's transaction has any corrections */
  corrected: boolean
  /** Restores the original values and refreshes the row; rejects
   *  with an error message on failure */
  undo: () => Promise<unknown>
}

const props = defineProps<Props>()

const { $gettext } = useGettext()
const undoing = ref(false)
const error = ref<string | undefined>(undefined)

async function undoCorrections(): Promise<void> {
  if (undoing.value) return
  undoing.value = true
  error.value = undefined
  try {
    await props.undo()
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err)
  } finally {
    undoing.value = false
  }
}
</script>

<template>
  <button
    v-if="corrected"
    type="button"
    class="btn btn-sm bg-surface-secondary text-on-dark border-secondary text-nowrap"
    :title="$gettext('Undo corrections')"
    :disabled="undoing"
    @click="undoCorrections"
  >
    <span
      v-if="undoing"
      class="spinner-border spinner-border-sm"
    ></span>
    <i v-else class="bi bi-arrow-counterclockwise"></i>
    {{ $gettext('Undo') }}
  </button>
  <div v-if="error" class="text-danger small">
    {{ error }}
  </div>
</template>
