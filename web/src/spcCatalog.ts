import {
  BarChart3,
  ClipboardList,
  Fish,
  Layers3,
  ScatterChart,
  SlidersHorizontal,
  TrendingUp,
  type LucideIcon,
} from "lucide-react";

export type SpcTool = {
  id: string;
  title: string;
  english: string;
  purpose: string;
  fieldUse: string;
  route: string;
  icon: LucideIcon;
  workflow: string[];
};

export const spcTools: SpcTool[] = [
  {
    id: "check-sheet",
    title: "체크 시트",
    english: "Check Sheet",
    purpose: "불량·위치·원인·시간 정보를 같은 기준으로 빠짐없이 수집합니다.",
    fieldUse: "현장 기록 양식을 표준화하거나 결함 발생 패턴을 처음 파악할 때",
    route: "/spc/tools/check-sheet",
    icon: ClipboardList,
    workflow: ["수집 항목 정의", "현장 기록", "빈도 집계", "후속 분석 연결"],
  },
  {
    id: "histogram",
    title: "히스토그램",
    english: "Histogram",
    purpose: "측정값의 분포, 중심, 산포와 규격 적합 가능성을 확인합니다.",
    fieldUse: "공정 데이터의 치우침·다봉성·이상값을 확인하고 관리도 전제를 검토할 때",
    route: "/spc/tools/histogram",
    icon: BarChart3,
    workflow: ["측정값 선택", "구간 설정", "분포 확인", "규격·층별 비교"],
  },
  {
    id: "stratification",
    title: "계층화",
    english: "Stratification",
    purpose: "설비·작업자·로트·시간대별로 데이터를 나눠 숨은 차이를 찾습니다.",
    fieldUse: "전체 데이터에서는 보이지 않는 특정 조건의 반복 문제를 확인할 때",
    route: "/spc/tools/stratification",
    icon: Layers3,
    workflow: ["층별 변수 선택", "그룹 분리", "차이 비교", "원인 후보 확정"],
  },
  {
    id: "scatter-diagram",
    title: "산점도",
    english: "Scatter Diagram",
    purpose: "두 변수의 방향·강도·형태를 시각화해 관계 가설을 점검합니다.",
    fieldUse: "공정 인자와 품질 특성 사이의 연관성을 먼저 탐색할 때",
    route: "/spc/tools/scatter-diagram",
    icon: ScatterChart,
    workflow: ["X·Y 선택", "산점 확인", "상관 검토", "시험 가설 연결"],
  },
  {
    id: "fishbone",
    title: "특성요인도",
    english: "Fishbone Diagram",
    purpose: "사람·설비·재료·방법 등 원인 후보를 구조화해 누락 없이 검토합니다.",
    fieldUse: "문제의 잠재 원인을 팀과 함께 발산하고 검증 대상을 정할 때",
    route: "/spc/tools/fishbone",
    icon: Fish,
    workflow: ["문제 정의", "원인 범주화", "세부 원인 전개", "검증 과제 선정"],
  },
  {
    id: "pareto-chart",
    title: "파레토 차트",
    english: "Pareto Chart",
    purpose: "빈도·손실을 내림차순과 누적 비율로 비교해 핵심 소수를 찾습니다.",
    fieldUse: "제한된 자원으로 먼저 해결할 결함·원인·고객 불만을 정할 때",
    route: "/spc/tools/pareto-chart",
    icon: TrendingUp,
    workflow: ["분류 기준 선택", "빈도·손실 집계", "누적 비율 확인", "우선순위 확정"],
  },
  {
    id: "control-chart",
    title: "관리도",
    english: "Control Chart",
    purpose: "시간 순서의 중심선과 관리한계로 일반원인과 특별원인 변동을 구분합니다.",
    fieldUse: "공정 안정성을 지속 감시하고 이상 신호를 현장 조치로 연결할 때",
    route: "/spc/control-charts",
    icon: SlidersHorizontal,
    workflow: ["데이터 유형 판단", "관리도 선택", "시간순 데이터 입력", "신호 해석·조치"],
  },
];

export type ControlChartGroup = {
  id: "variables" | "attributes";
  title: string;
  english: string;
  description: string;
  selectionRule: string;
  charts: {
    title: string;
    description: string;
    whenToUse: string;
    route: string;
  }[];
};

export const controlChartGroups: ControlChartGroup[] = [
  {
    id: "variables",
    title: "계량형",
    english: "Variables",
    description: "길이·두께·온도·중량처럼 연속적인 측정값을 관리합니다.",
    selectionRule: "부분군 크기와 작은 평균 이동의 탐지 필요성을 기준으로 선택합니다.",
    charts: [
      { title: "Xbar-R", description: "부분군 평균과 범위를 함께 감시합니다.", whenToUse: "작은 합리적 부분군(보통 2~10개)", route: "/analyses/spc/xbar-r" },
      { title: "Xbar-S", description: "부분군 평균과 표준편차를 함께 감시합니다.", whenToUse: "큰 부분군(통상 9개 이상)", route: "/analyses/spc/xbar-s" },
      { title: "I-MR", description: "개별값과 인접 측정값의 이동범위를 감시합니다.", whenToUse: "부분군을 만들기 어려운 개별 측정", route: "/analyses/imr/new" },
      { title: "EWMA", description: "최근 관측값에 가중치를 둬 작고 지속적인 이동을 탐지합니다.", whenToUse: "작은 평균 이동을 민감하게 탐지", route: "/analyses/spc/ewma" },
      { title: "CUSUM", description: "목표로부터의 편차를 누적해 지속적인 이동을 탐지합니다.", whenToUse: "목표 평균 대비 미세한 공정 이동", route: "/analyses/spc/cusum" },
    ],
  },
  {
    id: "attributes",
    title: "계수형",
    english: "Attributes",
    description: "합격·불합격 또는 결점 개수처럼 세어서 얻는 데이터를 관리합니다.",
    selectionRule: "부적합품인지 결점인지, 표본 크기·검사 기회가 고정인지에 따라 선택합니다.",
    charts: [
      { title: "p", description: "부분군별 부적합품 비율을 감시합니다.", whenToUse: "표본 크기가 달라지는 합격·불합격 데이터", route: "/analyses/spc/attribute?chart=p" },
      { title: "np", description: "부분군별 부적합품 수를 감시합니다.", whenToUse: "표본 크기가 일정한 합격·불합격 데이터", route: "/analyses/spc/attribute?chart=np" },
      { title: "c", description: "고정된 검사 기회에서 결점 수를 감시합니다.", whenToUse: "면적·시간·단위가 일정한 결점 데이터", route: "/analyses/spc/attribute?chart=c" },
      { title: "u", description: "검사 단위당 결점 수를 감시합니다.", whenToUse: "검사 기회가 달라지는 결점 데이터", route: "/analyses/spc/attribute?chart=u" },
      { title: "Laney P′", description: "p 관리도의 과산포·과소산포를 보정합니다.", whenToUse: "큰 표본에서 일반 p 관리도의 오경보가 우려될 때", route: "/analyses/spc/attribute?chart=p_prime" },
      { title: "Laney U′", description: "u 관리도의 과산포·과소산포를 보정합니다.", whenToUse: "결점률 변동이 포아송 가정보다 크거나 작을 때", route: "/analyses/spc/attribute?chart=u_prime" },
      { title: "G/T", description: "희귀사건 사이의 기회 수 또는 시간을 감시합니다.", whenToUse: "불량·사고가 드물어 일반 계수형 관리도가 둔감할 때", route: "/analyses/spc/rare-events" },
    ],
  },
];
