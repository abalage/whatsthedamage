# Data Subject Request (DSR) Runbook

**Effective date:** 2026-10-07

Operational procedure for handling personal data requests. Most
rights are self-service in the application (Settings page); this
runbook covers requests that arrive by e-mail and the operator steps
that have no in-app tooling. The deadline for responding is one month
from receipt (GDPR Art. 12(3)).

## Self-service features (first line of response)

| Right | In-app feature | API |
|---|---|---|
| Access / portability | Settings → Your data → Download my data | `GET /api/v2/auth/me/export` |
| Rectification (account) | Settings → Your account | `PUT /api/v2/auth/me` |
| Rectification (transactions) | Transaction editing in the app | `PUT /api/v2/transactions/<id>` |
| Password change | Settings → Your account | `PUT /api/v2/auth/me/password` |
| Consent withdrawal (sharing) | Settings → Share corrections | `PUT /api/v2/auth/me` (`opt_in_sharing: false`) |
| Erasure | Settings → Delete account | `DELETE /api/v2/auth/account` |
| Withdrawal of shared corrections | Settings → Delete account → "Also remove the anonymized corrections I shared" | `DELETE /api/v2/auth/account` (`revoke_shared_corrections: true`) |

When a request arrives by e-mail and maps to a self-service feature,
reply with instructions (or the direct Settings link) and offer to
assist. There is no admin interface by design; operators never access
user data directly.

## E-mail procedure

1. **Record the request.** Log the receipt date, the requester, the
   right(s) invoked, and the deadline (receipt + 1 month) in the DSR
   log. This starts the statutory clock.
2. **Verify identity — never ask for more data than needed.** For
   requests about an existing account, ask the requester to log in and
   confirm the username in their message. Do not request transaction
   data, bank details, or identity documents.
3. **Route by right:**
   - *Access / portability / rectification / consent withdrawal:* point
     to the self-service feature; if the user cannot log in (e.g. lost
     password), guide them through the recovery-code reset flow.
   - *Erasure:* the in-app deletion request is the canonical path
     because it verifies the password. For a user who cannot log in,
     an operator may delete the account directly in the database:
     `DELETE FROM users WHERE username = ?` — the ORM cascade removes
     sessions, transactions, corrections, and processing results. Run
     the retention purge afterwards (`flask --app whatsthedamage.app
     retention-purge`) and keep its output as the deletion proof.
   - *Withdrawal of shared corrections:* performed automatically when
     the deletion request includes `revoke_shared_corrections: true`.
     For a direct database deletion, first set the user's
     `revoke_shared_corrections` flag, then delete the account and run
     the purge; the purge withdraws the contributions.
   - *Restriction of processing:* no in-app feature exists. Record the
     request, inform the user of the expected duration, and if
     restriction is required for longer than a short period, disable
     the account (`is_active = false`) until resolved.
4. **Fulfil and confirm.** Reply within the deadline confirming what
   was done. For erasure, include the scheduled/performed date.
5. **Log the completion** with the response date in the DSR log.

## Special cases

- **Pending deletion cancellation.** A user who scheduled deletion
  can cancel it simply by logging in during the 7-day grace period;
  no operator action is needed. Past the grace period the login is
  refused and the account is deleted by the next purge run.
- **Already deleted accounts.** Data subject data is permanently
  deleted by the retention job; nothing can be retrieved or exported
  after the purge. Respond that no data is held anymore.
- **Backups.** Deletions do not propagate into existing backups; see
  the "Backups" section of `docs/retention-policy.md` for the restore
  procedure (run the retention purge after a restore).
- **Complaints.** If the requester is dissatisfied, remind them of
  their right to lodge a complaint with the NAIH (www.naih.hu); the
  contact point is the address published in the Privacy Policy.
