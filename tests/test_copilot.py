from __future__ import annotations

import os
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
    FallbackChainCopilotProvider,
    GeminiCopilotProvider,
    LocalLlmCopilotProvider,
    LocalKnowledgeCopilotProvider,
    RuleFirstCopilotProvider,
    build_default_copilot_provider,
)
from statpro.application.copilot_rules import COPILOT_RULE_CATALOG


class FakeGeminiClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, str]] = []

    def generate(self, *, api_key: str, model: str, prompt: str) -> dict[str, object]:
        self.calls.append((api_key, model, prompt))
        return {
            "candidates": [{
                "content": {
                    "parts": [{
                        "text": (
                            '{"answer":"열처리 코드 정의를 확인하세요.",'
                            '"recommended_tool":null,'
                            '"menu_path":["홈 (Home)"],'
                            '"checklist":["설비 매뉴얼 확보"],'
                            '"workflow_steps":["코드 발생 시점 확인"]}'
                        )
                    }]
                }
            }]
        }


class FakeLocalLlmClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, str]] = []

    def complete(self, *, endpoint: str, model: str, prompt: str) -> dict[str, object]:
        self.calls.append((endpoint, model, prompt))
        return {
            "choices": [{
                "message": {
                    "content": (
                        '{"answer":"로컬 모델 안내입니다.",'
                        '"recommended_tool":"분석 선택",'
                        '"menu_path":["홈 (Home)"],'
                        '"checklist":["입력 구조 확인"],'
                        '"workflow_steps":["질문 검토"]}'
                    )
                }
            }]
        }


class MalformedGeminiClient:
    def generate(self, *, api_key: str, model: str, prompt: str) -> dict[str, object]:
        return {"candidates": []}


class MalformedLocalLlmClient:
    def complete(self, *, endpoint: str, model: str, prompt: str) -> dict[str, object]:
        return {"choices": []}


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
            provider="gemini-2.5-flash",
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
                "STATPRO_COPILOT_LLM_ENABLED=true\n"
                "GEMINI_API_KEY=local-secret\n"
                "STATPRO_COPILOT_GEMINI_SIMPLE_MODEL=gemini-test-lite\n"
                "STATPRO_COPILOT_GEMINI_COMPLEX_MODEL=gemini-test-complex\n"
                "STATPRO_COPILOT_OLLAMA_ENABLED=true\n"
                "STATPRO_COPILOT_OLLAMA_URL=http://127.0.0.1:11434/v1/chat/completions\n"
                "STATPRO_COPILOT_OLLAMA_WORKFLOW_MODEL=workflow-model\n"
                "STATPRO_COPILOT_OLLAMA_CODE_MODEL=code-model\n"
                "STATPRO_COPILOT_LOCAL_LLM_ENABLED=true\n"
                "STATPRO_COPILOT_LOCAL_LLM_URL=http://127.0.0.1:11434/v1/chat/completions\n"
                "STATPRO_COPILOT_LOCAL_LLM_MODEL=quality-model\n"
                "UNRELATED_SECRET=must-not-load\n",
                encoding="utf-8",
            )
            with patch.dict(
                os.environ,
                {"GEMINI_API_KEY": "process-secret"},
                clear=True,
            ):
                load_copilot_env(env_file)

                self.assertEqual(os.environ["STATPRO_COPILOT_LLM_ENABLED"], "true")
                self.assertEqual(os.environ["GEMINI_API_KEY"], "process-secret")
                self.assertEqual(os.environ["STATPRO_COPILOT_GEMINI_SIMPLE_MODEL"], "gemini-test-lite")
                self.assertEqual(os.environ["STATPRO_COPILOT_OLLAMA_CODE_MODEL"], "code-model")
                self.assertEqual(os.environ["STATPRO_COPILOT_LOCAL_LLM_MODEL"], "quality-model")
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

    def test_unmatched_question_calls_gemini_once(self) -> None:
        fallback = RecordingFallbackProvider()
        provider = RuleFirstCopilotProvider(LocalKnowledgeCopilotProvider(), fallback)

        guidance = provider.answer(
            question="사내 신규 열처리 장비의 고유 진단 코드를 해석해줘",
            pathname="/home",
            workspace="홈 (Home)",
            evidence_context=None,
        )

        self.assertEqual(fallback.questions, ["사내 신규 열처리 장비의 고유 진단 코드를 해석해줘"])
        self.assertEqual(guidance.provider, "gemini-2.5-flash")
        self.assertEqual(guidance.guidance_mode, "llm_fallback")

    def test_fallback_chain_uses_light_gemini_for_a_simple_question(self) -> None:
        simple = RecordingFallbackProvider()
        complex_provider = RecordingFallbackProvider()
        chain = FallbackChainCopilotProvider(
            gemini_simple=simple,
            gemini_complex=complex_provider,
            ollama_workflow=RecordingFallbackProvider(),
            ollama_code=RecordingFallbackProvider(),
        )

        guidance = chain.answer(
            question="작업표 열 이름을 설명해줘",
            pathname="/data",
            workspace="작업표 및 데이터 (Worksheet & Data)",
            evidence_context=None,
        )

        self.assertEqual(simple.questions, ["작업표 열 이름을 설명해줘"])
        self.assertEqual(complex_provider.questions, [])
        self.assertEqual(guidance.guidance_mode, "llm_fallback")

    def test_fallback_chain_uses_complex_gemini_then_code_ollama(self) -> None:
        code_ollama = RecordingFallbackProvider()
        chain = FallbackChainCopilotProvider(
            gemini_simple=RecordingFallbackProvider(),
            gemini_complex=FailingFallbackProvider(),
            ollama_workflow=RecordingFallbackProvider(),
            ollama_code=code_ollama,
        )

        chain.answer(
            question="SPC 이상 신호를 정리하는 Python 코드를 만들어줘",
            pathname="/spc",
            workspace="통계적 공정관리 (SPC)",
            evidence_context=None,
        )

        self.assertEqual(code_ollama.questions, ["SPC 이상 신호를 정리하는 Python 코드를 만들어줘"])

    def test_fallback_chain_uses_workflow_ollama_after_simple_gemini_failure(self) -> None:
        workflow_ollama = RecordingFallbackProvider()
        chain = FallbackChainCopilotProvider(
            gemini_simple=FailingFallbackProvider(),
            gemini_complex=RecordingFallbackProvider(),
            ollama_workflow=workflow_ollama,
            ollama_code=RecordingFallbackProvider(),
        )

        chain.answer(
            question="현장 작업표 열 이름을 설명해줘",
            pathname="/data",
            workspace="작업표 및 데이터 (Worksheet & Data)",
            evidence_context=None,
        )

        self.assertEqual(workflow_ollama.questions, ["현장 작업표 열 이름을 설명해줘"])

    def test_malformed_gemini_response_falls_through_to_workflow_ollama(self) -> None:
        local_client = FakeLocalLlmClient()
        chain = FallbackChainCopilotProvider(
            gemini_simple=GeminiCopilotProvider(
                "test-key",
                model="gemini-test-lite",
                client=MalformedGeminiClient(),
            ),
            gemini_complex=None,
            ollama_workflow=LocalLlmCopilotProvider(
                "http://127.0.0.1:11434/v1/chat/completions",
                "qwen3:4b-q4_K_M",
                client=local_client,
            ),
            ollama_code=None,
        )

        guidance = chain.answer(
            question="현장 작업표 열 이름을 설명해줘",
            pathname="/data",
            workspace="작업표 및 데이터 (Worksheet & Data)",
            evidence_context=None,
        )

        self.assertEqual(guidance.provider, "local:qwen3:4b-q4_K_M")
        self.assertEqual(len(local_client.calls), 1)

    def test_malformed_local_response_returns_manual_guidance(self) -> None:
        chain = FallbackChainCopilotProvider(
            gemini_simple=None,
            gemini_complex=None,
            ollama_workflow=LocalLlmCopilotProvider(
                "http://127.0.0.1:11434/v1/chat/completions",
                "qwen3:4b-q4_K_M",
                client=MalformedLocalLlmClient(),
            ),
            ollama_code=None,
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
            gemini_simple=FailingFallbackProvider(),
            gemini_complex=FailingFallbackProvider(),
            ollama_workflow=FailingFallbackProvider(),
            ollama_code=FailingFallbackProvider(),
        )

        guidance = chain.answer(
            question="현장 특수 문제를 도와줘",
            pathname="/home",
            workspace="홈 (Home)",
            evidence_context=None,
        )

        self.assertEqual(guidance.provider, "statpro-fallback-unavailable")
        self.assertEqual(guidance.guidance_mode, "unmatched")
        self.assertTrue(guidance.answer)

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

    def test_gemini_fallback_uses_structured_contract(self) -> None:
        client = FakeGeminiClient()
        provider = GeminiCopilotProvider("test-key", client=client)

        guidance = provider.answer(
            question="사내 열처리 장비 코드 E97은 무엇인가요?",
            pathname="/home",
            workspace="홈 (Home)",
            evidence_context=None,
        )

        self.assertEqual(len(client.calls), 1)
        self.assertEqual(client.calls[0][0:2], ("test-key", "gemini-2.5-flash"))
        self.assertIn("열처리 장비 코드 E97", client.calls[0][2])
        self.assertEqual(guidance.guidance_mode, "llm_fallback")
        self.assertEqual(guidance.checklist, ("설비 매뉴얼 확보",))
        self.assertEqual(guidance.workflow_steps, ("코드 발생 시점 확인",))

    def test_local_llm_fallback_requires_loopback_and_returns_the_same_contract(self) -> None:
        client = FakeLocalLlmClient()
        provider = LocalLlmCopilotProvider(
            "http://127.0.0.1:11434/v1/chat/completions",
            "quality-model",
            client=client,
        )

        guidance = provider.answer(
            question="사내 장비의 새로운 코드가 무엇인가요?",
            pathname="/home",
            workspace="홈 (Home)",
            evidence_context=None,
        )

        self.assertEqual(client.calls[0][0:2], ("http://127.0.0.1:11434/v1/chat/completions", "quality-model"))
        self.assertIn("JSON만 반환", client.calls[0][2])
        self.assertEqual(guidance.provider, "local:quality-model")
        self.assertEqual(guidance.guidance_mode, "llm_fallback")
        self.assertIn("loopback", guidance.limitations[0])
        with self.assertRaisesRegex(ValueError, "loopback"):
            LocalLlmCopilotProvider("https://example.invalid/v1/chat/completions", "quality-model")

    def test_invalid_ollama_configuration_continues_to_manual_input_when_gemini_is_disabled(self) -> None:
        with patch.dict(
            os.environ,
            {
                "STATPRO_COPILOT_LOCAL_LLM_ENABLED": "true",
                "STATPRO_COPILOT_LOCAL_LLM_URL": "https://example.invalid/v1/chat/completions",
                "STATPRO_COPILOT_LOCAL_LLM_MODEL": "quality-model",
                "STATPRO_COPILOT_LLM_ENABLED": "false",
                "GEMINI_API_KEY": "",
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
        self.assertEqual(guidance.guidance_mode, "unmatched")
        self.assertIn("Gemini 및 로컬 Ollama", guidance.limitations[1])


if __name__ == "__main__":
    unittest.main()
