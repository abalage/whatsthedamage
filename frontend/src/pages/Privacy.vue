<script setup lang="ts">
import { computed } from 'vue'
import { useGettext } from 'vue3-gettext'

const { $gettext } = useGettext()

// Email obfuscation using JavaScript string manipulation
// This provides basic obfuscation without using v-html
const emailUsername = 'balagetech'
const emailDomain = 'protonmail.com'
const email = computed(() => `${emailUsername}@${emailDomain}`)
const emailHref = computed(() => `mailto:${emailUsername}@${emailDomain}`)

// Controller identity placeholders: replace with the actual legal name
// and postal address of the data controller before production use.
const controllerName = '[Controller legal name]'
const controllerAddress = '[Controller postal address]'
</script>

<template>
  <div class="container">
    <h1>{{ $gettext('Privacy Policy') }}</h1>
    <p><strong>{{ $gettext('Effective Date:') }}</strong> 10-07-2026</p>
    <h2>1. Introduction</h2>
    <p>Welcome to Whatsthedamage (the "App"). This Privacy Policy explains how we collect, use, disclose, and protect your personal information when you use our App. We are committed to protecting your privacy and ensuring that your personal data is handled in accordance with the General Data Protection Regulation (GDPR) and other applicable data protection laws.</p>
    <h2>2. Who We Are</h2>
    <p>The data controller for the personal data processed through the App is <strong>{{ controllerName }}</strong>, {{ controllerAddress }}. No Data Protection Officer has been appointed; you can reach us with any data protection question at <a :href="emailHref">{{ email }}</a>.</p>
    <h2>3. Information We Collect</h2>
    <p>We may collect and process the following types of personal data when you use our App:</p>
    <ul>
        <li><strong>Account Information:</strong> Your username and password (stored only as an Argon2id hash). We never ask for or store your e-mail address.</li>
        <li><strong>Bank Account Information:</strong> This includes bank account numbers and account names associated with the transactions.</li>
        <li><strong>Transaction Data:</strong> Information contained in the bank account transaction histories you upload, which may include:
            <ul>
                <li>Partner Names: Names of individuals or entities involved in the transactions.</li>
                <li>Transaction Identifiers: Unique identifiers for each transaction that help track and reference them.</li>
                <li>Partner Account Names: Names of the accounts associated with the partners in the transactions.</li>
                <li>Foreign Exchange Information: Details regarding any currency conversions or foreign exchange rates applied to the transactions.</li>
                <li>Comments: Any additional notes or comments you may include in the CSV file related to the transactions.</li>
            </ul>
        </li>
    </ul>
    <p>By collecting this information, we aim to provide you with accurate and comprehensive reports based on your transaction histories. The raw CSV files you upload are deleted immediately after processing.</p>
    <h2>4. Purpose of Data Processing</h2>
    <p>We process your personal data for the following purposes:</p>
    <ul>
        <li>To create and maintain your account and authenticate you.</li>
        <li>To generate reports based on the transaction histories you upload.</li>
        <li>If you opt in, to contribute anonymized merchant names and categories from your corrections to improve future categorization for everyone.</li>
    </ul>
    <h2>5. Legal Basis for Processing</h2>
    <p>We process your personal data based on the following legal grounds under the GDPR:</p>
    <ul>
        <li><strong>Contract:</strong> Processing of your account data and uploaded transaction data is necessary for the performance of the service you requested (generating reports from your transaction histories).</li>
        <li><strong>Consent:</strong> Sharing anonymized corrections is based on your explicit, freely given opt-in (default: off). You can withdraw this consent at any time in the settings.</li>
    </ul>
    <h2>6. Data Retention</h2>
    <p>We retain your personal data only for as long as necessary to fulfill the purposes for which it was collected. Your account, including all transactions, corrections, and processing results, is permanently deleted 6 months after your last login, or when you request account deletion in the settings (with a 7-day grace period during which logging in cancels the request).</p>
    <p>If you opted in to sharing corrections, the anonymized corrections you contributed (merchant names and categories only) are retained. When you request account deletion, you may choose to also remove the corrections you contributed; already-trained machine learning models cannot be changed, but new models reflect the absence of withdrawn data once they are made available and older models are deprecated.</p>
    <p>Further details are available in our <a href="https://github.com/abalage/whatsthedamage/blob/main/docs/retention-policy.md">Data Retention Policy</a>.</p>
    <h2>7. Data Security</h2>
    <p>We implement appropriate technical and organizational measures to protect your personal data against unauthorized access, loss, or destruction. Passwords and session tokens are stored only as Argon2id and SHA-256 hashes, all state-changing requests are protected against cross-site request forgery, and sensitive endpoints are rate-limited. However, please be aware that no method of transmission over the internet or method of electronic storage is 100% secure.</p>
    <h2>8. Your Rights</h2>
    <p>Under the GDPR, you have the following rights regarding your personal data:</p>
    <ul>
        <li><strong>Right to Access:</strong> You have the right to obtain a copy of your personal data. You can download all of your data in a machine-readable document under <em>Settings &rarr; Your data</em>.</li>
        <li><strong>Right to Rectification:</strong> You have the right to correct inaccurate or incomplete data. You can change your username and password under <em>Settings &rarr; Account</em> and edit your transactions and corrections in the app.</li>
        <li><strong>Right to Erasure:</strong> You have the right to request the erasure of your personal data. You can schedule the deletion of your account under <em>Settings &rarr; Delete account</em>.</li>
        <li><strong>Right to Restrict Processing:</strong> You have the right to request that we restrict the processing of your personal data, under certain conditions.</li>
        <li><strong>Right to Data Portability:</strong> You have the right to receive the data we have collected about you in a machine-readable format; use the export feature under <em>Settings &rarr; Your data</em>.</li>
        <li><strong>Right to Withdraw Consent:</strong> For processing based on consent (sharing of corrections), you can withdraw your consent at any time in the settings, and request removal of your shared corrections together with the account deletion.</li>
    </ul>
    <p>To exercise any of these rights, use the self-service features in the app, or contact us at <a :href="emailHref">{{ email }}</a>.</p>
    <h2>9. Right to Lodge a Complaint</h2>
    <p>You have the right to lodge a complaint with a supervisory authority. In Hungary, the supervisory authority is the National Authority for Data Protection and Freedom of Information (NAIH), <a href="https://www.naih.hu">www.naih.hu</a>.</p>
    <h2>10. Changes to This Privacy Policy</h2>
    <p>We may update this Privacy Policy from time to time. Any changes will be effective immediately upon posting the revised policy on the App. Your continued use of the App after any changes constitutes your acceptance of the new terms.</p>
    <h2>11. Contact Us</h2>
    <p>If you have any questions or concerns about this Privacy Policy or our data practices, please contact us at <a :href="emailHref">{{ email }}</a>.</p>
    <p>By using the App, you acknowledge that you have read and understood this Privacy Policy and agree to its terms.</p>
  </div>
</template>
