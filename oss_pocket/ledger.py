# oss-pocket ledger
# Author: Mourad.Soltani
"""Parse a sales CSV and score progress toward the EU-wide €10,000 threshold.

This is a bookkeeping aid for solo sellers. It does not file OSS returns and
it is not legal or tax advice. Confirm treatment with a qualified adviser.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Iterable

from oss_pocket import THRESHOLD_EUR

# EU-27 ISO codes. Domestic sales are excluded from the cross-border sum.
EU_MEMBER_STATES = frozenset(
    {
        "AT",
        "BE",
        "BG",
        "HR",
        "CY",
        "CZ",
        "DK",
        "EE",
        "FI",
        "FR",
        "DE",
        "GR",
        "HU",
        "IE",
        "IT",
        "LV",
        "LT",
        "LU",
        "MT",
        "NL",
        "PL",
        "PT",
        "RO",
        "SK",
        "SI",
        "ES",
        "SE",
    }
)


class LedgerError(ValueError):
    """Raised when a sales row cannot be interpreted."""


@dataclass
class Sale:
    sold_on: date
    seller_country: str
    buyer_country: str
    net_eur: Decimal
    buyer_type: str
    supply: str
    note: str = ""

    @property
    def counts_toward_threshold(self) -> bool:
        if self.buyer_type != "b2c":
            return False
        if self.seller_country not in EU_MEMBER_STATES:
            return False
        if self.buyer_country not in EU_MEMBER_STATES:
            return False
        if self.seller_country == self.buyer_country:
            return False
        if self.supply not in {"goods", "tbe"}:
            return False
        return self.net_eur > 0


@dataclass
class ThresholdReport:
    year: int
    seller_country: str
    threshold_eur: Decimal
    cross_border_net_eur: Decimal
    remaining_eur: Decimal
    over_threshold: bool
    by_country: dict[str, Decimal] = field(default_factory=dict)
    included_rows: int = 0
    skipped_rows: int = 0

    def as_dict(self) -> dict:
        return {
            "year": self.year,
            "seller_country": self.seller_country,
            "threshold_eur": str(self.threshold_eur),
            "cross_border_net_eur": str(self.cross_border_net_eur),
            "remaining_eur": str(self.remaining_eur),
            "over_threshold": self.over_threshold,
            "progress_pct": str(
                (self.cross_border_net_eur / self.threshold_eur * Decimal("100")).quantize(
                    Decimal("0.1")
                )
            ),
            "by_country": {k: str(v) for k, v in sorted(self.by_country.items())},
            "included_rows": self.included_rows,
            "skipped_rows": self.skipped_rows,
            "disclaimer": "Not tax advice. Mourad.Soltani",
        }


def _dec(raw: str, line_no: int) -> Decimal:
    try:
        value = Decimal(raw.strip())
    except (InvalidOperation, AttributeError) as exc:
        raise LedgerError(f"line {line_no}: invalid net_eur {raw!r}") from exc
    return value.quantize(Decimal("0.01"))


def _country(raw: str, line_no: int, field_name: str) -> str:
    code = (raw or "").strip().upper()
    if len(code) != 2 or not code.isalpha():
        raise LedgerError(f"line {line_no}: {field_name} must be ISO-2, got {raw!r}")
    return code


def parse_sales(rows: Iterable[dict], *, source: str = "csv") -> list[Sale]:
    required = {"date", "seller_country", "buyer_country", "net_eur", "buyer_type", "supply"}
    sales: list[Sale] = []
    for line_no, row in enumerate(rows, start=2):
        missing = required - set(row)
        if missing:
            raise LedgerError(f"{source}: missing columns {sorted(missing)}")
        try:
            sold_on = date.fromisoformat(row["date"].strip())
        except ValueError as exc:
            raise LedgerError(f"line {line_no}: date must be YYYY-MM-DD") from exc
        buyer_type = row["buyer_type"].strip().lower()
        supply = row["supply"].strip().lower()
        if buyer_type not in {"b2c", "b2b"}:
            raise LedgerError(f"line {line_no}: buyer_type must be b2c or b2b")
        if supply not in {"goods", "tbe", "service"}:
            raise LedgerError(f"line {line_no}: supply must be goods, tbe, or service")
        sales.append(
            Sale(
                sold_on=sold_on,
                seller_country=_country(row["seller_country"], line_no, "seller_country"),
                buyer_country=_country(row["buyer_country"], line_no, "buyer_country"),
                net_eur=_dec(row["net_eur"], line_no),
                buyer_type=buyer_type,
                supply=supply,
                note=(row.get("note") or "").strip(),
            )
        )
    return sales


def load_csv(path: str) -> list[Sale]:
    with open(path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise LedgerError("CSV has no header")
        return parse_sales(reader, source=path)


def build_report(sales: Iterable[Sale], *, year: int, seller_country: str) -> ThresholdReport:
    seller = seller_country.strip().upper()
    if seller not in EU_MEMBER_STATES:
        raise LedgerError(f"seller_country {seller} is not an EU-27 code in this tool")
    total = Decimal("0.00")
    by_country: dict[str, Decimal] = {}
    included = 0
    skipped = 0
    for sale in sales:
        if sale.sold_on.year != year or sale.seller_country != seller:
            skipped += 1
            continue
        if not sale.counts_toward_threshold:
            skipped += 1
            continue
        total += sale.net_eur
        by_country[sale.buyer_country] = by_country.get(sale.buyer_country, Decimal("0.00")) + sale.net_eur
        included += 1
    threshold = Decimal(THRESHOLD_EUR).quantize(Decimal("0.01"))
    remaining = (threshold - total).quantize(Decimal("0.01"))
    return ThresholdReport(
        year=year,
        seller_country=seller,
        threshold_eur=threshold,
        cross_border_net_eur=total.quantize(Decimal("0.01")),
        remaining_eur=remaining,
        over_threshold=total >= threshold,
        by_country=by_country,
        included_rows=included,
        skipped_rows=skipped,
    )
