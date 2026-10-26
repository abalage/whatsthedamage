# Epic C — Review & correct

Persona: [Péter](../personas/peter-selfhoster.md). The correction/ML loop is the
product's differentiator; its discoverability is a P0.

### UX-C1 (P0, draft)

**As** a user finishing an import, **I want** to land on a summary first (total spend,
top categories, a chart), **so that** I get the insight without wading through rows.

Acceptance criteria:
- [ ] Post-import default view is a summary; the transaction table is the drill-down.

### UX-C2 (P0, draft)

**As** a user seeing a wrong category, **I want** to fix it inline and understand that
the fix can apply to future imports, **so that** the app gets better with use.

Acceptance criteria:
- [ ] Inline correction is discoverable without documentation.
- [ ] The "apply to future imports" option is explained at the moment of correction.

### UX-C3 (P0, draft)

**As** a user making a correction, **I want** to undo it and know it is undone, **so
that** I can experiment fearlessly.

Acceptance criteria:
- [ ] Undo is offered after each correction and gives clear confirmation.

### UX-C4 (P1, draft)

**As** a user, **I want** to review just the low-confidence transactions (e.g.
"Other"), **so that** cleanup is a routine, not archaeology.

Acceptance criteria:
- [ ] A one-click view of unknown/low-confidence rows exists.

### UX-C5 (P1, draft)

**As** a user, **I want** to filter by date and category with a visible result count,
**so that** I always know what I am looking at.

Acceptance criteria:
- [ ] Filters show the number of matching transactions.
