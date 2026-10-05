# oss-pocket ledger tests
# Author: Mourad.Soltani

import tempfile
import unittest
from pathlib import Path

from oss_pocket.cli import main
from oss_pocket.ledger import LedgerError, build_report, load_csv

SAMPLE = """date,seller_country,buyer_country,net_eur,buyer_type,supply,note
2026-01-15,FR,DE,4000.00,b2c,goods,berlin order
2026-02-02,FR,ES,3500.50,b2c,tbe,download
2026-02-03,FR,FR,900.00,b2c,goods,domestic ignored
2026-02-04,FR,DE,200.00,b2b,goods,reverse charge ignored
2026-03-01,FR,US,500.00,b2c,goods,export ignored
2026-03-09,FR,IT,2500.00,b2c,service,general service ignored
2025-12-31,FR,DE,9999.00,b2c,goods,prior year ignored
"""


class LedgerTests(unittest.TestCase):
    def write_sample(self, text: str = SAMPLE) -> str:
        handle = tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, encoding="utf-8")
        handle.write(text)
        handle.close()
        self.addCleanup(lambda: Path(handle.name).unlink(missing_ok=True))
        return handle.name

    def test_threshold_math_excludes_non_qualifying_rows(self):
        sales = load_csv(self.write_sample())
        report = build_report(sales, year=2026, seller_country="fr")
        self.assertEqual(str(report.cross_border_net_eur), "7500.50")
        self.assertEqual(str(report.remaining_eur), "2499.50")
        self.assertFalse(report.over_threshold)
        self.assertEqual(report.included_rows, 2)
        self.assertEqual(str(report.by_country["DE"]), "4000.00")
        self.assertEqual(str(report.by_country["ES"]), "3500.50")

    def test_over_threshold_exit_code(self):
        path = self.write_sample(
            "date,seller_country,buyer_country,net_eur,buyer_type,supply\n"
            "2026-04-01,NL,BE,10000.00,b2c,goods\n"
        )
        self.assertEqual(main(["report", path, "--seller", "NL", "--year", "2026"]), 2)

    def test_under_threshold_exit_code(self):
        path = self.write_sample()
        self.assertEqual(main(["report", path, "--seller", "FR", "--year", "2026"]), 0)

    def test_bad_date_is_an_error(self):
        path = self.write_sample(
            "date,seller_country,buyer_country,net_eur,buyer_type,supply\n"
            "04/01/2026,NL,BE,10.00,b2c,goods\n"
        )
        with self.assertRaises(LedgerError):
            load_csv(path)

    def test_non_eu_seller_rejected(self):
        path = self.write_sample(
            "date,seller_country,buyer_country,net_eur,buyer_type,supply\n"
            "2026-04-01,US,DE,10.00,b2c,goods\n"
        )
        sales = load_csv(path)
        with self.assertRaises(LedgerError):
            build_report(sales, year=2026, seller_country="US")


if __name__ == "__main__":
    unittest.main()
