<script setup lang="ts">
import { useLocaleStore } from '../stores/locale'
import { RouterLink } from 'vue-router'
import { useGettext } from 'vue3-gettext'
const { $gettext } = useGettext()

const localeStore = useLocaleStore()

const setLocale = (locale: string) => {
  localeStore.setLocale(locale)
}
</script>

<template>
  <div>
    <header>
      <nav class="navbar navbar-expand-lg navbar-dark bg-success mb-3">
        <div class="container-fluid">
          <RouterLink to="/" class="navbar-brand">What's the Damage?</RouterLink>
          <span class="text-white align-middle">{{ $gettext('Generate reports from your bank account CSV history') }}</span>
          <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav" aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
            <span class="navbar-toggler-icon"></span>
          </button>
          <div id="navbarNav" class="collapse navbar-collapse">
            <ul class="navbar-nav ms-auto">
              <li class="nav-item">
                <RouterLink to="/" class="nav-link">{{ $gettext('Home') }}</RouterLink>
              </li>
              <li class="nav-item">
                <RouterLink to="/privacy" class="nav-link">{{ $gettext('Privacy') }}</RouterLink>
              </li>
              <li class="nav-item">
                <RouterLink to="/legal" class="nav-link">{{ $gettext('Legal') }}</RouterLink>
              </li>
              <li class="nav-item">
                <RouterLink to="/about" class="nav-link">{{ $gettext('About') }}</RouterLink>
              </li>
              <li class="nav-item dropdown">
                <a id="langDropdown" class="nav-link dropdown-toggle" href="#" role="button" data-bs-toggle="dropdown" aria-expanded="false">
                  {{ $gettext('Languages') }}
                </a>
                <ul class="dropdown-menu dropdown-menu-end" aria-labelledby="langDropdown">
                  <li>
                    <a class="dropdown-item" href="#" @click.prevent="setLocale('en')">🇬🇧 English</a>
                  </li>
                  <li>
                    <a class="dropdown-item" href="#" @click.prevent="setLocale('hu')">🇭🇺 Magyar</a>
                  </li>
                </ul>
              </li>
            </ul>
          </div>
        </div>
      </nav>
    </header>

    <main id="main-content" class="container-fluid" tabindex="-1">
      <a class="sr-only sr-only-focusable" href="#main-content">{{ $gettext('Skip to main content') }}</a>
      <slot></slot>
    </main>

    <footer class="bg-success text-white text-center py-3 mt-3">
      <div class="container">
        <a href="https://balagetech.com" class="text-white me-3">@ 2025 Balagetech</a>
        <span class="text-white me-3">v1.0.0</span>
      </div>
    </footer>
  </div>
</template>

<style scoped>
header, footer {
  padding: 15px 0;
}

.navbar {
  padding: 0;
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

.sr-only-focusable:focus {
  position: static;
  width: auto;
  height: auto;
  padding: 0.5rem;
  margin: 0;
  overflow: visible;
  clip: auto;
  white-space: normal;
}
</style>