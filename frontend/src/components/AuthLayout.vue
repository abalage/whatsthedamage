<!--
  Authentication Layout Component
  
  Wrapper component for authentication pages (Login, Register).
  Provides consistent styling and layout for auth-related views.
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

<style scoped>
.auth-layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background-color: #f5f5f5;
  padding: 2rem;
}

.auth-container {
  width: 100%;
  max-width: 400px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  padding: 2rem;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.auth-header {
  text-align: center;
}

.app-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: #333;
  margin: 0;
}

.auth-main {
  flex: 1;
}

.auth-footer {
  text-align: center;
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #eee;
}

.footer-text {
  color: #666;
  font-size: 0.875rem;
  margin: 0;
}
</style>
