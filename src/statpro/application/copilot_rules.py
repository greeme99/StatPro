"""Reviewed field-situation catalog used by the StatPro AI Copilot.

The catalog deliberately describes a bounded product surface.  A rule does not
diagnose a process or change an analysis: it only routes a user to a reviewed
workspace with the inputs and workflow that must be checked by the user.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CopilotRule:
    rule_id: str
    domain: str
    situation: str
    trigger_groups: tuple[tuple[str, ...], ...]
    recommended_tool: str
    menu_path: tuple[str, ...]
    action_label: str
    action_href: str
    checklist: tuple[str, ...]
    workflow_steps: tuple[str, ...]
    source_reference: str

    def matches(self, normalized_question: str) -> bool:
        return all(any(token in normalized_question for token in group) for group in self.trigger_groups)


def _rule(
    rule_id: str, domain: str, situation: str, triggers: tuple[tuple[str, ...], ...],
    tool: str, path: tuple[str, ...], label: str, href: str,
    checklist: tuple[str, ...], workflow: tuple[str, ...], source: str,
) -> CopilotRule:
    return CopilotRule(rule_id, domain, situation, triggers, tool, path, label, href, checklist, workflow, source)


# Each rule is intentionally tied to a navigable, currently implemented local
# workspace.  Rules that require an organisation policy state that dependency
# in their checklist rather than pretending that an external service is live.
COPILOT_RULE_CATALOG: tuple[CopilotRule, ...] = (
    _rule("data-csv-import", "데이터", "CSV 작업표를 가져와 분석용 데이터를 준비한다.", (("csv", "가져오기", "업로드"),), "작업표 및 데이터", ("홈 (Home)", "작업표 및 데이터 (Worksheet & Data)", "데이터 가져오기"), "데이터 가져오기 열기", "/data", ("원본 파일과 열 의미를 확인합니다.", "결측값·단위·시간 순서를 확인합니다."), ("CSV 가져오기", "변수 유형 검토", "작업표 개정 저장", "분석 입력으로 선택"), "docs/03.StatPro_IA.md"),
    _rule("spc-chart-selection", "SPC", "공정 안정성 감시용 관리도를 선택한다.", (("관리도", "spc", "공정 안정", "이상 신호"),), "관리도 선택", ("홈 (Home)", "통계적 공정관리 (SPC)", "관리도 선택"), "관리도 선택 열기", "/spc/control-charts", ("데이터가 계량형인지 계수형인지 구분합니다.", "시간 순서와 합리적 부분군을 확인합니다."), ("데이터 구조 분류", "관리도 선택", "입력·검증", "분석 실행", "신호 조사·조치"), "docs/evidence/2026-11-01-spc-seven-tools-workspace.md"),
    _rule("spc-imr-single-observation", "SPC", "부분군 없이 개별 연속 측정값을 감시한다.", (("i-mr", "개별값", "이동범위"),), "I-MR 관리도", ("홈 (Home)", "통계적 공정관리 (SPC)", "계량형", "I-MR 관리도"), "I-MR 설정 열기", "/analyses/imr/new", ("관측 순서가 실제 시간 순서인지 확인합니다.", "자기상관과 계절성을 점검합니다."), ("개별값 입력", "기준 구간 확인", "분석 실행", "신호 조사"), "docs/evidence/2026-11-01-spc-seven-tools-workspace.md"),
    _rule("spc-xbar-s-large-subgroup", "SPC", "큰 부분군의 평균과 산포를 감시한다.", (("xbar-s", "xbar s", "평균 표준편차"),), "Xbar-S 관리도", ("홈 (Home)", "통계적 공정관리 (SPC)", "계량형", "Xbar-S 관리도"), "Xbar-S 설정 열기", "/analyses/spc/xbar-s", ("부분군별 크기와 수집 조건을 확인합니다.", "S 관리도의 산포 안정성을 먼저 검토합니다."), ("부분군 입력", "S 관리도 검토", "Xbar 관리도 검토", "신호 조치"), "docs/evidence/2026-11-01-spc-seven-tools-workspace.md"),
    _rule("spc-p-variable-sample", "SPC", "표본 크기가 달라지는 부적합품 비율을 감시한다.", (("p 관리도", "불량률", "부적합품 비율"),), "p 관리도", ("홈 (Home)", "통계적 공정관리 (SPC)", "계수형", "p 관리도"), "p 관리도 설정 열기", "/analyses/spc/attribute?chart=p", ("각 표본의 부적합품 수와 검사 수를 준비합니다.", "부적합품 수가 검사 수를 넘지 않는지 확인합니다."), ("표본별 수량 입력", "유효성 검증", "관리도 실행", "과산포와 신호 검토"), "docs/evidence/2026-11-01-spc-seven-tools-workspace.md"),
    _rule("spc-np-fixed-sample", "SPC", "표본 크기가 일정한 부적합품 개수를 감시한다.", (("np 관리도", "불량품 개수", "부적합품 개수"),), "np 관리도", ("홈 (Home)", "통계적 공정관리 (SPC)", "계수형", "np 관리도"), "np 관리도 설정 열기", "/analyses/spc/attribute?chart=np", ("모든 행의 검사 수가 같은지 확인합니다.", "표본 크기가 바뀌면 p 관리도로 전환합니다."), ("고정 검사 수 확인", "부적합품 수 입력", "관리도 실행", "신호 조치"), "docs/evidence/2026-11-01-spc-seven-tools-workspace.md"),
    _rule("spc-c-defect-count", "SPC", "고정 기회에서 결점 수를 감시한다.", (("c 관리도", "결점 개수", "결함 개수"),), "c 관리도", ("홈 (Home)", "통계적 공정관리 (SPC)", "계수형", "c 관리도"), "c 관리도 설정 열기", "/analyses/spc/attribute?chart=c", ("검사 면적·시간·기회가 일정한지 확인합니다.", "부적합품과 결점을 혼동하지 않습니다."), ("검사 기회 확인", "결점 수 입력", "관리도 실행", "특수원인 조사"), "docs/evidence/2026-11-01-spc-seven-tools-workspace.md"),
    _rule("spc-u-variable-opportunity", "SPC", "검사 기회가 달라지는 단위당 결점률을 감시한다.", (("u 관리도", "단위당 결점", "결함률"),), "u 관리도", ("홈 (Home)", "통계적 공정관리 (SPC)", "계수형", "u 관리도"), "u 관리도 설정 열기", "/analyses/spc/attribute?chart=u", ("행마다 결점 수와 검사 단위 수를 준비합니다.", "검사 단위 정의를 기간 동안 고정합니다."), ("단위 수 입력", "결점 수 입력", "관리도 실행", "과산포와 신호 검토"), "docs/evidence/2026-11-01-spc-seven-tools-workspace.md"),
    _rule("spc-ewma-small-shift", "SPC", "작고 지속적인 평균 이동을 조기 감시한다.", (("ewma", "지속 이동", "작은 이동"),), "EWMA 관리도", ("홈 (Home)", "통계적 공정관리 (SPC)", "EWMA 관리도"), "EWMA 설정 열기", "/analyses/spc/ewma", ("안정된 기준 평균과 sigma 출처를 확인합니다.", "lambda와 관리한계 폭의 변경 이유를 기록합니다."), ("기준선 확인", "lambda 설정", "분석 실행", "지속 신호 조사"), "docs/evidence/2026-10-25-ewma-control-chart.md"),
    _rule("spc-cusum-small-shift", "SPC", "목표에서의 작은 지속 이동을 누적합으로 감시한다.", (("cusum", "누적합", "결정구간"),), "CUSUM 관리도", ("홈 (Home)", "통계적 공정관리 (SPC)", "CUSUM 관리도"), "CUSUM 설정 열기", "/analyses/spc/cusum", ("기준 평균과 sigma의 출처를 확인합니다.", "k와 h 값의 탐지 목적을 기록합니다."), ("기준선 확인", "k·h 설정", "분석 실행", "누적 신호 조사"), "docs/evidence/2026-10-25-cusum-control-chart.md"),
    _rule("spc-rare-event", "SPC", "희귀사건 사이의 기회 수 또는 시간을 감시한다.", (("희귀", "g 관리도", "t 관리도", "사건 사이"),), "G/T 관리도", ("홈 (Home)", "통계적 공정관리 (SPC)", "희귀사건 G/T 관리도"), "G/T 설정 열기", "/analyses/spc/rare-events", ("사건 정의와 수집 단위를 고정합니다.", "G는 양의 정수 기회 수, T는 양의 연속 시간을 사용합니다."), ("사건 정의", "간격 데이터 입력", "관리도 실행", "신호 조사"), "docs/evidence/2026-10-29-spc-rare-event-g-t.md"),
    _rule("spc-capability", "SPC", "공정이 규격을 만족하는지 능력지수로 평가한다.", (("공정능력", "cpk", "ppk", "규격"),), "공정능력 분석", ("홈 (Home)", "통계적 공정관리 (SPC)", "공정능력 분석"), "공정능력 분석 열기", "/analyses/capability", ("LSL·USL·목표값과 단위를 확인합니다.", "공정 안정성과 분포 가정을 먼저 확인합니다."), ("측정 데이터 입력", "규격 정의", "능력 계산", "가정·결과 검토"), "docs/evidence/2026-10-28-empirical-nonnormal-capability.md"),
    _rule("doe-screening", "DOE", "많은 인자 중 중요한 인자를 빠르게 선별한다.", (("선별", "plackett", "플라켓", "인자 많"),), "DOE 선별 설계", ("홈 (Home)", "실험계획법 (DOE)", "선별 설계"), "DOE 선별설계 열기", "/doe", ("후보 인자와 안전 범위를 정리합니다.", "별칭 구조와 상호작용 제한을 검토합니다."), ("선별 목표 정의", "설계 생성", "무작위 실행", "중요 인자 확인", "후속 실험 계획"), "docs/evidence/2026-10-25-doe-automatic-fractional-generators.md"),
    _rule("doe-response-surface", "DOE", "곡률을 추정하고 최적 조건을 찾는다.", (("반응표면", "box-behnken", "중심합성", "곡률"),), "DOE 반응표면 설계", ("홈 (Home)", "실험계획법 (DOE)", "반응표면 및 최적화"), "DOE 반응표면 열기", "/doe", ("응답 목표와 안전 제약을 정의합니다.", "중심점·블록·반복의 필요성을 확인합니다."), ("요인 범위 설정", "Box-Behnken 또는 중앙합성 선택", "실행표 생성", "모형 진단", "최적 조건 확인 실험"), "docs/evidence/2026-10-25-box-behnken.md"),
    _rule("doe-report-export", "DOE", "실험 결과를 검토 가능한 보고서로 내보낸다.", (("doe", "보고서", "내보내기", "export"),), "DOE 결과 및 보고서", ("홈 (Home)", "실험계획법 (DOE)", "결과 및 보고서"), "DOE 보고서 열기", "/runs", ("분석 실행과 입력 개정을 확인합니다.", "설계·모형·진단·최적화 근거가 모두 있는지 확인합니다."), ("분석 실행 선택", "보고서 검토", "형식 선택", "내보낸 파일 검증"), "docs/evidence/2026-10-28-doe-standard-report-export.md"),
    _rule("fmea-pfmea-start", "FMEA", "공정 변경 또는 신규 공정의 위험을 구조화한다.", (("pfmea", "신규 공정", "공정 변경", "고장 형태"),), "PFMEA 작업공간", ("홈 (Home)", "고장 형태 및 영향 분석 (FMEA)", "PFMEA 분석"), "PFMEA 작업공간 열기", "/fmea", ("공정 흐름과 특성 ID를 준비합니다.", "팀·표준 버전·조치 우선순위 정책을 확인합니다."), ("기획", "구조·기능 분석", "고장·위험 분석", "조치 최적화", "관리계획·승인"), "docs/evidence/2026-10-25-fmea-seven-step-workflow.md"),
    _rule("fmea-control-plan", "FMEA", "위험 조치를 관리계획과 SPC·MSA 증거로 연결한다.", (("fmea", "관리계획", "spc", "msa"),), "FMEA 관리계획서", ("홈 (Home)", "고장 형태 및 영향 분석 (FMEA)", "관리계획서"), "FMEA 관리계획 열기", "/fmea", ("공정·특성·관리항목 ID를 확인합니다.", "연결할 SPC·MSA 실행이 유효한지 검토합니다."), ("관리항목 정의", "분석 실행 연결", "조치·반응 계획 지정", "개정 검토", "승인"), "docs/evidence/2026-10-27-fmea-spc-msa-run-evidence.md"),
    _rule("fmea-enterprise-approval", "FMEA", "기업 계정으로 승인·직무분리를 적용한다.", (("idp", "mfa", "직무분리", "기업 승인"),), "FMEA 기업 승인", ("홈 (Home)", "고장 형태 및 영향 분석 (FMEA)", "조치·검토·승인"), "FMEA 승인 화면 열기", "/fmea", ("조직의 Entra OIDC claims와 권한 마스터를 제공받습니다.", "승인자와 작성자의 독립성을 정책으로 확인합니다."), ("조직 정책 확인", "계정·역할 검증", "분석 근거 재검증", "승인·감사 기록"), "docs/evidence/2026-11-01-fmea-enterprise-idp-policy.md"),
    _rule("dmaic-root-cause", "DMAIC", "문제의 검증 가능한 원인을 찾는다.", (("근본원인", "fishbone", "5 why", "특성요인"),), "DMAIC 분석 (Analyze)", ("홈 (Home)", "개선 프로젝트 (DMAIC)", "분석 (Analyze)"), "원인 분석 작업공간 열기", "/home/dmaic/analyze/root-causes", ("문제 정의와 기준 데이터를 확인합니다.", "원인 후보와 검증 증거를 구분합니다."), ("원인 후보 수집", "Pareto로 우선순위 지정", "Fishbone·5 Why 구조화", "데이터로 원인 검증", "조치 대상으로 확정"), "docs/evidence/2026-10-29-dmaic-ui-structure.md"),
    _rule("dmaic-solution-pilot", "DMAIC", "개선 대책을 선정하고 파일럿으로 검증한다.", (("파일럿", "개선안", "대책", "솔루션"),), "DMAIC 개선 (Improve)", ("홈 (Home)", "개선 프로젝트 (DMAIC)", "개선 (Improve)"), "개선안 선정 열기", "/home/dmaic/improve/solution-selection", ("검증된 원인과 후보 대책을 연결합니다.", "성공지표·중단 기준·위험 대응을 정의합니다."), ("평가 기준 정의", "개선안 비교", "파일럿 계획", "효과 검증", "관리 단계 이관"), "docs/evidence/2026-10-29-dmaic-ui-structure.md"),
    _rule("dmaic-control-handoff", "DMAIC", "개선 효과를 현장 관리 체계로 인수인계한다.", (("관리 인수", "효과 유지", "반응 계획", "관리 단계"),), "DMAIC 관리 (Control)", ("홈 (Home)", "개선 프로젝트 (DMAIC)", "관리 (Control)"), "관리 인수인계 열기", "/home/dmaic/control", ("효과 기준과 검토 주기를 정합니다.", "FMEA 관리항목과 SPC·능력 실행을 연결합니다."), ("관리 지표 정의", "반응 계획 지정", "FMEA·SPC 근거 연결", "책임자 검토", "정기 재검증"), "docs/evidence/2026-10-29-dmaic-ui-structure.md"),
    _rule("spc-pareto", "7대 품질 도구", "결함·원인의 우선순위를 파레토로 좁힌다.", (("파레토", "pareto", "결함 우선"),), "파레토 분석", ("홈 (Home)", "통계적 공정관리 (SPC)", "7대 품질 도구", "파레토 분석"), "파레토 작업공간 열기", "/spc/tools/pareto-chart", ("집계 기준과 기간을 정합니다.", "결함 수·기회 수·손실 지표를 구분합니다."), ("결함 데이터 입력", "누적 비율 계산", "집중 영역 선정", "원인 분석 연결"), "docs/evidence/2026-11-01-spc-seven-tools-workspace.md"),
    _rule("spc-fishbone", "7대 품질 도구", "원인 후보를 6M 구조로 정리한다.", (("fishbone", "특성요인", "이시카와"),), "특성요인도", ("홈 (Home)", "통계적 공정관리 (SPC)", "7대 품질 도구", "특성요인도"), "특성요인도 열기", "/spc/tools/fishbone", ("문제 문장을 측정 가능하게 정의합니다.", "후보 원인과 검증된 원인을 구분합니다."), ("문제 정의", "6M 원인 후보 등록", "검증 대상 선정", "분석 근거 연결"), "docs/evidence/2026-11-01-spc-seven-tools-workspace.md"),
    _rule("case-smt-solder-defect", "전자제조", "SMT 납땜·미부착·브리지 불량을 공정 흐름으로 줄인다.", (("smt", "pcb", "납땜", "리플로우"), ("불량", "수율", "미부착", "브리지", "툼스톤")), "DMAIC·DOE·SPC 개선 흐름", ("홈 (Home)", "개선 프로젝트 (DMAIC)", "분석·개선"), "SMT 개선 흐름 시작", "/home/dmaic", ("불량 유형·공정 위치·FPY·재작업률을 정의합니다.", "SPI/AOI/X-ray 측정시스템과 기준선을 확인합니다.", "리플로우·인쇄·배치 조건의 안전 범위를 확인합니다."), ("Pareto로 불량 유형 압축", "MSA 및 기준선 확인", "Fishbone·FMEA로 원인 가설화", "DOE로 공정 인자 검증", "SPC·Control Plan으로 유지"), "docs/evidence/2026-10-29-dmaic-ui-structure.md"),
    _rule("case-aoi-measurement", "전자제조", "AOI·ICT·FCT·X-ray의 오탐과 미탐을 측정시스템 관점에서 평가한다.", (("aoi", "ict", "fct", "x-ray", "검사"), ("오탐", "미탐", "판정", "검사자")), "Attribute Agreement", ("홈 (Home)", "개선 프로젝트 (DMAIC)", "측정 (Measure)", "Attribute Agreement"), "Attribute Agreement 열기", "/analyses/msa/attribute-agreement", ("Golden Sample과 기준 판정을 준비합니다.", "검사자·장비·반복·판정 결과를 구분합니다.", "모든 검사자가 모든 샘플을 같은 횟수로 판정하도록 설계합니다."), ("판정 기준 확정", "샘플·검사자·반복 설계", "일치도·오탐·미탐 검토", "측정시스템 개선", "신뢰된 데이터만 SPC·능력에 사용"), "docs/03.StatPro_IA.md"),
    _rule("case-reflow-optimization", "전자제조", "리플로우 조건을 평균과 변동을 함께 고려해 최적화한다.", (("리플로우", "reflow", "솔더", "인쇄"), ("최적", "조건", "void", "신뢰성")), "DOE 반응표면 및 최적화", ("홈 (Home)", "실험계획법 (DOE)", "반응표면 및 최적화"), "리플로우 DOE 시작", "/doe", ("반응값과 측정시스템을 확정합니다.", "온도·시간·속도·압력의 안전 범위를 정합니다.", "평균 목표와 변동 목표를 함께 정의합니다."), ("요인·반응 정의", "설계·반복·무작위화", "실행 및 데이터 수집", "모형·진단 검토", "확인 실험과 SPC 인계"), "docs/evidence/2026-10-25-box-behnken.md"),
    _rule("case-supplier-variation", "공급사 품질", "납입 부품 변동과 대체품 리스크를 입고부터 관리한다.", (("공급사", "납입", "입고", "supplier"), ("변동", "대체", "ppm", "품질 편차")), "FMEA·MSA·공정능력 분석", ("홈 (Home)", "고장 형태 및 영향 분석 (FMEA)", "관리계획서"), "공급사 품질 흐름 시작", "/fmea", ("부품 특성·공급사·로트 식별자를 준비합니다.", "검사방법과 측정시스템의 신뢰성을 확인합니다.", "입고 규격·샘플링·반응계획을 정의합니다."), ("공급사 위험 FMEA", "입고 MSA·검사 기준", "로트별 능력·변동 검토", "부적합 조치와 8D 요청", "Control Plan에 반영"), "docs/03.StatPro_IA.md"),
    _rule("case-semiconductor-drift", "반도체·팹", "공정 drift와 excursion을 조기에 탐지한다.", (("반도체", "wafer", "팹", "식각", "증착", "cmp"), ("drift", "excursion", "군집", "수율")), "SPC 공정 감시", ("홈 (Home)", "통계적 공정관리 (SPC)", "관리도 선택"), "반도체 SPC 흐름 시작", "/spc", ("공정 단계·설비·lot·wafer 식별자를 보존합니다.", "FDC/APC/R2R은 외부 데이터·정책 연계가 필요한지 확인합니다.", "SPC 기준선과 알람 반응계획을 지정합니다."), ("수율·결함 데이터 연결", "공간·시간 구조 확인", "적합한 SPC 실행", "excursion 원인 조사", "격리·반응·재검증"), "docs/03.StatPro_IA.md"),
    _rule("case-customer-complaint", "출하·현장 품질", "고객불만과 반복불량을 원인·조치·효과검증으로 연결한다.", (("고객불만", "클레임", "출하", "보증", "현장고장"), ("반복", "재발", "원인", "시정")), "DMAIC 근본원인 및 FMEA 관리", ("홈 (Home)", "개선 프로젝트 (DMAIC)", "분석 (Analyze)"), "고객불량 개선 흐름 시작", "/home/dmaic/analyze/root-causes", ("제품·로트·고객·발생일·불량코드를 정의합니다.", "즉시 containment와 근본원인 가설을 분리합니다.", "효과검증 KPI와 종료 조건을 정합니다."), ("문제·영향 정의", "불량 Pareto", "Fishbone·5 Why·FMEA", "데이터·DOE로 원인 검증", "CAPA·SPC·FMEA로 재발 방지"), "docs/evidence/2026-11-03-dmaic-define-measure-traceability.md"),
    _rule("case-dfss-new-product", "제품·회로 설계", "신규 제품·공정은 DFSS/DMADV 관점에서 CTQ와 설계 위험을 정의한다.", (("신제품", "회로", "설계", "dfss", "dmadv"), ("수율", "신뢰성", "emc", "열", "공차", "ctq")), "DFSS/DMADV 설계 품질 안내", ("홈 (Home)", "개선 프로젝트 (DMAIC)", "정의 (Define)"), "신규 설계 품질 흐름 시작", "/home/dmaic", ("고객 요구를 CTQ와 설계 사양으로 변환합니다.", "DFMEA와 검증계획의 범위를 정합니다.", "공차·온도·전원 변동을 Robust DOE 후보로 등록합니다."), ("요구사항·CTQ 정의", "DFMEA·공차 위험 검토", "설계안·DOE 비교", "시제품·Pilot 검증", "양산 이관 기준 확정"), "docs/evidence/2026-11-07-industrial-business-case-catalog.md"),
    _rule("case-pcb-process-variation", "PCB 제조", "표면처리·에칭·도금 편차를 CTQ, DOE, SPC, PFMEA로 연결한다.", (("pcb", "기판", "도금", "에칭", "표면처리"), ("편차", "산화", "두께", "저항", "스크랩", "수율")), "PCB 공정 변동 개선", ("홈 (Home)", "통계적 공정관리 (SPC)", "관리도 선택"), "PCB 공정 관리 흐름 시작", "/spc", ("도금두께·표면저항의 측정방법을 확인합니다.", "설비·lot·욕조·시간 식별자를 보존합니다.", "규격과 기준선을 확정한 뒤 관리도를 선택합니다."), ("CTQ·규격 정의", "MSA·기준선 검토", "DOE 원인 검증", "SPC 감시", "PFMEA·Control Plan 반영"), "docs/evidence/2026-11-07-industrial-business-case-catalog.md"),
    _rule("case-paste-printing", "솔더페이스트 인쇄", "SPI 인쇄 볼륨·면적·높이 편차의 원인을 실험과 관리도로 검증한다.", (("spi", "인쇄", "스텐실", "페이스트"), ("볼륨", "면적", "높이", "압력", "속도", "편차")), "SPI 인쇄 DOE·SPC", ("홈 (Home)", "실험계획법 (DOE)", "실험 설정"), "SPI 인쇄 개선 흐름 시작", "/doe", ("SPI 측정시스템과 허용범위를 확인합니다.", "압력·속도·분리속도·스텐실 두께를 인자로 정의합니다.", "Transfer Efficiency와 CV를 반응값으로 지정합니다."), ("측정 신뢰성 확인", "요인·반응 정의", "DOE 실행", "SPC 기준선 설정", "청소주기·SOP 표준화"), "docs/evidence/2026-11-07-industrial-business-case-catalog.md"),
    _rule("case-placement-accuracy", "부품 배치", "칩·MLCC 배치 Offset과 회전 편차를 측정·실험·관리한다.", (("배치", "placement", "칩", "mlcc", "노즐", "피더"), ("offset", "회전", "미스픽", "정확도", "편차")), "배치 정확도 개선", ("홈 (Home)", "통계적 공정관리 (SPC)", "관리도 선택"), "배치 정확도 관리 흐름 시작", "/spc", ("X/Y Offset과 회전각의 측정 정의를 확인합니다.", "노즐·피더·속도·압력을 잠재 인자로 등록합니다.", "부품·설비·프로그램별 기준선을 비교합니다."), ("데이터·식별자 정리", "MSA 확인", "DOE 또는 원인분석", "관리도 감시", "점검표·프로그램 반영"), "docs/evidence/2026-11-07-industrial-business-case-catalog.md"),
    _rule("case-functional-test-yield", "기능검사", "ICT·FCT의 접촉·프로그램·전원 변동과 오검출을 검증한다.", (("ict", "fct", "기능검사", "테스트"), ("탈락", "오검출", "오검", "fail", "yield", "접촉")), "기능검사 MSA·수율 개선", ("홈 (Home)", "개선 프로젝트 (DMAIC)", "측정 (Measure)"), "기능검사 개선 흐름 시작", "/home/dmaic", ("Fail·False Fail·Escape의 정의를 분리합니다.", "Fixture·Test Program·전원·온도 조건을 식별합니다.", "검사 판정 신뢰성을 확인한 뒤 개선 실험을 계획합니다."), ("문제·KPI 정의", "검사 MSA", "원인·조건 비교", "DOE 검증", "Test Plan·교정 기준 반영"), "docs/evidence/2026-11-07-industrial-business-case-catalog.md"),
    _rule("case-assembly-fastening", "조립·체결", "토크·각도·체결순서 변동을 FMEA와 SPC로 관리한다.", (("조립", "체결", "커넥터", "나사", "케이블", "토크"), ("누락", "과토크", "미체결", "불량", "변동")), "조립 체결 품질 관리", ("홈 (Home)", "고장 형태 및 영향 분석 (FMEA)", "관리계획서"), "조립 품질 흐름 시작", "/fmea", ("체결 특성과 허용규격을 정의합니다.", "토크 장비의 교정·측정 신뢰성을 확인합니다.", "누락·과토크·순서 오류의 반응계획을 정의합니다."), ("PFMEA 위험 검토", "토크 MSA·기준선", "원인·조건 검증", "Torque SPC", "Poka-Yoke·SOP 반영"), "docs/evidence/2026-11-07-industrial-business-case-catalog.md"),
    _rule("case-field-capa", "출하·현장 품질", "출하 불량·보증·현장고장을 8D/CAPA와 분석·재발방지로 연결한다.", (("출하", "현장", "보증", "field", "capa", "8d"), ("고장", "클레임", "반품", "재발", "ppm", "불량")), "현장품질 CAPA 안내", ("홈 (Home)", "개선 프로젝트 (DMAIC)", "관리 (Control)"), "현장품질 개선 흐름 시작", "/home/dmaic", ("고객·제품·로트·발생일·불량코드를 추적합니다.", "containment와 근본원인·시정조치를 분리합니다.", "효과검증 결과를 Control Plan과 FMEA에 연결합니다."), ("고객영향·KPI 정의", "Pareto·원인분석", "시정조치 검증", "CAPA 추적", "재발방지·감사"), "docs/evidence/2026-11-07-industrial-business-case-catalog.md"),
    _rule("fmea-prevention-detection-action", "FMEA", "고장모드별 예방조치와 탐지조치를 분리해 위험을 낮추고 효과를 재평가한다.", (("fmea", "고장모드", "예방조치", "탐지조치"), ("occurrence", "발생도", "detection", "탐지도", "ap")), "FMEA 예방·탐지 조치", ("홈 (Home)", "고장 형태 및 영향 분석 (FMEA)", "조치·검토·승인"), "FMEA 조치 검토 열기", "/fmea", ("Severity·Occurrence·Detection과 현재 관리의 근거를 확인합니다.", "예방조치와 탐지조치를 별도 항목으로 기록합니다.", "조치 후 O·D·AP와 검증 증거를 재평가합니다."), ("고장모드·영향 정의", "현재 예방·탐지관리 기록", "조치 설계 및 담당 지정", "효과 검증", "FMEA·Control Plan 개정"), "docs/evidence/2026-11-07-industrial-business-case-catalog-4-6.md"),
    _rule("dmaic-yield-optimization", "DMAIC", "수율·스크랩·재작업·DPMO·Cpk를 함께 기준선으로 두고 개선한다.", (("수율", "fpy", "rty", "dpmo", "스크랩", "재작업", "cpk"), ("최적화", "개선", "기준선", "kpi")), "DMAIC 수율 최적화", ("홈 (Home)", "개선 프로젝트 (DMAIC)", "프로젝트 개요"), "수율 개선 프로젝트 시작", "/home/dmaic", ("FPY·RTY·Scrap·Rework·DPMO·Cpk의 정의와 기간을 고정합니다.", "MSA와 데이터 기준선을 먼저 확인합니다.", "사업영향이 명확한 경우 DMAIC 프로젝트로 승격할지 승인받습니다."), ("문제·재무영향 정의", "MSA·기준선 설정", "Pareto·FMEA·DOE로 원인 검증", "Pilot과 KPI 비교", "Control Plan·SPC·교육으로 유지"), "docs/evidence/2026-11-07-industrial-business-case-catalog-4-6.md"),
    _rule("doe-monte-carlo-robustness", "DOE", "공정·부품 변동과 규격을 반영한 Monte Carlo 강건성 검토를 계획한다.", (("monte carlo", "몬테카를로", "시뮬레이션", "강건성", "robust"), ("수율", "dpmo", "cpk", "공차", "분포")), "DOE 강건성·시뮬레이션 검토", ("홈 (Home)", "실험계획법 (DOE)", "반응표면 및 최적화"), "DOE 강건성 검토 열기", "/doe", ("실측 데이터로 분포·상관관계·규격을 확인합니다.", "시뮬레이션 횟수와 난수 조건을 기록합니다.", "시뮬레이션 결과를 Pilot Run으로 검증할 계획을 세웁니다."), ("분포·공차 정의", "상관관계 검토", "시나리오 실행", "Yield·DPMO·Cpk 비교", "확인 실험 및 SPC 인계"), "docs/evidence/2026-11-07-industrial-business-case-catalog-4-6.md"),
    _rule("doe-reflow-profile-void", "DOE", "리플로우 Ramp·Soak·TAL·Peak·Cooling과 페이스트·스텐실 조건으로 BGA Void를 줄인다.", (("리플로우", "reflow", "bga", "void", "툼스톤"), ("ramp", "soak", "tal", "peak", "cooling", "프로파일")), "리플로우 프로파일 DOE", ("홈 (Home)", "실험계획법 (DOE)", "실험 설정"), "리플로우 DOE 시작", "/doe", ("Void·툼스톤·솔더볼·Bridging과 측정방법을 정의합니다.", "온도·시간·분위기·페이스트·스텐실의 안전 범위를 확인합니다.", "IPC·재료 공급사 기준은 적용 제품과 개정판을 확인합니다."), ("반응변수·규격 정의", "프로파일 요인·수준 설정", "DOE 실행 및 X-ray/AOI 수집", "최적조건·진단 검토", "Pilot·SPC·PFMEA 반영"), "docs/evidence/2026-11-07-industrial-business-case-catalog-4-6.md"),
    _rule("spc-rule-response-plan", "SPC", "관리도 신호를 반응계획·담당자·CAPA로 연결한다.", (("spc", "관리도", "공정 감시"), ("western electric", "nelson", "반응계획", "capa", "이상")), "SPC 신호·반응계획", ("홈 (Home)", "통계적 공정관리 (SPC)", "관리도 결과·반응계획"), "SPC 반응계획 열기", "/spc", ("관리특성과 기준선을 확인합니다.", "적용할 신호 규칙과 경보 수준을 명시합니다.", "담당자·기한·격리·재검증 조건을 지정합니다."), ("관리도 선택", "기준선·관리한계 확인", "규칙 신호 검토", "현장 반응 실행", "반복 이상은 CAPA·DMAIC로 승격 검토"), "docs/evidence/2026-11-07-industrial-business-case-catalog-4-6.md"),
    _rule("fmea-high-ap-evidence", "FMEA", "High AP 고장모드의 예방·탐지 개선 또는 현행관리 근거를 문서화한다.", (("fmea", "ap high", "high ap", "고위험"), ("예방", "탐지", "근거", "검증")), "FMEA High AP 조치", ("홈 (Home)", "고장 형태 및 영향 분석 (FMEA)", "조치·검토·승인"), "High AP 조치 검토 열기", "/fmea", ("Severity·Occurrence·Detection과 AP 산정 정책을 확인합니다.", "예방·탐지 조치와 검증방법을 분리해 기록합니다.", "조치 후 등급과 증거를 재검토합니다."), ("High AP 항목 선정", "조치·담당·기한 지정", "검증 데이터 연결", "개선 후 AP 재평가", "승인·감사 이력 저장"), "docs/evidence/2026-11-07-industrial-business-case-catalog-4-6.md"),
)


def match_catalog_rule(question: str) -> CopilotRule | None:
    normalized = question.casefold()
    matched = [rule for rule in COPILOT_RULE_CATALOG if rule.matches(normalized)]
    if not matched:
        return None
    # Broad navigation rules are fallbacks.  A question that names a concrete
    # chart or method must reach its method-specific checklist first.
    generic_ids = {"spc-chart-selection"}
    specific = [rule for rule in matched if rule.rule_id not in generic_ids]
    priority = ("fmea-high-ap-evidence", "spc-rule-response-plan")
    for rule_id in priority:
        for rule in specific:
            if rule.rule_id == rule_id:
                return rule
    return (specific or matched)[0]
