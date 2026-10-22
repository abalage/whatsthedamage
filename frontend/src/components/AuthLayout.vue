<!--
  Authentication Layout Component

  Wrapper component for authentication pages (Login, Register).
  Provides consistent styling and layout for auth-related views.
  Styling comes from the shared css/auth.css.
-->

<script setup lang="ts">
// No script logic needed for this layout component
</script>

<template>
  <div class="auth-layout">
    <div class="auth-container">
      <div class="auth-header">
        <h1 class="app-title">What's the Damage</h1>
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
