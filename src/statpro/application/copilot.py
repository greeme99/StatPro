"""Evidence-aware guidance boundary for the StatPro Copilot.

The default provider is deterministic and local-only.  An approved enterprise
model can implement :class:`CopilotProvider` later without changing the API or
the browser contract.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


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


class LocalKnowledgeCopilotProvider:
    """Deterministic guidance over reviewed StatPro product knowledge."""

    provider_name = "statpro-local-knowledge-v1"

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
        )
