<script setup lang="ts">
import { computed } from 'vue';
import { useGettext } from 'vue3-gettext';
import { useLocaleStore } from '../stores/locale';

type Variant = 'floating' | 'navbar';

withDefaults(defineProps<{ variant?: Variant }>(), { variant: 'floating' });

const FLAGS: Record<string, string> = {
  en: '🇬🇧',
  hu: '🇭🇺'
};

const { $gettext, available } = useGettext();
const localeStore = useLocaleStore();

const languages = computed(() =>
  Object.entries(available).map(([code, name]) => ({
    code,
    name,
    flag: FLAGS[code] ?? code.toUpperCase()
  }))
);
</script>

<template>
  <div v-if="variant === 'floating'" class="locale-switch" role="group" :aria-label="$gettext('Languages')">
    <button
      v-for="language in languages"
      :key="language.code"
      type="button"
      :class="{ active: localeStore.locale === language.code }"
      :aria-pressed="localeStore.locale === language.code"
      :aria-label="language.name"
      @click="localeStore.setLocale(language.code)"
    >
      {{ language.flag }} {{ language.name }}
    </button>
  </div>
  <li v-else class="nav-item dropdown">
    <button id="langDropdown" class="nav-link dropdown-toggle" type="button" data-bs-toggle="dropdown" aria-expanded="false" @keydown.enter.prevent="($event.currentTarget as HTMLButtonElement).click()" @keydown.space.prevent="($event.currentTarget as HTMLButtonElement).click()">
      {{ $gettext('Languages') }}
    </button>
    <ul class="dropdown-menu dropdown-menu-end" aria-labelledby="langDropdown">
      <li v-for="language in languages" :key="language.code">
        <button
          class="dropdown-item"
          :class="{ active: localeStore.locale === language.code }"
          type="button"
          @click.prevent="localeStore.setLocale(language.code)"
          @keydown.enter.prevent="localeStore.setLocale(language.code)"
          @keydown.space.prevent="localeStore.setLocale(language.code)"
        >
          {{ language.flag }} {{ language.name }}
        </button>
      </li>
    </ul>
  </li>
</template>

<style scoped>
.locale-switch {
  position: absolute;
  top: 1rem;
  right: 1rem;
  display: flex;
  gap: 0.5rem;
  z-index: 1;
}

.locale-switch button {
  background: var(--color-surface-base);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--border-radius);
  box-shadow: var(--box-shadow);
  padding: 0.25rem 0.75rem;
  font-size: 0.875rem;
  cursor: pointer;
  color: var(--color-text-on-light);
  transition: var(--transition);
}

.locale-switch button.active {
  background-color: var(--color-surface-primary);
  border-color: var(--color-surface-primary);
  color: var(--color-text-on-primary);
}
</style>
