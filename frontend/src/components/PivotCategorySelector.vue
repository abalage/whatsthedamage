<script setup lang="ts">
import { computed } from 'vue';
import { useGettext } from 'vue3-gettext';
import { usePivotStore } from '../stores/pivot.js';
import { useCategoriesStore } from '../stores/categories.js';
import CardComponent from '../components/ui/CardComponent.vue'
import ButtonComponent from '../components/ui/ButtonComponent.vue'

const { $gettext } = useGettext();
const pivotStore = usePivotStore();
const categoriesStore = useCategoriesStore();

const allCategories = computed(() => pivotStore.availableCategoryNames);
const selectedCategories = computed(() => pivotStore.selectedCategoryIds);
const defaultCategories = computed(() => pivotStore.defaultCostOfLivingCategoryIds);

const isSelected = (categoryId: string): boolean => selectedCategories.value.includes(categoryId);
const isDefaultCategory = (categoryId: string): boolean => defaultCategories.value.includes(categoryId);

const toggleCategory = (categoryId: string) => pivotStore.toggleCategory(categoryId);
const selectAll = () => pivotStore.selectAll();
const clearAll = () => pivotStore.clearAll();
const resetToDefaults = () => pivotStore.resetToDefaults();

const selectedCount = computed(() => selectedCategories.value.length);
const hasNoAllCategories = computed(() => allCategories.value.length === 0);
const allSelected = computed(() => selectedCategories.value.length === allCategories.value.length && !hasNoAllCategories.value);

// Use categories store to get proper display name with translation
const getCategoryDisplayName = (categoryId: string): string => categoriesStore.getCategoryDisplayName(categoryId);
</script>

<template>
  <div class="category-selector mb-4">
    <CardComponent :title="$gettext('Select Categories')" class="mb-4" width="auto">
      <p class="text-secondary small mb-3">
        {{ $gettext('Select which categories to include in your calculation. Your selection is saved automatically. (Defaults to categories belonging to "Cost of Living")') }}
      </p>

      <div class="d-flex gap-2 mb-3 flex-wrap">
        <ButtonComponent
          icon="bi bi-check-square"
          :text="$gettext('Select All')"
          variant="success"
          size="sm"
          :disabled="allSelected"
          @click="selectAll"
        />
        <ButtonComponent
          icon="bi bi-x-square"
          :text="$gettext('Clear All')"
          variant="danger"
          size="sm"
          :disabled="selectedCount === 0"
          @click="clearAll"
        />
        <ButtonComponent
          icon="bi bi-arrow-clockwise"
          :text="$gettext('Reset to Defaults')"
          variant="outline-secondary"
          size="sm"
          @click="resetToDefaults"
        />
      </div>

      <p class="small text-secondary mb-2">
        <i class="bi bi-info-circle me-1"></i>
        {{ $gettext('Selected') }}: <strong>{{ selectedCount }}</strong> / {{ allCategories.length }}
        <span v-if="selectedCount > 0" class="ms-2">
          | {{ $gettext('Default categories') }}:
          <span class="bg-surface-primary text-on-primary px-2 py-1 rounded text-xs ms-1">{{ defaultCategories.length }}</span>
        </span>
      </p>

      <fieldset class="category-grid" aria-label="Selected Categories">
        <div
          v-for="category in allCategories.filter(c => c)"
          :key="category"
          class="category-item"
          :class="{
            selected: isSelected(category),
            default: isDefaultCategory(category)
          }"
        >
          <button
            class="btn px-2 py-1 text-sm rounded-sm border-primary bg-surface-elevated text-primary"
            :class="{
              'bg-status-success text-on-dark': isSelected(category),
              'bg-surface-secondary': isDefaultCategory(category) && !isSelected(category)
            }"
            type="button"
            :aria-pressed="isSelected(category)"
            :aria-label="`${getCategoryDisplayName(category)}, ${isSelected(category) ? $gettext('selected, press to deselect') : $gettext('not selected, press to select')}`"
            tabindex="0"
            @click.stop="toggleCategory(category)"
            @keydown.enter.stop="toggleCategory(category)"
            @keydown.space.stop="toggleCategory(category)"
          >
            <span class="category-checkbox">
              <i v-if="isSelected(category)" class="bi bi-check-square-fill"></i>
              <i v-else class="bi bi-square"></i>
            </span>
            <span class="category-name">
              {{ getCategoryDisplayName(category) }}
            </span>
            <span v-if="isDefaultCategory(category)" class="default-badge text-status-warning" :title="$gettext('Default category')">
              <i class="bi bi-star-fill"></i>
            </span>
          </button>
        </div>
      </fieldset>
    </CardComponent>
  </div>
</template>

<style scoped>
.category-selector {
  margin-left: auto;
  margin-right: auto;
}

.category-grid {
  display: grid;
  grid-template-columns: repeat(5, auto);
  gap: 8px;
}

.category-item {
  cursor: pointer;
}

.category-grid button {
  display: flex;
  align-items: center;
  border: 1px solid;
  transition: all 0.2s ease;
  cursor: pointer;
  width: 100%;
}

.category-grid button:focus {
  outline: 2px solid;
  outline-offset: 2px;
}

.category-checkbox {
  font-size: 1.1rem;
  min-width: 20px;
  text-align: center;
}

.category-checkbox i {
  pointer-events: none;
}

.default-badge i {
  pointer-events: none;
}

.category-name {
  flex: 1;
  padding: 8px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.default-badge {
  font-size: 0.75rem;
}
</style>
