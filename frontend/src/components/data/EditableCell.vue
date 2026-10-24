<script setup lang="ts">
/**
 * EditableCell - Inline editor for VueDataTable cells.
 *
 * Click-to-edit cell with either a category dropdown (editor='select',
 * options from the categories store) or a free-text input
 * (editor='text', for merchant and notice). The persistence logic is
 * injected through the `save` prop; Enter or the Save button commits
 * the new value, Esc, the Cancel button, or losing focus discards it.
 * With `applyToFuture` enabled an "apply to future transactions"
 * checkbox is offered and its state is passed to `save` as the
 * second argument.
 */

import { computed, nextTick, onMounted, ref } from 'vue'
import { useGettext } from 'vue3-gettext'
import { useCategoriesStore } from '../../stores/categories'
import { UNCATEGORIZED } from '../../composables/useTransactionCorrections'

interface Props {
  /** Editor kind: category dropdown or free-text input */
  editor: 'select' | 'text'
  /** Current raw value ('uncategorized' marks an empty category) */
  value: string
  /** Maximum accepted length, matches the backend column (text only) */
  maxLength?: number
  /** Whether an empty value may be saved (text only) */
  allowEmpty?: boolean
  /** Whether to offer the "apply to future transactions" toggle */
  applyToFuture?: boolean
  /** Persists the new value (null clears the category); rejects on
   *  failure. The second argument is the toggle state, passed when
   *  applyToFuture is enabled. */
  save: (value: string | null, applyToFuture?: boolean) => Promise<unknown>
}

const props = withDefaults(defineProps<Props>(), {
  maxLength: 500,
  allowEmpty: true,
  applyToFuture: false
})

const { $gettext } = useGettext()
const categoriesStore = useCategoriesStore()
const editing = ref(false)
const draft = ref('')
const saving = ref(false)
const error = ref<string | undefined>(undefined)
const select = ref<HTMLSelectElement | undefined>(undefined)
const input = ref<HTMLInputElement | undefined>(undefined)
const applyToFutureChecked = ref(true)

const isSelect = computed(() => props.editor === 'select')

onMounted(() => {
  if (isSelect.value) {
    categoriesStore.loadCategories()
  }
})

const displayName = computed(() =>
  isSelect.value
    ? categoriesStore.getCategoryDisplayName(props.value)
    : props.value
)

const options = computed(() => categoriesStore.categories.map(cat => ({
  value: cat.id,
  label: categoriesStore.getCategoryDisplayName(cat.id),
})))

const currentValue = computed<string | null>(() =>
  isSelect.value
    ? props.value === UNCATEGORIZED ? null : props.value
    : props.value
)

async function startEdit(): Promise<void> {
  if (saving.value) return
  if (isSelect.value) {
    await categoriesStore.loadCategories()
  }
  draft.value = currentValue.value ?? ''
  error.value = undefined
  applyToFutureChecked.value = true
  editing.value = true
  await nextTick()
  if (isSelect.value) {
    select.value?.focus()
  } else {
    input.value?.focus()
  }
}

function cancelEdit(): void {
  if (saving.value) return
  editing.value = false
  error.value = undefined
}

async function commit(): Promise<void> {
  if (saving.value) return
  let nextValue: string | null
  if (isSelect.value) {
    nextValue = draft.value === '' ? null : draft.value
  } else {
    const trimmed = draft.value.trim()
    if (trimmed.length > props.maxLength) {
      error.value = $gettext('Value is too long')
      return
    }
    if (trimmed === '' && !props.allowEmpty) {
      error.value = $gettext('Value must not be empty')
      return
    }
    nextValue = trimmed
  }
  if (nextValue === currentValue.value) {
    editing.value = false
    error.value = undefined
    return
  }
  saving.value = true
  error.value = undefined
  try {
    if (props.applyToFuture) {
      await props.save(nextValue, applyToFutureChecked.value)
    } else {
      await props.save(nextValue)
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
    {{ displayName }}
  </button>
  <div v-else class="editable-cell-editor">
    <select
      v-if="isSelect"
      ref="select"
      v-model="draft"
      class="form-select form-select-sm"
      :disabled="saving"
      @keydown.esc.prevent="cancelEdit"
      @blur="cancelEdit"
    >
      <option value="">{{ $gettext('Uncategorized') }}</option>
      <option v-for="option in options" :key="option.value" :value="option.value">
        {{ option.label }}
      </option>
    </select>
    <input
      v-else
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
        v-model="applyToFutureChecked"
        type="checkbox"
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
