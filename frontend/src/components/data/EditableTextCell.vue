<script setup lang="ts">
/**
 * EditableTextCell - Inline free-text editor for VueDataTable cells.
 *
 * Click-to-edit cell for correctable text fields (merchant, notice).
 * The persistence logic is injected through the `save` prop; Enter or
 * the Save button commits the new value, Esc, the Cancel button, or
 * losing focus discards it. With `applyToFuture` enabled an "apply to
 * future transactions" checkbox is offered and its state is passed to
 * `save` as the second argument.
 */

import { nextTick, ref } from 'vue'
import { useGettext } from 'vue3-gettext'

interface Props {
  /** Current value displayed in the cell */
  value: string
  /** Maximum accepted length (matches the backend column size) */
  maxLength: number
  /** Whether an empty value may be saved (false for required fields) */
  allowEmpty?: boolean
  /** Whether to offer the "apply to future transactions" toggle */
  applyToFuture?: boolean
  /** Persists the new value; rejects with an error message on failure.
   *  The second argument is the toggle state, passed when applyToFuture
   *  is enabled. */
  save: (value: string, applyToFuture?: boolean) => Promise<unknown>
}

const props = withDefaults(defineProps<Props>(), {
  allowEmpty: true,
  applyToFuture: false
})

const { $gettext } = useGettext()
const editing = ref(false)
const draft = ref('')
const saving = ref(false)
const error = ref<string | undefined>(undefined)
const input = ref<HTMLInputElement | undefined>(undefined)
const applyToFutureChecked = ref(true)

async function startEdit(): Promise<void> {
  if (saving.value) return
  draft.value = props.value
  error.value = undefined
  applyToFutureChecked.value = true
  editing.value = true
  await nextTick()
  input.value?.focus()
}

function cancelEdit(): void {
  if (saving.value) return
  editing.value = false
  error.value = undefined
}

async function commit(): Promise<void> {
  if (saving.value) return
  const trimmed = draft.value.trim()
  if (trimmed.length > props.maxLength) {
    error.value = $gettext('Value is too long')
    return
  }
  if (trimmed === '' && !props.allowEmpty) {
    error.value = $gettext('Value must not be empty')
    return
  }
  if (trimmed === props.value) {
    editing.value = false
    error.value = undefined
    return
  }
  saving.value = true
  error.value = undefined
  try {
    if (props.applyToFuture) {
      await props.save(trimmed, applyToFutureChecked.value)
    } else {
      await props.save(trimmed)
    }
    editing.value = false
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err)
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <button
    v-if="!editing"
    type="button"
    class="editable-cell-trigger"
    :title="$gettext('Click to edit')"
    @click="startEdit"
  >
    {{ value }}
  </button>
  <div v-else class="editable-cell-editor">
    <input
      ref="input"
      v-model="draft"
      type="text"
      class="form-control form-control-sm"
      :maxlength="maxLength"
      :disabled="saving"
      @keydown.enter.prevent="commit"
      @keydown.esc.prevent="cancelEdit"
      @blur="cancelEdit"
    >
    <label
      v-if="applyToFuture"
      class="apply-future-toggle"
      :title="$gettext('Apply to all future transactions of this merchant')"
      @mousedown.prevent
    >
      <input
        type="checkbox"
        v-model="applyToFutureChecked"
        :disabled="saving"
      >
      {{ $gettext('Apply to future') }}
    </label>
    <button
      type="button"
      class="btn btn-sm bg-surface-secondary text-on-dark border-secondary"
      :disabled="saving"
      @mousedown.prevent
      @click="commit"
    >
      {{ $gettext('Save') }}
    </button>
    <button
      type="button"
      class="btn btn-sm bg-surface-secondary text-on-dark border-secondary"
      :disabled="saving"
      @mousedown.prevent
      @click="cancelEdit"
    >
      {{ $gettext('Cancel') }}
    </button>
  </div>
  <div v-if="error" class="text-danger small">
    {{ error }}
  </div>
</template>

<style scoped>
.editable-cell-trigger {
  all: unset;
  cursor: pointer;
  width: 100%;
}

.editable-cell-trigger:hover {
  text-decoration: underline dotted;
}

.editable-cell-trigger:focus-visible {
  outline: 2px solid currentColor;
  outline-offset: 1px;
}

.editable-cell-editor {
  display: flex;
  gap: 0.25rem;
  align-items: center;
}

.apply-future-toggle {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.75rem;
  white-space: nowrap;
  cursor: pointer;
}
</style>
