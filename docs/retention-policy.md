# Data Retention Policy

**Effective date:** 2026-10-06
**Applies to:** all user accounts of Whatsthedamage (web application and API)

This document describes what personal data Whatsthedamage stores, how
long it is kept, and how it is deleted. It implements the retention
requirements of the user-driven transaction categorization epic
(Decision #4) and is referenced by the in-app Legal Notice and Privacy
Policy.

## Data categories and retention periods

| Data category | Content | Retention |
|---|---|---|
| Account data | username, Argon2id password hash, Argon2id recovery code hash, timestamps | Lifetime of the account; deleted with the account |
| Sessions | hashed session tokens, CSRF token hashes, IP address, user agent | Until expiry/revocation; deleted with the account |
| Processing results | import metadata bound to the account | 6 months after last login, or with the account |
| Transactions | date, type, original partner, amount, currency, account, category, partner, notice | 6 months after last login, or with the account |
| Corrections (merchant rules) | original partner, corrected partner, corrected category | 6 months after last login, or with the account |
| Shared corrections | SHA-256 hash of the original partner name, corrected partner, corrected category | **Permanent.** Anonymized (no user linkage, no amounts, dates, or account data) and never deleted, per the opt-in agreement |

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
3. **Shared corrections are exempt.** They contain no user linkage
   and are retained permanently. This is stated explicitly in the
   opt-in text and cannot be revoked retroactively.

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

It prints a summary of the deleted accounts and is idempotent and
safe to run concurrently with the application. Anonymized shared
corrections are never deleted.

In containerized deployments the command runs inside the container,
e.g. `docker exec <container> flask --app whatsthedamage.app
retention-purge`.

## Known gap

There is currently no data export feature. Users whose accounts are
deleted due to inactivity have no way to export their data before
deletion. This is tracked in the project TODO list and should be
prioritized in a follow-up effort.
