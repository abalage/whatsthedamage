<!--
  Recovery Code Display Component
  
  Displays the new recovery code after successful password reset.
  Requires user acknowledgment before continuing.
-->

<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';

// Props
interface Props {
  recoveryCode: string;
}

const props = defineProps<Props>();

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
      // Fallback for browsers that don't support clipboard API
      // User will need to manually copy
    }
  }
}

/**
 * Handle acknowledgment and navigation.
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
    <h2>Password Reset Successful!</h2>

    <div class="success-message">
      <p>Your password has been successfully reset.</p>
      <p>
        <strong>Important:</strong> A new recovery code has been generated.
        You must save it as you will not be able to see it again.
      </p>
    </div>

    <div class="recovery-code-display">
      <div class="recovery-code-box">
        <code>{{ props.recoveryCode }}</code>
        <button
          type="button"
          class="copy-btn"
          title="Copy to clipboard"
          @click="copyToClipboard"
        >
          <span v-if="!copySuccess">Copy</span>
          <span v-else>Copied!</span>
        </button>
      </div>
      <div v-if="copySuccess" class="copy-success-message">
        Recovery code copied to clipboard!
      </div>
    </div>

    <div class="warning-message">
      <p>
        <strong>WARNING: SAVE THIS CODE NOW!</strong> You will not be able to retrieve it later.
      </p>
      <p>
        Without this recovery code, you will not be able to reset your password
        if you forget it again.
      </p>
    </div>

    <div class="acknowledgment">
      <label class="checkbox-label">
        <input
          v-model="recoveryCodeAcknowledged"
          type="checkbox"
        />
        I have saved my new recovery code in a secure location
      </label>
    </div>

    <button
      :disabled="!recoveryCodeAcknowledged"
      class="btn btn-primary"
      type="button"
      @click="handleAcknowledged"
    >
      Continue to Login
    </button>

    <div class="auth-links">
      <p>
        <button class="link-btn" type="button" @click="goToLogin">
          Back to Login
        </button>
      </p>
    </div>
  </div>
</template>

<style scoped>
/* Success state styles */
.success-message {
  background-color: #d4edda;
  color: #155724;
  padding: 1rem;
  border-radius: 4px;
  margin-bottom: 1.5rem;
}

.warning-message {
  background-color: #fff3cd;
  color: #856404;
  padding: 1rem;
  border-radius: 4px;
  margin-bottom: 1.5rem;
  border: 1px solid #ffeeba;
}

.warning-message p {
  margin: 0.25rem 0;
}

.recovery-code-display {
  margin: 1.5rem 0;
  text-align: center;
}

.recovery-code-box {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  background-color: #f8f9fa;
  border: 2px dashed #6c757d;
  border-radius: 4px;
  padding: 1rem;
  font-size: 1.25rem;
  font-weight: bold;
  letter-spacing: 0.1em;
  word-break: break-all;
}

.recovery-code-box code {
  font-family: monospace;
  color: #212529;
  user-select: text;
}

.copy-btn {
  background-color: #6c757d;
  color: white;
  border: none;
  border-radius: 4px;
  padding: 0.25rem 0.75rem;
  font-size: 0.875rem;
  cursor: pointer;
  transition: background-color 0.2s;
}

.copy-btn:hover {
  background-color: #5a6268;
}

.acknowledgment {
  margin: 1.5rem 0;
}

.checkbox-label {
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
  cursor: pointer;
  font-size: 0.9375rem;
  line-height: 1.5;
}

.checkbox-label input[type="checkbox"] {
  margin-top: 0.25rem;
}

.copy-success-message {
  color: #28a745;
  font-size: 0.875rem;
  margin-top: 0.5rem;
  text-align: center;
}

.btn {
  padding: 0.75rem 1rem;
  border: none;
  border-radius: 4px;
  font-size: 1rem;
  cursor: pointer;
  transition: background-color 0.2s, opacity 0.2s;
  width: 100%;
}

.btn-primary {
  background-color: #007bff;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background-color: #0069d9;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.auth-links {
  text-align: center;
  margin-top: 1rem;
}

.link-btn {
  background: none;
  border: none;
  color: #007bff;
  text-decoration: none;
  cursor: pointer;
  font-size: inherit;
  padding: 0;
}

.link-btn:hover {
  text-decoration: underline;
}

.recovery-code-container h2 {
  margin-top: 0;
}
</style>
