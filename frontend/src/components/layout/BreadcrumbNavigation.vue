<script setup lang="ts">
import type { BreadcrumbItem } from '../../composables/useDrilldownData.js'

defineProps<{
  items: BreadcrumbItem[]
}>()
</script>

<template>
  <nav v-if="items.length" aria-label="breadcrumb">
    <ol class="breadcrumb">
      <li
        v-for="(item, index) in items"
        :key="index"
        class="breadcrumb-item"
        :class="{ 'active': item.active }"
        :aria-current="item.active ? 'page' : undefined"
      >
        <router-link v-if="item.to && !item.active" :to="item.to">{{ item.name }}</router-link>
        <span v-else>{{ item.name }}</span>
      </li>
    </ol>
  </nav>
</template>
