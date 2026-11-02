# Epic B — First import

The make-or-break journey moment for [Péter](../personas/peter-selfhoster.md).

### UX-B1 (P0, draft)

**As** a new user with no data, **I want** an empty state that tells me exactly what to
do next, **so that** I am never stuck on a blank screen.

Acceptance criteria:
- [ ] With an empty account, the landing view explains: export your bank's CSV, then
      upload it here, with a link to per-bank instructions.

### UX-B2 (P0, draft)

**As** a user uploading a CSV, **I want** immediate feedback on whether my bank's format
was recognized, **so that** a wrong file never ends in a raw parsing error.

Acceptance criteria:
- [ ] On upload failure, the user sees what was wrong and which banks are supported,
      never a stack trace or generic 500.

### UX-B3 (P0, draft)

**As** a user during import and processing, **I want** visible progress and a result
count, **so that** I know the app is working and did something.

Acceptance criteria:
- [ ] Import and processing show status (stage, row counts) and finish with a summary
      (imported rows, unknown-category rows).

### UX-B4 (P1, draft)

**As** a user whose bank is not supported, **I want** a clear explanation and a path to
request or contribute a CSV profile, **so that** the failure converts into progress.

Acceptance criteria:
- [ ] Unsupported bank produces a friendly message with supported-bank list and a
      contribution pointer.

### UX-B5 (P1, draft)

**As** a user, **I want** to import several months of history in one or several files and
understand what happened to previous imports, **so that** I can build a full picture.

Acceptance criteria:
- [ ] Multi-file/period import works or is clearly explained; previous imports remain
      distinguishable.
