# Data Retention Policy

**Effective date:** 2026-10-07
**Applies to:** all user accounts of Whatsthedamage (web application and API)

This document describes what personal data Whatsthedamage stores, how
long it is kept, and how it is deleted. It implements the retention
requirements of the user-driven transaction categorization epic
(Decision #4) and the GDPR compliance effort, and is referenced by the
in-app Legal Notice and Privacy Policy.

## Data categories and retention periods

| Data category | Content | Retention |
|---|---|---|
| Account data | username, Argon2id password hash, Argon2id recovery code hash, consent timestamps (sharing opt-in/opt-out), timestamps | Lifetime of the account; deleted with the account |
| Sessions | hashed session tokens, CSRF token hashes, IP address, user agent | Until expiry/revocation; expired and revoked rows are physically deleted by the daily retention job; deleted with the account |
| Processing results | import metadata bound to the account | 6 months after last login, or with the account |
| Transactions | date, type, original partner, amount, currency, account, category, partner, notice | 6 months after last login, or with the account |
| Corrections (merchant rules) | original partner, corrected partner, corrected category | 6 months after last login, or with the account |
| Shared corrections | SHA-256 hash of the original partner name, corrected partner, corrected category | Anonymized (no amounts, dates, or account data). Retained permanently unless the user requests withdrawal together with the account deletion (see below) |
| Contribution links | user ID, shared correction ID, contribution count | Deleted with the account in every case; used solely to honor withdrawal and erasure |
| Application logs | user IDs, actions, and outcomes (no transaction content, credentials, or e-mail) | Stdout only; no persistent log storage. If a deployment persists access or application logs, keep them at most 6 months |

No other personal data is stored. Raw uploaded CSV files are deleted
immediately after processing.

## Deletion triggers

1. **Inactivity.** The account of a user without a login for 6 months
   (configurable via `WHATSTHEDAMAGE_RETENTION_INACTIVITY_DAYS`) is
   deleted together with all of its personal data (sessions,
   transactions, corrections, processing results). The deletion is
   permanent; a returning user must register a new account.
2. **Account deletion.** A user can request account deletion in the
   settings (API: `DELETE /api/v2/auth/account`, requires the current
   password). The deletion is scheduled with a 7-day grace period
   (configurable via `WHATSTHEDAMAGE_ACCOUNT_DELETION_GRACE_DAYS`):
   - All sessions are revoked immediately.
   - Logging in before the scheduled timestamp cancels the deletion
     and nothing is lost. This covers accidental deletion requests.
   - After the grace period, the retention job deletes the account
     with all sessions, processing results, transactions, and
     corrections. The deletion is permanent.
3. **Shared corrections are exempt unless revoked.** They contain no
   user linkage exposed in the app, no amounts, dates, or account
   data, and are retained permanently. However, when requesting the
   account deletion, the user may opt to withdraw the shared
   corrections they contributed (GDPR Art. 7(3), default off). The
   withdrawal removes the user's contributions together with the
   account. Machine learning models already trained on withdrawn
   data cannot be changed; new models reflect the absence of
   withdrawn data once they are made available and older models are
   deprecated.

## Running the retention job

Neither deletion trigger runs automatically; both are executed by a
Flask CLI command that must be scheduled periodically (e.g. daily
via cron):

```bash
flask --app whatsthedamage.app retention-purge
```

The command permanently deletes:

- accounts whose deletion grace period has elapsed, and
- the accounts of users inactive for longer than the retention
  window, together with all of their personal data.

It also physically deletes expired and revoked session rows (they
contain IP address and user agent data) and prints a summary of the
deleted accounts and sessions. The output serves as the deletion
proof required by GDPR Art. 5(2) and CNIL GDPR Developer Guide
sheet 7.

In containerized deployments the command runs inside the container,
e.g. `docker exec <container> flask --app whatsthedamage.app
retention-purge`.

## Backups

Database backups, if taken, must be encrypted. Erasure requests do
not propagate into existing backups automatically; when restoring a
backup, the retention purge must be run afterwards so that accounts
deleted before the backup was taken do not reappear. Backups older
than the inactivity window (6 months) should be discarded.
