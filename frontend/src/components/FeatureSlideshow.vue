<!--
  Feature Slideshow Component

  Auto-advancing slideshow used on the landing page. Mixes message slides
  and screenshot slides; pauses on hover/focus and respects
  prefers-reduced-motion (manual controls only in that case).
-->

<script setup lang="ts">
import { computed, onBeforeUnmount, ref } from 'vue';
import { useGettext } from 'vue3-gettext';
import type { FeatureSlide } from '../types';

const props = defineProps<{ slides: FeatureSlide[] }>();

const { $gettext } = useGettext();

const AUTO_ADVANCE_MS = 5000;

const currentIndex = ref(0);
let timer: number | undefined;

const prefersReducedMotion = typeof window.matchMedia === 'function'
  ? window.matchMedia('(prefers-reduced-motion: reduce)').matches
  : false;

const hasMultiple = computed(() => props.slides.length > 1);
const currentSlide = computed<FeatureSlide | undefined>(
  () => props.slides[currentIndex.value] ?? props.slides[0]
);

/**
 * Stop the auto-advance timer if it is running.
 */
function clearTimer(): void {
  if (timer !== undefined) {
    window.clearInterval(timer);
    timer = undefined;
  }
}

/**
 * Start the auto-advance timer unless the user prefers reduced motion
 * or there is nothing to advance through.
 */
function startTimer(): void {
  if (prefersReducedMotion || !hasMultiple.value) return;
  clearTimer();
  timer = window.setInterval(() => {
    next();
  }, AUTO_ADVANCE_MS);
}

/**
 * Show the slide at the given index, wrapping around.
 * @param index - Target slide index
 */
function goTo(index: number): void {
  if (props.slides.length === 0) return;
  currentIndex.value = (index + props.slides.length) % props.slides.length;
}

/**
 * Advance to the next slide.
 */
function next(): void {
  goTo(currentIndex.value + 1);
}

/**
 * Go back to the previous slide.
 */
function prev(): void {
  goTo(currentIndex.value - 1);
}

onBeforeUnmount(clearTimer);
startTimer();
</script>

<template>
  <div
    v-if="currentSlide"
    class="feature-slideshow"
    role="region"
    aria-roledescription="carousel"
    :aria-label="$gettext('Feature highlights')"
    :data-slide-index="currentIndex"
    @mouseenter="clearTimer"
    @mouseleave="startTimer"
    @focusin="clearTimer"
    @focusout="startTimer"
  >
    <div class="slide-viewport" aria-live="polite">
      <div v-if="currentSlide.type === 'message'" class="slide slide-message">
        <h3 v-if="currentSlide.title" class="slide-title">{{ currentSlide.title }}</h3>
        <p v-if="currentSlide.text" class="slide-text">{{ currentSlide.text }}</p>
      </div>
      <img
        v-else
        class="slide slide-image"
        :src="currentSlide.src"
        :alt="currentSlide.alt ?? ''"
      />
    </div>

    <div v-if="hasMultiple" class="slideshow-controls">
      <button
        type="button"
        class="slideshow-nav"
        :aria-label="$gettext('Previous slide')"
        @click="prev"
      >
        &#8249;
      </button>
      <div class="slideshow-dots">
        <button
          v-for="(slide, index) in slides"
          :key="index"
          type="button"
          class="slideshow-dot"
          :class="{ active: index === currentIndex }"
          :aria-label="$gettext('Go to slide {n}').replace('{n}', String(index + 1))"
          :aria-current="index === currentIndex ? 'true' : undefined"
          @click="goTo(index)"
        ></button>
      </div>
      <button
        type="button"
        class="slideshow-nav"
        :aria-label="$gettext('Next slide')"
        @click="next"
      >
        &#8250;
      </button>
    </div>
  </div>
</template>
