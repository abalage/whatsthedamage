# Persona: Péter, the privacy-aware self-hoster

> Status: active · Created: 2026-10-26 · Primary persona for the broader-release effort

## Profile

| | |
|---|---|
| **Name / age** | Péter, 34, Budapest |
| **Location** | Hungary |
| **Occupation** | Mid-level software engineer |
| **Financial setup** | One K&H account (HUF) + one Revolut card; exports CSV monthly-ish |
| **Current tooling** | Hand-built Excel sheet with pivot tables; breaks whenever the bank changes the export format |
| **Motivation** | Wants real insight into spending without handing transaction data to a third party. Reads r/selfhosted, runs Home Assistant / a NAS / a small VPS |
| **Attitude to privacy** | Strongly prefers self-hosted; distrusts Mint-style SaaS; likes the "your data, your model" principle |
| **Technical skill** | Can run a Docker container and read a stack trace; will **not** write regex rules or edit `config.yml` unless the app walks him through it |
| **Devices** | Desktop browser at home for money tasks; occasional phone checks |
| **Language** | Hungarian first, English fine |

## Goals

- Import his bank's CSV and get a categorized overview of the month quickly.
- Fix wrong categories once and have the fix apply to future imports.
- Keep full control: everything stays on his own infrastructure.

## Frustrations

- Manual re-categorizing every month.
- Tools that assume an accountant's vocabulary.
- Apps that dump 500 raw rows with no summary.

## Success looks like

> "I imported this month's CSV and in 3 minutes I saw where my money went — and it's all on my own machine."

## Anti-persona (do not design for, v1)

**Anna, the casual budgeter**: non-technical, expects a hosted app with email login and
automatic bank sync. Out of scope for v1: no hosted offering, no email-based password
reset, YAML-based config, and single-bank support would all fail her. Recording her
prevents accidentally designing for an audience the product cannot serve yet.
