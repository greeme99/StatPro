import { ArrowRight, CheckCircle2, ClipboardCheck, Route, ShieldCheck } from "lucide-react";
import { useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { defaultSamplingFor, recommendAnalysis, type AnalysisGoal, type SamplingStructure, type StabilityDataType } from "../analysisSelection";

const goals: { value: AnalysisGoal; title: string; detail: string }[] = [
  { value: "stability", title: "공정 안정성 감시", detail: "시간에 따른 변동과 이상 신호를 관리도로 확인" },
  { value: "capability", title: "규격 충족 능력 평가", detail: "규격 대비 산포·중심·불량 PPM을 평가" },
  { value: "measurement", title: "측정시스템 신뢰성 평가", detail: "측정 변동이 공정 판단에 적합한지 확인" },
  { value: "screening", title: "중요 인자 선별", detail: "많은 후보 인자에서 영향이 큰 인자를 좁힘" },
  { value: "optimization", title: "조건 최적화", detail: "곡률과 상호작용을 모델링해 목표 조건 탐색" },
  { value: "risk", title: "공정 위험 관리", detail: "고장 형태와 예방·검출 조치를 추적" },
  { value: "improvement", title: "개선 프로젝트 운영", detail: "분석과 조치를 DMAIC 단계로 연결" },
];

const dataTypes: { value: StabilityDataType; title: string; detail: string }[] = [
  { value: "continuous", title: "연속형 측정값", detail: "치수, 중량, 온도, 시간 등" },
  { value: "defective", title: "부적합품", detail: "단위별 합격·불합격 판정" },
  { value: "defects", title: "결점 수", detail: "한 단위에 여러 결점이 발생 가능" },
  { value: "rare", title: "희귀 사건 간격", detail: "고장·사고 사이 기회 수 또는 시간" },
];

const samplingOptions: Record<StabilityDataType, { value: SamplingStructure; title: string }[]> = {
  continuous: [
    { value: "individual", title: "개별값(부분군 없음)" },
    { value: "small-subgroup", title: "작은 부분군(2~10)" },
    { value: "large-subgroup", title: "큰 부분군(9 이상)" },
    { value: "small-shift", title: "작은 평균 이동 탐지" },
  ],
  defective: [{ value: "varying-opportunity", title: "검사 수가 매번 다름" }, { value: "fixed-opportunity", title: "검사 수가 일정함" }],
  defects: [{ value: "varying-opportunity", title: "기회·단위 수가 매번 다름" }, { value: "fixed-opportunity", title: "기회·단위 수가 일정함" }],
  rare: [{ value: "rare-opportunity", title: "사건 사이 기회 수" }, { value: "rare-time", title: "사건 사이 경과 시간" }],
};

type AnalysisEntry = { title: string; detail: string; to: string };
type AnalysisGroup = { id: string; title: string; detail: string; items: AnalysisEntry[] };

const analysisGroups: AnalysisGroup[] = [
  {
    id: "summary",
    title: "데이터 요약·가정",
    detail: "분포와 기초 특성을 먼저 확인합니다.",
    items: [
      { title: "정규성 검정", detail: "측정값의 정규성 가정을 Jarque–Bera 검정으로 점검합니다.", to: "/analyses/normality" },
      { title: "기초통계", detail: "연속형 데이터의 중심·산포·사분위수와 평균 신뢰구간을 요약합니다.", to: "/analyses/descriptive-statistics" },
    ],
  },
  {
    id: "hypothesis",
    title: "가설검정",
    detail: "평균·비율·분포 차이와 연관성을 검증합니다.",
    items: [
      { title: "단일 표본 t-검정", detail: "공정 평균을 사전 정의한 목표값과 비교합니다.", to: "/analyses/hypothesis/one-sample-t" },
      { title: "단일 비율 검정", detail: "불량률을 목표 불량률과 비교하고 Wilson 신뢰구간을 확인합니다.", to: "/analyses/hypothesis/one-sample-proportion" },
      { title: "두 비율 비교", detail: "두 생산라인 또는 개선 전후의 불량률 차이를 검증합니다.", to: "/analyses/hypothesis/two-sample-proportion" },
      { title: "독립표본 t-검정", detail: "독립 두 집단의 평균차를 Welch 방법으로 비교합니다.", to: "/analyses/hypothesis/independent-welch-t" },
      { title: "등가성 검정 (TOST)", detail: "사전 정의한 허용차 안에서 두 집단 평균이 실질적으로 같은지 확인합니다.", to: "/analyses/hypothesis/independent-tost-equivalence" },
      { title: "Mann–Whitney U 검정", detail: "정규성 가정이 어려운 독립 두 집단을 순위로 비교합니다.", to: "/analyses/hypothesis/mann-whitney-u" },
      { title: "대응표본 t-검정", detail: "같은 대상의 전후 또는 짝지어진 두 측정값 차이를 비교합니다.", to: "/analyses/hypothesis/paired-t" },
      { title: "Kruskal–Wallis 검정", detail: "세 집단 이상을 순위로 비교하는 비모수 검정입니다.", to: "/analyses/hypothesis/kruskal-wallis" },
      { title: "Wilcoxon 부호순위 검정", detail: "정규성 가정이 어려운 대응 측정값을 순위로 비교합니다.", to: "/analyses/hypothesis/wilcoxon-signed-rank" },
      { title: "카이제곱 독립성 검정", detail: "두 범주형 변수의 연관성을 분할표로 확인합니다.", to: "/analyses/hypothesis/chi-square-independence" },
      { title: "일원 분산분석", detail: "세 개 이상 독립 집단의 평균을 비교합니다.", to: "/analyses/hypothesis/one-way-anova" },
    ],
  },
  {
    id: "power",
    title: "검정력·표본수 계획",
    detail: "검출 목표에 필요한 표본 수를 분석 전에 계획합니다.",
    items: [
      { title: "표본크기 계획", detail: "독립 두 집단 평균 비교에 필요한 표본 수를 사전에 산정합니다.", to: "/analyses/power/two-sample-mean" },
      { title: "두 비율 표본수 계획", detail: "두 생산라인의 예상 불량률 차이를 검출할 검사 수를 사전에 산정합니다.", to: "/analyses/power/two-sample-proportion" },
      { title: "단일 비율 표본수 계획", detail: "목표 불량률과 검출하려는 불량률 차이에 필요한 검사 수를 산정합니다.", to: "/analyses/power/one-sample-proportion" },
      { title: "대응 평균 표본수 계획", detail: "같은 설비·제품의 개선 전후 차이를 검출할 필요한 쌍 수를 산정합니다.", to: "/analyses/power/paired-mean" },
      { title: "ANOVA 검정력·표본수 계획", detail: "세 집단 이상 평균의 전체 차이를 검출할 균형 표본 수를 산정합니다.", to: "/analyses/power/one-way-anova" },
    ],
  },
  {
    id: "regression",
    title: "회귀·예측",
    detail: "연속형·범주형·건수 결과와 설명변수의 관계를 모델링합니다.",
    items: [
      { title: "선형회귀 분석", detail: "연속형 결과(Y)와 하나 이상의 설명변수(X) 관계를 추정합니다.", to: "/analyses/regression/linear" },
      { title: "다항회귀 분석", detail: "관측 범위 안에서 곡선형 X–Y 관계를 2차 또는 3차 항으로 추정합니다.", to: "/analyses/regression/polynomial" },
      { title: "교호작용 회귀 분석", detail: "두 X의 결합 효과가 연속형 결과(Y)에 미치는 변화를 추정합니다.", to: "/analyses/regression/interaction" },
      { title: "단계선택 회귀", detail: "AICc 기준으로 계층성을 지키며 설명변수 후보를 탐색합니다.", to: "/analyses/regression/stepwise" },
      { title: "회귀 모형 검증", detail: "홀드아웃 또는 k-fold로 새 관측값에 대한 예측오차를 점검합니다.", to: "/analyses/regression/validation" },
      { title: "최적 부분집합 회귀", detail: "모든 X 조합을 AICc·BIC·PRESS·Cp로 비교합니다.", to: "/analyses/regression/best-subsets" },
      { title: "정규화 회귀", detail: "Ridge·Lasso·Elastic Net을 교차검증으로 비교해 공선성을 완화합니다.", to: "/analyses/regression/regularized" },
      { title: "범주형 OLS 회귀", detail: "라인·설비 등 범주형 X를 기준 범주와 비교해 연속형 결과(Y)를 추정합니다.", to: "/analyses/regression/categorical-ols" },
      { title: "Poisson 회귀", detail: "불량·고장 등 비음수 정수 건수(Y)의 발생률을 설명합니다.", to: "/analyses/regression/poisson" },
      { title: "음이항 회귀", detail: "과산포가 있는 비음수 정수 건수(Y)의 발생률을 NB2 분산모형으로 추정합니다.", to: "/analyses/regression/negative-binomial" },
      { title: "로지스틱 회귀", detail: "합격·불합격 등 0/1 결과(Y)의 발생확률을 추정합니다.", to: "/analyses/regression/logistic" },
    ],
  },
];

export function AnalysisSelectionPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const worksheetId = searchParams.get("worksheet");
  const worksheetRevision = searchParams.get("revision");
  const [goal, setGoal] = useState<AnalysisGoal>(() => searchParams.get("goal") === "capability" ? "capability" : "stability");
  const [dataType, setDataType] = useState<StabilityDataType>("continuous");
  const [sampling, setSampling] = useState<SamplingStructure>("small-subgroup");
  const [analysisQuery, setAnalysisQuery] = useState(() => searchParams.get("analysis") ?? "");
  const [openAnalysisGroups, setOpenAnalysisGroups] = useState(() => {
    if (searchParams.get("analysisGroups") === "none") return new Set<string>();
    const saved = searchParams.get("analysisGroups")?.split(",").filter((id) => analysisGroups.some((group) => group.id === id));
    return new Set(saved?.length ? saved : analysisGroups.map((group) => group.id));
  });
  const recommendation = useMemo(() => recommendAnalysis(goal, sampling, dataType), [dataType, goal, sampling]);
  const filteredAnalysisGroups = useMemo(() => {
    const query = analysisQuery.trim().toLocaleLowerCase("ko-KR");
    if (!query) return analysisGroups;
    return analysisGroups
      .map((group) => ({ ...group, items: group.items.filter((item) => `${item.title} ${item.detail}`.toLocaleLowerCase("ko-KR").includes(query)) }))
      .filter((group) => group.items.length > 0);
  }, [analysisQuery]);
  const analysisResultCount = filteredAnalysisGroups.reduce((count, group) => count + group.items.length, 0);

  function updateAnalysisLocation(query: string, groups: Set<string>) {
    const next = new URLSearchParams(searchParams);
    if (query) next.set("analysis", query); else next.delete("analysis");
    const groupIds = [...groups];
    if (groupIds.length === analysisGroups.length) next.delete("analysisGroups");
    else if (groupIds.length) next.set("analysisGroups", groupIds.join(","));
    else next.set("analysisGroups", "none");
    setSearchParams(next, { replace: true });
  }

  function changeAnalysisQuery(query: string) {
    setAnalysisQuery(query);
    updateAnalysisLocation(query, openAnalysisGroups);
  }

  function toggleAnalysisGroup(groupId: string) {
    const next = new Set(openAnalysisGroups);
    if (next.has(groupId)) next.delete(groupId); else next.add(groupId);
    setOpenAnalysisGroups(next);
    updateAnalysisLocation(analysisQuery, next);
  }

  function selectDataType(next: StabilityDataType) {
    setDataType(next);
    setSampling(defaultSamplingFor(next));
  }

  return (
    <div className="page analysis-selection-page" data-density="comfortable">
      <nav className="breadcrumb" aria-label="경로"><Link to="/home">홈 (Home)</Link><span>분석 선택 (Analysis Selection)</span></nav>
      <header className="analysis-selection-hero">
        <div><span className="eyebrow">Workspace → Workflow</span><h1>통합 분석 추천</h1><p>현장의 판단 목적과 데이터 구조를 선택하면 SPC, 공정능력, MSA, DOE, FMEA, DMAIC 작업공간과 분석 전 확인사항을 제안합니다.</p></div>
        <Route aria-hidden="true" />
      </header>

      {worksheetId && <aside className="method-note workflow-source-context" aria-label="선택한 작업표 맥락"><strong>선택한 작업표</strong><p><code>{worksheetId}</code>{worksheetRevision ? ` · revision ${worksheetRevision}` : ""}에서 분석 목적을 고릅니다. 이 단계는 원본 값을 자동 전송하지 않으므로, 다음 화면에서 사용할 열과 측정값을 검토해 명시적으로 입력하세요.</p></aside>}

      <ol className="analysis-selection-rail" aria-label="분석 선택 단계">
        <li className="is-active"><span>1</span><strong>판단 목적</strong></li><li className={goal === "stability" ? "is-active" : ""}><span>2</span><strong>데이터 유형</strong></li><li className={goal === "stability" ? "is-active" : ""}><span>3</span><strong>수집 구조</strong></li><li className="is-active"><span>4</span><strong>추천·실행</strong></li>
      </ol>

      <section className="analysis-question-panel" aria-labelledby="goal-title">
        <header><span className="eyebrow">질문 1</span><h2 id="goal-title">지금 내려야 할 판단은 무엇입니까?</h2></header>
        <div className="analysis-choice-grid">
          {goals.map((item) => <button className={goal === item.value ? "analysis-choice is-selected" : "analysis-choice"} type="button" key={item.value} aria-pressed={goal === item.value} onClick={() => setGoal(item.value)}><strong>{item.title}</strong><span>{item.detail}</span></button>)}
        </div>
      </section>

      {goal === "stability" && <>
        <section className="analysis-question-panel" aria-labelledby="data-title">
          <header><span className="eyebrow">질문 2</span><h2 id="data-title">어떤 데이터를 감시합니까?</h2></header>
          <div className="analysis-choice-grid is-compact">
            {dataTypes.map((item) => <button className={dataType === item.value ? "analysis-choice is-selected" : "analysis-choice"} type="button" key={item.value} aria-pressed={dataType === item.value} onClick={() => selectDataType(item.value)}><strong>{item.title}</strong><span>{item.detail}</span></button>)}
          </div>
        </section>
        <section className="analysis-question-panel" aria-labelledby="sampling-title">
          <header><span className="eyebrow">질문 3</span><h2 id="sampling-title">데이터는 어떤 구조로 수집됩니까?</h2></header>
          <div className="analysis-choice-grid is-compact">
            {samplingOptions[dataType].map((item) => <button className={sampling === item.value ? "analysis-choice is-selected" : "analysis-choice"} type="button" key={item.value} aria-pressed={sampling === item.value} onClick={() => setSampling(item.value)}><strong>{item.title}</strong></button>)}
          </div>
        </section>
      </>}

      <section className="analysis-question-panel basic-analysis-panel" aria-labelledby="basic-analysis-title">
        <header><span className="eyebrow">기본 분석 작업공간</span><h2 id="basic-analysis-title">데이터 가정과 변수 관계를 먼저 확인합니다</h2></header>
        <div className="analysis-finder">
          <label className="field"><span>분석 항목 검색</span><input type="search" value={analysisQuery} onChange={(event) => changeAnalysisQuery(event.target.value)} placeholder="예: 불량률, 회귀, 표본수" /></label>
          <p aria-live="polite">전체 29개 중 {analysisResultCount}개 표시</p>
          {analysisQuery && <button className="button" type="button" onClick={() => changeAnalysisQuery("")}>검색 초기화</button>}
        </div>
        {analysisResultCount ? <div className="analysis-groups">
          {filteredAnalysisGroups.map((group) => <section className="analysis-group" key={group.id}>
            <header><button type="button" aria-expanded={openAnalysisGroups.has(group.id)} aria-controls={`analysis-group-${group.id}`} onClick={() => toggleAnalysisGroup(group.id)}><span><h3>{group.title}</h3><p>{group.detail}</p></span><span>{group.items.length}개</span></button></header>
            {openAnalysisGroups.has(group.id) && <div id={`analysis-group-${group.id}`} className="analysis-choice-grid is-compact">
              {group.items.map((item) => <Link className="analysis-choice" to={item.to} key={item.to}><strong>{item.title}</strong><span>{item.detail}</span></Link>)}
            </div>}
          </section>)}
        </div> : <div className="state-message analysis-empty"><strong>검색 결과가 없습니다.</strong><span>다른 용어를 입력하거나 검색을 초기화하세요.</span><button className="button" type="button" onClick={() => changeAnalysisQuery("")}>검색 초기화</button></div>}
      </section>

      <section className="analysis-recommendation" aria-live="polite" aria-labelledby="recommendation-title">
        <header><span className="recommendation-icon"><ClipboardCheck aria-hidden="true" /></span><div><span className="eyebrow">추천 작업공간</span><h2 id="recommendation-title">{recommendation.method}</h2><p>{recommendation.family}</p></div></header>
        <p className="recommendation-rationale">{recommendation.rationale}</p>
        <div className="recommendation-details">
          <div><h3><CheckCircle2 aria-hidden="true" /> 필요한 입력</h3><ul>{recommendation.requiredInputs.map((item) => <li key={item}>{item}</li>)}</ul></div>
          <div><h3><ShieldCheck aria-hidden="true" /> 분석 전 확인</h3><ul>{recommendation.checks.map((item) => <li key={item}>{item}</li>)}</ul></div>
        </div>
        <Link className="primary-link" to={worksheetId ? `${recommendation.href}?worksheet=${encodeURIComponent(worksheetId)}${worksheetRevision ? `&revision=${encodeURIComponent(worksheetRevision)}` : ""}` : recommendation.href}>{recommendation.action} <ArrowRight aria-hidden="true" /></Link>
      </section>
    </div>
  );
}
