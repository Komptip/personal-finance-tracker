# Agent runbook

This is a local Nuxt finance dashboard with a Python bank-export pipeline. Complete setup and verify the result; do not stop at describing commands. Read README.md, docs/SETUP.md and docs/IMPORTING.md before changing the data workflow.

## Non-negotiable data boundaries

- Preserve existing exports, datasets, private rules and `.env`. Never run demo with `--replace` over a real dataset. `npm run setup` and `demo --if-missing` preserve existing output.
- `private/`, `data/`, `review/`, raw exports and generated CSVs are intentionally ignored. Personal names, account/card numbers, phone numbers, merchant-specific personal patterns and transaction examples must never enter tracked source, docs, tests, screenshots or commit messages.
- Do not read or copy another checkout's private data, even on the same PC. Each clone starts with its own demo or empty state.
- Do not upload bank exports to external APIs, issue trackers or other services. For cloud AI assistance, ask the owner to supply synthetic rows/header names or explicitly approve reading private material in the assistant session. The application itself needs no AI access.
- Any individual-specific category/own-account rules belong in `private/rules.json`, never `config/rules.example.json`.
- PLN remains the default analysis currency. Filter currencies separately; never sum unlike currencies or restore guessed conversion rates.
- Bind to loopback. There is no authentication. Do not publish or tunnel the app with real data.

## Setup task

1. Inspect `git status --short`, the OS and installed Node/Python versions. Use the repository's own instructions, not another user's home paths. On Windows prefer WSL Ubuntu and keep the clone in its Linux filesystem.
2. Use Node 22+ (`nvm install && nvm use` if nvm is installed) and Python 3.10+. Install missing prerequisites only within the task's authorization; explain any system-level dependency that requires user intervention.
3. Run `npm run setup`. It installs the locked npm dependencies, creates local directories, prepares Nuxt, installs local privacy hooks if none are configured, and generates fictional data only when the default dataset is absent.
4. Run `npm run check` and `npm run build`. For PDF work, use a virtual environment and install requirements.txt; CSV/demo need no pip packages.
5. Run `npm run dev`. Keep its process alive and report the actual URL. If port 3000 is occupied, identify the existing process or choose a free port; do not kill unrelated processes.
6. Verify `/`, `/transactions`, `/suggestions`, and `/api/transactions` return successful responses. Do not dump the transaction API body into logs. Inspect a synthetic demo when taking screenshots.
7. Report setup status, port, whether data is demo or existing, and any remaining limitation.

## Import task

1. Determine the export format, encoding, delimiter, date format, signed amount vs. debit/credit columns and currency. Prefer header names plus fictional rows. CSV is the supported general-purpose path; PDFs depend on layout.
2. Keep raw exports in `private/imports/` and copy example settings to `private/import.json` and `private/rules.json`. No bank credentials are needed.
3. Map dates, amounts and currency explicitly. Negative = outgoing; positive = incoming. Do not guess ambiguous dates or transaction direction. Map actual stable transaction IDs when available; overlapping exports without IDs need manual reconciliation.
4. First import into a separate ignored output (for example `data/processed/candidate.csv`). Verify row counts, date range, currencies, signed totals and a few user-approved samples against the export. The CLI is local and prints only counts/currencies, not rows.
5. Replace the active dataset only when the user has authorized it. Use the documented CLI with `--replace`. Reload and verify app/API counts. Preserve originals.
6. Unknown banks require a local mapping or adapter, not changes containing real bank records. Add only synthetic regression fixtures when implementing an adapter.

## Before committing or pushing

Run `npm run check`, `npm run build`, `git diff --check`, and review `git diff --cached --stat` and the staged source diff. Run `npm run privacy` after staging; run `npm run privacy:history` before pushing. The scanner is heuristic, so manually inspect names, patterns and hardcoded values too. Never bypass hooks or force-add ignored bank data.

Do not publish existing history that contains private data even if the tip is clean. Preserve it locally and prepare a sanitized publication history. Rewriting an already populated remote requires explicit authorization and coordination.

## Code map

- `pipeline/core.py`: strict mapped CSV import, classification, atomic writes.
- `pipeline/__main__.py`: demo/import/pdf commands.
- `pipeline/pdf.py`: experimental Polish statement text parser.
- `server/api/transactions.get.ts`: private server-side dataset path and no-store responses.
- `utils/transactionData.ts`: validates API data and limits exposed fields.
- `utils/analysis.ts`, `utils/categoryRanking.ts`: filters, totals and category ranking.
- `composables/useAnalysis.ts`: shared scope and data state.
- `components/`, `pages/`: UI.
- `tests/`: synthetic regression tests. `scripts/check_privacy.py`: index/history checks.

Keep dependencies focused. Format changes with `npm run format`. Avoid rebuilding the user's UI or modifying unrelated projects as part of setup.
