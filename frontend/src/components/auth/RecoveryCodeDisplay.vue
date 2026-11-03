<!--
  Recovery Code Display Component

  Displays a recovery code with copy button, warning, and acknowledgment
  checkbox. Reusable across contexts (password reset, regeneration) via
  configurable props for title, instructions, and button labels.
-->

<script setup lang="ts">
import { ref, computed } from 'vue';
import { useRouter } from 'vue-router';
import { useGettext } from 'vue3-gettext';

const { $gettext } = useGettext();

// Props
interface Props {
  recoveryCode: string;
  title?: string;
  instructions?: string;
  warningText?: string;
  acknowledgeLabel?: string;
  continueLabel?: string;
  showBackLink?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  title: '',
  instructions: '',
  warningText: '',
  acknowledgeLabel: '',
  continueLabel: '',
  showBackLink: true,
});

// Computed display text with gettext defaults
const displayTitle = computed(() => props.title || $gettext('Password Reset Successful!'));
const displayInstructions = computed(() => props.instructions || $gettext('Your password has been successfully reset.'));
const displayWarningText = computed(() => props.warningText || $gettext('A new recovery code has been generated. You must save it as you will not be able to see it again.'));
const displayAcknowledgeLabel = computed(() => props.acknowledgeLabel || $gettext('I have saved my new recovery code in a secure location'));
const displayContinueLabel = computed(() => props.continueLabel || $gettext('Continue to Login'));

// Emits
interface Emits {
  (e: 'continue'): void;
}

const emit = defineEmits<Emits>();

const router = useRouter();

// State
const recoveryCodeAcknowledged = ref(false);
const copySuccess = ref(false);

/**
 * Copy recovery code to clipboard.
 */
async function copyToClipboard() {
  if (props.recoveryCode) {
    try {
      await navigator.clipboard.writeText(props.recoveryCode);
      copySuccess.value = true;
      // Hide the success message after 2 seconds
      setTimeout(() => {
        copySuccess.value = false;
      }, 2000);
    } catch {
      // Clipboard API unavailable; the user can copy the code manually
    }
  }
}

/**
 * Handle acknowledgment and emit continue.
 */
function handleAcknowledged() {
  if (recoveryCodeAcknowledged.value) {
    emit('continue');
  }
}

/**
 * Navigate to login page directly.
 */
function goToLogin() {
  router.push({ name: 'login' });
}
</script>

<template>
  <div class="recovery-code-container">
    <h2>{{ displayTitle }}</h2>

    <div class="auth-status-success">
      <p>{{ displayInstructions }}</p>
      <p>
        <strong>{{ $gettext('Important:') }}</strong>
        {{ displayWarningText }}
      </p>
    </div>

    <div>
      <div class="recovery-code-box">
        <code>{{ props.recoveryCode }}</code>
        <button
          type="button"
          class="recovery-copy-btn"
          :title="$gettext('Copy to clipboard')"
          @click="copyToClipboard"
        >
          <span v-if="!copySuccess">{{ $gettext('Copy') }}</span>
          <span v-else>{{ $gettext('Copied!') }}</span>
        </button>
      </div>
      <div v-if="copySuccess" class="recovery-copy-success">
        {{ $gettext('Recovery code copied to clipboard!') }}
      </div>
    </div>

    <div class="auth-status-warning">
      <p>
        <strong>{{ $gettext('WARNING: SAVE THIS CODE NOW!') }}</strong>
        {{ $gettext('You will not be able to retrieve it later.') }}
      </p>
      <p>
        {{ $gettext('Without this recovery code, you will not be able to reset your password if you forget it again.') }}
      </p>
    </div>

    <div class="auth-acknowledgment">
      <label>
        <input
          v-model="recoveryCodeAcknowledged"
          type="checkbox"
        />
        {{ displayAcknowledgeLabel }}
      </label>
    </div>

    <button
      :disabled="!recoveryCodeAcknowledged"
      class="auth-primary-btn"
      type="button"
      @click="handleAcknowledged"
    >
      {{ displayContinueLabel }}
    </button>

    <div v-if="props.showBackLink" class="auth-links">
      <p>
        <button class="link-btn" type="button" @click="goToLogin">
          {{ $gettext('Back to Login') }}
        </button>
      </p>
    </div>
  </div>
</template>
