<!--
  Authentication Layout Component

  Wrapper component for authentication pages (Login, Register).
  Provides consistent styling and layout for auth-related views.
  Styling comes from the shared css/auth.css.
-->

<script setup lang="ts">
import { computed } from 'vue';
import { useRoute } from 'vue-router';
import { buildRedirectQuery, safeRedirectParam } from '../js/routeUtils';

const route = useRoute();

// Preserve a pending post-login redirect when bouncing back to the landing page
const redirectQuery = computed(() => buildRedirectQuery(safeRedirectParam(route.query)));
</script>

<template>
  <div class="auth-layout">
    <div class="auth-container">
      <div class="auth-header">
        <h1 class="app-title">
          <router-link class="app-title-link" :to="{ name: 'landing', query: redirectQuery }">What's the Damage</router-link>
        </h1>
      </div>

      <main class="auth-main">
        <slot></slot>
      </main>

      <div class="auth-footer">
        <p class="footer-text">
          &copy; {{ new Date().getFullYear() }} What's the Damage
        </p>
      </div>
    </div>
  </div>
</template>
