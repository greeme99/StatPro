export type AnalysisGoal = "stability" | "screening" | "optimization" | "risk" | "improvement";
export type StabilityDataType = "continuous" | "defective" | "defects" | "rare";
export type SamplingStructure =
  | "individual"
  | "small-subgroup"
  | "large-subgroup"
  | "small-shift"
  | "fixed-opportunity"
  | "varying-opportunity"
  | "rare-opportunity"
  | "rare-time";

export type AnalysisRecommendation = {
  family: string;
  method: string;
  rationale: string;
  requiredInputs: string[];
  checks: string[];
  href: string;
  action: string;
};

const workflowRecommendations: Record<Exclude<AnalysisGoal, "stability">, AnalysisRecommendation> = {
  screening: {
    family: "실험계획법 (DOE)",
    method: "Plackett–Burman 선별 설계",
    rationale: "많은 후보 인자에서 중요한 주효과를 적은 실행으로 좁힌 뒤 후속 검증 설계로 연결합니다.",
    requiredInputs: ["후보 인자와 수준", "반응 변수", "실행 가능 범위"],
    checks: ["상호작용 분리 한계를 기록", "유의 인자는 완전요인 또는 반응표면으로 재검증"],
    href: "/analyses/doe/plackett-burman",
    action: "선별 설계 설정 열기",
  },
  optimization: {
    family: "실험계획법 (DOE)",
    method: "Box–Behnken 반응표면 설계",
    rationale: "주요 인자의 곡률과 상호작용을 추정해 목표 반응을 만족하는 공정 조건을 탐색합니다.",
    requiredInputs: ["연속형 인자 3개 이상", "인자별 안전 범위", "반응 목표와 제약"],
    checks: ["극단 조합이 필요한 경우 중심합성설계와 비교", "확인 실행을 별도로 예약"],
    href: "/analyses/doe/box-behnken",
    action: "반응표면 설계 설정 열기",
  },
  risk: {
    family: "고장 형태 및 영향 분석 (FMEA)",
    method: "PFMEA 7단계 분석",
    rationale: "공정 흐름·특성·고장 형태·관리 항목을 연결해 위험과 조치 후 근거를 추적합니다.",
    requiredInputs: ["공정 흐름", "제품·공정 특성", "예방·검출 관리"],
    checks: ["조치 우선순위 정책 버전 확인", "SPC·MSA 실행 근거 연결"],
    href: "/fmea",
    action: "FMEA 작업공간 열기",
  },
  improvement: {
    family: "개선 프로젝트 (DMAIC)",
    method: "DMAIC 프로젝트 흐름",
    rationale: "분석 결과를 문제 정의, 측정 근거, 원인 검증, 개선안과 관리계획으로 운영합니다.",
    requiredInputs: ["문제와 고객 요구", "기준 지표", "프로젝트 범위와 책임자"],
    checks: ["단계별 완료 기준 합의", "분석 실행 ID와 문서 개정 연결"],
    href: "/home/dmaic/project",
    action: "DMAIC 프로젝트 열기",
  },
};

const stabilityRecommendations: Record<SamplingStructure, AnalysisRecommendation> = {
  individual: {
    family: "통계적 공정관리 (SPC)", method: "I-MR 관리도", rationale: "한 시점에 하나씩 수집한 연속형 측정값의 중심과 단기 변동을 함께 감시합니다.",
    requiredInputs: ["시간 순서의 측정값", "합리적인 사건·시간 순서"], checks: ["연속된 두 값의 이동범위 사용", "자기상관과 측정시스템 확인"], href: "/analyses/imr/new", action: "I-MR 분석 설정 열기",
  },
  "small-subgroup": {
    family: "통계적 공정관리 (SPC)", method: "Xbar-R 관리도", rationale: "크기 2~10의 작은 부분군에서 평균과 범위를 함께 감시합니다.",
    requiredInputs: ["시간 순서의 부분군", "부분군별 연속형 측정값"], checks: ["부분군 내 조건을 최대한 동일하게 유지", "부분군 크기와 관리도 상수 확인"], href: "/analyses/spc/xbar-r", action: "Xbar-R 분석 설정 열기",
  },
  "large-subgroup": {
    family: "통계적 공정관리 (SPC)", method: "Xbar-S 관리도", rationale: "비교적 큰 부분군의 평균과 표준편차를 함께 감시합니다.",
    requiredInputs: ["시간 순서의 부분군", "부분군별 연속형 측정값"], checks: ["부분군 크기 9 이상 권장", "부분군별 표준편차 추정의 안정성 확인"], href: "/analyses/spc/xbar-s", action: "Xbar-S 분석 설정 열기",
  },
  "small-shift": {
    family: "통계적 공정관리 (SPC)", method: "EWMA 관리도", rationale: "최근 관측값에 더 큰 가중치를 주어 작고 지속적인 평균 이동을 탐지합니다.",
    requiredInputs: ["시간 순서의 연속형 측정값", "기준 평균과 sigma"], checks: ["lambda와 L의 출처 기록", "기준 구간의 안정성 확인"], href: "/analyses/spc/ewma", action: "EWMA 분석 설정 열기",
  },
  "fixed-opportunity": {
    family: "통계적 공정관리 (SPC)", method: "np 관리도", rationale: "검사 수가 일정할 때 부적합품 개수의 변화를 감시합니다.",
    requiredInputs: ["부분군별 부적합품 수", "고정 검사 수"], checks: ["각 단위의 판정 기준 일관성", "부적합품 수가 검사 수를 넘지 않는지 확인"], href: "/analyses/spc/attribute?chart=np", action: "np 관리도 설정 열기",
  },
  "varying-opportunity": {
    family: "통계적 공정관리 (SPC)", method: "p 관리도", rationale: "부분군마다 검사 수가 다를 때 부적합품 비율을 감시합니다.",
    requiredInputs: ["부분군별 부적합품 수", "부분군별 검사 수"], checks: ["표본 크기에 따라 관리한계가 달라짐", "0과 1 사이 비율 계약 확인"], href: "/analyses/spc/attribute?chart=p", action: "p 관리도 설정 열기",
  },
  "rare-opportunity": {
    family: "통계적 공정관리 (SPC)", method: "G 관리도", rationale: "희귀 사건 사이의 기회 수를 감시합니다.",
    requiredInputs: ["사건 사이의 기회 수", "고정된 사건 정의"], checks: ["0보다 큰 정수 입력", "기회 단위를 분석 전 고정"], href: "/analyses/spc/rare-events?chart=g", action: "G 관리도 설정 열기",
  },
  "rare-time": {
    family: "통계적 공정관리 (SPC)", method: "T 관리도", rationale: "희귀 사건 사이의 경과 시간을 감시합니다.",
    requiredInputs: ["사건 사이의 양의 경과 시간", "고정된 시간 단위"], checks: ["시간 단위를 혼합하지 않음", "휴지 시간 포함 기준 명시"], href: "/analyses/spc/rare-events?chart=t", action: "T 관리도 설정 열기",
  },
};

export function recommendAnalysis(goal: AnalysisGoal, sampling: SamplingStructure, dataType: StabilityDataType = "continuous"): AnalysisRecommendation {
  if (goal !== "stability") return workflowRecommendations[goal];
  if (dataType === "defects") {
    return sampling === "fixed-opportunity"
      ? {
          family: "통계적 공정관리 (SPC)", method: "c 관리도", rationale: "검사 기회나 단위가 일정할 때 단위별 결점 수를 감시합니다.",
          requiredInputs: ["부분군별 결점 수", "고정된 검사 기회·단위"], checks: ["한 단위에 여러 결점 허용", "검사 영역과 기회를 동일하게 유지"], href: "/analyses/spc/attribute?chart=c", action: "c 관리도 설정 열기",
        }
      : {
          family: "통계적 공정관리 (SPC)", method: "u 관리도", rationale: "검사 기회나 단위 수가 달라질 때 단위당 결점률을 감시합니다.",
          requiredInputs: ["부분군별 결점 수", "부분군별 검사 기회·단위 수"], checks: ["표본 크기에 따라 관리한계가 달라짐", "기회 단위 정의를 일관되게 유지"], href: "/analyses/spc/attribute?chart=u", action: "u 관리도 설정 열기",
        };
  }
  return stabilityRecommendations[sampling];
}

export function defaultSamplingFor(dataType: StabilityDataType): SamplingStructure {
  if (dataType === "continuous") return "small-subgroup";
  if (dataType === "rare") return "rare-opportunity";
  return "varying-opportunity";
}
