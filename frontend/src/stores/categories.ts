/**
 * Pinia store for category definitions
 * 
 * This store manages the list of available categories fetched from the backend.
 * Categories are used to translate category_id values to display names.
 */

import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { CategoryDefinition } from '../types/api.js';
import { fetchCategories } from '../js/api.js';
import { useLocaleStore } from './locale.js';

/**
 * Store for managing category definitions and translations
 */
export const useCategoriesStore = defineStore('categories', () => {
  const categories = ref<CategoryDefinition[]>([]);
  const isLoading = ref<boolean>(false);
  const error = ref<string | null>(null);

  /**
   * Fetch categories from the API
   */
  async function loadCategories(): Promise<void> {
    if (categories.value.length > 0) {
      // Already loaded
      return;
    }

    try {
      isLoading.value = true;
      error.value = null;
      categories.value = await fetchCategories();
    } catch (err) {
      error.value = err instanceof Error ? err.message : String(err);
      console.error('Failed to load categories:', err);
    } finally {
      isLoading.value = false;
    }
  }

  /**
   * Get category by ID
   * @param categoryId - The category ID to look up
   * @returns The CategoryDefinition or undefined if not found
   */
  function getCategoryById(categoryId: string): CategoryDefinition | undefined {
    return categories.value.find(cat => cat.id === categoryId);
  }

  /**
   * Get display name for a category ID
   * Uses the locale store for i18n translation
   * @param categoryId - The category ID to get display name for
   * @returns The localized display name, or the category_id if not found
   */
  function getCategoryDisplayName(categoryId: string): string {
    const category = getCategoryById(categoryId);
    if (category) {
      // Use the locale store's translation function
      const localeStore = useLocaleStore();
      return localeStore.translate(category.default_name);
    }
    // Fallback to the category_id if category not found
    return categoryId;
  }

  /**
   * Extract category_id from row/data object
   * Supports extraction from direct field or from category_url via regex
   * @param data - The data object containing category information
   * @returns The extracted category_id or empty string if not found
   */
  function extractCategoryIdFromData(data: Record<string, unknown>): string {
    const categoryUrl = data.category_url as string | undefined;
    const category_id = data.category_id as string | undefined;

    // Try to extract from category_url first (for drilldown responses)
    if (categoryUrl) {
      const match = categoryUrl.match(/categories\/([^/]+)\/months/);
      if (match) return match[1];
    }

    // Fall back to direct category_id field
    return category_id || '';
  }

  /**
   * Get all category IDs
   * @returns Array of all category IDs
   */
  const categoryIds = computed(() => categories.value.map(cat => cat.id));

  /**
   * Check if categories are loaded
   */
  const hasCategories = computed(() => categories.value.length > 0);

  return {
    categories,
    isLoading,
    error,
    loadCategories,
    getCategoryById,
    getCategoryDisplayName,
    extractCategoryIdFromData,
    categoryIds,
    hasCategories,
  };
});
