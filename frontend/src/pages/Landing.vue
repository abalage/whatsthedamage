<!--
  Landing Page Component

  Public page shown to unauthenticated visitors. Carries the trust message
  (self-hosted, no telemetry, data stays local), a feature slideshow, a
  language switcher, and Login/Register buttons that preserve the redirect
  target from the query string.
-->

<script setup lang="ts">
import { computed } from 'vue';
import { useRoute } from 'vue-router';
import { useGettext } from 'vue3-gettext';
import FeatureSlideshow from '../components/FeatureSlideshow.vue';
import { useLocaleStore } from '../stores/locale';
import { buildRedirectQuery, safeRedirectParam } from '../js/routeUtils';
import type { FeatureSlide } from '../types';

const { $gettext } = useGettext();
const route = useRoute();
const localeStore = useLocaleStore();

const redirectQuery = computed(() => buildRedirectQuery(safeRedirectParam(route.query)));

const slides = computed<FeatureSlide[]>(() => [
  {
    type: 'message',
    title: $gettext('Self-hosted'),
    text: $gettext('Runs on your own machine. No telemetry, no accounts on third-party servers.')
  },
  {
    type: 'message',
    title: $gettext('Your data stays local'),
    text: $gettext('Your bank exports never leave your machine. Nothing is sent anywhere.')
  },
  {
    type: 'image',
    src: '/screenshots/transactions.png',
    alt: $gettext('Screenshot of the transactions page')
  },
  {
    type: 'message',
    title: $gettext('Automatic categorization'),
    text: $gettext('Import a CSV export and transactions are categorized automatically.')
  },
  {
    type: 'image',
    src: '/screenshots/statistics.png',
    alt: $gettext('Screenshot of the statistics report')
  },
  {
    type: 'message',
    title: $gettext('Insightful reports'),
    text: $gettext('See where your money went with category and monthly reports, pivot tables, and statistics.')
  }
]);
</script>

<template>
  <div class="landing-layout">
    <div class="landing-locale-switch" role="group" :aria-label="$gettext('Languages')">
      <button
        type="button"
        :class="{ active: localeStore.locale === 'en' }"
        @click="localeStore.setLocale('en')"
      >
        EN
      </button>
      <button
        type="button"
        :class="{ active: localeStore.locale === 'hu' }"
        @click="localeStore.setLocale('hu')"
      >
        HU
      </button>
    </div>

    <div class="landing-content">
      <section class="landing-pitch">
        <h1 class="landing-title">What's the Damage</h1>
        <p class="landing-tagline">{{ $gettext("Tell me I didn't spend that much…") }}</p>

        <p class="landing-trust">
          <strong>{{ $gettext('Self-hosted. No telemetry. Your data never leaves your machine.') }}</strong>
        </p>

        <ul class="landing-features">
          <li>{{ $gettext('Import your bank CSV exports and get them categorized automatically') }}</li>
          <li>{{ $gettext('Reports, pivot tables, and statistics show where your money went') }}</li>
          <li>{{ $gettext('Everything runs locally — nothing is uploaded or shared') }}</li>
        </ul>

        <div class="landing-cta">
          <router-link class="landing-btn landing-btn-primary" :to="{ name: 'login', query: redirectQuery }">
            {{ $gettext('Login') }}
          </router-link>
          <router-link class="landing-btn landing-btn-secondary" :to="{ name: 'register', query: redirectQuery }">
            {{ $gettext('Register') }}
          </router-link>
        </div>

        <p class="landing-links">
          <router-link to="/about">{{ $gettext('About') }}</router-link>
          <router-link to="/privacy">{{ $gettext('Privacy') }}</router-link>
          <router-link to="/legal">{{ $gettext('Legal') }}</router-link>
        </p>
      </section>

      <section class="landing-slideshow">
        <FeatureSlideshow :slides="slides" />
      </section>
    </div>
  </div>
</template>
