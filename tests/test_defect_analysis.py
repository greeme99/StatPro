import unittest

from statpro.defect_analysis import (
    DefectAnalysisInputError,
    DefectCategory,
    create_defect_analysis,
    revise_defect_analysis,
    summarize_defect_analysis,
)


class DefectAnalysisTests(unittest.TestCase):
    def test_revision_preserves_parent_and_prior_snapshot(self) -> None:
        first = create_defect_analysis(
            analysis_id="DEF-001",
            title="조립 결함",
            process_name="조립",
            period="2026-W45",
            owner_ref="quality.team",
            categories=(DefectCategory("스크래치", 4, 1000, 12.5, 4),),
        )
        revised = revise_defect_analysis(
            first,
            title=first.title,
            process_name=first.process_name,
            period=first.period,
            owner_ref=first.owner_ref,
            categories=(DefectCategory("스크래치", 5, 1000, 12.5, 4),),
        )
        self.assertEqual(revised.revision, 2)
        self.assertEqual(revised.parent_digest, first.digest)
        self.assertEqual(first.categories[0].defect_count, 4)

    def test_summary_exposes_dpmo_loss_and_risk_priority(self) -> None:
        snapshot = create_defect_analysis(
            analysis_id="DEF-002",
            title="검사 결함",
            process_name="검사",
            period="2026-11",
            owner_ref="quality.team",
            categories=(DefectCategory("A", 2, 1000, 10, 3), DefectCategory("B", 1, 1000, 100, 9)),
        )
        summary = summarize_defect_analysis(snapshot)
        self.assertEqual(summary["dpmo"], 1500)
        self.assertEqual(summary["estimated_loss"], 120)
        self.assertEqual(summary["top_risk_category"], "B")

    def test_rejects_defects_above_opportunities(self) -> None:
        with self.assertRaises(DefectAnalysisInputError):
            create_defect_analysis(
                analysis_id="DEF-003",
                title="x",
                process_name="x",
                period="x",
                owner_ref="x",
                categories=(DefectCategory("A", 2, 1),),
            )


if __name__ == "__main__":
    unittest.main()
