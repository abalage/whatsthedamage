<script setup lang="ts">
import { useGettext } from 'vue3-gettext'

const { $gettext } = useGettext()
</script>

<template>
  <div class="text-center my-5">
    <output class="spinner-border text-on-primary">
      <span class="visually-hidden">{{ $gettext('loading') }}...</span>
    </output>
    <p class="mt-2">{{ $gettext('Loading data') }}...</p>
  </div>
</template>
