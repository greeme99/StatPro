from __future__ import annotations

import os
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from statpro.api.server import load_copilot_env
from statpro.application.copilot import (
    CopilotAction,
    CopilotGuidance,
    CopilotSource,
    CodexSdkCopilotProvider,
    FallbackChainCopilotProvider,
    ExaoneCopilotProvider,
    LocalKnowledgeCopilotProvider,
    RuleFirstCopilotProvider,
    UrlLibExaoneChatCompletionClient,
    build_default_copilot_provider,
    copilot_runtime_status,
)
from statpro.application.copilot_rules import COPILOT_RULE_CATALOG


class FakeExaoneClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, str, str, str]] = []

    def complete(self, *, api_key: str, endpoint: str, model: str, prompt: str, reasoning_effort: str) -> dict[str, object]:
        self.calls.append((api_key, endpoint, model, prompt, reasoning_effort))
        return {
            "choices": [{
                "message": {
                    "content": (
                            '{"answer":"열처리 코드 정의를 확인하세요.",'
                            '"recommended_tool":null,'
                            '"menu_path":["홈 (Home)"],'
                            '"checklist":["설비 매뉴얼 확보"],'
                            '"workflow_steps":["코드 발생 시점 확인"]}'
                    )
                }
            }]
        }


class FakeCodexClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str | None, str, str]] = []

    def run_read_only(self, *, model: str | None, prompt: str) -> str:
        self.calls.append((model, prompt, "read_only"))
        return (
            '{"answer":"Codex SDK 안내입니다.",'
            '"recommended_tool":"분석 선택",'
            '"menu_path":["홈 (Home)"],'
            '"checklist":["입력 구조 확인"],'
            '"workflow_steps":["질문 검토"]}'
        )


class MalformedCodexClient:
    def run_read_only(self, *, model: str | None, prompt: str) -> str:
        return "not-json"


class FakeHttpResponse:
    def __enter__(self) -> FakeHttpResponse:
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        return None

    def read(self) -> bytes:
        return b'{"choices":[{"message":{"content":"{}"}}]}'


class MalformedExaoneClient:
    def complete(self, *, api_key: str, endpoint: str, model: str, prompt: str, reasoning_effort: str) -> dict[str, object]:
        return {"choices": []}


class IncompleteGuidanceExaoneClient:
    def complete(self, *, api_key: str, endpoint: str, model: str, prompt: str, reasoning_effort: str) -> dict[str, object]:
        return {
            "choices": [{
                "message": {
                    "content": (
                            '{"answer":"필수 필드가 빠진 응답입니다.",'
                            '"menu_path":[],"checklist":[],"workflow_steps":[]}'
                    )
                }
            }]
        }


class RecordingFallbackProvider:
    def __init__(self) -> None:
        self.questions: list[str] = []

    def answer(
        self,
        *,
        question: str,
        pathname: str,
        workspace: str,
        evidence_context: str | None,
    ) -> CopilotGuidance:
        self.questions.append(question)
        return CopilotGuidance(
            answer="LLM 보완 안내",
            provider="k-exaone_v2.5",
            sources=(CopilotSource("사용자 질문", "copilot://question", "user_context"),),
            limitations=("생성형 AI 응답은 사용자가 검토해야 합니다.",),
            action=CopilotAction("분석 선택 열기", "/analyses"),
            guidance_mode="llm_fallback",
        )


class FailingFallbackProvider:
    def answer(
        self,
        *,
        question: str,
        pathname: str,
        workspace: str,
        evidence_context: str | None,
    ) -> CopilotGuidance:
        raise OSError("model unavailable")


class RateLimitedFallbackProvider:
    def answer(
        self,
        *,
        question: str,
        pathname: str,
        workspace: str,
        evidence_context: str | None,
    ) -> CopilotGuidance:
        raise OSError("EXAONE request failed with HTTP 429")


class RuleFirstCopilotProviderTests(unittest.TestCase):
    def test_catalog_covers_every_supported_field_domain_with_complete_rules(self) -> None:
        rule_ids = [rule.rule_id for rule in COPILOT_RULE_CATALOG]

        self.assertEqual(len(rule_ids), len(set(rule_ids)))
        self.assertTrue({"데이터", "SPC", "DOE", "측정시스템 분석", "FMEA", "DMAIC", "7대 품질 도구"} <= {
            rule.domain for rule in COPILOT_RULE_CATALOG
        })
        for rule in COPILOT_RULE_CATALOG:
            self.assertTrue(rule.situation)
            self.assertTrue(rule.recommended_tool)
            self.assertTrue(rule.action_href.startswith("/"))
            self.assertGreaterEqual(len(rule.checklist), 2)
            self.assertGreaterEqual(len(rule.workflow_steps), 4)
            self.assertTrue(rule.source_reference.startswith("docs/"))
            self.assertTrue(
                (Path(__file__).resolve().parents[1] / rule.source_reference).is_file(),
                f"missing Rulebase evidence: {rule.source_reference}",
            )

    def test_catalog_exposes_core_workspace_entry_rules(self) -> None:
        rules = {rule.rule_id: rule for rule in COPILOT_RULE_CATALOG}
        expected_routes = {
            "spc-xbar-r-small-subgroup": "/analyses/spc/xbar-r",
            "spc-xbar-s-large-subgroup": "/analyses/spc/xbar-s",
            "spc-imr-single-observation": "/analyses/imr/new",
            "spc-p-variable-sample": "/analyses/spc/attribute?chart=p",
            "spc-rare-event": "/analyses/spc/rare-events",
            "msa-crossed-gage-rr": "/analyses/msa/gage-rr",
            "msa-nested-gage-rr": "/analyses/msa/gage-rr-nested",
            "msa-attribute-agreement": "/analyses/msa/attribute-agreement",
            "msa-bias-linearity": "/analyses/msa/bias-linearity",
            "doe-screening": "/doe",
            "doe-response-surface": "/doe",
            "fmea-pfmea-start": "/fmea",
            "dmaic-root-cause": "/home/dmaic/analyze/root-causes",
        }
        self.assertEqual({rule_id: rules[rule_id].action_href for rule_id in expected_routes}, expected_routes)

    def test_catalog_covers_general_workspace_routes_not_covered_by_industry_cases(self) -> None:
        rules = {rule.rule_id: rule for rule in COPILOT_RULE_CATALOG}
        expected_routes = {
            "analysis-guided-selection": "/analyses",
            "data-worksheet-transformation": "/data",
            "spc-check-sheet": "/spc/tools/check-sheet",
            "quality-dashboard": "/quality",
            "defect-dpmo-analysis": "/defects",
            "doe-full-factorial": "/analyses/doe/full-factorial",
            "doe-fractional-factorial": "/analyses/doe/fractional-factorial",
            "doe-desirability-optimizer": "/analyses/doe/response-optimizer",
            "dmaic-define-project": "/home/dmaic/define",
            "dmaic-measure-plan": "/home/dmaic/measure",
            "dmaic-cost-benefit": "/home/dmaic/improve/cost-benefit",
            "dmaic-implementation-plan": "/home/dmaic/improve/implementation-plan",
            "learning-resources": "/home/learning",
        }
        self.assertEqual({rule_id: rules[rule_id].action_href for rule_id in expected_routes}, expected_routes)

        for rule_id in expected_routes:
            rule = rules[rule_id]
            self.assertGreaterEqual(len(rule.checklist), 2)
            self.assertGreaterEqual(len(rule.workflow_steps), 4)

    def test_xbar_r_guidance_has_a_complete_text_to_workflow_contract(self) -> None:
        guidance = LocalKnowledgeCopilotProvider().answer(
            question="Xbar-R 소집단 관리도를 설정하고 싶어요",
            pathname="/analyses/spc/xbar-r",
            workspace="통계적 공정관리 (SPC)",
            evidence_context=None,
        )

        self.assertEqual(guidance.rule_id, "spc-xbar-r-selection")
        self.assertGreaterEqual(len(guidance.checklist), 3)
        self.assertGreaterEqual(len(guidance.workflow_steps), 5)

    def test_env_file_loads_only_copilot_settings_without_overriding_process(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            env_file = Path(directory) / ".env"
            env_file.write_text(
                "STATPRO_COPILOT_EXAONE_ENABLED=true\n"
                "EXAONE_API_KEY=local-secret\n"
                "STATPRO_COPILOT_EXAONE_MODEL=k-exaone_v2.5\n"
                "STATPRO_COPILOT_EXAONE_SIMPLE_REASONING_EFFORT=low\n"
                "STATPRO_COPILOT_EXAONE_COMPLEX_REASONING_EFFORT=high\n"
                "STATPRO_COPILOT_CODEX_ENABLED=true\n"
                "STATPRO_COPILOT_CODEX_ENABLED=true\n"
                "STATPRO_COPILOT_CODEX_MODEL=gpt-test\n"
                "UNRELATED_SECRET=must-not-load\n",
                encoding="utf-8",
            )
            with patch.dict(
                os.environ,
                {"EXAONE_API_KEY": "process-secret"},
                clear=True,
            ):
                load_copilot_env(env_file)

                self.assertEqual(os.environ["STATPRO_COPILOT_EXAONE_ENABLED"], "true")
                self.assertEqual(os.environ["EXAONE_API_KEY"], "process-secret")
                self.assertEqual(os.environ["STATPRO_COPILOT_EXAONE_SIMPLE_REASONING_EFFORT"], "low")
                self.assertEqual(os.environ["STATPRO_COPILOT_CODEX_MODEL"], "gpt-test")
                self.assertNotIn("UNRELATED_SECRET", os.environ)
    def test_rule_match_never_calls_the_llm_fallback(self) -> None:
        fallback = RecordingFallbackProvider()
        provider = RuleFirstCopilotProvider(LocalKnowledgeCopilotProvider(), fallback)

        guidance = provider.answer(
            question="품질 수율 Y를 높이기 위해 온도, 압력, 시간 설정값을 실험하고 싶어요",
            pathname="/home",
            workspace="홈 (Home)",
            evidence_context=None,
        )

        self.assertEqual(fallback.questions, [])
        self.assertEqual(guidance.guidance_mode, "rulebase")
        self.assertEqual(guidance.rule_id, "doe-yield-optimization")
        self.assertEqual(guidance.recommended_tool, "실험계획법 (DOE)")
        self.assertEqual(
            guidance.menu_path,
            ("홈 (Home)", "실험계획법 (DOE)", "설계 및 생성"),
        )
        self.assertGreaterEqual(len(guidance.checklist), 4)
        self.assertGreaterEqual(len(guidance.workflow_steps), 5)

    def test_coating_discoloration_optimization_uses_doe_without_llm(self) -> None:
        fallback = RecordingFallbackProvider()
        provider = RuleFirstCopilotProvider(LocalKnowledgeCopilotProvider(), fallback)

        guidance = provider.answer(
            question="휴대폰 케이스의 착색 방지를 위한 최적 코팅 조건을 찾는 방법",
            pathname="/analyses",
            workspace="분석 선택",
            evidence_context=None,
        )

        self.assertEqual(fallback.questions, [])
        self.assertEqual(guidance.rule_id, "doe-coating-discoloration-optimization")
        self.assertEqual(guidance.action.href, "/doe")
        self.assertIn("ΔE", guidance.answer)
        self.assertEqual(len(guidance.workflow_steps), 5)

    def test_complex_rulebase_request_uses_api_to_enrich_unanswered_parts(self) -> None:
        fallback = RecordingFallbackProvider()
        provider = RuleFirstCopilotProvider(LocalKnowledgeCopilotProvider(), fallback)

        guidance = provider.answer(
            question="비가동의 정의와 MTBF 기준, 관리지표를 제안하고 데이터 분석으로 문제점 도출 및 개선방안 수립 절차를 상세히 설명해줘",
            pathname="/home",
            workspace="홈 (Home)",
            evidence_context=None,
        )

        self.assertEqual(len(fallback.questions), 1)
        self.assertIn("반복하지 말고", fallback.questions[0])
        self.assertEqual(guidance.rule_id, "dmaic-equipment-downtime")
        self.assertIn("추가 분석 가이드", guidance.answer)

    def test_unmatched_question_calls_exaone_once(self) -> None:
        fallback = RecordingFallbackProvider()
        provider = RuleFirstCopilotProvider(LocalKnowledgeCopilotProvider(), fallback)

        guidance = provider.answer(
            question="사내 신규 열처리 장비의 고유 진단 코드를 해석해줘",
            pathname="/home",
            workspace="홈 (Home)",
            evidence_context=None,
        )

        self.assertEqual(fallback.questions, ["사내 신규 열처리 장비의 고유 진단 코드를 해석해줘"])
        self.assertEqual(guidance.provider, "k-exaone_v2.5")
        self.assertEqual(guidance.guidance_mode, "llm_fallback")

    def test_fallback_chain_uses_light_exaone_for_a_simple_question(self) -> None:
        simple = RecordingFallbackProvider()
        complex_provider = RecordingFallbackProvider()
        codex = RecordingFallbackProvider()
        chain = FallbackChainCopilotProvider(
            exaone_simple=simple,
            exaone_complex=complex_provider,
            codex=codex,
        )

        guidance = chain.answer(
            question="작업표 열 이름을 설명해줘",
            pathname="/data",
            workspace="작업표 및 데이터 (Worksheet & Data)",
            evidence_context=None,
        )

        self.assertEqual(simple.questions, ["작업표 열 이름을 설명해줘"])
        self.assertEqual(complex_provider.questions, [])
        self.assertEqual(codex.questions, ["작업표 열 이름을 설명해줘"])
        self.assertEqual(guidance.guidance_mode, "llm_fallback")
        self.assertEqual([(step.stage, step.status) for step in guidance.fallback_steps], [("EXAONE API", "answered"), ("Codex SDK", "answered")])

    def test_selected_exaone_bypasses_codex(self) -> None:
        exaone = RecordingFallbackProvider()
        codex = RecordingFallbackProvider()
        chain = FallbackChainCopilotProvider(
            exaone_simple=RecordingFallbackProvider(),
            exaone_complex=exaone,
            codex=codex,
        )

        guidance = chain.answer_selected_model(
            model_preference="exaone",
            question="EXAONE API로 답변해줘",
            pathname="/home",
            workspace="홈 (Home)",
            evidence_context=None,
        )

        self.assertEqual(exaone.questions, ["EXAONE API로 답변해줘"])
        self.assertEqual(codex.questions, [])
        self.assertEqual([(step.stage, step.status) for step in guidance.fallback_steps], [("EXAONE API", "answered"), ("Codex SDK", "skipped")])

    def test_fallback_chain_uses_codex_after_complex_exaone_failure(self) -> None:
        codex = RecordingFallbackProvider()
        chain = FallbackChainCopilotProvider(
            exaone_simple=RecordingFallbackProvider(),
            exaone_complex=FailingFallbackProvider(),
            codex=codex,
        )

        chain.answer(
            question="SPC 이상 신호를 정리하는 Python 코드를 만들어줘",
            pathname="/spc",
            workspace="통계적 공정관리 (SPC)",
            evidence_context=None,
        )

        self.assertEqual(codex.questions, ["SPC 이상 신호를 정리하는 Python 코드를 만들어줘"])

    def test_fallback_chain_uses_codex_after_simple_exaone_failure(self) -> None:
        codex = RecordingFallbackProvider()
        chain = FallbackChainCopilotProvider(
            exaone_simple=FailingFallbackProvider(),
            exaone_complex=RecordingFallbackProvider(),
            codex=codex,
        )

        chain.answer(
            question="현장 작업표 열 이름을 설명해줘",
            pathname="/data",
            workspace="작업표 및 데이터 (Worksheet & Data)",
            evidence_context=None,
        )

        self.assertEqual(codex.questions, ["현장 작업표 열 이름을 설명해줘"])

    def test_malformed_exaone_response_falls_through_to_codex(self) -> None:
        codex_client = FakeCodexClient()
        chain = FallbackChainCopilotProvider(
            exaone_simple=ExaoneCopilotProvider(
                "test-key",
                model="k-exaone_v2.5",
                client=MalformedExaoneClient(),
            ),
            exaone_complex=None,
            codex=CodexSdkCopilotProvider(model="gpt-test", client=codex_client),
        )

        guidance = chain.answer(
            question="현장 작업표 열 이름을 설명해줘",
            pathname="/data",
            workspace="작업표 및 데이터 (Worksheet & Data)",
            evidence_context=None,
        )

        self.assertEqual(guidance.provider, "codex-sdk:gpt-test")
        self.assertEqual(len(codex_client.calls), 1)

    def test_incomplete_exaone_contract_falls_through_to_codex(self) -> None:
        codex_client = FakeCodexClient()
        chain = FallbackChainCopilotProvider(
            exaone_simple=ExaoneCopilotProvider(
                "test-key",
                model="k-exaone_v2.5",
                client=IncompleteGuidanceExaoneClient(),
            ),
            exaone_complex=None,
            codex=CodexSdkCopilotProvider(model="gpt-test", client=codex_client),
        )

        guidance = chain.answer(
            question="현장 작업표 열 이름을 설명해줘",
            pathname="/data",
            workspace="작업표 및 데이터 (Worksheet & Data)",
            evidence_context=None,
        )

        self.assertEqual(guidance.provider, "codex-sdk:gpt-test")
        self.assertEqual(len(codex_client.calls), 1)

    def test_malformed_codex_response_returns_manual_guidance(self) -> None:
        chain = FallbackChainCopilotProvider(
            exaone_simple=None,
            exaone_complex=None,
            codex=CodexSdkCopilotProvider(model="gpt-test", client=MalformedCodexClient()),
        )

        guidance = chain.answer(
            question="현장 작업표 열 이름을 설명해줘",
            pathname="/data",
            workspace="작업표 및 데이터 (Worksheet & Data)",
            evidence_context=None,
        )

        self.assertEqual(guidance.provider, "statpro-fallback-unavailable")

    def test_fallback_chain_requests_manual_input_after_all_models_fail(self) -> None:
        chain = FallbackChainCopilotProvider(
            exaone_simple=FailingFallbackProvider(),
            exaone_complex=FailingFallbackProvider(),
            codex=FailingFallbackProvider(),
        )

        guidance = chain.answer(
            question="현장 특수 문제를 도와줘",
            pathname="/home",
            workspace="홈 (Home)",
            evidence_context=None,
        )

        self.assertEqual(guidance.provider, "statpro-fallback-unavailable")
        self.assertEqual(guidance.guidance_mode, "manual_guidance")
        self.assertTrue(guidance.answer)
        self.assertEqual([(step.stage, step.status) for step in guidance.fallback_steps], [("EXAONE API", "failed"), ("Codex SDK", "failed")])

    def test_exaone_rate_limit_is_reported_without_a_false_connection_error(self) -> None:
        chain = FallbackChainCopilotProvider(
            exaone_simple=RateLimitedFallbackProvider(),
            exaone_complex=None,
            codex=None,
        )

        guidance = chain.answer(
            question="현장 특수 문제를 도와줘",
            pathname="/home",
            workspace="홈 (Home)",
            evidence_context=None,
        )

        self.assertIn("요청 한도", guidance.answer)
        self.assertIn("EXAONE: HTTP 429", guidance.limitations[1])

    def test_general_symptom_cause_action_request_uses_local_workflow(self) -> None:
        fallback = RecordingFallbackProvider()
        provider = RuleFirstCopilotProvider(LocalKnowledgeCopilotProvider(), fallback)

        guidance = provider.answer(
            question="현상, 원인, 대책 가이드 해줘",
            pathname="/analyses",
            workspace="분석 선택",
            evidence_context=None,
        )

        self.assertEqual(fallback.questions, [])
        self.assertEqual(guidance.guidance_mode, "rulebase")
        self.assertEqual(guidance.rule_id, "dmaic-symptom-cause-action-guide")
        self.assertIn("원인을 단정하지 않습니다", guidance.answer)
        self.assertIn("원인 검증", guidance.workflow_steps[3])
        self.assertEqual(guidance.action.href, "/home/dmaic/analyze/root-causes")

    def test_equipment_downtime_rule_leads_through_dmaic(self) -> None:
        fallback = RecordingFallbackProvider()
        provider = RuleFirstCopilotProvider(LocalKnowledgeCopilotProvider(), fallback)

        guidance = provider.answer(
            question="설비 비가동 시간이 높아 원인을 상세히 찾고 개선하고 싶어요",
            pathname="/home",
            workspace="홈 (Home)",
            evidence_context=None,
        )

        self.assertEqual(fallback.questions, [])
        self.assertEqual(guidance.rule_id, "dmaic-equipment-downtime")
        self.assertEqual(guidance.recommended_tool, "개선 프로젝트 (DMAIC)")
        self.assertEqual(guidance.action.href, "/home/dmaic/define")
        self.assertEqual(len(guidance.workflow_steps), 5)

    def test_downtime_metric_request_uses_rulebase_then_api_enrichment(self) -> None:
        fallback = RecordingFallbackProvider()
        provider = RuleFirstCopilotProvider(LocalKnowledgeCopilotProvider(), fallback)

        guidance = provider.answer(
            question="비가동의 시작·종료와 계획정지 제외 기준, 현재 비가동 시간·빈도·MTBF·MTTR 기준선, 관리지표 제안해줘",
            pathname="/home",
            workspace="홈 (Home)",
            evidence_context=None,
        )

        self.assertEqual(len(fallback.questions), 1)
        self.assertEqual(guidance.rule_id, "dmaic-equipment-downtime")
        self.assertIn("계획정지 제외", guidance.checklist[0])

    def test_symptom_cause_action_wording_answers_from_rulebase(self) -> None:
        fallback = RecordingFallbackProvider()
        provider = RuleFirstCopilotProvider(LocalKnowledgeCopilotProvider(), fallback)

        guidance = provider.answer(
            question="현상 및 원인 파악하여 개선 조치해줘",
            pathname="/analyses",
            workspace="분석 선택",
            evidence_context=None,
        )

        self.assertEqual(fallback.questions, [])
        self.assertEqual(guidance.rule_id, "dmaic-symptom-cause-action-guide")

    def test_catalog_rule_routes_p_chart_without_calling_llm(self) -> None:
        fallback = RecordingFallbackProvider()
        provider = RuleFirstCopilotProvider(LocalKnowledgeCopilotProvider(), fallback)

        guidance = provider.answer(
            question="표본 수가 다른 공정의 불량률을 p 관리도로 보고 싶어요",
            pathname="/spc",
            workspace="통계적 공정관리 (SPC)",
            evidence_context=None,
        )

        self.assertEqual(fallback.questions, [])
        self.assertEqual(guidance.rule_id, "spc-p-variable-sample")
        self.assertEqual(guidance.action.href, "/analyses/spc/attribute?chart=p")
        self.assertGreaterEqual(len(guidance.checklist), 2)
        self.assertGreaterEqual(len(guidance.workflow_steps), 4)

    def test_catalog_rule_routes_nested_gage_rr_without_calling_llm(self) -> None:
        fallback = RecordingFallbackProvider()
        provider = RuleFirstCopilotProvider(LocalKnowledgeCopilotProvider(), fallback)

        guidance = provider.answer(
            question="파괴검사에서 작업자별 다른 부품의 측정 변동을 중첩 Gage R&R으로 확인하고 싶어요",
            pathname="/home",
            workspace="홈 (Home)",
            evidence_context=None,
        )

        self.assertEqual(fallback.questions, [])
        self.assertEqual(guidance.guidance_mode, "rulebase")
        self.assertEqual(guidance.rule_id, "msa-nested-gage-rr")
        self.assertEqual(guidance.action.href, "/analyses/msa/gage-rr-nested")
        self.assertIn("부품", guidance.checklist[0])

    def test_catalog_rule_exposes_external_policy_dependency_for_fmea_approval(self) -> None:
        provider = LocalKnowledgeCopilotProvider()

        guidance = provider.answer(
            question="기업 승인에 IdP와 직무분리를 적용하려면 어떻게 하나요?",
            pathname="/fmea",
            workspace="고장 형태 및 영향 분석 (FMEA)",
            evidence_context=None,
        )

        self.assertEqual(guidance.rule_id, "fmea-enterprise-approval")
        self.assertIn("Entra OIDC claims", guidance.checklist[0])

    def test_business_case_seven_routes_high_ap_to_fmea_evidence(self) -> None:
        guidance = LocalKnowledgeCopilotProvider().answer(
            question="High AP 고장모드의 예방조치와 탐지조치 검증 근거를 기록하고 싶어요",
            pathname="/fmea",
            workspace="고장 형태 및 영향 분석 (FMEA)",
            evidence_context=None,
        )

        self.assertEqual(guidance.rule_id, "fmea-high-ap-evidence")
        self.assertIn("예방·탐지", guidance.checklist[1])

    def test_business_case_seven_routes_spc_rules_to_response_plan(self) -> None:
        guidance = LocalKnowledgeCopilotProvider().answer(
            question="SPC Western Electric 규칙 신호를 반응계획과 CAPA로 연결하고 싶어요",
            pathname="/spc",
            workspace="통계적 공정관리 (SPC)",
            evidence_context=None,
        )

        self.assertEqual(guidance.rule_id, "spc-rule-response-plan")
        self.assertIn("반응", guidance.workflow_steps[3])

    def test_out_of_scope_business_case_declares_boundary_and_suggests_tool(self) -> None:
        guidance = LocalKnowledgeCopilotProvider().answer(
            question="FDC와 APC R2R로 설비를 자동 제어하는 업무를 하고 싶어요",
            pathname="/home",
            workspace="홈 (Home)",
            evidence_context=None,
        )

        self.assertEqual(guidance.guidance_mode, "unmatched")
        self.assertIn("범위 밖", guidance.answer)
        self.assertIn("MES·FDC·APC/R2R", guidance.answer)
        self.assertEqual(guidance.recommended_tool, "MES·FDC·APC/R2R 플랫폼")
        self.assertIn("자동 실행하지 않습니다", guidance.limitations[2])

    def test_exaone_fallback_uses_structured_contract(self) -> None:
        client = FakeExaoneClient()
        provider = ExaoneCopilotProvider("test-key", client=client)

        guidance = provider.answer(
            question="사내 열처리 장비 코드 E97은 무엇인가요?",
            pathname="/home",
            workspace="홈 (Home)",
            evidence_context=None,
        )

        self.assertEqual(len(client.calls), 1)
        self.assertEqual(client.calls[0][0], "test-key")
        self.assertEqual(client.calls[0][2], "k-exaone_v2.5")
        self.assertEqual(client.calls[0][4], "low")
        self.assertIn("열처리 장비 코드 E97", client.calls[0][3])
        self.assertEqual(guidance.guidance_mode, "llm_fallback")
        self.assertEqual(guidance.checklist, ("설비 매뉴얼 확보",))
        self.assertEqual(guidance.workflow_steps, ("코드 발생 시점 확인",))

    def test_codex_sdk_fallback_uses_read_only_thread_and_the_guidance_contract(self) -> None:
        client = FakeCodexClient()
        provider = CodexSdkCopilotProvider(model="gpt-test", client=client)

        guidance = provider.answer(
            question="사내 장비의 새로운 코드가 무엇인가요?",
            pathname="/home",
            workspace="홈 (Home)",
            evidence_context=None,
        )

        self.assertEqual(client.calls[0][0], "gpt-test")
        self.assertEqual(client.calls[0][2], "read_only")
        self.assertIn("도구를 실행하거나 파일을 변경하지 마세요", client.calls[0][1])
        self.assertEqual(guidance.provider, "codex-sdk:gpt-test")
        self.assertEqual(guidance.guidance_mode, "llm_fallback")

    def test_local_openai_client_requests_a_single_non_streaming_json_response(self) -> None:
        with patch(
            "statpro.application.copilot.urllib.request.urlopen",
            return_value=FakeHttpResponse(),
        ) as urlopen:
            client = UrlLibExaoneChatCompletionClient(timeout_seconds=47)
            client.complete(
                api_key="secret",
                endpoint="https://api.exaone.ai/v1/chat/completions",
                model="k-exaone_v2.5",
                prompt="JSON only",
                reasoning_effort="high",
            )

        request = urlopen.call_args.args[0]
        body = json.loads(request.data.decode("utf-8"))
        self.assertFalse(body["stream"])
        self.assertEqual(request.full_url, "https://api.exaone.ai/v1/chat/completions")
        self.assertEqual(request.get_header("Authorization"), "Bearer secret")
        self.assertEqual(body["model"], "k-exaone_v2.5")
        self.assertEqual(body["reasoning_effort"], "high")
        self.assertEqual(body["max_tokens"], 4096)
        self.assertIn("Do not use Markdown fences", body["messages"][0]["content"])
        self.assertEqual(urlopen.call_args.kwargs["timeout"], 47)

    def test_disabled_codex_configuration_continues_to_manual_input_when_exaone_is_disabled(self) -> None:
        with patch.dict(
            os.environ,
            {
                "STATPRO_COPILOT_CODEX_ENABLED": "false",
                "STATPRO_COPILOT_EXAONE_ENABLED": "false",
                "EXAONE_API_KEY": "",
            },
            clear=True,
        ):
            guidance = build_default_copilot_provider().answer(
                question="사내 장비의 새로운 코드가 무엇인가요?",
                pathname="/home",
                workspace="홈 (Home)",
                evidence_context=None,
            )

        self.assertEqual(guidance.provider, "statpro-fallback-unavailable")
        self.assertEqual(guidance.guidance_mode, "manual_guidance")
        self.assertIn("EXAONE API 및 Codex SDK", guidance.limitations[1])
        self.assertIn("EXAONE: 미설정", guidance.limitations[1])
        self.assertIn("Codex SDK: 미설정", guidance.limitations[1])

    def test_runtime_status_reports_readiness_without_exposing_the_api_key(self) -> None:
        with patch.dict(
            os.environ,
            {
                "STATPRO_COPILOT_EXAONE_ENABLED": "true",
                "EXAONE_API_KEY": "must-not-appear",
                "STATPRO_COPILOT_EXAONE_MODEL": "k-exaone_v2.5",
                "STATPRO_COPILOT_CODEX_ENABLED": "true",
                "STATPRO_COPILOT_CODEX_MODEL": "gpt-test",
            },
            clear=True,
        ):
            status = copilot_runtime_status()

        self.assertTrue(status["rulebase"]["configured"])
        self.assertTrue(status["exaone"]["ready"])
        self.assertTrue(status["codex"]["ready"])
        self.assertFalse(status["exaone"]["live_verified"])
        self.assertFalse(status["codex"]["live_verified"])
        self.assertNotIn("must-not-appear", repr(status))


if __name__ == "__main__":
    unittest.main()
