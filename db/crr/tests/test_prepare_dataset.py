"""One known-format fixture for month expansion and TOU mapping."""
import csv
import io
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
import zipfile

import openpyxl

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from import_inputs import ACCOUNTS, HOLDINGS, HOURS
from prepare_dataset import build_dataset


class MonthlyFixture(unittest.TestCase):
    def test_monthly_expansion_and_tou_mapping(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)

            # Arrange: account workbook.
            workbook = openpyxl.Workbook()
            sheet = workbook.active
            sheet.title = "CRRAH"
            for _ in range(10):
                sheet.append([None])
            sheet.append(["Example LLC", "X", None, None, None, "a@example.com"])
            workbook.save(root / ACCOUNTS)

            # Arrange: published TOU hours.
            workbook = openpyxl.Workbook()
            sheet = workbook.active
            sheet.title = "CRR Time of Use Hours"
            sheet.append(["CRR Time of Use Hours"])
            sheet.append(["Year", "Month", "OffPeak", "PeakWD", "PeakWE", "Total"])
            for row in [(2026, "October", 248, 352, 144, 744),
                        (2026, "November", 241, 320, 160, 721),
                        (2026, "December", 248, 352, 144, 744)]:
                sheet.append(row)
            workbook.save(root / HOURS)

            # Arrange: whole-month contracts in the ZIP.
            stream = io.StringIO()
            writer = csv.writer(stream)
            writer.writerow("CRR_ID,SegmentID,AccountHolder,HedgeType,CRRType,Source,Sink,StartDate,EndDate,TimeOfUse,MW".split(","))
            for row in [(101, "OPT", "10/01/2026", "12/31/2026", "PeakWD", 100),
                        (102, "OPT", "11/01/2026", "12/31/2026", "PeakWD", 50),
                        (103, "OPT", "10/01/2026", "11/30/2026", "OffPeak", 75),
                        (104, "OBL", "11/01/2026", "11/30/2026", "PeakWE", 2)]:
                crr_id, hedge, start, end, block, mw = row
                writer.writerow([crr_id, 1, "X", hedge, "STANDARD", "A", "B", start, end, block, mw])
            with zipfile.ZipFile(root / HOLDINGS, "w") as archive:
                archive.writestr("Common_ExistingCRR.csv", stream.getvalue())

            # Arrange: settlement-point location and lowercase labels.
            (root / "topology.json").write_text(json.dumps({"settlement_points": {"features": [{
                "geometry": {"type": "Point", "coordinates": [-97, 30]},
                "properties": {"sp_id": "A", "sp_type": "hub", "load_zone": "houston"},
            }]}}))

            # Act: run the build, including validate.sql.
            output = root / "crr.sqlite"
            results = build_dataset(root, output)

            # Assert: counts and uppercase settlement-point labels.
            self.assertEqual((results["raw_rows"], results["monthly_rows"]), (4, 4))
            with sqlite3.connect(output) as db:
                self.assertEqual(db.execute("SELECT point_type, load_zone FROM settlement_points WHERE settlement_point='A'").fetchone(),
                                 ("HUB", "HOUSTON"))
                rows = list(db.execute("""SELECT delivery_month, hedge_type, peak_wd_mw, peak_we_mw,
                    off_peak_mw, peak_wd_mwh, peak_we_mwh, off_peak_mwh
                    FROM crr_monthly_holdings ORDER BY delivery_month, hedge_type"""))
                summary_rows = list(db.execute("""SELECT hedge_type, mwh
                    FROM crr_summary_holdings ORDER BY hedge_type"""))

            # Assert: inclusive months, separate hedges, and TOU MW/MWh.
            self.assertEqual(rows, [
                ("2026-10-01", "OPT", 100, 0, 75, 35200, 0, 18600),
                ("2026-11-01", "OBL", 0, 2, 0, 0, 320, 0),
                ("2026-11-01", "OPT", 150, 0, 75, 48000, 0, 18075),
                ("2026-12-01", "OPT", 150, 0, 0, 52800, 0, 0),
            ])
            self.assertEqual(summary_rows, [("OBL", 320), ("OPT", 172675)])
            self.assertEqual(results["summary_total_errors"], 0)
