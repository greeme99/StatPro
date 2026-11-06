import { ArrowRight, CheckCircle2, ClipboardCheck, Route, ShieldCheck } from "lucide-react";
import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { defaultSamplingFor, recommendAnalysis, type AnalysisGoal, type SamplingStructure, type StabilityDataType } from "../analysisSelection";

const goals: { value: AnalysisGoal; title: string; detail: string }[] = [
  { value: "stability", title: "공정 안정성 감시", detail: "시간에 따른 변동과 이상 신호를 관리도로 확인" },
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

export function AnalysisSelectionPage() {
  const [goal, setGoal] = useState<AnalysisGoal>("stability");
  const [dataType, setDataType] = useState<StabilityDataType>("continuous");
  const [sampling, setSampling] = useState<SamplingStructure>("small-subgroup");
  const recommendation = useMemo(() => recommendAnalysis(goal, sampling, dataType), [dataType, goal, sampling]);

  function selectDataType(next: StabilityDataType) {
    setDataType(next);
    setSampling(defaultSamplingFor(next));
  }

  return (
    <div className="page analysis-selection-page" data-density="comfortable">
      <nav className="breadcrumb" aria-label="경로"><Link to="/home">홈 (Home)</Link><span>분석 선택 (Analysis Selection)</span></nav>
      <header className="analysis-selection-hero">
        <div><span className="eyebrow">Workspace → Workflow</span><h1>분석 선택 도우미 (Analysis Selection Assistant)</h1><p>현장의 판단 목적과 데이터 구조를 선택하면, 현재 실행 가능한 StatPro 작업공간과 분석 전 확인사항을 제안합니다.</p></div>
        <Route aria-hidden="true" />
      </header>

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

      <section className="analysis-recommendation" aria-live="polite" aria-labelledby="recommendation-title">
        <header><span className="recommendation-icon"><ClipboardCheck aria-hidden="true" /></span><div><span className="eyebrow">추천 작업공간</span><h2 id="recommendation-title">{recommendation.method}</h2><p>{recommendation.family}</p></div></header>
        <p className="recommendation-rationale">{recommendation.rationale}</p>
        <div className="recommendation-details">
          <div><h3><CheckCircle2 aria-hidden="true" /> 필요한 입력</h3><ul>{recommendation.requiredInputs.map((item) => <li key={item}>{item}</li>)}</ul></div>
          <div><h3><ShieldCheck aria-hidden="true" /> 분석 전 확인</h3><ul>{recommendation.checks.map((item) => <li key={item}>{item}</li>)}</ul></div>
        </div>
        <Link className="primary-link" to={recommendation.href}>{recommendation.action} <ArrowRight aria-hidden="true" /></Link>
      </section>
    </div>
  );
}
