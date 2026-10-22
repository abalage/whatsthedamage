<script setup lang="ts">
import { useGettext } from 'vue3-gettext'
import { RouterLink } from 'vue-router'

const { $gettext } = useGettext()
</script>

<template>
  <div class="container text-center mt-5">
    <h1>404</h1>
    <p class="mb-4">{{ $gettext('The page you are looking for does not exist.') }}</p>
    <RouterLink to="/" class="btn bg-surface-primary text-on-primary border-primary">
      {{ $gettext('Back to Home') }}
    </RouterLink>
  </div>
</template>
