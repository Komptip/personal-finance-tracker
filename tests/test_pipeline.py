import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from pipeline.core import import_csv, parse_amount, write_output

MAPPING = {'columns': {'transaction_date': 'Date', 'amount': 'Amount', 'currency': 'Currency', 'counterparty': 'Merchant', 'transaction_id': 'ID'}}
RULES = {'rules': [{'tag': 'groceries', 'pattern': 'Grocery'}]}


class ImportTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)

    def file(self, rows, name='input.csv', headers=None, delimiter=','):
        path = self.root / name
        with path.open('w', newline='', encoding='utf-8-sig') as stream:
            writer = csv.writer(stream, delimiter=delimiter)
            writer.writerow(headers or ['Date', 'Amount', 'Currency', 'Merchant', 'ID'])
            writer.writerows(rows)
        return path

    def test_signed_amount_and_classification(self):
        path = self.file([['2026-01-03', '-12.50', 'PLN', 'DEMO Grocery', 'demo-a']])
        row = import_csv([path], MAPPING, RULES)[0]
        self.assertEqual(row['amount'], '-12.50')
        self.assertEqual(json.loads(row['tags']), ['groceries'])

    def test_decimal_comma_and_thousands(self):
        self.assertEqual(str(parse_amount('-1.234,56', ',')), '-1234.56')
        self.assertEqual(str(parse_amount('1\u00a0234,56', ',')), '1234.56')
        for value in ['NaN', '12,34', '', '1.234', '1e3']:
            with self.assertRaises(ValueError):
                parse_amount(value)

    def test_debit_credit_and_local_date(self):
        path = self.file([['31.01.2026', '12,50', '', 'PLN']], headers=['Date', 'Debit', 'Credit', 'Currency'], delimiter=';')
        mapping = {'delimiter': ';', 'decimal_separator': ',', 'date_format': '%d.%m.%Y', 'columns': {'transaction_date': 'Date', 'debit': 'Debit', 'credit': 'Credit', 'currency': 'Currency'}}
        self.assertEqual(import_csv([path], mapping, RULES)[0]['amount'], '-12.50')

    def test_invalid_input_does_not_replace_existing_output(self):
        output = self.root / 'output.csv'
        output.write_text('keep me')
        path = self.file([['2026-02-31', '-12.50', 'PLN', 'DEMO', 'demo-a']])
        mapping = self.root / 'mapping.json'
        mapping.write_text(json.dumps(MAPPING))
        result = subprocess.run([sys.executable, '-m', 'pipeline', 'import', '--input', str(path), '--mapping', str(mapping), '--output', str(output), '--replace'], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(output.read_text(), 'keep me')
        self.assertNotIn('2026-02-31', result.stderr)

    def test_deduplicate_only_identical_explicit_ids(self):
        row = ['2026-01-03', '-12.50', 'PLN', 'DEMO', 'demo-a']
        path = self.file([row, row])
        self.assertEqual(len(import_csv([path], MAPPING, RULES)), 1)
        path = self.file([row, [*row[:1], '-13.00', *row[2:]]])
        with self.assertRaises(ValueError):
            import_csv([path], MAPPING, RULES)
        mapping = {'columns': {key: value for key, value in MAPPING['columns'].items() if key != 'transaction_id'}}
        path = self.file([row, row])
        self.assertEqual(len(import_csv([path], mapping, RULES)), 2)

    def test_output_requires_explicit_replace(self):
        output = self.root / 'output.csv'
        output.write_text('keep me')
        with self.assertRaises(ValueError):
            write_output([], output)
        self.assertEqual(output.read_text(), 'keep me')

    def test_setup_demo_never_overwrites_data(self):
        output = self.root / 'output.csv'
        output.write_text('keep me')
        result = subprocess.run([sys.executable, '-m', 'pipeline', 'demo', '--if-missing', '--output', str(output)], capture_output=True)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(output.read_text(), 'keep me')

    def test_mixed_currencies_are_preserved(self):
        path = self.file([['2026-01-03', '-12.50', 'PLN', 'DEMO', 'demo-a'], ['2026-01-04', '-3.50', 'EUR', 'DEMO', 'demo-b']])
        self.assertEqual([row['currency'] for row in import_csv([path], MAPPING, RULES)], ['PLN', 'EUR'])


if __name__ == '__main__':
    unittest.main()
