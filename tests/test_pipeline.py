import unittest
from pathlib import Path

from services.analyzer import analyze_all
from services.regulation import extract_change
from services.retrieval import retrieve_affected_sections


ROOT = Path(__file__).parents[1]
REGULATION = ROOT / "data" / "regulations" / "pdpa_section_26_amendment.txt"
COMPANY_DOCS = ROOT / "data" / "company_docs"


class PipelineTests(unittest.TestCase):
    def test_regulation_extracts_effective_date_and_requirement(self):
        change = extract_change(REGULATION)
        self.assertIn("Proposed MAS SCS", change["title"])
        self.assertIn("five days", change["new_requirement"])

    def test_retrieval_finds_transfer_documents(self):
        sections = retrieve_affected_sections(
            "stablecoin reserve redemption yield five days",
            str(COMPANY_DOCS),
        )
        names = {section["document"] for section in sections}
        self.assertIn("data_transfer_policy.txt", names)
        self.assertIn("transfer_checklist.txt", names)

    def test_analyzer_produces_evidence_linked_findings(self):
        change = extract_change(REGULATION)
        sections = retrieve_affected_sections(
            change["new_requirement"], str(COMPANY_DOCS)
        )
        findings = analyze_all(change, sections)
        self.assertTrue(findings)
        self.assertTrue(all(item["legal_quote"] for item in findings))
        self.assertTrue(all(item["company_quote"] for item in findings))
        self.assertTrue(all(0 <= item["impact_score"] <= 100 for item in findings))


if __name__ == "__main__":
    unittest.main()
