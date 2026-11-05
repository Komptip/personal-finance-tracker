# Local setup

## Windows + WSL Ubuntu

From PowerShell, check `wsl --list --verbose`, then enter Ubuntu with `wsl -d Ubuntu`. If WSL is missing, install it using Microsoft's WSL instructions before continuing. All commands below run in the Linux shell, not PowerShell.

Clone into a directory you own in the WSL filesystem:

```bash
mkdir -p ~/projects
cd ~/projects
git clone https://github.com/Komptip/personal-finance-tracker.git
cd personal-finance-tracker
```

Use your own clone. Do not reuse someone else's checkout or bank files just because they are on the same computer.

## Prerequisites

- Node.js 22+ and npm; `.nvmrc` selects the Node 22 line.
- Python 3.10+ (`python3 --version`). CSV import uses only the standard library.
- Git.

If nvm is already installed:

```bash
source ~/.nvm/nvm.sh
nvm install
nvm use
```

If Ubuntu lacks Python/Git, install the missing packages through the system package manager (`sudo apt install python3 python3-venv git` after updating package indexes). Install Node from a trusted Node distribution/version manager; setup does not execute a downloaded shell installer or change system packages.

## Install and run

```bash
npm run setup
npm run check
npm run build
npm run dev
```

Open <http://localhost:3000> in Windows. WSL localhost forwarding normally makes this available to Windows browsers. Setup checks prerequisites, runs `npm ci` from the lockfile, prepares Nuxt, creates local directories and generates a fictional demo **only if the default dataset is missing**. No account, API key, database or paid service is required.

Setup configures `.githooks` only when there is no pre-existing `core.hooksPath`. If you already use a hook manager, add `python3 scripts/check_privacy.py --staged` before commits and `python3 scripts/check_privacy.py --history` before pushes yourself.

The foreground dev process stays alive until Ctrl+C. For a persistent WSL session you can use an existing terminal multiplexer. Do not terminate unrelated services to free a port. To use another port:

```bash
npm run dev -- --port 3001
```

## Existing local data

The default active dataset is `data/processed/tagged_transactions.csv`. To use another local file, copy `.env.example` to `.env` and set `NUXT_DATA_FILE` (absolute or relative to the repository root). Restart the server after changing `.env`; reload the browser after replacing data.

For older checkouts with `tagged_transactions.csv` at the repository root, either set `NUXT_DATA_FILE=tagged_transactions.csv` in `.env`, or copy it into the default processed-data location. Do not regenerate a demo over it. For compatibility, blank currency cells in legacy datasets are interpreted as PLN in memory; the CSV is not modified. Nonempty currency values must be three-letter codes. Setup respects an existing default/custom file and does not generate a demo for a missing custom path.

Keep original exports separately. Imports validate the complete input before replacing the active output, but an explicit successful `--replace` replaces the dataset rather than appending.

## Optional PDF dependency

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pipeline pdf --help
```

This installs pdfplumber only for the experimental text-PDF path. The default demo and CSV workflow do not require it.

## Troubleshooting

| Symptom                             | Action                                                                                                                                                       |
| ----------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Unsupported Node version            | Run `nvm use`, then rerun setup. Do not mix Windows Node with WSL node_modules.                                                                              |
| `python3` missing                   | Install Python in the same OS/WSL environment as the checkout.                                                                                               |
| Missing history                     | Check `NUXT_DATA_FILE`, import data or generate the demo. A missing file produces an empty state.                                                            |
| Import refuses to overwrite         | Review the candidate output, then explicitly pass `--replace` if intended.                                                                                   |
| Invalid transaction data / HTTP 422 | Check mapped date, amount, currency and JSON tags. Invalid rows are not silently counted as zero.                                                            |
| Empty PLN selection                 | Choose a currency present in your export. Use the display-currency selector for conversion. The separate source selector appears for mixed-currency imports. |
| Port already used                   | Choose a free port and use the actual URL printed by Nuxt.                                                                                                   |
| Windows cannot reach WSL localhost  | First check `curl -I http://127.0.0.1:3000` inside WSL; inspect WSL forwarding/firewall settings without exposing the financial app publicly.                |

## Display currencies

PLN is the default. The main currency selector converts totals, chart labels and transaction display amounts to EUR, USD or UAH using the latest available NBP average rates. The rate date and conversion basis are shown below the toolbar. Transaction details keep original amounts. Mixed-currency imports have a separate **Transactions in** selector so unlike source currencies are never added together.

Rates are fetched server-side from a fixed public NBP endpoint and cached for one hour. No transaction data is sent. Conversion is a display estimate, not a historic transaction valuation or the exchange rate charged by your bank. If rates cannot be loaded, same-currency views still work and unavailable conversions show a dash with a retry action. A previously fetched rate can be reused, visibly marked as stale.

## Verification

With the server running, check `/`, `/transactions`, `/suggestions` and `/api/transactions` using the browser or an HTTP client. Check status codes and counts without saving personal response bodies into tracked files. The clean demo has 42 transactions, all in PLN, and a visible demo notice.

`npm run preview` serves a production build on loopback. Nuxt preview reads `.env`; when running `.output/server/index.mjs` directly, provide `NUXT_DATA_FILE` and `HOST=127.0.0.1` through the environment and run from the repository root. No data file is bundled into a public static directory.
