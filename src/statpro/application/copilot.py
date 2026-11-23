"""Evidence-aware guidance boundary for the StatPro Copilot.

The default provider is deterministic and local-only.  An approved enterprise
model can implement :class:`CopilotProvider` later without changing the API or
the browser contract.
"""

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from dataclasses import dataclass, replace
from typing import Any, Protocol

from statpro.application.copilot_rules import (
    COPILOT_RULE_CATALOG,
    CopilotRule,
    match_catalog_rule,
)


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
class CopilotFallbackStep:
    """A non-secret outcome for one fixed Copilot fallback stage."""

    stage: str
    status: str
    detail: str


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
    fallback_steps: tuple[CopilotFallbackStep, ...] = ()


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


class CodexSdkClient(Protocol):
    """Minimal boundary over the official local Codex Python SDK."""

    def run_read_only(self, *, model: str | None, prompt: str) -> str: ...


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
_ASSISTANT_REFERENCE = (
    "StatPro 제공 기능: DOE(요인·반응표면·최적화), SPC(Xbar-R/S·I-MR·p/np/c/u·EWMA·CUSUM·G/T·능력), "
    "MSA(Gage R&R·편의/선형성·속성 일치도), FMEA·DMAIC, 회귀(OLS·다항·교호작용·로지스틱·단계선택·검증·Best Subsets). "
    "Laney·다변량 SPC, 혼합물·Taguchi·D-optimal DOE는 현재 제공하지 않는다. "
    "메뉴 경로·입력 점검·확인실험을 안내하되 실행 또는 승인 완료를 주장하지 않는다."
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

        downtime_terms = any(token in normalized for token in ("비가동", "다운타임", "정지", "고장시간"))
        investigation_terms = any(token in normalized for token in ("원인", "개선", "높", "줄", "감소"))
        downtime_measure_terms = any(token in normalized for token in ("mtbf", "mttr", "기준선", "관리지표", "시작", "종료", "빈도"))
        if downtime_terms and (investigation_terms or downtime_measure_terms):
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

        coating_terms = any(token in normalized for token in ("코팅", "coating"))
        discoloration_terms = any(token in normalized for token in ("착색", "변색", "황변", "색상"))
        optimization_terms = any(token in normalized for token in ("최적", "조건", "방지", "개선"))
        if coating_terms and discoloration_terms and optimization_terms:
            return CopilotGuidance(
                answer=(
                    "착색 방지 코팅 조건은 색차(ΔE), 황변지수, 광택·밀착력 같은 반응값을 먼저 정한 뒤 DOE로 최적화하세요. "
                    "코팅 두께·조성·경화 온도·시간·UV 에너지·소재 전처리를 인자로 두고, 가속 내후성 시험으로 후보 조건을 확인합니다."
                ),
                provider=self.provider_name,
                sources=(_DOE_SOURCE,),
                limitations=limitations + ("소재·코팅계·시험 규격이 없어 최적 조건값은 제시하지 않습니다.",),
                action=CopilotAction("DOE 절차 시작", "/doe"),
                rule_id="doe-coating-discoloration-optimization",
                recommended_tool="실험계획법 (DOE)",
                menu_path=("홈 (Home)", "실험계획법 (DOE)", "설계 및 생성"),
                checklist=(
                    "기준 색상과 허용 ΔE·광택·밀착력 기준을 정합니다.",
                    "코팅 조성·두께·경화 조건과 소재 전처리의 안전 범위를 확인합니다.",
                    "가속 내후성·열·UV 시험 조건과 측정 방법을 고정합니다.",
                    "반복·무작위화·소재 lot을 블록으로 둘지 결정합니다.",
                ),
                workflow_steps=(
                    "착색 방지 목표와 반응값 정의",
                    "코팅·경화·전처리 인자와 수준 정의",
                    "스크리닝 DOE로 영향 인자 선별",
                    "반응표면 DOE로 후보 조건 최적화",
                    "가속 시험·실사용 조건에서 확인 후 관리 기준 설정",
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
                checklist=(
                    "합리적 소집단과 실제 시간 순서를 고정합니다.",
                    "부분군 크기가 일정한지와 측정시스템의 적합성을 확인합니다.",
                    "R 관리도의 산포 안정성을 먼저 검토합니다.",
                ),
                workflow_steps=(
                    "부분군·기준 구간을 정의합니다.",
                    "Xbar-R 입력과 검증을 실행합니다.",
                    "R 관리도의 산포를 먼저 검토합니다.",
                    "Xbar 신호와 반응계획을 검토합니다.",
                    "안정된 기준을 다음 실행의 근거로 보존합니다.",
                ),
            )

        if all(any(term in normalized for term in group) for group in (("현상", "증상"), ("원인",), ("대책", "조치"))):
            return CopilotGuidance(
                answer=(
                    "현상·원인·대책을 순서대로 정리할 수 있습니다. 먼저 무엇이 언제부터 얼마나 달라졌는지, "
                    "제품·설비·공정과 영향 범위를 알려주세요. 원인은 현재 가설과 확인된 근거를 구분하고, "
                    "대책은 임시 조치와 검증할 개선안을 나눠 제안하겠습니다. 구체 현상이나 데이터가 없으므로 원인을 단정하지 않습니다."
                ),
                provider=self.provider_name,
                sources=(_DMAIC_SOURCE, _SELECTION_SOURCE),
                limitations=limitations + ("구체적인 현상·데이터가 없어 원인과 효과는 아직 검증되지 않았습니다.",),
                action=CopilotAction("원인 분석 작업공간 열기", "/home/dmaic/analyze/root-causes"),
                rule_id="dmaic-symptom-cause-action-guide",
                recommended_tool="DMAIC 원인 분석",
                menu_path=("홈 (Home)", "개선 프로젝트 (DMAIC)", "분석 (Analyze)", "원인 분석"),
                checklist=("현상·발생 시점·영향 범위를 정의합니다.", "기준선과 비교 데이터의 출처를 확인합니다.", "원인 후보와 검증된 원인을 구분합니다."),
                workflow_steps=("현상을 수치와 범위로 정의", "데이터·측정 신뢰성 확인", "Pareto·특성요인도로 원인 후보 정리", "데이터로 원인 검증", "임시 조치와 개선 대책의 효과 확인"),
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
        if rule_guidance.rule_id is not None:
            if self._fallback_provider is not None and _requires_model_enrichment(question):
                try:
                    enrichment = self._fallback_provider.answer(
                        question=_enrichment_question(question, rule_guidance),
                        pathname=pathname,
                        workspace=workspace,
                        evidence_context=evidence_context,
                    )
                    return replace(
                        enrichment,
                        answer=rule_guidance.answer + "\n\n추가 분석 가이드\n" + enrichment.answer,
                        sources=rule_guidance.sources + enrichment.sources,
                        limitations=rule_guidance.limitations + enrichment.limitations,
                        action=rule_guidance.action or enrichment.action,
                        rule_id=rule_guidance.rule_id,
                        recommended_tool=rule_guidance.recommended_tool or enrichment.recommended_tool,
                        menu_path=rule_guidance.menu_path or enrichment.menu_path,
                        checklist=rule_guidance.checklist or enrichment.checklist,
                        workflow_steps=rule_guidance.workflow_steps or enrichment.workflow_steps,
                        fallback_steps=(
                            CopilotFallbackStep("Rulebase", "answered", "검토된 규칙으로 답변 가능한 부분을 먼저 제시했습니다."),
                            *enrichment.fallback_steps,
                        ),
                    )
                except (OSError, ValueError, KeyError, TypeError):
                    pass
            return replace(
                rule_guidance,
                fallback_steps=(
                    CopilotFallbackStep("Rulebase", "answered", "검토된 규칙으로 답변을 생성했습니다."),
                    CopilotFallbackStep("Codex SDK", "skipped", "Rulebase 답변이 있어 호출하지 않았습니다."),
                ),
            )
        if self._fallback_provider is None:
            return replace(
                rule_guidance,
                fallback_steps=(
                    CopilotFallbackStep("Rulebase", "unmatched", "직접 대응하는 검토 규칙을 찾지 못했습니다."),
                    CopilotFallbackStep("Codex SDK", "unavailable", "모델 연결이 설정되지 않았습니다."),
                ),
            )
        try:
            fallback_guidance = self._fallback_provider.answer(
                question=question, pathname=pathname, workspace=workspace, evidence_context=evidence_context,
            )
            return replace(
                fallback_guidance,
                fallback_steps=(
                    CopilotFallbackStep("Rulebase", "unmatched", "직접 대응하는 검토 규칙을 찾지 못했습니다."),
                    *fallback_guidance.fallback_steps,
                ),
            )
        except (OSError, ValueError, KeyError, TypeError):
            return replace(
                rule_guidance,
                limitations=rule_guidance.limitations
                + ("생성형 AI 보완을 사용할 수 없어 검토된 로컬 안내만 제공합니다.",),
                fallback_steps=(
                    CopilotFallbackStep("Rulebase", "unmatched", "직접 대응하는 검토 규칙을 찾지 못했습니다."),
                    CopilotFallbackStep("Codex SDK", "failed", "Codex SDK 폴백을 시작하지 못했습니다."),
                ),
            )

    def answer_selected_model(
        self,
        *,
        model_preference: str,
        question: str,
        pathname: str,
        workspace: str,
        evidence_context: str | None,
    ) -> CopilotGuidance:
        if model_preference == "rulebase":
            return replace(
                self._rule_provider.answer(
                    question=question, pathname=pathname, workspace=workspace, evidence_context=evidence_context,
                ),
                fallback_steps=(
                    CopilotFallbackStep("Rulebase", "answered", "사용자가 Rulebase를 지정해 답변을 생성했습니다."),
                    CopilotFallbackStep("Codex SDK", "skipped", "사용자가 Rulebase를 지정했습니다."),
                ),
            )
        if isinstance(self._fallback_provider, FallbackChainCopilotProvider) and model_preference == "codex":
            return self._fallback_provider.answer_selected_model(
                model_preference=model_preference,
                question=question,
                pathname=pathname,
                workspace=workspace,
                evidence_context=evidence_context,
            )
        raise ValueError("The selected Copilot model is not available")


def _requires_model_enrichment(question: str) -> bool:
    normalized = question.casefold()
    definition_terms = ("정의", "설명", "기준", "kpi", "지표", "표준")
    action_terms = ("제안", "분석", "문제점", "개선", "수립", "방안", "계산", "비교")
    return len(normalized) >= 160 or (
        any(term in normalized for term in definition_terms)
        and any(term in normalized for term in action_terms)
    )


def _enrichment_question(question: str, rule_guidance: CopilotGuidance) -> str:
    return (
        "다음 사용자 요청에 대해 Rulebase가 아래 내용을 이미 안내했습니다. "
        "반복하지 말고, Rulebase가 다루지 못한 정의·산식·분석 관점·현장 적용 주의사항만 보완하세요.\n"
        f"사용자 요청: {question}\n"
        f"Rulebase 안내: {rule_guidance.answer}"
    )


def _model_error_detail(error: Exception) -> str:
    message = str(error)
    if "429" in message:
        return "요청 한도(HTTP 429)에 도달했습니다."
    if "timed out" in message.casefold():
        return "모델 요청의 연결 또는 응답 수신 시간이 제한을 초과했습니다."
    if "invalid JSON" in message or "invalid guidance contract" in message:
        return "모델 응답이 JSON 안내 형식과 일치하지 않습니다."
    if "empty answer" in message:
        return "모델이 비어 있는 답변을 반환했습니다."
    return "모델 연결 또는 응답 생성에 실패했습니다."


class FallbackChainCopilotProvider:
    """Use the read-only Codex SDK for questions outside the Rulebase."""

    def __init__(
        self,
        *,
        codex: CopilotProvider | None,
    ) -> None:
        self._codex = codex

    def answer(
        self,
        *,
        question: str,
        pathname: str,
        workspace: str,
        evidence_context: str | None,
    ) -> CopilotGuidance:
        if self._codex is None:
            return self._manual_guidance("unavailable", "사용 가능한 연결 또는 모델이 설정되지 않았습니다.")
        try:
            guidance = self._codex.answer(
                question=question,
                pathname=pathname,
                workspace=workspace,
                evidence_context=evidence_context,
            )
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
            return self._manual_guidance("failed", _model_error_detail(error))
        return replace(
            guidance,
            fallback_steps=(CopilotFallbackStep("Codex SDK", "answered", "답변을 생성했습니다."),),
        )

    @staticmethod
    def _manual_guidance(status: str, detail: str) -> CopilotGuidance:
        return CopilotGuidance(
            answer="자동 안내 모델에 연결할 수 없습니다. 잠시 후 같은 질문을 다시 시도하거나, 분석 목적·결과 변수·데이터 구조·현재 제약을 직접 입력해 주세요.",
            provider="statpro-fallback-unavailable",
            sources=(_SELECTION_SOURCE,),
            limitations=(
                "Rulebase에 직접 대응하는 규칙을 찾지 못했습니다.",
                "Codex SDK 폴백 응답을 사용할 수 없었습니다.",
                "분석 설정이나 저장 문서는 자동으로 변경하지 않습니다.",
            ),
            action=CopilotAction("분석 선택 시작", "/analyses"),
            guidance_mode="manual_guidance",
            checklist=("분석 목표 입력", "결과 변수의 데이터형 입력", "수집 구조와 표본 수 입력", "현장 제약·안전 범위 입력"),
            workflow_steps=("필수 입력 보완", "분석 선택 도우미에서 방법 검토", "사용자가 설정을 검토·실행"),
            fallback_steps=(CopilotFallbackStep("Codex SDK", status, detail),),
        )

    def answer_selected_model(
        self,
        *,
        model_preference: str,
        question: str,
        pathname: str,
        workspace: str,
        evidence_context: str | None,
    ) -> CopilotGuidance:
        if model_preference != "codex":
            raise ValueError("The selected Copilot model is not available")
        guidance = self.answer(
            question=question,
            pathname=pathname,
            workspace=workspace,
            evidence_context=evidence_context,
        )
        if guidance.provider == "statpro-fallback-unavailable":
            return guidance
        return replace(
            guidance,
            fallback_steps=(CopilotFallbackStep("Codex SDK", "answered", "사용자가 지정한 모델로 답변을 생성했습니다."),),
        )


def _guidance_from_llm_payload(
    payload: Mapping[str, Any],
    *,
    provider: str,
    source: CopilotSource,
    local_only: bool,
) -> CopilotGuidance:
    answer = payload["answer"]
    menu_path = payload["menu_path"]
    checklist = payload["checklist"]
    workflow_steps = payload["workflow_steps"]
    if not isinstance(answer, str) or not answer.strip():
        raise ValueError("LLM returned an empty answer")
    if not all(isinstance(values, list) for values in (menu_path, checklist, workflow_steps)):
        raise ValueError("LLM returned an invalid guidance contract")
    if not all(
        isinstance(item, str)
        for values in (menu_path, checklist, workflow_steps)
        for item in values
    ):
        raise ValueError("LLM returned a non-string guidance item")
    recommended_tool = payload["recommended_tool"]
    if recommended_tool is not None and not isinstance(recommended_tool, str):
        raise ValueError("LLM returned an invalid recommended tool")
    locality = "로컬 loopback 모델" if local_only else "생성형 AI 보완"
    return CopilotGuidance(
        answer=answer.strip(),
        provider=provider,
        sources=(source,),
        limitations=(
            f"{locality} 응답이며 정확성과 현장 적용 가능성을 사용자가 검토해야 합니다.",
            "분석 설정이나 저장 문서를 자동으로 변경하지 않습니다.",
        ),
        guidance_mode="llm_fallback",
        recommended_tool=recommended_tool,
        menu_path=tuple(menu_path[:8]),
        checklist=tuple(checklist[:12]),
        workflow_steps=tuple(workflow_steps[:12]),
    )


def _decode_llm_guidance_payload(text: object, *, provider_name: str) -> Mapping[str, Any]:
    """Normalize a model's JSON content once at the provider boundary."""

    if not isinstance(text, str):
        raise ValueError(f"{provider_name} returned non-string content")
    normalized = text.strip()
    if normalized.startswith("```") and normalized.endswith("```"):
        normalized = normalized.split("\n", 1)[1].rsplit("\n", 1)[0].strip()
    try:
        payload = json.loads(normalized)
    except (TypeError, json.JSONDecodeError) as error:
        start = normalized.find("{")
        if start < 0:
            raise ValueError(f"{provider_name} returned invalid JSON guidance") from error
        try:
            payload, _ = json.JSONDecoder().raw_decode(normalized[start:])
        except json.JSONDecodeError as extraction_error:
            raise ValueError(f"{provider_name} returned invalid JSON guidance") from extraction_error
    if not isinstance(payload, Mapping):
        raise ValueError(f"{provider_name} returned a non-object JSON response")
    return payload


def _guidance_from_provider_text(
    text: object,
    *,
    provider_name: str,
    provider: str,
    source: CopilotSource,
    local_only: bool,
) -> CopilotGuidance:
    """Own all generated-content validation at the provider boundary."""

    payload = _decode_llm_guidance_payload(text, provider_name=provider_name)
    try:
        return _guidance_from_llm_payload(
            payload,
            provider=provider,
            source=source,
            local_only=local_only,
        )
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError(f"{provider_name} returned an invalid guidance contract") from error


class OpenAICodexSdkClient:
    """Run one Copilot turn through the local Codex app-server.

    The optional dependency is imported only when the administrator enables
    this fallback, so a normal Rulebase request never requires the SDK.
    """

    def run_read_only(self, *, model: str | None, prompt: str) -> str:
        try:
            from openai_codex import Codex, Sandbox
        except ImportError as error:
            raise OSError("Codex SDK is not installed") from error
        with Codex() as codex:
            options: dict[str, object] = {"sandbox": Sandbox.read_only}
            if model:
                options["model"] = model
            thread = codex.thread_start(**options)
            result = thread.run(prompt)
        if not isinstance(result.final_response, str):
            raise ValueError("Codex SDK returned an invalid guidance response")
        return result.final_response


class CodexSdkCopilotProvider:
    """Read-only Codex SDK fallback for unmatched Copilot questions."""

    def __init__(self, *, model: str | None = None, client: CodexSdkClient | None = None) -> None:
        self._model = model.strip() if model else None
        self._client = client or OpenAICodexSdkClient()

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
            "도구를 실행하거나 파일을 변경하지 마세요. 분석 설정을 자동 변경했다고 말하지 마세요. "
            "다음 JSON만 반환하세요: "
            '{"answer":string,"recommended_tool":string|null,"menu_path":string[],"checklist":string[],"workflow_steps":string[]}.\n'
            f"제품 참조: {_ASSISTANT_REFERENCE}\n"
            f"현재 작업공간: {workspace}\n현재 경로: {pathname}\n"
            f"사용자 질문: {question}\n"
            f"사용자가 선택한 근거 문맥: {evidence_context or '없음'}"
        )
        text = self._client.run_read_only(model=self._model, prompt=prompt)
        return _guidance_from_provider_text(
            text,
            provider_name="Codex SDK",
            provider=f"codex-sdk:{self._model or 'default'}",
            source=CopilotSource("Codex SDK의 사용자 질문과 선택 문맥", "copilot://codex-question", "user_context"),
            local_only=False,
        )


def build_default_copilot_provider() -> CopilotProvider:
    """Build Rulebase → read-only Codex SDK → manual guidance."""

    codex_enabled = os.getenv("STATPRO_COPILOT_CODEX_ENABLED", "").casefold() == "true"
    codex_model = os.getenv("STATPRO_COPILOT_CODEX_MODEL", "").strip() or None
    codex = CodexSdkCopilotProvider(model=codex_model) if codex_enabled else None

    return RuleFirstCopilotProvider(
        LocalKnowledgeCopilotProvider(),
        FallbackChainCopilotProvider(
            codex=codex,
        ),
    )


def copilot_runtime_status() -> dict[str, object]:
    """Describe configured fallback readiness without exposing credentials.

    This is configuration evidence only.  It intentionally does not probe a
    local Codex app-server, because a status request must not transmit a
    user's context or create an unexpected model call.
    """
    codex_enabled = os.getenv("STATPRO_COPILOT_CODEX_ENABLED", "").casefold() == "true"
    codex_model = os.getenv("STATPRO_COPILOT_CODEX_MODEL", "").strip() or None
    try:
        import importlib.util
        codex_sdk_installed = importlib.util.find_spec("openai_codex") is not None
    except (ImportError, ValueError):
        codex_sdk_installed = False

    return {
        "rulebase": {
            "configured": True,
            "rule_count": len(COPILOT_RULE_CATALOG),
            "live_verified": True,
        },
        "codex": {
            "enabled": codex_enabled,
            "sdk_installed": codex_sdk_installed,
            "ready": codex_enabled and codex_sdk_installed,
            "model": codex_model,
            "sandbox": "read_only",
            "live_verified": False,
        },
        "manual_input_available": True,
        "limitations": (
            "이 상태는 설정만 확인하며 Codex SDK에 요청하지 않습니다. "
            "실제 연결·모델 가용성은 사용자가 명시적으로 활성화한 환경에서 별도로 검증해야 합니다."
        ),
    }
