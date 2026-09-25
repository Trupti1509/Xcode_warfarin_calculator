import unittest
from app import app


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_health_endpoint(self):
        res = self.client.get("/health")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["version"], "1.3.1")

    def test_calculate_clinical(self):
        payload = {
            "age": "70",
            "height_cm": "180",
            "weight_kg": "75",
            "population": "white_other",
            "amiodarone": "false",
            "enzyme_inducer": "false",
        }
        res = self.client.post("/api/calculate", data=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["method_label"], "IWPC clinical algorithm")
        self.assertIn("Complete PGx information", data["pathway_reason"])
        self.assertNotIn("dose_range_mg", data)
        self.assertTrue(data["weekly_mg"] > 0)
        self.assertTrue(data["daily_average_mg"] > 0)

    def test_calculate_pgx_manual(self):
        payload = {
            "age": "70",
            "height_cm": "180",
            "weight_kg": "75",
            "population": "white_other",
            "amiodarone": "false",
            "enzyme_inducer": "false",
            "manual_pgx": "true",
            "cyp2c9_allele1": "*1",
            "cyp2c9_allele2": "*1",
            "vkorc1": "G/A",
        }
        res = self.client.post("/api/calculate", data=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["method_label"], "IWPC pharmacogenetic algorithm")
        self.assertEqual(
            data["pathway_reason"],
            "CYP2C9 and VKORC1 information required for the pharmacogenetic pathway was available.",
        )
        self.assertAlmostEqual(data["weekly_mg"], 29.5, places=1)
        self.assertAlmostEqual(data["daily_average_mg"], 4.2, places=1)
        self.assertEqual(data["fda_label_range"], "5–7 mg/day")

    def test_invalid_target_inr(self):
        payload = {
            "age": "70",
            "height_cm": "180",
            "weight_kg": "75",
            "population": "white_other",
            "target_inr": "other",
        }
        res = self.client.post("/api/calculate", data=payload)
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertIn("not validated for the selected INR target", data["error"])


if __name__ == "__main__":
    unittest.main()
