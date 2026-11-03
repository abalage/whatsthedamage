# Epic A — Discover & sign up

Persona: [Péter](../personas/peter-selfhoster.md)

### UX-A1 (P0, draft)

**As** a new visitor, **I want** to see what the app does, that it is self-hosted, and
that my data never leaves my machine, **so that** I can decide to trust it before
registering.

Acceptance criteria:
- [ ] The trust message (self-hosted, no telemetry, data stays local) is visible on the
      first screen without scrolling, in Hungarian and English.

Issues found:
- [BUG] Login layout needs to be scrolled even on FullHD resolution. The value of `min-height` CSS attribute in CSS class `auth-layout` is too large (#135).
- [FEAT] Login box should be left-aligned to create space on the right to highlight main features of the software in a slideshow. Slideshow should contain 'slides' of main messages, as well as screenshots. Should have the same size as the login box. Re-scoped: the slideshow is implemented on the new landing page; the auth layout itself stays unchanged (#137).
- Lower the current `padding: 20px` to 5px in CSS class `container-fluid` to further save space (#136).

Linked issues: #135, #136, #137

### UX-A2 (P0, draft)

**As** a new user, **I want** to register with just username and password and understand
what my recovery code is for before I am shown one, **so that** I do not lose access
irrecoverably.

Acceptance criteria:
- [ ] The registration flow explains the recovery code's purpose.
- [ ] A logged-in user can re-create their recovery code. Existing recovery code gets invalidated.

Issues found:
- [BUG] The recovery code screen is vertically large (probably preoptimized for mobile) (#138).
- [BUG] No form to re-generate recovery code after login (#139).

Linked issues: #138, #139. The acceptance criterion "The registration flow explains the recovery code's purpose" is already satisfied by the existing registration copy; no issue needed.

### UX-A3 (P1, draft)

**As** a returning user, **I want** to switch the interface language to Hungarian on any
page, **so that** I never have to guess in a foreign language.

Acceptance criteria:
- [ ] Language switching is reachable from every page, persistent, and immediate.

Linked issues: #140
