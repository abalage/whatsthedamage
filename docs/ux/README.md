# UX Documentation

Personas and user stories driving the frontend's user experience. This directory is the
source of truth for *who* the product is for and *what* they need to accomplish.

## Layout

```
docs/ux/
├── README.md              # This file: index and conventions
├── personas/
│   ├── _template.md       # Copy this for a new persona
│   └── peter-selfhoster.md
└── stories/
    ├── README.md          # ID scheme, priority and status definitions
    ├── A-discover-signup.md
    ├── B-first-import.md
    ├── C-review-corrections.md
    ├── D-insight-reporting.md
    └── E-trust-account.md
```

## Conventions

- One file per persona, named `<slug>.md` (kebab-case).
- One file per epic, named `<letter>-<slug>.md`; stories live inside their epic file.
- Story IDs are stable: `UX-<epic-letter><number>` (e.g. `UX-B2`). Never renumber or
  reuse IDs; mark obsolete stories as `status: dropped` instead of deleting them.
- Every story has exactly one persona, a priority (P0/P1/P2), and a status.
- Acceptance criteria are written from the persona's viewpoint and are testable by
  manual walkthrough ("run the journey as the persona", no repo knowledge).

## Workflow

1. Add or edit personas/stories here first; implementation issues reference the
   story IDs (e.g. "Implements UX-B2").
2. When a story's acceptance criteria all pass in a manual walkthrough, set its
   status to `done` and note the date.
3. Revisit personas after real external users arrive; record findings in the
   persona file rather than rewriting history.
