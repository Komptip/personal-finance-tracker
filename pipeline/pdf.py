#!/usr/bin/env python3
"""Experimental adapter for a limited Polish text-statement layout.

Not a universal bank PDF parser; reconcile results before use.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Iterable


DATE_RE = re.compile(r"\b(?P<date>\d{2}[.-]\d{2}[.-]\d{4}|\d{4}-\d{2}-\d{2})\b")
TIME_RE = re.compile(r"\b(?P<time>\d{1,2}:\d{2}(?::\d{2})?)\b")
ACCOUNT_RE = re.compile(r"\b(?:\d{2}\s*){13}\b")
PERIOD_RE = re.compile(
    r"(?:od|za okres)\s+(\d{2}[.-]\d{2}[.-]\d{4})\s+(?:do|-)\s+(\d{2}[.-]\d{2}[.-]\d{4})",
    re.IGNORECASE,
)
MONEY_RE = re.compile(
    r"(?P<amount>[+-]?(?:\d{1,3}(?:[ .]\d{3})+|\d+),\d{2})\s*(?P<currency>PLN|EUR|USD|GBP)?",
    re.IGNORECASE,
)
TRANSACTION_ID_RE = re.compile(r"^\s*\d{2}[.-]\d{2}[.-]\d{4}\s+(?P<id>[A-Z0-9]{10,})\s+")
CARD_RE = re.compile(r"\bKarta:\s*(?P<card>\S+)", re.IGNORECASE)
LOCATION_RE = re.compile(
    r"\bLokalizacja:\s*(?P<location>.*?)(?:\s+Nr ref:|\s+Ref\.|\s+Niniejszy dokument|$)",
    re.IGNORECASE,
)
REFERENCE_RE = re.compile(
    r"\b(?:Nr ref:|Ref\. wł\. zlec\.:|Ref\.)\s*(?P<reference>[A-Z0-9/-]+)",
    re.IGNORECASE,
)


@dataclass
class StatementMeta:
    account: str = ""
    period_start: str = ""
    period_end: str = ""


def import_pdfplumber():
    try:
        import pdfplumber  # type: ignore
    except ImportError:
        print(
            "Missing dependency: pdfplumber. Install it with "
            "`python3 -m pip install -r requirements.txt`.",
            file=sys.stderr,
        )
        raise SystemExit(2)
    return pdfplumber


def normalize_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value.replace("\u00a0", " ")).strip()


def normalize_date(value: str) -> str:
    value = value.strip().replace(".", "-")
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return value
    day, month, year = value.split("-")
    return f"{year}-{month}-{day}"


def parse_decimal(value: str) -> str:
    normalized = value.replace("\u00a0", " ").replace(" ", "").replace(".", "")
    normalized = normalized.replace(",", ".")
    try:
        return str(Decimal(normalized))
    except InvalidOperation:
        return ""


def extract_meta(text: str) -> StatementMeta:
    meta = StatementMeta()
    account_match = ACCOUNT_RE.search(text)
    if account_match:
        meta.account = re.sub(r"\s+", "", account_match.group(0))

    period_match = PERIOD_RE.search(text)
    if period_match:
        meta.period_start = normalize_date(period_match.group(1))
        meta.period_end = normalize_date(period_match.group(2))

    return meta


def row_cells_to_line(row: Iterable[object]) -> str:
    return normalize_whitespace(" ".join(str(cell or "") for cell in row))


def extract_page_lines(page) -> list[str]:
    lines: list[str] = []

    try:
        tables = page.extract_tables() or []
    except Exception:
        tables = []

    for table in tables:
        for row in table:
            line = row_cells_to_line(row)
            if line:
                lines.append(line)

    if lines:
        return lines

    text = page.extract_text(x_tolerance=1, y_tolerance=3) or ""
    return [normalize_whitespace(line) for line in text.splitlines() if normalize_whitespace(line)]


def looks_like_transaction_start(line: str) -> bool:
    return bool(re.match(r"^\s*\d{2}[.-]\d{2}[.-]\d{4}\b", line) and MONEY_RE.search(line))


def merge_continuation_lines(lines: list[str]) -> list[str]:
    merged: list[str] = []
    for line in lines:
        if looks_like_transaction_start(line):
            merged.append(line)
        elif merged and not is_noise_line(line):
            merged[-1] = normalize_whitespace(f"{merged[-1]} {line}")
    return merged


def is_noise_line(line: str) -> bool:
    lowered = line.lower()
    noise_fragments = [
        "data operacji",
        "data ksi",
        "kwota",
        "saldo",
        "strona",
        "wyci",
        "historia rachunku",
        "zestawienie transakcji",
        "niniejszy dokument",
        "informacja o bankowym funduszu",
        "środki na rachunku",
        "podstawa prawna",
        "szczegółowy zakres",
        "zadbaj o wygodę",
        "po każdej zrobionej",
        "dzięki temu",
        "poinformujemy cię",
        "masz również stały",
        "jeśli korzystasz",
        "jeśli masz dostęp",
        "jeśli nie korzystasz",
        "aby korzystać",
        "powszechna kasa",
        "sąd rejonowy",
        "kapitał zakładowy",
    ]
    return any(fragment in lowered for fragment in noise_fragments)


def extract_counterparty_account(line: str) -> str:
    match = ACCOUNT_RE.search(line)
    if not match:
        return ""
    return re.sub(r"\s+", "", match.group(0))


def classify_direction(amount: str) -> str:
    if not amount:
        return ""
    if amount.startswith("-"):
        return "debit"
    if amount.startswith("+"):
        return "credit"
    return "credit"


def extract_match(pattern: re.Pattern[str], line: str, group: str) -> str:
    match = pattern.search(line)
    if not match:
        return ""
    return normalize_whitespace(match.group(group))


def trim_bank_footer(value: str) -> str:
    footer_markers = [
        "Informacja o Bankowym Funduszu",
        "Niniejszy dokument",
        "Powszechna Kasa",
        "Sąd Rejonowy",
        "Zadbaj o wygodę",
        "Podstawa prawna:",
        "kapitał zakładowy",
    ]
    end = len(value)
    for marker in footer_markers:
        marker_at = value.find(marker)
        if marker_at >= 0:
            end = min(end, marker_at)
    return normalize_whitespace(value[:end])


def parse_transaction_line(
    line: str,
    source_file: str,
    page_number: int,
    meta: StatementMeta,
) -> dict[str, str] | None:
    line = trim_bank_footer(line)
    dates = [normalize_date(match.group("date")) for match in DATE_RE.finditer(line)]
    money_matches = list(MONEY_RE.finditer(line))
    if not dates or not money_matches:
        return None

    amount_match = money_matches[0]
    balance_match = money_matches[1] if len(money_matches) > 1 else None
    amount = parse_decimal(amount_match.group("amount"))
    balance_after = parse_decimal(balance_match.group("amount")) if balance_match else ""
    currency = (amount_match.group("currency") or (balance_match.group("currency") if balance_match else "") or "").upper()

    time_match = TIME_RE.search(line)
    counterparty_account = extract_counterparty_account(line)

    first_date = DATE_RE.search(line)
    before_amount = normalize_whitespace(line[(first_date.end() if first_date else 0) : amount_match.start()])
    transaction_id = extract_match(TRANSACTION_ID_RE, line, "id")
    title = before_amount
    if transaction_id and title.startswith(transaction_id):
        title = normalize_whitespace(title[len(transaction_id) :])

    date_matches = list(DATE_RE.finditer(line))
    transaction_date_match = None
    date_anchor = balance_match.end() if balance_match else amount_match.end()
    for date_match in date_matches:
        if date_match.start() >= date_anchor:
            transaction_date_match = date_match
            break
    if transaction_date_match is None:
        transaction_date_match = date_matches[-1]

    after_transaction_date = ""
    if transaction_date_match:
        after_transaction_date = normalize_whitespace(line[transaction_date_match.end() :])
    description = normalize_whitespace(f"{title} {after_transaction_date}")

    location = extract_match(LOCATION_RE, description, "location")
    card = extract_match(CARD_RE, description, "card")
    reference_match = REFERENCE_RE.search(description)
    reference_number = normalize_whitespace(reference_match.group("reference")) if reference_match else ""
    if reference_match:
        description = trim_bank_footer(description[: reference_match.end()])

    counterparty = location
    for label in ("Odbiorca:", "Nadawca:", "Kontrahent:"):
        if label in description:
            counterparty = normalize_whitespace(description.split(label, 1)[1].split(":", 1)[0])
            break

    return {
        "source_file": source_file,
        "source_page": str(page_number),
        "statement_account": meta.account,
        "statement_period_start": meta.period_start,
        "statement_period_end": meta.period_end,
        "booking_date": dates[0],
        "transaction_date": normalize_date(transaction_date_match.group("date")) if transaction_date_match else dates[0],
        "transaction_time": time_match.group("time") if time_match else "",
        "transaction_id": transaction_id,
        "title": title,
        "description": description,
        "counterparty": counterparty,
        "counterparty_account": counterparty_account,
        "card": card,
        "location": location,
        "reference_number": reference_number,
        "amount": amount,
        "currency": currency,
        "direction": classify_direction(amount),
        "balance_after": balance_after,
        "raw_row": line,
    }


def extract_pdf(pdf_path: Path) -> tuple[list[dict[str, str]], dict[str, str]]:
    pdfplumber = import_pdfplumber()
    rows: list[dict[str, str]] = []
    page_count = 0

    with pdfplumber.open(pdf_path) as pdf:
        page_count = len(pdf.pages)
        all_text = "\n".join(page.extract_text() or "" for page in pdf.pages[:2])
        meta = extract_meta(all_text)

        for page_number, page in enumerate(pdf.pages, start=1):
            lines = merge_continuation_lines(extract_page_lines(page))
            for line in lines:
                parsed = parse_transaction_line(line, pdf_path.name, page_number, meta)
                if parsed:
                    rows.append(parsed)

    status = "ok" if rows else "skipped"
    message = "" if rows else "No transaction rows detected"
    report = {
        "source_file": pdf_path.name,
        "status": status,
        "pages": str(page_count),
        "transactions": str(len(rows)),
        "message": message,
    }
    return rows, report
