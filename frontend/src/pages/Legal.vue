<script setup lang="ts">
import { computed } from 'vue'

// Email obfuscation using JavaScript string manipulation
// This provides basic obfuscation without using v-html
const emailUsername = 'balagetech'
const emailDomain = 'protonmail.com'
const email = computed(() => `${emailUsername}@${emailDomain}`)
const emailHref = computed(() => `mailto:${emailUsername}@${emailDomain}`)
</script>

<template>
  <div class="container">
    <h1>Legal Notice</h1>
    <p><strong>Effective Date:</strong> 10-06-2026</p>
    <h2>1. Introduction</h2>
    <p>Welcome to Whatsthedamage (the "App"). By accessing or using this App, you agree to comply with and be bound by the following terms and conditions. If you do not agree with these terms, please do not use the App.</p>
    <h2>2. Data Processing and Retention</h2>
    <p>The App processes bank account transaction histories uploaded in CSV format. When you create an account, your transactions, corrections, and processing results are stored on our servers bound to your account so you can access them across sessions and devices.</p>
    <p>We retain your personal data only as long as necessary: your account and all of its data are permanently deleted 6 months after your last login, or when you request account deletion in the settings. Account deletion takes effect after a 7-day grace period during which logging in cancels the request.</p>
    <p>If you opted in to sharing corrections, the anonymized corrections you contributed (merchant names and categories only, never amounts, dates, or account information) are retained permanently and cannot be retracted, even after your account is deleted.</p>
    <p>The full details are published in our <a href="https://github.com/abalage/whatsthedamage/blob/main/docs/retention-policy.md">Data Retention Policy</a>.</p>
    <h2>3. No Warranty</h2>
    <p>While we strive to provide accurate and reliable reports, the App is provided "as is" without any warranties of any kind, either express or implied. We do not guarantee the accuracy, completeness, or reliability of the reports generated.</p>
    <h2>4. Limitation of Liability</h2>
    <p>By using this App, you acknowledge and agree that <a href="https://balagetech.com">balagetech.com</a> shall not be held liable for any errors, inaccuracies, or omissions in the reports. You accept full responsibility for any decisions made based on the information provided by the App. In no event shall <a href="https://balagetech.com">balagetech.com</a> be liable for any direct, indirect, incidental, special, or consequential damages arising from your use of the App.</p>
    <h2>5. User Responsibility</h2>
    <p>You are solely responsible for ensuring that the data you upload complies with all applicable laws and regulations. You must have the necessary rights to upload and process the data contained in the CSV files.</p>
    <h2>6. Changes to the Legal Notice</h2>
    <p>We reserve the right to modify this Legal Notice at any time. Any changes will be effective immediately upon posting the revised notice on the App. Your continued use of the App after any changes constitutes your acceptance of the new terms.</p>
    <h2>7. Contact Information</h2>
    <!-- eslint-disable-next-line vue/no-v-html -->
    <p>If you have any questions or concerns regarding this Legal Notice, please contact us at <a :href="emailHref">{{ email }}</a>.</p>
    <h2>8. Governing Law</h2>
    <p>This Legal Notice shall be governed by and construed in accordance with the laws of Hungary, without regard to its conflict of law principles.</p>
    <p>By using the App, you acknowledge that you have read, understood, and agree to be bound by this Legal Notice.</p>
  </div>
</template>
