# Record of Processing Activities

**Effective date:** 2026-10-07
**Controller:** [Controller legal name], [Controller postal address]
**Applies to:** Whatsthedamage (web application and API)

This document is the record of processing activities required by
GDPR Art. 30 (model: CNIL record of processing activities). It lists
each processing operation performed by the application, its purpose,
legal basis, data categories, retention, and the rights of the data
subjects. The retention details are governed by
[`docs/retention-policy.md`](retention-policy.md).

## Processing operations

### 1. User account management and authentication

| Item | Value |
|---|---|
| Purpose | Creating and maintaining user accounts; authenticating users |
| Legal basis | Contract — necessary for the performance of the service requested by the user (GDPR Art. 6(1)(b)) |
| Data categories | Username, Argon2id password hash, Argon2id recovery code hash, account timestamps, sharing consent state and timestamps |
| Recipients | None (no third-party processors; self-hosted) |
| Retention | Lifetime of the account; 6 months after last login; or with the account deletion (7-day grace) |
| Rights | Access, rectification (username/password change in Settings), erasure (account deletion in Settings), portability (data export in Settings) |

### 2. Session management

| Item | Value |
|---|---|
| Purpose | Keeping users logged in; protecting against cross-site request forgery |
| Legal basis | Contract — necessary for providing the service |
| Data categories | Hashed session tokens, hashed CSRF tokens, IP address, user agent |
| Recipients | None |
| Retention | Until expiry/revocation (1 hour, 7 days with remember-me); expired and revoked rows are physically deleted by the daily retention job |

### 3. Bank transaction processing and reporting

| Item | Value |
|---|---|
| Purpose | Generating statistical reports and categorizations from uploaded bank transaction CSV histories |
| Legal basis | Contract — necessary for the performance of the service requested by the user |
| Data categories | Transaction date, type, partner (merchant) name, amount, currency, bank account number, notices; processing result metadata |
| Recipients | None |
| Retention | 6 months after last login, or with the account; raw CSV uploads are deleted immediately after processing |
| Rights | Access, rectification (transaction editing), erasure, portability (export) |

### 4. Merchant rule corrections

| Item | Value |
|---|---|
| Purpose | Storing the user's own correction rules for recurring merchants |
| Legal basis | Contract — necessary for the service |
| Data categories | Original partner name, corrected partner, corrected category |
| Recipients | None |
| Retention | 6 months after last login, or with the account |

### 5. Anonymous shared corrections (opt-in)

| Item | Value |
|---|---|
| Purpose | Improving future transaction categorization for all users |
| Legal basis | Consent — explicit, informed, default-off opt-in (GDPR Art. 6(1)(a)); consent state and timestamps are recorded (Art. 7(1)) |
| Data categories | SHA-256 hash of the original partner name, corrected partner, corrected category; contribution link rows (user ID, shared correction ID, count) held solely to honor withdrawal and erasure |
| Recipients | None (data stays within the application; no external ML service) |
| Retention | Anonymized values are retained; the user may request withdrawal together with the account deletion (default off), which removes the user's contributions. Contribution link rows are deleted with the account in every case |
| Rights | Access (via export), withdrawal of consent (Art. 7(3)), erasure of contributions at account deletion |

## Data minimization reviews

- **Bank account numbers.** The full account number from the CSV is
  stored. Truncating or masking it was reviewed on 2026-10-07 and
  rejected: truncation on display would cause ambiguity between
  accounts, and the number is needed to distinguish accounts within
  an upload.
- **No e-mail addresses.** Accounts use username + recovery code only;
  no e-mail address is collected.
- **Uploads.** Raw CSV files are deleted immediately after processing
  (also on failure).

## Data flow overview

```
Browser (Vue SPA)
   │  session cookie (HttpOnly, Secure, SameSite)
   ▼
REST API v2 (Flask) ── file upload (deleted after processing)
   │
   ▼
Relational database (SQLAlchemy; default SQLite)
   ├── users, sessions
   ├── transactions, corrections, processing_results
   └── shared_corrections, shared_correction_contributions
```

There are no third-party processors: no analytics or tracking
services, no CDN-hosted scripts, and no external machine learning
services.

## Risk assessment (lightweight PIA note)

A full Privacy Impact Assessment is not considered mandatory: the
processed data is financial but not Art. 9 special-category data,
there is no large-scale systematic monitoring, and no third-party
processors are involved. Identified risks and mitigations:

| Risk | Mitigation |
|---|---|
| Database compromise exposes transactions and account data | Argon2id password hashes; hashed session/CSRF tokens; data at rest encryption recommended at the host level (see TODO backlog) |
| Session hijacking | HttpOnly + Secure + SameSite cookies, session expiry, revocation on logout/password change/deletion request |
| Credential stuffing / brute force | Per-username+IP and per-IP rate limits on login, registration, and recovery endpoints |
| Re-identification through shared corrections | Only merchant names and categories shared, keyed by hash; no amounts, dates, or account data; contributions withdrawable at account deletion |
| Retention of expired sessions (IP, user agent) | Daily retention job physically deletes expired and revoked session rows |
