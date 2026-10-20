# TODO

Descoped or follow-up items that are intentionally not part of the
current epic ("User-Driven Transaction Categorization").

## Conflict review for merchant rules (descoped)

Epic Decision #3 originally called for conflicting categories for the
same merchant across uploads to be marked for manual review. This is
descoped: rule-mode corrections upsert the merchant rule and silently
overwrite the previous corrected category. Reintroducing conflict
detection would require a review state on the merchant rule plus a
review UI.

## Security hardening backlog (GDPR compliance follow-up)

Follow-up items from the GDPR compliance effort (see
`docs/retention-policy.md` and the CNIL GDPR Developer Guide). These
are intentionally descoped from the compliance epic; none of them is
required for the data subject rights features.

- **Rate-limiting store is per-process memory.** The
  `RateLimitService` keeps its counters in process memory, so the
  limits do not hold across gunicorn workers or restarts. Decided to
  keep it in-memory for now. Backlog: move the counters to a shared
  store (a DB-backed repository to avoid new dependencies, or Redis).
- **Deployment security documentation.** Document the
  production deployment security baseline: TLS 1.2+ termination and
  the HSTS header at the reverse proxy, the production cookie
  `secure` flag (`secure=False` on localhost is a development-only
  control), encrypted database backups, and verification that the
  daily `retention-purge` cron is scheduled. Backup handling notes
  are in `docs/retention-policy.md` ("Backups").
- **Dependency vulnerability watch.** Add `pip-audit` to the backend
  CI/tox checks and `npm audit` to the frontend CI, and document the
  security-update procedure. See also GitHub issue
  https://github.com/abalage/whatsthedamage/issues/100.
