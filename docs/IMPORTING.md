# Bank export import specification

## Supported input formats

| Input                             | Support                                                                        |
| --------------------------------- | ------------------------------------------------------------------------------ |
| CSV with a signed amount          | Configurable headers, delimiter, encoding, date and decimal formats            |
| CSV with debit and credit columns | Map both; values must be nonnegative, with only one nonzero per row            |
| Polish text-based statement PDF   | Experimental legacy adapter; layout-dependent and needs reconciliation         |
| Scanned PDF, Excel, OFX/QFX/QIF   | Not directly supported; export CSV from the bank or add a tested local adapter |

No live bank connection is used. Export files manually. The pipeline does not require bank credentials.

## 1. Configure input storage

Place exports in `private/imports/`. Copy `config/import.example.json` to `private/import.json` and `config/rules.example.json` to `private/rules.json`. These directories are ignored by Git. Do not place real exports or screenshots under `public/`, `docs/`, `tests/` or `config/`.

## 2. Configure field mapping

The default mapping expects the following CSV structure. All example records are synthetic:

```csv
Date,Amount,Currency,Merchant,Description,ID
2026-01-04,-12.50,PLN,DEMO Grocery Market,Fictional purchase,demo-a
2026-01-25,100.00,PLN,DEMO Employer,Fictional salary,demo-b
```

Configure `private/import.json` for the bank export format. Keys under `columns` are application fields; values are exact CSV headers. Remove optional mappings whose headers are absent.

| Setting              | Meaning                                                                                   |
| -------------------- | ----------------------------------------------------------------------------------------- |
| `encoding`           | Usually `utf-8-sig`; `cp1250` can be used for older Polish exports                        |
| `delimiter`          | One character, such as `,`, `;` or `\t`                                                   |
| `date_format`        | Python strptime format: `%Y-%m-%d`, `%d.%m.%Y`, `%d/%m/%Y`, etc.                          |
| `decimal_separator`  | `.` or `,`; grouped thousands and spaces are supported                                    |
| `default_currency`   | Used only when the currency column is unmapped or empty; PLN by default                   |
| `invert_amount_sign` | Use only if signed amounts in this export use positive for outgoing                       |
| `id_prefix`          | Optional stable namespace for IDs, such as `account-a-`; do not use a real account number |

Required fields: `transaction_date`, plus `amount` **or** both `debit` and `credit`. Currency must come from a mapped column or `default_currency`. Amounts support up to two decimal places; outgoing is negative and incoming is positive.

Optional fields include: `transaction_id`, `counterparty`, `description`, `title`, `location`. Extra bank columns are ignored. The canonical output does not include dedicated account/card/raw-statement fields; descriptions may still contain sensitive data, so the output must remain excluded from version control.

For separate debit/credit columns, remove the `amount` mapping and add:

```json
"debit": "Debit",
"credit": "Credit"
```

Resolve ambiguous dates, transaction direction and currency using the bank's export settings or information provided by the data owner.

## 3. Configure classification rules

Rules are case-insensitive regular expressions matched against merchant, title, description and location. More than one tag may match. Unmatched transactions remain uncategorized.

```json
{
  "rules": [
    { "tag": "groceries", "pattern": "\\bDEMO Grocery\\b" },
    { "tag": "own_account_transfer", "pattern": "DEMO internal transfer" }
  ]
}
```

The example rules are intentionally generic. Store personal merchant patterns and transfer identifiers only in `private/rules.json`. Own-account transfer matches take precedence and are excluded from default totals. Cash withdrawals are not automatically assumed to be rent. The default configuration contains no user-specific income, medical, donation, rent-amount or account assumptions.

## 4. Validate the candidate dataset

```bash
python3 -m pipeline import \
  --input private/imports \
  --mapping private/import.json \
  --rules private/rules.json \
  --output data/processed/candidate.csv
```

When the input is a directory, the importer processes all `.csv` files directly inside it using the same mapping. Keep processed outputs outside the input directory. Validate counts, date range, currencies and signed totals against your exports. Inspect a few records locally, especially debit/credit signs and refund transactions.

Stable, identical transaction IDs are deduplicated within one import. Conflicting IDs cause the import to fail. Without bank IDs, identical purchases are retained; overlapping exports may therefore produce duplicate records. Avoid overlaps or reconcile manually. Imports rebuild a dataset from the specified input set; they do not merge with the previous output.

Files requiring different mappings should be normalized separately into the canonical schema and reconciled before combining. The CLI does not automatically combine different bank formats. Additional adapters must include tests using synthetic data.

## 5. Replace the active dataset

After reviewing the candidate and authorizing replacement:

```bash
python3 -m pipeline import \
  --input private/imports \
  --mapping private/import.json \
  --rules private/rules.json \
  --replace
```

The importer validates all rows before an atomic output replacement. Failed imports preserve the existing output. Refresh the dashboard to load it. PLN remains the default currency. The display-currency selector converts the current selection to PLN, EUR, USD or UAH with dated NBP average rates. Mixed-currency datasets also have a separate source-currency selector; original currencies and amounts stay unchanged.

## Experimental PDF import

Install the optional dependency as described in SETUP.md, then:

```bash
.venv/bin/python -m pipeline pdf \
  --input private/imports \
  --rules private/rules.json \
  --output data/processed/pdf-candidate.csv
```

The adapter recognizes a limited Polish statement layout with day-month-year dates and decimal-comma amounts. It does not OCR scanned pages, and it cannot certify completeness. A PDF can yield some rows while omitting others; compare every statement's counts and totals before activation. Unsupported or empty PDFs cause the import to fail. Prefer CSV whenever available. PDF imports do not deduplicate overlapping statements. When this Polish adapter finds no currency label, it uses PLN; verify the statement currency before activation.

## Demo dataset management

`python3 -m pipeline demo --if-missing` never replaces an existing file. To intentionally discard the current active dataset and restore the synthetic demo, first back up your dataset, then use `python3 -m pipeline demo --replace`.
