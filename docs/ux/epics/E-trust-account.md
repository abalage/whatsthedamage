# Epic E — Trust & account

Persona: [Péter](../personas/peter-selfhoster.md). A privacy tool must make its privacy
promises operable.

### UX-E1 (P0, draft)

**As** a user who lost my password, **I want** to recover access with my recovery code —
and if I lost the code, an honest explanation of my options, **so that** account loss is
never a surprise.

Acceptance criteria:
- [ ] Password reset via recovery code works end to end.
- [ ] The data retention policy (6-month purge after last login) is stated plainly
      in-app, not only in docs.

### UX-E2 (P1, draft)

**As** a user, **I want** to delete all my data and trust that it is gone, **so that**
the privacy promise is something I can act on.

Acceptance criteria:
- [ ] A self-service, full data deletion path exists and confirms completion.

### UX-E3 (P2, draft)

**As** a user, **I want** to understand the anonymized correction-sharing option and opt
in or out knowingly, **so that** no feature shares data I did not intend to share.

Acceptance criteria:
- [ ] The sharing feature explains exactly what is shared (partner+category, hashed)
      before opt-in; default is off.
