# User Stories

Stories are grouped into epics (one file each) named `<letter>-<slug>.md`.

## Epics

- [A — Discover & sign up](A-discover-signup.md)
- [B — First import](B-first-import.md)
- [C — Review & correct](C-review-corrections.md)
- [D — Insight & reporting](D-insight-reporting.md)
- [E — Trust & account](E-trust-account.md)

## Story format

Each story follows this block; keep it copy-pasteable:

```markdown
### UX-<E><n> (<P0|P1|P2>, <status>)

**As** <persona>, **I want** ... **so that** ...

Acceptance criteria:
- [ ] Testable, persona-viewpoint criterion
```

## Priorities

- **P0** — blocks the persona from reaching first success. Must ship with v1.
- **P1** — makes the persona stay and return; ship shortly after v1.
- **P2** — valuable once the persona is hooked; schedule freely.

## Statuses

- `draft` — being written, not agreed yet
- `ready` — agreed, not implemented
- `in-progress` — being implemented
- `done` — acceptance criteria pass in a manual walkthrough (note the date)
- `dropped` — no longer wanted; keep the record, never reuse the ID

## Definition of "v1 is user friendly"

Péter goes from `docker run` → registered → first CSV imported → sees a spending
summary → fixes one wrong category → finds where his money went — in under 10 minutes,
in Hungarian, without reading the README.
