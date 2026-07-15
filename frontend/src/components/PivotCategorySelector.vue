<script setup lang="ts">
import { computed } from 'vue';
import { useGettext } from 'vue3-gettext';
import { usePivotStore } from '../stores/pivot.js';
import { useCategoriesStore } from '../stores/categories.js';
import CardComponent from '../components/ui/CardComponent.vue'

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
      <p class="text-muted small mb-3">
        {{ $gettext('Select which categories to include in your calculation. Your selection is saved automatically. (Defaults to categories belonging to "Cost of Living")') }}
      </p>

      <div class="d-flex gap-2 mb-3 flex-wrap">
        <button class="btn btn-sm btn-outline-success" :disabled="allSelected" @click="selectAll">
          <i class="bi bi-check-square me-1"></i> {{ $gettext('Select All') }}
        </button>
        <button class="btn btn-sm btn-outline-danger" :disabled="selectedCount === 0" @click="clearAll">
          <i class="bi bi-x-square me-1"></i> {{ $gettext('Clear All') }}
        </button>
        <button class="btn btn-sm btn-outline-secondary" @click="resetToDefaults">
          <i class="bi bi-arrow-clockwise me-1"></i> {{ $gettext('Reset to Defaults') }}
        </button>
      </div>

      <p class="small text-muted mb-2">
        <i class="bi bi-info-circle me-1"></i>
        {{ $gettext('Selected') }}: <strong>{{ selectedCount }}</strong> / {{ allCategories.length }}
        <span v-if="selectedCount > 0" class="ms-2">
          | {{ $gettext('Default categories') }}:
          <span class="badge bg-primary ms-1">{{ defaultCategories.length }}</span>
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
            class="category-label"
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
            <span class="category-name">{{ getCategoryDisplayName(category) }}</span>
            <span v-if="isDefaultCategory(category)" class="default-badge" :title="$gettext('Default category')">
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

.category-item.selected .category-label {
  background-color: #e7f1ff;
  border-color: #0d6efd;
  color: #0d6efd;
}

.category-item.default .category-label {
  border-style: dashed;
  background-color: #fff3cd;
}

.category-item.selected.default .category-label {
  border-style: dashed;
  background-color: #d0ebff;
}

.category-label {
  align-items: center;
  padding: 8px;
  border: 1px solid #dee2e6;
  border-radius: 6px;
  transition: all 0.2s ease;
  background-color: white;
  font-size: 0.875rem;
  cursor: pointer;
}

.category-label:hover {
  background-color: #f8f9fa;
  border-color: #adb5bd;
}

.category-label:focus {
  outline: 2px solid #0d6efd;
  outline-offset: 2px;
}

.category-checkbox {
  color: #0d6efd;
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
  color: #ffc107;
  font-size: 0.75rem;
}
</style>