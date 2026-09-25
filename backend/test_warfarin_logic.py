import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from warfarin_logic import (
    WarfarinCalculatorError,
    calculate,
    get_fda_label_range,
    parse_manual_genetic,
)


class WarfarinCalculatorTests(unittest.TestCase):
    def test_published_iwpc_reference_case(self):
        """
        Published IWPC QA benchmark:
        Age 70, Height 180 cm, Weight 75 kg, White/other, VKORC1 G/A, CYP2C9 *1/*1,
        no inducer, no amiodarone -> 29.51640241 mg/week (approx 29.5 mg/week, 4.2 mg/day).
        """
        pgx = parse_manual_genetic(
            cyp2c9_allele1="*1",
            cyp2c9_allele2="*1",
            vkorc1="G/A",
        )
        result = calculate(
            age=70,
            height_cm=180,
            weight_kg=75,
            population="white_other",
            amiodarone=False,
            enzyme_inducer=False,
            genetic=pgx,
        )

        self.assertNotIn("dose_range_mg", result)
        self.assertEqual(result["method"], "pharmacogenetic_iwpc")
        self.assertEqual(result["method_label"], "IWPC pharmacogenetic algorithm")
        self.assertEqual(
            result["pathway_reason"],
            "CYP2C9 and VKORC1 information required for the pharmacogenetic pathway was available.",
        )
        self.assertAlmostEqual(result["weekly_mg"], 29.5, places=1)
        self.assertAlmostEqual(result["daily_average_mg"], 4.2, places=1)
        self.assertEqual(result["fda_label_range"], "5–7 mg/day")

    def test_clinical_iwpc_fallback_no_pgx(self):
        """When no PGx is supplied, calculate via IWPC clinical algorithm with explicit pathway reason."""
        result = calculate(
            age=70,
            height_cm=180,
            weight_kg=75,
            population="white_other",
            amiodarone=False,
            enzyme_inducer=False,
            genetic=None,
        )

        self.assertNotIn("dose_range_mg", result)
        self.assertEqual(result["method"], "clinical_iwpc")
        self.assertEqual(result["method_label"], "IWPC clinical algorithm")
        self.assertEqual(
            result["pathway_reason"],
            "Complete PGx information required for the pharmacogenetic pathway was not available. "
            "No missing genotype was assumed to be normal.",
        )
        self.assertGreater(result["weekly_mg"], 0)
        self.assertGreater(result["daily_average_mg"], 0)

    def test_african_ancestry_expanded_alleles_untested_fallback(self):
        """
        In African ancestry, CPIC directs clinical dosing if CYP2C9 *5, *6, *8, and *11
        were not all tested.
        """
        pgx = parse_manual_genetic(
            cyp2c9_allele1="*1",
            cyp2c9_allele2="*1",
            vkorc1="G/A",
            expanded_tested=False,
        )
        result = calculate(
            age=60,
            height_cm=175,
            weight_kg=80,
            population="black_african_american",
            amiodarone=False,
            enzyme_inducer=False,
            genetic=pgx,
        )

        self.assertEqual(result["method"], "clinical_iwpc")
        self.assertEqual(result["method_label"], "IWPC clinical algorithm")
        self.assertIn("CYP2C9 *5, *6, *8 and *11 were not all available", result["pathway_reason"])

    def test_african_ancestry_rs12777823_a_allele_separate_consideration(self):
        """
        In African Americans with complete expanded testing and rs12777823 A allele,
        CPIC recommends a separate 10-25% decrease without compounding into IWPC result.
        """
        pgx = parse_manual_genetic(
            cyp2c9_allele1="*1",
            cyp2c9_allele2="*1",
            vkorc1="G/G",
            expanded_tested=True,
            rs12777823="G/A",
        )
        result = calculate(
            age=55,
            height_cm=170,
            weight_kg=75,
            population="black_african_american",
            african_context="african_american",
            amiodarone=False,
            enzyme_inducer=False,
            genetic=pgx,
        )

        self.assertEqual(result["method"], "pharmacogenetic_iwpc")
        self.assertTrue(any("rs12777823" in note["title"] for note in result["pgx_notes"]))
        rs127_note = next(n for n in result["pgx_notes"] if "rs12777823" in n["title"])
        self.assertEqual(rs127_note["strength"], "Moderate")
        self.assertIsNotNone(rs127_note["range"])
        # Expected range is 75% to 90% of base weekly dose
        self.assertAlmostEqual(rs127_note["range"][0], round(result["weekly_mg"] * 0.75, 1), places=1)
        self.assertAlmostEqual(rs127_note["range"][1], round(result["weekly_mg"] * 0.90, 1), places=1)

    def test_african_ancestry_rs12777823_unconfirmed_context_informational_only(self):
        """When African American context is not confirmed, rs127 note is Informational only with no adjustment applied."""
        pgx = parse_manual_genetic(
            cyp2c9_allele1="*1",
            cyp2c9_allele2="*1",
            vkorc1="G/G",
            expanded_tested=True,
            rs12777823="G/A",
        )
        result = calculate(
            age=55,
            height_cm=170,
            weight_kg=75,
            population="black_african_american",
            african_context="unknown",
            amiodarone=False,
            enzyme_inducer=False,
            genetic=pgx,
        )

        self.assertEqual(result["method"], "pharmacogenetic_iwpc")
        rs127_note = next(n for n in result["pgx_notes"] if "rs12777823" in n["title"])
        self.assertEqual(rs127_note["title"], "rs12777823 A allele detected — no dose adjustment applied")
        self.assertEqual(rs127_note["strength"], "Informational only")
        self.assertIsNone(rs127_note["range"])
        self.assertIn("Because the relevant African American population context was not confirmed", rs127_note["text"])

    def test_non_african_cyp4f2_3_separate_consideration(self):
        """Non-African CYP4F2*3 carriers receive a separate 5-10% increase consideration."""
        pgx = parse_manual_genetic(
            cyp2c9_allele1="*1",
            cyp2c9_allele2="*1",
            vkorc1="G/A",
            cyp4f2="*1/*3",
        )
        result = calculate(
            age=65,
            height_cm=172,
            weight_kg=70,
            population="white_other",
            amiodarone=False,
            enzyme_inducer=False,
            genetic=pgx,
        )

        self.assertEqual(result["method"], "pharmacogenetic_iwpc")
        cyp4f2_note = next((n for n in result["pgx_notes"] if "CYP4F2" in n["title"]), None)
        self.assertIsNotNone(cyp4f2_note)
        self.assertEqual(cyp4f2_note["strength"], "Optional")
        self.assertAlmostEqual(cyp4f2_note["range"][0], round(result["weekly_mg"] * 1.05, 1), places=1)
        self.assertAlmostEqual(cyp4f2_note["range"][1], round(result["weekly_mg"] * 1.10, 1), places=1)

    def test_cyp2c9_expanded_allele_11_detected(self):
        """
        CYP2C9 *1/*11 uses *1/*1 for historical IWPC equation and reports
        a separate 15-30% reduction consideration.
        """
        pgx = parse_manual_genetic(
            cyp2c9_allele1="*1",
            cyp2c9_allele2="*11",
            vkorc1="G/G",
        )
        result = calculate(
            age=64,
            height_cm=172,
            weight_kg=78,
            population="white_other",
            amiodarone=False,
            enzyme_inducer=False,
            genetic=pgx,
        )

        self.assertEqual(result["method"], "pharmacogenetic_iwpc")
        self.assertEqual(result["genetic_summary"]["iwpc_cyp2c9_base"], "*1/*1")
        self.assertEqual(result["genetic_summary"]["iwpc_cyp2c9_input_text"], "No *2 or *3 coefficient applied")
        self.assertEqual(result["genetic_summary"]["additional_cyp2c9_finding"], "CYP2C9 *11 detected")
        self.assertIsNone(result["fda_label_range"])
        self.assertIsNone(result["fda_label_reference"])
        exp_note = next((n for n in result["pgx_notes"] if "CYP2C9" in n["title"]), None)
        self.assertIsNotNone(exp_note)
        self.assertAlmostEqual(exp_note["range"][0], round(result["weekly_mg"] * 0.70, 1), places=1)
        self.assertAlmostEqual(exp_note["range"][1], round(result["weekly_mg"] * 0.85, 1), places=1)

    def test_fda_label_range_lookup(self):
        """Verify FDA Coumadin label reference ranges."""
        self.assertEqual(get_fda_label_range("*1/*1", "G/G"), "5–7 mg/day")
        self.assertEqual(get_fda_label_range("*1/*3", "G/A"), "3–4 mg/day")
        self.assertEqual(get_fda_label_range("*3/*3", "A/A"), "0.5–2 mg/day")
        self.assertIsNone(get_fda_label_range("*1/*11", "G/G"))
        self.assertIsNone(get_fda_label_range("*1/*8", "G/G"))

    def test_age_decades_capping_at_9_for_centenarians(self):
        """Published IWPC defines decades as 1 for 10-19, ..., 9 for 90+. Age 100+ must be capped at 9."""
        res_90 = calculate(age=90, height_cm=170, weight_kg=70, population="white_other", amiodarone=False, enzyme_inducer=False)
        res_100 = calculate(age=100, height_cm=170, weight_kg=70, population="white_other", amiodarone=False, enzyme_inducer=False)
        self.assertEqual(res_90["weekly_mg"], res_100["weekly_mg"])

    def test_cyp2c9_poor_metabolizer_cpic_warning(self):
        """CYP2C9 *2/*3 and *3/*3 should trigger CPIC alternative anticoagulant recommendation."""
        pgx = parse_manual_genetic(
            cyp2c9_allele1="*3",
            cyp2c9_allele2="*3",
            vkorc1="A/A",
        )
        result = calculate(
            age=65,
            height_cm=170,
            weight_kg=70,
            population="white_other",
            amiodarone=False,
            enzyme_inducer=False,
            genetic=pgx,
        )
        self.assertTrue(any("alternative oral anticoagulant" in w for w in result["warnings"]))

    def test_clinical_input_validations(self):
        """Verify age, height, and weight boundaries."""
        with self.assertRaises(WarfarinCalculatorError):
            calculate(age=17, height_cm=170, weight_kg=70, population="white_other", amiodarone=False, enzyme_inducer=False)

        with self.assertRaises(WarfarinCalculatorError):
            calculate(age=125, height_cm=170, weight_kg=70, population="white_other", amiodarone=False, enzyme_inducer=False)

        with self.assertRaises(WarfarinCalculatorError):
            calculate(age=50, height_cm=90, weight_kg=70, population="white_other", amiodarone=False, enzyme_inducer=False)

        with self.assertRaises(WarfarinCalculatorError):
            calculate(age=50, height_cm=170, weight_kg=20, population="white_other", amiodarone=False, enzyme_inducer=False)


if __name__ == "__main__":
    unittest.main()
