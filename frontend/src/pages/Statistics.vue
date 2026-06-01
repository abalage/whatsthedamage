<script setup lang="ts">
import { useGettext } from 'vue3-gettext'

const { $gettext } = useGettext()

</script>

<template>
  <div class="container">
    <h1>{{ $gettext('What\'s the Damage') }} - Statistical Analysis</h1>
    <p>This page will display statistical analysis of your transactions.</p>
    <div class="alert alert-info">
      Statistical analysis will be shown here after processing your data.
    </div>
  </div>
</template>
