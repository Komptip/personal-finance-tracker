<p align="center">
  <img src="docs/assets/cover.svg" alt="Fin stats — your money, clearly. A local finance dashboard." width="960">
</p>

<h1 align="center">Personal Finance Tracker</h1>
<p align="center">Bring your bank exports. Understand your spending. Keep the data on your computer.</p>
<p align="center"><strong>Local data</strong> &nbsp;·&nbsp; <strong>PLN by default</strong> &nbsp;·&nbsp; <strong>No bank login</strong> &nbsp;·&nbsp; <strong>AI-ready setup</strong></p>

---

Fin stats turns bank exports into a searchable finance dashboard. Explore spending, income and net flow; drill into categories and merchants; and review the transactions behind every total.

The public repository contains **code and fictional demo generation only**. Your exports, processed transactions and personal matching rules stay in ignored local folders. The app and importer do not call an AI service or upload your bank data.

## Start with your AI assistant

Clone the repository **inside WSL** on Windows, then open that folder in Claude Code or Codex:

```bash
git clone https://github.com/Komptip/personal-finance-tracker.git
cd personal-finance-tracker
```

Paste this:

> Read AGENTS.md and docs/SETUP.md. Set this repository up locally, preserve any existing dataset, run the checks, and start the dashboard. Then help me map my bank export using docs/IMPORTING.md. Keep my exports and personal rules out of Git, and ask me before replacing an existing dataset.

`AGENTS.md` is the shared runbook. `CLAUDE.md` points Claude at the same instructions. No API key is needed to run the app.

## Or start it yourself

Requires **Node.js 22+**, **npm**, **Python 3.10+** and Git. Windows users should run these commands in WSL Ubuntu.

```bash
nvm install                 # if you use nvm; reads .nvmrc
nvm use
npm run setup               # install locked dependencies + demo if no dataset exists
npm run dev
```

Open **[localhost:3000](http://localhost:3000)**. Setup is safe to rerun: it keeps an existing dataset. Fresh installs get 42 clearly marked, fictional PLN transactions.

## What you can explore

| View                   | What it does                                                                                 |
| ---------------------- | -------------------------------------------------------------------------------------------- |
| **Overview**           | Spending, incoming funds, net flow, trends, ranked categories and recent transactions        |
| **Transactions**       | Search descriptions and merchants, filter dates and tags, inspect original details           |
| **Review**             | Trace observations back to transactions and inspect uncertain or uncategorized labels        |
| **Currency selection** | PLN is the default; other currencies are analyzed separately, without guessed exchange rates |

Own-account transfers are excluded from totals by default when tagged. Category matches are configurable suggestions, not verified facts. This is an analysis tool, not bank synchronization or accounting software.

## Bring your own data

1. Put CSV exports in `private/imports/`.
2. Copy the example mapping and rules into `private/`, then adapt them to your bank's headers.
3. Import all exports for the dataset together:

```bash
mkdir -p private/imports
cp config/import.example.json private/import.json
cp config/rules.example.json private/rules.json

python3 -m pipeline import \
  --input private/imports \
  --mapping private/import.json \
  --rules private/rules.json \
  --replace
```

`--replace` deliberately replaces the current dataset (including the demo). Original exports are untouched. Reload the browser after import. **[The import guide](docs/IMPORTING.md)** covers decimal commas, debit/credit columns, duplicate IDs, custom tags and the experimental Polish PDF adapter.

## How it fits together

```text
private/imports/       →  Python validation + local rules
                                   ↓
data/processed/        →  tagged_transactions.csv
                                   ↓
local Nuxt API         →  Overview · Transactions · Review
```

| Area                          | Technology                  |
| ----------------------------- | --------------------------- |
| UI and local API              | Nuxt 3 · Vue 3 · TypeScript |
| Charts                        | Chart.js · vue-chartjs      |
| CSV import and classification | Python standard library     |
| Optional PDF extraction       | pdfplumber                  |

## Development

```bash
npm run check              # formatting, types, Python + TypeScript tests
npm run build              # production build
npm run privacy:history    # inspect tracked files + reachable commit history
```

The development and preview servers bind to `127.0.0.1`. There is no authentication: keep this a local app. Do not deploy a build with personal data or expose it through a public tunnel.

## Guides

- **[Setup and troubleshooting](docs/SETUP.md)** — WSL, prerequisites, setup, startup and recovery.
- **[Importing bank exports](docs/IMPORTING.md)** — file mapping, validation and supported formats.
- **[Privacy and contributing](docs/PRIVACY.md)** — ignored files, Git checks and public-release precautions.
- **[Agent runbook](AGENTS.md)** — steps an assistant can execute and how to verify success.

> **Data stays yours.** Git ignores help prevent accidents; they do not encrypt files. Keep local backups somewhere you control, and review changes before publishing.
