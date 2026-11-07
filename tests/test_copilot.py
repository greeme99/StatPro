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
    GeminiCopilotProvider,
    LocalKnowledgeCopilotProvider,
    RuleFirstCopilotProvider,
)


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


class RuleFirstCopilotProviderTests(unittest.TestCase):
    def test_env_file_loads_only_copilot_settings_without_overriding_process(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            env_file = Path(directory) / ".env"
            env_file.write_text(
                "STATPRO_COPILOT_LLM_ENABLED=true\n"
                "GEMINI_API_KEY=local-secret\n"
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


if __name__ == "__main__":
    unittest.main()
