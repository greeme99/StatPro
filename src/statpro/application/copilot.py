"""Evidence-aware guidance boundary for the StatPro Copilot.

The default provider is deterministic and local-only.  An approved enterprise
model can implement :class:`CopilotProvider` later without changing the API or
the browser contract.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from collections.abc import Mapping
from dataclasses import dataclass, replace
from typing import Any, Protocol

from statpro.application.copilot_rules import CopilotRule, match_catalog_rule


@dataclass(frozen=True)
class CopilotSource:
    title: str
    reference: str
    evidence_kind: str = "product_documentation"


@dataclass(frozen=True)
class CopilotAction:
    label: str
    href: str


@dataclass(frozen=True)
class CopilotGuidance:
    answer: str
    provider: str
    sources: tuple[CopilotSource, ...]
    limitations: tuple[str, ...]
    action: CopilotAction | None = None
    guidance_mode: str = "rulebase"
    rule_id: str | None = None
    recommended_tool: str | None = None
    menu_path: tuple[str, ...] = ()
    checklist: tuple[str, ...] = ()
    workflow_steps: tuple[str, ...] = ()


class CopilotProvider(Protocol):
    """Application boundary for a local or explicitly approved model provider."""

    def answer(
        self,
        *,
        question: str,
        pathname: str,
        workspace: str,
        evidence_context: str | None,
    ) -> CopilotGuidance: ...


class GeminiContentClient(Protocol):
    def generate(
        self,
        *,
        api_key: str,
        model: str,
        prompt: str,
    ) -> Mapping[str, Any]: ...


_SPC_SOURCE = CopilotSource(
    "SPC 통계 근거 및 관리도 계약",
    "docs/evidence/2026-11-01-spc-seven-tools-workspace.md",
)
_DOE_SOURCE = CopilotSource(
    "DOE 표준 보고서 및 내보내기",
    "docs/evidence/2026-10-28-doe-standard-report-export.md",
)
_FMEA_SOURCE = CopilotSource(
    "PFMEA 7단계 업무 흐름",
    "docs/evidence/2026-10-25-fmea-seven-step-workflow.md",
)
_DMAIC_SOURCE = CopilotSource(
    "DMAIC 프로젝트 UI 구조",
    "docs/evidence/2026-10-29-dmaic-ui-structure.md",
)
_SELECTION_SOURCE = CopilotSource(
    "분석 선택 도우미 규칙",
    "docs/evidence/2026-11-07-analysis-selection-assistant.md",
)
_SCOPE_SOURCE = CopilotSource(
    "StatPro 지원 범위 및 후속 연계 항목",
    "docs/10.StatPro_AI_Copilot_Rule_Catalog.md",
)

_OUT_OF_SCOPE_GUIDANCE: tuple[tuple[tuple[str, ...], str, str], ...] = (
    (("ppap", "8d", "capa"), "고객 품질·시정조치 관리", "고객 포털·QMS·CAPA/8D 시스템"),
    (("fdc", "apc", "r2r"), "설비 데이터 수집·제어", "MES·FDC·APC/R2R 플랫폼"),
    (("mes", "erp", "생산실행"), "생산·자원 관리", "MES·ERP"),
    (("dmadv", "dfss"), "신제품 설계 품질", "DFSS/DMADV 전용 설계·품질 시스템"),
    (("임상", "clinical", "의료통계"), "임상·의료 연구 통계", "임상시험·의료통계 전용 도구"),
)


def _catalog_source(rule: CopilotRule) -> CopilotSource:
    return CopilotSource(
        title=f"AI Copilot 현장 Rule: {rule.recommended_tool}",
        reference=rule.source_reference,
    )


class LocalKnowledgeCopilotProvider:
    """Deterministic guidance over reviewed StatPro product knowledge."""

    provider_name = "statpro-rulebase-v2"

    def answer(
        self,
        *,
        question: str,
        pathname: str,
        workspace: str,
        evidence_context: str | None,
    ) -> CopilotGuidance:
        normalized = question.casefold()
        evidence_prefix = f"현재 근거는 {evidence_context}입니다. " if evidence_context else ""
        limitations = (
            "검토용 안내이며 분석 설정이나 저장 문서를 자동으로 변경하지 않습니다.",
            "현재 응답은 검토된 로컬 지식 규칙을 사용하며 외부 AI 모델로 전송되지 않습니다.",
        )

        yield_terms = any(token in normalized for token in ("수율", "yield", "y값", "반응값"))
        factor_terms = any(
            token in normalized
            for token in ("온도", "압력", "시간", "설정값", "변수", "인자", "요인", "xs")
        )
        experiment_terms = any(
            token in normalized for token in ("실험", "최적", "높이", "개선", "조건")
        )
        if yield_terms and factor_terms and experiment_terms:
            return CopilotGuidance(
                answer=(
                    evidence_prefix
                    + "수율(Y)에 영향을 주는 온도·압력·시간 등의 인자(Xs)를 동시에 검증하고 최적 조건을 찾는 문제이므로 실험계획법(DOE)이 적합합니다. "
                    "한 번에 한 인자씩 바꾸기보다 설계된 실행표로 주효과와 상호작용을 추정하고, 최적 조건은 확인 실험으로 검증하세요."
                ),
                provider=self.provider_name,
                sources=(_DOE_SOURCE,),
                limitations=limitations,
                action=CopilotAction("DOE 절차 시작", "/doe"),
                rule_id="doe-yield-optimization",
                recommended_tool="실험계획법 (DOE)",
                menu_path=("홈 (Home)", "실험계획법 (DOE)", "설계 및 생성"),
                checklist=(
                    "반응값(Y), 현재 수율과 목표 수율을 수치로 정의합니다.",
                    "온도·압력·시간 등 제어 가능한 인자(Xs)와 안전 범위를 확인합니다.",
                    "측정시스템과 원자재·설비·작업자 같은 잡음 요인을 점검합니다.",
                    "반복, 중심점, 블록과 확인 실험에 사용할 자원을 확보합니다.",
                ),
                workflow_steps=(
                    "목표와 반응(Y)을 정의합니다.",
                    "인자(Xs), 수준, 제약조건과 잡음 요인을 정의합니다.",
                    "목적에 맞는 요인설계 또는 반응표면 설계를 생성합니다.",
                    "무작위 실행 순서를 지키며 데이터를 수집합니다.",
                    "모형·잔차·상호작용을 검토하고 최적 조건을 확인 실험으로 검증합니다.",
                ),
            )

        equipment_terms = any(token in normalized for token in ("설비", "장비", "기계"))
        downtime_terms = any(token in normalized for token in ("비가동", "다운타임", "정지", "고장시간"))
        investigation_terms = any(token in normalized for token in ("원인", "개선", "높", "줄", "감소"))
        if equipment_terms and downtime_terms and investigation_terms:
            return CopilotGuidance(
                answer=(
                    evidence_prefix
                    + "설비 비가동은 고장 유형, 시간, 운전 조건, 정비 이력과 측정 기준을 함께 다뤄야 하므로 DMAIC 개선 프로젝트로 구조화하는 것이 적합합니다. "
                    "정의 단계에서 손실 범위를 고정하고, 측정 단계에서 비가동 기준과 기준선을 확보한 뒤 데이터로 원인을 검증하세요."
                ),
                provider=self.provider_name,
                sources=(_DMAIC_SOURCE, _SPC_SOURCE),
                limitations=limitations,
                action=CopilotAction("DMAIC 정의 단계 시작", "/home/dmaic/define"),
                rule_id="dmaic-equipment-downtime",
                recommended_tool="개선 프로젝트 (DMAIC)",
                menu_path=("홈 (Home)", "개선 프로젝트 (DMAIC)", "정의 (Define)"),
                checklist=(
                    "비가동의 시작·종료와 계획정지 제외 기준을 합의합니다.",
                    "설비, 고장코드, 제품, 교대, 작업자, 정비 이력 데이터를 확보합니다.",
                    "현재 비가동 시간·빈도·MTBF·MTTR 기준선을 확인합니다.",
                    "개선 목표, 범위, 책임자와 관리 지표를 지정합니다.",
                ),
                workflow_steps=(
                    "정의(Define): 문제, 손실, 고객 영향과 범위를 명확히 합니다.",
                    "측정(Measure): 비가동 기준을 통일하고 기준선과 데이터 신뢰성을 확인합니다.",
                    "분석(Analyze): Pareto·Fishbone·5 Whys와 통계 분석으로 원인을 검증합니다.",
                    "개선(Improve): 대책을 파일럿하고 효과와 부작용을 검증합니다.",
                    "관리(Control): SPC·관리계획·FMEA와 책임자를 연결해 효과를 유지합니다.",
                ),
            )

        if any(token in normalized for token in ("nelson", "넬슨")) and (
            any(token in normalized for token in ("xbar-r", "xbar r", "x̄-r", "소집단"))
            or pathname.endswith("/xbar-r")
        ):
            return CopilotGuidance(
                answer=(
                    evidence_prefix
                    + "Nelson 규칙은 3σ 한계 밖 점뿐 아니라 연속, 추세, 교대와 중심선 주변의 비무작위 패턴을 검토합니다. "
                    "Xbar-R에서는 Xbar 규칙 1–8과 R 규칙 1–4를 평가하므로 경보가 늘 수 있습니다. "
                    "아래 링크는 검토용 초안만 열며, 분석 설정은 작업공간에서 사용자가 확인해야 적용됩니다."
                ),
                provider=self.provider_name,
                sources=(_SPC_SOURCE,),
                limitations=limitations,
                action=CopilotAction(
                    "Nelson 규칙 초안 검토",
                    "/analyses/spc/xbar-r?draft=nelson",
                ),
                rule_id="spc-xbar-r-nelson-draft",
                recommended_tool="Xbar-R 관리도",
                menu_path=("홈 (Home)", "통계적 공정관리 (SPC)", "Xbar-R 관리도"),
                checklist=(
                    "합리적 소집단과 시간 순서를 확인합니다.",
                    "Nelson 규칙 적용으로 늘어날 경보를 검토할 책임자를 정합니다.",
                    "기존 실행을 보존하고 새 실행으로 비교합니다.",
                ),
                workflow_steps=("설정 초안 검토", "규칙 적용", "분석 실행", "신호 원인 조사"),
            )

        if any(token in normalized for token in ("xbar-r", "xbar r", "x̄-r", "소집단")):
            return CopilotGuidance(
                answer=(
                    evidence_prefix
                    + "Xbar-R 관리도는 연속형 측정값을 합리적 소집단으로 묶어 평균과 범위를 함께 감시할 때 사용합니다. "
                    "먼저 측정 순서와 소집단 기준을 고정하고, Phase 1에서 특수원인을 검토한 뒤 안정된 기준만 Phase 2 한계로 사용하세요. "
                    "부분군 크기·관리한계·검출 규칙을 바꿀 때에는 새 분석 실행으로 남겨 이전 결과와 구분해야 합니다."
                ),
                provider=self.provider_name,
                sources=(_SPC_SOURCE,),
                limitations=limitations,
                action=CopilotAction("Xbar-R 작업공간 열기", "/analyses/spc/xbar-r"),
                rule_id="spc-xbar-r-selection",
                recommended_tool="Xbar-R 관리도",
                menu_path=("홈 (Home)", "통계적 공정관리 (SPC)", "Xbar-R 관리도"),
            )

        catalog_rule = match_catalog_rule(question)
        if catalog_rule is not None:
            return CopilotGuidance(
                answer=(
                    evidence_prefix
                    + f"{catalog_rule.situation} 적합한 작업공간은 {catalog_rule.recommended_tool}입니다. "
                    "아래 점검표를 확인한 뒤 단계별 업무 절차에 따라 분석을 진행하세요."
                ),
                provider=self.provider_name,
                sources=(_catalog_source(catalog_rule),),
                limitations=limitations,
                action=CopilotAction(
                    catalog_rule.action_label,
                    catalog_rule.action_href,
                ),
                rule_id=catalog_rule.rule_id,
                recommended_tool=catalog_rule.recommended_tool,
                menu_path=catalog_rule.menu_path,
                checklist=catalog_rule.checklist,
                workflow_steps=catalog_rule.workflow_steps,
            )

        if any(token in normalized for token in ("관리한계", "ucl", "lcl", "이상 신호", "관리도")):
            return CopilotGuidance(
                answer=(
                    evidence_prefix
                    + "관리한계는 공정의 자연 변동을 판별하는 통계적 기준이며 규격한계와 다릅니다. "
                    "한계 밖 점이나 런 규칙 신호가 있으면 데이터를 삭제하기보다 시간, 설비, 자재, 작업자, 측정계통의 특수원인을 조사하고 조치 근거를 실행 기록에 연결하세요."
                ),
                provider=self.provider_name,
                sources=(_SPC_SOURCE,),
                limitations=limitations,
                action=CopilotAction("SPC 작업공간 열기", "/spc"),
                rule_id="spc-control-limit-guidance",
            )

        if any(token in normalized for token in ("doe", "실험계획", "블록", "중심점", "반복")):
            return CopilotGuidance(
                answer=(
                    evidence_prefix
                    + "DOE에서는 목적을 선별, 모형화, 최적화 중 하나로 먼저 정하고 요인 범위와 반응을 정의합니다. "
                    "반복은 순수오차 추정, 중심점은 곡률 확인, 블록은 통제하기 어려운 배치·일자 변동 분리에 사용합니다. "
                    "설계표를 확정한 뒤 무작위 실행 순서를 보존하고 결과 보고서에 설계·모형·진단·최적화 근거를 함께 남기세요."
                ),
                provider=self.provider_name,
                sources=(_DOE_SOURCE,),
                limitations=limitations,
                action=CopilotAction("DOE 작업공간 열기", "/doe"),
                rule_id="doe-general-guidance",
            )

        if any(token in normalized for token in ("fmea", "pfmea", "고장", "조치 우선", "관리계획")):
            return CopilotGuidance(
                answer=(
                    evidence_prefix
                    + "PFMEA는 기획, 구조 분석, 기능 분석, 고장 분석, 위험 분석, 최적화, 결과 문서화의 7단계로 진행합니다. "
                    "공정 단계와 특성 ID를 유지하고 고장 원인별 예방·검출 관리를 연결한 뒤, 조치 우선순위 정책과 승인 시점의 SPC·MSA 실행 근거를 재검증하세요."
                ),
                provider=self.provider_name,
                sources=(_FMEA_SOURCE,),
                limitations=limitations,
                action=CopilotAction("FMEA 작업공간 열기", "/fmea"),
                rule_id="fmea-general-guidance",
            )

        if any(token in normalized for token in ("dmaic", "개선 프로젝트", "현재 단계", "다음 절차")):
            return CopilotGuidance(
                answer=(
                    evidence_prefix
                    + "DMAIC는 정의에서 문제와 범위, 측정에서 기준선과 측정 신뢰성, 분석에서 검증된 원인, 개선에서 실험·파일럿 결과, 관리에서 SPC·관리계획 인계를 확정합니다. "
                    "각 단계는 다음 단계의 입력이 되는 저장 산출물과 분석 실행 ID를 남긴 뒤 넘어가는 것이 안전합니다."
                ),
                provider=self.provider_name,
                sources=(_DMAIC_SOURCE,),
                limitations=limitations,
                action=CopilotAction("DMAIC 작업공간 열기", "/home/dmaic"),
                rule_id="dmaic-general-guidance",
            )

        if any(token in normalized for token in ("추천", "어떤 분석", "무엇을 사용", "차이")):
            return CopilotGuidance(
                answer=(
                    "분석 목적, 결과 변수의 데이터형, 수집 구조를 순서대로 확인해야 방법을 좁힐 수 있습니다. "
                    "분석 선택 화면에서 공정 감시, 실험 최적화, 위험 분석, 개선 프로젝트 중 목적을 선택하면 필요한 입력과 사전 점검을 함께 안내합니다."
                ),
                provider=self.provider_name,
                sources=(_SELECTION_SOURCE,),
                limitations=limitations,
                action=CopilotAction("분석 선택 시작", "/analyses"),
                rule_id="analysis-selection-guidance",
            )

        for terms, capability, suggested_tool in _OUT_OF_SCOPE_GUIDANCE:
            if any(term in normalized for term in terms):
                return CopilotGuidance(
                    answer=(
                        f"요청하신 {capability}은 현재 StatPro의 제공 기능 및 확정된 Rulebase 범위 밖입니다. "
                        f"StatPro의 DOE·SPC·FMEA·DMAIC로 대신 처리한다고 단정하지 않으며, "
                        f"적합한 연계 도구는 {suggested_tool}입니다. "
                        "필요하면 해당 시스템의 결과를 StatPro의 분석 입력·근거로 가져오는 연계 요구사항을 별도로 정의하세요."
                    ),
                    provider=self.provider_name,
                    sources=(_SCOPE_SOURCE,),
                    limitations=limitations + (
                        "범위 밖 기능은 StatPro에서 계산·승인·자동 실행하지 않습니다.",
                        "연계 도구의 계약·권한·데이터 형식은 별도 확인이 필요합니다.",
                    ),
                    action=CopilotAction("지원 분석 범위 확인", "/analyses"),
                    guidance_mode="unmatched",
                    recommended_tool=suggested_tool,
                )

        return CopilotGuidance(
            answer=(
                f"{workspace}에서 질문을 확인했습니다. 현재 로컬 지식 범위에서는 단정적인 답을 만들 근거가 충분하지 않습니다. "
                "분석 목적, 데이터형, 수집 구조와 확인하려는 설정값을 함께 적거나 분석 선택 도우미에서 절차를 시작해 주세요."
            ),
            provider=self.provider_name,
            sources=(_SELECTION_SOURCE,),
            limitations=limitations + ("질문에 직접 대응하는 검토된 지식 규칙을 찾지 못했습니다.",),
            action=CopilotAction("분석 선택 시작", "/analyses"),
            guidance_mode="unmatched",
        )


class RuleFirstCopilotProvider:
    """Use reviewed rules first and call the model only for an unmatched question."""

    def __init__(self, rule_provider: CopilotProvider, fallback_provider: CopilotProvider | None) -> None:
        self._rule_provider = rule_provider
        self._fallback_provider = fallback_provider

    def answer(
        self,
        *,
        question: str,
        pathname: str,
        workspace: str,
        evidence_context: str | None,
    ) -> CopilotGuidance:
        rule_guidance = self._rule_provider.answer(
            question=question,
            pathname=pathname,
            workspace=workspace,
            evidence_context=evidence_context,
        )
        if rule_guidance.rule_id is not None or self._fallback_provider is None:
            return rule_guidance
        try:
            return self._fallback_provider.answer(
                question=question,
                pathname=pathname,
                workspace=workspace,
                evidence_context=evidence_context,
            )
        except (OSError, ValueError, KeyError, TypeError):
            return replace(
                rule_guidance,
                limitations=rule_guidance.limitations
                + ("외부 생성형 AI를 사용할 수 없어 로컬 안내만 제공합니다.",),
            )


class UrlLibGeminiContentClient:
    """Small dependency-free client for the Gemini generateContent endpoint."""

    def generate(
        self,
        *,
        api_key: str,
        model: str,
        prompt: str,
    ) -> Mapping[str, Any]:
        endpoint = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{model}:generateContent"
        )
        schema = {
            "type": "object",
            "properties": {
                "answer": {"type": "string"},
                "recommended_tool": {"type": ["string", "null"]},
                "menu_path": {"type": "array", "items": {"type": "string"}},
                "checklist": {"type": "array", "items": {"type": "string"}},
                "workflow_steps": {"type": "array", "items": {"type": "string"}},
            },
            "required": [
                "answer",
                "recommended_tool",
                "menu_path",
                "checklist",
                "workflow_steps",
            ],
            "additionalProperties": False,
        }
        body = json.dumps(
            {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0.2,
                    "responseMimeType": "application/json",
                    "responseJsonSchema": schema,
                },
            }
        ).encode("utf-8")
        request = urllib.request.Request(
            endpoint,
            data=body,
            headers={"Content-Type": "application/json", "x-goog-api-key": api_key},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            raise OSError(f"Gemini request failed with HTTP {error.code}") from error


class GeminiCopilotProvider:
    """Constrained Gemini 2.5 Flash fallback for questions outside the rulebase."""

    def __init__(
        self,
        api_key: str,
        *,
        model: str = "gemini-2.5-flash",
        client: GeminiContentClient | None = None,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._client = client or UrlLibGeminiContentClient()

    def answer(
        self,
        *,
        question: str,
        pathname: str,
        workspace: str,
        evidence_context: str | None,
    ) -> CopilotGuidance:
        prompt = (
            "당신은 제조·품질 통계 소프트웨어 StatPro의 한국어 업무 가이드입니다. "
            "검증되지 않은 수치나 기능을 만들지 말고, 초보자가 검토 후 실행할 수 있도록 설명하세요. "
            "분석 설정을 자동 변경했다고 말하지 마세요.\n"
            f"현재 작업공간: {workspace}\n현재 경로: {pathname}\n"
            f"사용자 질문: {question}\n"
            f"사용자가 선택한 근거 문맥: {evidence_context or '없음'}"
        )
        raw = self._client.generate(
            api_key=self._api_key,
            model=self._model,
            prompt=prompt,
        )
        candidates = raw["candidates"]
        text = candidates[0]["content"]["parts"][0]["text"]
        payload = json.loads(text)
        answer = payload["answer"]
        menu_path = payload["menu_path"]
        checklist = payload["checklist"]
        workflow_steps = payload["workflow_steps"]
        if not isinstance(answer, str) or not answer.strip():
            raise ValueError("Gemini returned an empty answer")
        if not all(isinstance(values, list) for values in (menu_path, checklist, workflow_steps)):
            raise ValueError("Gemini returned an invalid guidance contract")
        if not all(
            isinstance(item, str)
            for values in (menu_path, checklist, workflow_steps)
            for item in values
        ):
            raise ValueError("Gemini returned a non-string guidance item")
        recommended_tool = payload["recommended_tool"]
        if recommended_tool is not None and not isinstance(recommended_tool, str):
            raise ValueError("Gemini returned an invalid recommended tool")
        return CopilotGuidance(
            answer=answer.strip(),
            provider=self._model,
            sources=(CopilotSource("사용자 질문과 선택 문맥", "copilot://question", "user_context"),),
            limitations=(
                "생성형 AI 보완 응답이며 정확성과 현장 적용 가능성을 사용자가 검토해야 합니다.",
                "분석 설정이나 저장 문서를 자동으로 변경하지 않습니다.",
            ),
            guidance_mode="llm_fallback",
            recommended_tool=recommended_tool,
            menu_path=tuple(menu_path[:8]),
            checklist=tuple(checklist[:12]),
            workflow_steps=tuple(workflow_steps[:12]),
        )


def build_default_copilot_provider() -> CopilotProvider:
    """Build the opt-in Rulebase → Gemini provider chain without exposing credentials."""

    rule_provider = LocalKnowledgeCopilotProvider()
    enabled = os.getenv("STATPRO_COPILOT_LLM_ENABLED", "").casefold() == "true"
    api_key = os.getenv("GEMINI_API_KEY", "")
    fallback = GeminiCopilotProvider(api_key) if enabled and api_key else None
    return RuleFirstCopilotProvider(rule_provider, fallback)
