"""Run with python3 -m pipeline --help."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from .core import ROOT, DEFAULT_OUTPUT, COLUMNS, classify, compile_rules, import_csv, read_json, write_output, parse_amount, normalize_date


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description='Import local bank exports. Never uploads data.')
    commands = result.add_subparsers(dest='command', required=True)
    demo = commands.add_parser('demo', help='Create explicitly fictional demo transactions')
    demo.add_argument('--if-missing', action='store_true')
    for name, command in [('demo', demo), ('import', commands.add_parser('import', help='Import mapped CSV exports')), ('pdf', commands.add_parser('pdf', help='Import supported Polish text-PDF statements (experimental)'))]:
        command.add_argument('--output', type=Path, default=DEFAULT_OUTPUT)
        command.add_argument('--replace', action='store_true', help='Explicitly replace the existing dataset')
        if name != 'demo':
            command.add_argument('--input', type=Path, required=True, help='File or directory; all matching files are imported together')
            command.add_argument('--rules', type=Path, default=ROOT / 'config' / 'rules.example.json')
        if name == 'import':
            command.add_argument('--mapping', type=Path, default=ROOT / 'config' / 'import.example.json')
    return result


def demo_rows() -> list[dict]:
    rows = []
    entries = [
        ('04', '-120.00', 'DEMO Grocery Market', 'groceries'),
        ('08', '-35.00', 'DEMO Coffee Shop', 'restaurant_fast_food'),
        ('12', '-90.00', 'DEMO Transit', 'public_transport'),
        ('16', '-50.00', 'DEMO Software', 'software_ai_dev'),
        ('20', '-1800.00', 'DEMO Housing', 'rent_payment'),
        ('25', '5000.00', 'DEMO Employer', 'income_incoming'),
        ('27', '-200.00', 'DEMO Own Account', 'own_account_transfer'),
    ]
    for month in range(1, 7):
        for day, amount, merchant, tag in entries:
            row = dict.fromkeys(COLUMNS, '')
            row.update(transaction_date=f'2026-{month:02}-{day}', transaction_id=f'demo-{month}-{day}',
                       amount=amount, currency='PLN', counterparty=merchant,
                       description='Fictional demonstration transaction. Not a real bank record.',
                       source_file='generated-demo', tags=json.dumps([tag]))
            rows.append(row)
    return rows


def main() -> int:
    args = parser().parse_args()
    try:
        if args.command == 'demo':
            if args.if_missing and args.output.exists():
                print('Existing local dataset kept; demo was not written.')
                return 0
            rows = demo_rows()
        else:
            suffix = '.csv' if args.command == 'import' else '.pdf'
            paths = sorted(p for p in args.input.iterdir() if p.is_file() and p.suffix.lower() == suffix) if args.input.is_dir() else [args.input]
            if not paths or any(not p.is_file() or p.suffix.lower() != suffix for p in paths):
                raise ValueError('No supported input files found')
            if args.output.resolve() in [p.resolve() for p in paths]:
                raise ValueError('Output must be separate from original inputs')
            rules = read_json(args.rules)
            if args.command == 'import':
                rows = import_csv(paths, read_json(args.mapping), rules)
            else:
                from .pdf import extract_pdf
                compiled = compile_rules(rules)
                rows = []
                for path in paths:
                    extracted, report = extract_pdf(path)
                    if report['status'] != 'ok' or not extracted:
                        raise ValueError('PDF layout unsupported or empty; use a CSV export instead. Output not changed')
                    for row in extracted:
                        row['transaction_date'] = normalize_date(row['transaction_date'])
                        row['amount'] = str(parse_amount(row['amount']))
                        row['tags'] = json.dumps(classify(row, compiled), ensure_ascii=False)
                    rows.extend(extracted)
                rows.sort(key=lambda row: row['transaction_date'])
        write_output(rows, args.output, replace=args.replace)
        currencies = sorted({row['currency'] for row in rows})
        print(f'Imported {len(rows)} transactions. Currencies: {", ".join(currencies)}. Reload the dashboard.')
        if args.command == 'pdf':
            print('Experimental PDF import: reconcile counts and totals with every statement before relying on it.')
        return 0
    except (ValueError, OSError, UnicodeError, re.error) as exc:
        print(f'Import failed: {exc.__class__.__name__}. {exc if isinstance(exc, ValueError) and not isinstance(exc, (json.JSONDecodeError, UnicodeError)) else "Check local files and configuration."}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
