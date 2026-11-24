import json
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import urlopen

from app import make_server
from evidence import DATA, load_evidence, search


class EvidenceTests(unittest.TestCase):
    def test_normalization_drops_duplicate_and_joins_sources(self):
        evidence, summary = load_evidence()
        self.assertEqual(summary, {"input_rows": 9, "duplicates": 1})
        self.assertEqual(len(evidence), 8)
        self.assertTrue(evidence["record_id"].is_unique)
        row = evidence.set_index("record_id").loc["ev-02"]
        self.assertEqual(row["topic"], "medication access")
        self.assertEqual(row["source_ref"], "DEMO-WF-02")

    def test_filters_are_literal_casefolded_and_can_be_combined(self):
        evidence, _ = load_evidence()
        records = search(evidence, " FOREST COUNTY ", "REFERRALS")
        self.assertEqual([item["record_id"] for item in records], ["ev-01", "ev-04"])
        self.assertEqual(search(evidence, "["), [])
        self.assertEqual(search(evidence, "refill", "unlisted"), [])

    def test_missing_fields_become_null(self):
        evidence, _ = load_evidence()
        self.assertIsNone(search(evidence, "refill")[0]["published"])
        self.assertIsNone(search(evidence, "transportation")[0]["setting"])

    def test_missing_provenance_keeps_the_record(self):
        with tempfile.TemporaryDirectory() as directory:
            data = Path(directory)
            rows = (DATA / "evidence.csv").read_text(encoding="utf-8")
            (data / "evidence.csv").write_text(rows.replace("ev-01,s01,", "ev-01,unknown,"), encoding="utf-8")
            (data / "sources.csv").write_bytes((DATA / "sources.csv").read_bytes())
            evidence, _ = load_evidence(data)
        record = search(evidence, "Referral status")[0]
        self.assertEqual(record["source_id"], "unknown")
        self.assertIsNone(record["publisher"])


class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = make_server("127.0.0.1", 0)
        cls.worker = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.worker.start()
        cls.base = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.worker.join(timeout=2)
        cls.server.server_close()

    def test_api_returns_filtered_records_and_dataset_summary(self):
        with urlopen(f"{self.base}/api/evidence?topic=medication+access&q=refill", timeout=3) as response:
            payload = json.load(response)
        self.assertEqual(len(payload["records"]), 1)
        self.assertEqual(payload["records"][0]["source_ref"], "DEMO-INT-06")
        self.assertEqual(payload["summary"]["records"], 8)
        self.assertEqual(payload["summary"]["undated"], 1)

    def test_home_page_and_unknown_route(self):
        with urlopen(f"{self.base}/", timeout=3) as response:
            self.assertIn(b"Healthcare workflow evidence", response.read())
        with self.assertRaises(HTTPError) as error:
            urlopen(f"{self.base}/data/sources.csv", timeout=3)
        self.assertEqual(error.exception.code, 404)
