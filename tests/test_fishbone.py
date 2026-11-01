from __future__ import annotations

import unittest

from statpro.quality_tools import (
    FishboneInputError,
    FishboneSnapshot,
    add_fishbone_cause,
    create_fishbone,
)


class FishboneTests(unittest.TestCase):
    def setUp(self) -> None:
        self.diagram = create_fishbone(
            diagram_id="assembly-scratch",
            title="조립 스크래치 원인 분석",
            process_name="조립 1라인",
            problem_statement="외관 스크래치가 목표를 초과한다.",
            categories=(("man", "사람"), ("machine", "설비")),
        )

    def test_revision_digest_and_evidence_are_preserved(self) -> None:
        revised = add_fishbone_cause(
            self.diagram,
            category_id="machine",
            cause_id="guide-wear",
            text="이송 가이드 마모",
            evidence_refs=("run:pareto-01", " photo:guide-02 "),
            selected_for_verification=True,
        )

        self.assertEqual(revised.revision, 2)
        self.assertEqual(revised.parent_digest, self.diagram.digest)
        self.assertNotEqual(revised.digest, self.diagram.digest)
        cause = revised.categories[1].causes[0]
        self.assertEqual(cause.evidence_refs, ("run:pareto-01", "photo:guide-02"))
        self.assertTrue(cause.selected_for_verification)
        self.assertEqual(FishboneSnapshot.from_dict(revised.to_dict()), revised)

    def test_rejects_unknown_category_and_duplicate_cause(self) -> None:
        with self.assertRaises(FishboneInputError) as unknown:
            add_fishbone_cause(
                self.diagram, category_id="material", cause_id="oil", text="오염"
            )
        self.assertEqual(unknown.exception.detail.code, "unknown_category")

        revised = add_fishbone_cause(
            self.diagram, category_id="man", cause_id="training", text="교육 부족"
        )
        with self.assertRaises(FishboneInputError) as duplicate:
            add_fishbone_cause(
                revised, category_id="machine", cause_id="training", text="중복"
            )
        self.assertEqual(duplicate.exception.detail.code, "duplicate_cause_id")

    def test_requires_distinct_categories(self) -> None:
        with self.assertRaises(FishboneInputError) as context:
            create_fishbone(
                diagram_id="invalid",
                title="invalid",
                process_name="line",
                problem_statement="problem",
                categories=(("same", "사람"), ("same", "설비")),
            )
        self.assertEqual(context.exception.detail.code, "duplicate_category_id")


if __name__ == "__main__":
    unittest.main()
