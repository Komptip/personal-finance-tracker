"""Validated, deterministic imports. No network calls or account credentials."""
from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import tempfile
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / 'data' / 'processed' / 'tagged_transactions.csv'
COLUMNS = ['transaction_date', 'transaction_time', 'transaction_id', 'amount',
           'currency', 'counterparty', 'title', 'description', 'location',
           'source_file', 'source_page', 'statement_period_start',
           'statement_period_end', 'tags']


def read_json(path: Path) -> dict:
    with path.open(encoding='utf-8-sig') as stream:
        value = json.load(stream)
    if not isinstance(value, dict):
        raise ValueError('Configuration must be a JSON object')
    return value


def parse_amount(value: str, decimal_separator: str = '.') -> Decimal:
    value = value.strip().replace('\u00a0', '').replace(' ', '')
    if not value:
        raise ValueError('Missing amount')
    if decimal_separator not in ('.', ','):
        raise ValueError('decimal_separator must be . or ,')
    if value.startswith('(') and value.endswith(')'):
        value = '-' + value[1:-1]
    thousands = ',' if decimal_separator == '.' else '.'
    # Validate grouping instead of silently turning an unexpected decimal into thousands.
    if thousands in value:
        integer = value.lstrip('+-').split(decimal_separator)[0]
        if not re.fullmatch(r'\d{1,3}(?:' + re.escape(thousands) + r'\d{3})+', integer):
            raise ValueError('Invalid thousands separator; check decimal_separator')
        value = value.replace(thousands, '')
    value = value.replace(decimal_separator, '.')
    if not re.fullmatch(r'[+-]?\d+(?:\.\d{1,2})?', value):
        raise ValueError('Amount must be a number with at most two decimal places')
    try:
        result = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError('Invalid amount') from exc
    if not result.is_finite() or abs(result) > Decimal('1e12'):
        raise ValueError('Amount is outside the supported range')
    return result.quantize(Decimal('0.01'))


def normalize_date(value: str, date_format: str = '%Y-%m-%d') -> str:
    return datetime.strptime(value.strip(), date_format).date().isoformat()


def compile_rules(config: dict) -> list[tuple[str, re.Pattern]]:
    rules = config.get('rules', [])
    if not isinstance(rules, list):
        raise ValueError('rules must be an array')
    result = []
    for rule in rules:
        if not isinstance(rule, dict) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]*', rule.get('tag', '')):
            raise ValueError('Every rule needs a simple tag and a regex pattern')
        pattern = rule.get('pattern')
        if not isinstance(pattern, str) or not pattern:
            raise ValueError('Rule patterns must be nonempty strings')
        result.append((rule['tag'], re.compile(pattern, re.IGNORECASE)))
    return result


def classify(row: dict, rules: list[tuple[str, re.Pattern]]) -> list[str]:
    text = ' '.join(row.get(key, '') for key in ('counterparty', 'title', 'description', 'location'))
    tags = list(dict.fromkeys(tag for tag, pattern in rules if pattern.search(text)))
    if 'own_account_transfer' in tags:
        return ['own_account_transfer']
    if 'food_delivery' in tags and 'taxi_rideshare' in tags:
        tags.remove('taxi_rideshare')
    return tags


def import_csv(paths: list[Path], mapping: dict, rules_config: dict) -> list[dict]:
    columns = mapping.get('columns', {})
    if not isinstance(columns, dict) or not columns.get('transaction_date'):
        raise ValueError('Map columns.transaction_date to the export date header')
    if not columns.get('amount') and not (columns.get('debit') and columns.get('credit')):
        raise ValueError('Map amount, or both debit and credit columns')
    if columns.get('amount') and (columns.get('debit') or columns.get('credit')):
        raise ValueError('Choose signed amount OR debit/credit columns')
    delimiter = mapping.get('delimiter', ',')
    if not isinstance(delimiter, str) or len(delimiter) != 1:
        raise ValueError('delimiter must be one character')
    rules = compile_rules(rules_config)
    records: list[dict] = []
    seen: dict[str, dict] = {}
    for path in sorted(paths):
        with path.open(encoding=mapping.get('encoding', 'utf-8-sig'), newline='') as stream:
            reader = csv.DictReader(stream, delimiter=delimiter)
            headers = reader.fieldnames or []
            if len(headers) != len(set(headers)):
                raise ValueError('Duplicate CSV headers')
            if not all(header in headers for header in columns.values() if header):
                raise ValueError('Mapped columns are missing; check headers and delimiter')
            for line, source in enumerate(reader, 2):
                if None in source or any(value is None for value in source.values()):
                    raise ValueError(f'Row {line}: incorrect number of CSV fields')
                if not any(value.strip() for value in source.values()):
                    continue
                def field(key: str) -> str:
                    return source.get(columns.get(key, ''), '').strip()
                try:
                    row = {key: field(key) for key in COLUMNS}
                    row['transaction_date'] = normalize_date(field('transaction_date'), mapping.get('date_format', '%Y-%m-%d'))
                    separator = mapping.get('decimal_separator', '.')
                    if columns.get('amount'):
                        amount = parse_amount(field('amount'), separator)
                        if mapping.get('invert_amount_sign', False):
                            amount = -amount
                    else:
                        debit = parse_amount(field('debit') or '0', separator)
                        credit = parse_amount(field('credit') or '0', separator)
                        if debit < 0 or credit < 0 or (debit and credit):
                            raise ValueError('Debit/credit columns must be nonnegative and only one may be nonzero')
                        amount = credit - debit
                    row['amount'] = str(amount)
                    row['currency'] = (field('currency') or mapping.get('default_currency', '')).upper()
                    if not re.fullmatch('[A-Z]{3}', row['currency']):
                        raise ValueError('Currency must be a three-letter code or set default_currency')
                    row['source_file'] = path.name
                    row['tags'] = json.dumps(classify(row, rules), ensure_ascii=False)
                    original_id = field('transaction_id')
                    if original_id:
                        row['transaction_id'] = mapping.get('id_prefix', '') + original_id
                        # Same bank ID with different facts must never disappear silently.
                        facts = {key: value for key, value in row.items() if key not in ('source_file', 'source_page')}
                        if row['transaction_id'] in seen:
                            if seen[row['transaction_id']] != facts:
                                raise ValueError('Conflicting transaction ID; use a unique id_prefix per account/export set')
                            continue
                        seen[row['transaction_id']] = facts
                    else:
                        # Keep legitimate identical purchases; no fuzzy deduplication.
                        key = json.dumps([path.name, line, row], sort_keys=True)
                        row['transaction_id'] = 'local-' + hashlib.sha256(key.encode()).hexdigest()[:20]
                    records.append(row)
                except (ValueError, TypeError) as exc:
                    # Avoid printing the input row or values into terminal/CI logs.
                    raise ValueError(f'Row {line}: invalid mapped date, amount, currency or ID ({type(exc).__name__}). Check the local export and mapping.') from None
    if not records:
        raise ValueError('No transactions found; existing output was not changed')
    return sorted(records, key=lambda row: (row['transaction_date'], row['transaction_id']))


def write_output(rows: list[dict], path: Path, *, replace: bool = False) -> None:
    path = path.resolve()
    if path.exists() and not replace:
        raise ValueError('Output already exists. Review your input, then use --replace to replace it')
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix='.import-', suffix='.tmp', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'w', encoding='utf-8', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=COLUMNS, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(rows)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        path.chmod(0o600)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
