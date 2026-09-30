<script setup lang="ts">
/**
 * EditableCategoryCell - Inline category dropdown for VueDataTable cells.
 *
 * Click-to-edit cell that corrects the category of a transaction with
 * a value picked from the category list provided by the backend.
 * The persistence logic is injected through the `save` prop; the Save
 * button commits the selection, Esc, the Cancel button, or losing
 * focus discards it.
 */

import { computed, nextTick, onMounted, ref } from 'vue'
import { useGettext } from 'vue3-gettext'
import { useCategoriesStore } from '../../stores/categories.js'

/** Category id marker used by the frontend for uncategorized transactions */
const UNCATEGORIZED = 'uncategorized'

interface Props {
  /** Raw category id ('uncategorized' when the transaction has none) */
  categoryId: string
  /** Persists the new category id (null clears it); rejects on failure */
  save: (categoryId: string | null) => Promise<unknown>
}

const props = defineProps<Props>()

const { $gettext } = useGettext()
const categoriesStore = useCategoriesStore()
const editing = ref(false)
const draft = ref('')
const saving = ref(false)
const error = ref<string | undefined>(undefined)
const select = ref<HTMLSelectElement | undefined>(undefined)

onMounted(() => {
  categoriesStore.loadCategories()
})

const displayName = computed(() => categoriesStore.getCategoryDisplayName(props.categoryId))

const options = computed(() => categoriesStore.categories.map(cat => ({
  value: cat.id,
  label: categoriesStore.getCategoryDisplayName(cat.id),
})))

async function startEdit(): Promise<void> {
  if (saving.value) return
  await categoriesStore.loadCategories()
  draft.value = props.categoryId === UNCATEGORIZED ? '' : props.categoryId
  error.value = undefined
  editing.value = true
  await nextTick()
  select.value?.focus()
}

function cancelEdit(): void {
  if (saving.value) return
  editing.value = false
  error.value = undefined
}

async function commit(): Promise<void> {
  if (saving.value) return
  const nextValue = draft.value === '' ? null : draft.value
  const currentValue = props.categoryId === UNCATEGORIZED ? null : props.categoryId
  if (nextValue === currentValue) {
    editing.value = false
    error.value = undefined
    return
  }
  saving.value = true
  error.value = undefined
  try {
    await props.save(nextValue)
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
</style>
