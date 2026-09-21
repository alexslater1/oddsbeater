# oddsbeater

@README.md

The rough spec / build guide is in `planning/`.

## Workflow

- For code changes, propose a plan and wait for approval before implementing.
- Before finishing, run `just lint fmt-check typecheck test`. All must pass.
- Don't commit. End with a suggested one-line Conventional Commit message.

## Hard rules

1. Data and secrets never enter the repo. (Once needed) secrets go in `.env` (key names only in `.env.example`). Raw data goes in git-ignored `data/`.
2. New top-level folders are added only when an entire phase starts.
3. Contracts first: no data crosses a language boundary without a JSON Schema.
4. Every job is idempotent, resumable and logged.
5. Point-in-time data: every fact row carries `retrieved_at` (when we fetched it) and `available_at` (when it became public). No feature may use rows with `available_at` after its cut-off.
6. No code change without tests.
7. Non-obvious design decisions get a short ADR in `notes/adr/`.
8. Small, reviewable changes.
9. Take the minimal approach; don't add anything the task doesn't need.
