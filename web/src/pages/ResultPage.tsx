import { AlertTriangle, ArrowLeft, BookOpen, CheckCircle2, X } from "lucide-react";
import { lazy, Suspense, useEffect, useMemo, useRef, useState } from "react";
import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom";
import { getRun } from "../api";
import { toAttributeChartView, toDoeBoxBehnkenAnalysisView, toDoeBoxBehnkenView, toDoeCentralCompositeAnalysisView, toDoeCentralCompositeSurfaceView, toDoeCentralCompositeView, toDoeDesirabilityView, toDoeFractionalAnalysisView, toDoeFractionalView, toDoePlackettBurmanAnalysisView, toDoePlackettBurmanView, toDoeView, toEwmaView, toImrView, toXbarSView, type AttributeChartView, type DoeBoxBehnkenView, type DoeCentralCompositeSurfaceView, type DoeCentralCompositeView, type DoeDesirabilityView, type DoeFractionalAnalysisView, type DoeFractionalView, type DoePlackettBurmanAnalysisView, type DoePlackettBurmanView, type DoeQuadraticAnalysisView, type DoeView, type EwmaView, type XbarSView } from "../analysis";
import { Button } from "../components/Button";
import type { StoredRun } from "../types";

const ProcessRail = lazy(() => import("../components/ProcessRail").then((module) => ({ default: module.ProcessRail })));
const AttributeControlChart = lazy(() => import("../components/AttributeControlChart").then((module) => ({ default: module.AttributeControlChart })));
const EwmaControlChart = lazy(() => import("../components/EwmaControlChart").then((module) => ({ default: module.EwmaControlChart })));

export function ResultPage() {
  const { runId = "" } = useParams();
  const [run, setRun] = useState<StoredRun | null>(null);
  const [state, setState] = useState<"loading" | "ready" | "error">("loading");
  const [search, setSearch] = useSearchParams();
  const closeButton = useRef<HTMLButtonElement>(null);
  const drawer = useRef<HTMLElement>(null);
  const drawerTrigger = useRef<HTMLButtonElement>(null);
  const drawerOpen = search.get("detail") === "provenance";
  const navigate = useNavigate();

  useEffect(() => {
    getRun(runId).then((value) => { setRun(value); setState("ready"); }).catch(() => setState("error"));
  }, [runId]);

  useEffect(() => {
    if (!drawerOpen) return;
    closeButton.current?.focus();
    const listener = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setSearch({});
        drawerTrigger.current?.focus();
        return;
      }
      if (event.key !== "Tab") return;
      const focusable = drawer.current?.querySelectorAll<HTMLElement>("button, a[href], input, select, textarea, [tabindex]:not([tabindex='-1'])");
      if (!focusable?.length) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
    };
    document.addEventListener("keydown", listener);
    return () => document.removeEventListener("keydown", listener);
  }, [drawerOpen, setSearch]);

  const result = run?.result;
  const imr = toImrView(result);
  const attributeChart = toAttributeChartView(result);
  const xbarS = toXbarSView(result);
  const ewma = toEwmaView(result);
  const doe = toDoeView(result);
  const optimizer = toDoeDesirabilityView(result);
  const fractional = toDoeFractionalView(result);
  const fractionalAnalysis = toDoeFractionalAnalysisView(result);
  const centralComposite = toDoeCentralCompositeView(result);
  const boxBehnken = toDoeBoxBehnkenView(result);
  const boxBehnkenAnalysis = toDoeBoxBehnkenAnalysisView(result);
  const centralCompositeAnalysis = toDoeCentralCompositeAnalysisView(result);
  const centralCompositeSurface = toDoeCentralCompositeSurfaceView(result);
  const plackettBurman = toDoePlackettBurmanView(result);
  const plackettBurmanAnalysis = toDoePlackettBurmanAnalysisView(result);
  const signalCount = useMemo(() => imr?.points.filter((point) => point.signal).length ?? 0, [imr]);
  const closeDrawer = () => { setSearch({}); drawerTrigger.current?.focus(); };

  if (state === "loading") return <div className="page"><div className="skeleton page-skeleton" aria-label="결과 불러오는 중" /></div>;
  if (state === "error" || !run || !result) return <div className="page"><div className="state-message is-error"><AlertTriangle aria-hidden="true" /><h1>결과를 불러오지 못했습니다</h1><p>Run ID를 확인하거나 로컬 API 연결 상태를 점검하세요.</p><Button onClick={() => navigate("/")}>홈으로 이동</Button></div></div>;

  return (
    <div className="page result-page" data-density="compact">
      <Link className="back-link" to="/"><ArrowLeft aria-hidden="true" /> 분석 홈</Link>
      <section className="result-header">
        <div><span className="eyebrow">ANALYSIS RUN / {result.analysis_type}</span><h1>{run.run_id}</h1><p className="digest">SHA-256 · {result.input_digest}</p></div>
        <div className="result-actions"><span className="status-badge is-success"><CheckCircle2 aria-hidden="true" /> 완료</span><Button ref={drawerTrigger} icon={<BookOpen />} onClick={() => setSearch({ detail: "provenance" })}>계산 근거</Button></div>
      </section>
      {imr ? <>
      <section className="metric-grid result-metrics" aria-label="I-MR 결과 요약">
        <article className="metric-card"><span>평균</span><strong>{imr.center.toFixed(3)}</strong><small>개별값 중심선</small></article>
        <article className="metric-card"><span>관리상한 UCL</span><strong>{imr.ucl.toFixed(3)}</strong><small>3-sigma</small></article>
        <article className="metric-card"><span>관리하한 LCL</span><strong>{imr.lcl.toFixed(3)}</strong><small>3-sigma</small></article>
        <article className="metric-card"><span>신호 관측값</span><strong>{signalCount}</strong><small>{signalCount ? "검토 필요" : "신호 없음"}</small></article>
      </section>
      <section className="panel result-chart-panel">
        <header className="panel-heading"><div><span className="eyebrow">INDIVIDUALS CHART</span><h2>개별값 관리도</h2></div><span className="run-version">ENGINE {result.engine_version}</span></header>
        <Suspense fallback={<div className="skeleton chart-skeleton" aria-label="관리도 불러오는 중" />}><ProcessRail points={imr.points} center={imr.center} ucl={imr.ucl} lcl={imr.lcl} /></Suspense>
      </section>
      <section className="panel table-panel">
        <header className="panel-heading"><div><span className="eyebrow">ACCESSIBLE DATA</span><h2>관리도 원본 표</h2></div></header>
        <div className="table-scroll"><table><thead><tr><th scope="col">순서</th><th scope="col">관측값</th><th scope="col">상태</th></tr></thead><tbody>{imr.points.map((point) => <tr key={point.index}><td>{point.index}</td><td>{point.value.toFixed(4)}</td><td>{point.signal ? <span className="status-text is-danger"><AlertTriangle aria-hidden="true" /> {point.rules.length ? point.rules.join(", ") : "3σ 한계 이탈"}</span> : <span className="status-text is-success"><CheckCircle2 aria-hidden="true" /> 정상</span>}</td></tr>)}</tbody></table></div>
      </section>
      </> : ewma ? <EwmaResult view={ewma} /> : xbarS ? <XbarSResult view={xbarS} /> : attributeChart ? <AttributeChartResult view={attributeChart} /> : doe ? <DoeResult doe={doe} /> : optimizer ? <DoeDesirabilityResult optimizer={optimizer} /> : fractional ? <DoeFractionalResult design={fractional} /> : fractionalAnalysis ? <DoeFractionalAnalysisResult analysis={fractionalAnalysis} /> : boxBehnken ? <DoeBoxBehnkenResult design={boxBehnken} /> : boxBehnkenAnalysis ? <DoeQuadraticAnalysisResult analysis={boxBehnkenAnalysis} designLabel="Box–Behnken" methodLabel="Edge-midpoint design" /> : centralComposite ? <DoeCentralCompositeResult design={centralComposite} /> : centralCompositeAnalysis ? <DoeQuadraticAnalysisResult analysis={centralCompositeAnalysis} designLabel="중앙합성" methodLabel={centralCompositeAnalysis.rotatable ? "Rotatable" : "Face-centered"} /> : centralCompositeSurface ? <DoeCentralCompositeSurfaceResult surface={centralCompositeSurface} /> : plackettBurman ? <DoePlackettBurmanResult design={plackettBurman} /> : plackettBurmanAnalysis ? <DoePlackettBurmanAnalysisResult analysis={plackettBurmanAnalysis} /> : <section className="panel generic-result-panel"><header className="panel-heading"><div><span className="eyebrow">RESULT BUNDLE</span><h2>분석 결과 요약</h2></div></header><dl><div><dt>분석 유형</dt><dd>{result.analysis_type}</dd></div><div><dt>진단 항목</dt><dd>{Object.keys(result.diagnostics).length}개</dd></div><div><dt>결과 표</dt><dd>{Object.keys(result.tables).join(", ") || "없음"}</dd></div></dl><p>이 분석의 전용 시각화는 다음 개발 증분에서 제공됩니다. 계산 근거와 원본 ResultBundle은 보존되어 있습니다.</p></section>}
      {result.warnings.length > 0 && <section className="warning-panel"><AlertTriangle aria-hidden="true" /><div><h2>해석 전 확인</h2><ul>{result.warnings.map((warning) => <li key={warning}>{warning}</li>)}</ul></div></section>}
      {drawerOpen && <><button className="drawer-scrim" aria-label="계산 근거 닫기" onClick={closeDrawer} /><aside ref={drawer} className="detail-drawer" role="dialog" aria-modal="true" aria-labelledby="drawer-title"><header><div><span className="eyebrow">EVIDENCE</span><h2 id="drawer-title">계산 근거</h2></div><button ref={closeButton} className="icon-button" aria-label="닫기" onClick={closeDrawer}><X /></button></header><section><h3>분석 가정</h3><ul>{result.assumptions.map((item) => <li key={item}>{item}</li>)}</ul></section><section><h3>공개 출처</h3>{result.provenance.map((source) => <a className="source-link" href={source.url} target="_blank" rel="noreferrer" key={source.url}><strong>{source.title}</strong><span>{source.authority}</span></a>)}</section><section><h3>재현 정보</h3><dl><div><dt>엔진</dt><dd>{result.engine_version}</dd></div><div><dt>Storage version</dt><dd>{run.storage_version}</dd></div><div><dt>ETag</dt><dd className="digest">{run.etag}</dd></div></dl></section></aside></>}
    </div>
  );
}

function statistic(value: number | null, digits = 4) {
  if (value === null) return "—";
  if (!Number.isFinite(value)) return value > 0 ? "∞" : "—";
  return value.toFixed(digits);
}

function EwmaResult({ view }: { view: EwmaView }) {
  const signalCount = view.points.filter((point) => point.signal).length;
  return <>
    <section className="metric-grid result-metrics" aria-label="EWMA 관리도 요약">
      <article className="metric-card"><span>가중치 λ</span><strong>{statistic(view.weight, 3)}</strong><small>최근 관측 가중치</small></article>
      <article className="metric-card"><span>한계 폭 L</span><strong>{statistic(view.limitWidth, 2)}</strong><small>시작 시점 보정</small></article>
      <article className="metric-card"><span>공정 σ</span><strong>{statistic(view.processSigma)}</strong><small>{view.sigmaSource === "historical" ? "과거 기준" : "MRbar / 1.128 추정"}</small></article>
      <article className="metric-card"><span>신호</span><strong>{signalCount}</strong><small>{signalCount ? "조사 필요" : "신호 없음"}</small></article>
    </section>
    <section className="panel result-chart-panel">
      <header className="panel-heading"><div><span className="eyebrow">TIME-WEIGHTED CONTROL CHART</span><h2>EWMA 관리도</h2></div><span>평균 {view.meanSource === "historical" ? "과거 기준" : "현재 자료 추정"}</span></header>
      <Suspense fallback={<div className="skeleton chart-skeleton" aria-label="EWMA 관리도 불러오는 중" />}><EwmaControlChart points={view.points} /></Suspense>
    </section>
    <section className="panel table-panel">
      <header className="panel-heading"><div><span className="eyebrow">ACCESSIBLE DATA</span><h2>EWMA 관측값과 관리한계</h2></div></header>
      <div className="table-scroll"><table><thead><tr><th scope="col">순서</th><th scope="col">관측값</th><th scope="col">EWMA</th><th scope="col">LCL</th><th scope="col">CL</th><th scope="col">UCL</th><th scope="col">상태</th></tr></thead><tbody>{view.points.map((point) => <tr key={point.index}><td>{point.index}</td><td>{statistic(point.observation)}</td><td>{statistic(point.ewma)}</td><td>{statistic(point.lcl)}</td><td>{statistic(point.center)}</td><td>{statistic(point.ucl)}</td><td>{point.signal ? <span className="status-text is-danger"><AlertTriangle aria-hidden="true" /> 관리한계 이탈</span> : <span className="status-text is-success"><CheckCircle2 aria-hidden="true" /> 정상</span>}</td></tr>)}</tbody></table></div>
    </section>
  </>;
}

function XbarSResult({ view }: { view: XbarSView }) {
  return <>
    <section className="metric-grid result-metrics" aria-label="Xbar-S 관리도 요약">
      <article className="metric-card"><span>부분군 크기</span><strong>{view.subgroupSize}</strong><small>부분군당 측정값</small></article>
      <article className="metric-card"><span>추정 σ</span><strong>{statistic(view.estimatedSigma)}</strong><small>Sbar / c4</small></article>
      <article className="metric-card"><span>Xbar 신호</span><strong>{view.xbarPoints.filter((point) => point.signal).length}</strong><small>조사 후보</small></article>
      <article className="metric-card"><span>S 신호</span><strong>{view.sPoints.filter((point) => point.signal).length}</strong><small>변동을 먼저 확인</small></article>
    </section>
    <section className="panel result-chart-panel"><header className="panel-heading"><div><span className="eyebrow">XBAR CHART</span><h2>부분군 평균 관리도</h2></div></header><Suspense fallback={<div className="skeleton chart-skeleton" aria-label="Xbar 관리도 불러오는 중" />}><ProcessRail points={view.xbarPoints} center={view.xbarLimits.center} ucl={view.xbarLimits.ucl} lcl={view.xbarLimits.lcl} /></Suspense></section>
    <section className="panel result-chart-panel"><header className="panel-heading"><div><span className="eyebrow">S CHART</span><h2>부분군 표준편차 관리도</h2></div></header><Suspense fallback={<div className="skeleton chart-skeleton" aria-label="S 관리도 불러오는 중" />}><ProcessRail points={view.sPoints} center={view.sLimits.center} ucl={view.sLimits.ucl} lcl={view.sLimits.lcl} /></Suspense></section>
    <section className="panel table-panel"><header className="panel-heading"><div><span className="eyebrow">ACCESSIBLE DATA</span><h2>Xbar-S 부분군 표</h2></div></header><div className="table-scroll"><table><thead><tr><th scope="col">부분군</th><th scope="col">평균</th><th scope="col">표준편차</th><th scope="col">상태</th></tr></thead><tbody>{view.xbarPoints.map((point, index) => <tr key={point.index}><td>{point.index}</td><td>{statistic(point.value)}</td><td>{statistic(view.sPoints[index]?.value ?? null)}</td><td>{point.signal || view.sPoints[index]?.signal ? "검토 필요" : "관리상태"}</td></tr>)}</tbody></table></div></section>
  </>;
}

function AttributeChartResult({ view }: { view: AttributeChartView }) {
  const chartLabel = { p: "p · 부적합률", np: "np · 부적합품 수", c: "c · 결점 수", u: "u · 단위당 결점 수" }[view.chart];
  const statisticLabel = { p: "부적합률", np: "부적합품 수", c: "결점 수", u: "단위당 결점 수" }[view.chart];
  const eventLabel = view.chart === "p" || view.chart === "np" ? "부적합품" : "결점";
  const opportunityLabel = view.chart === "p" || view.chart === "np" ? "표본 크기" : "검사 단위";
  return <>
    <section className="metric-grid result-metrics" aria-label={`${chartLabel} 결과 요약`}>
      <article className="metric-card"><span>부분군</span><strong>{view.points.length}</strong><small>시간 순서</small></article>
      <article className="metric-card"><span>전체 검사 기회</span><strong>{view.totalOpportunity}</strong><small>{eventLabel} {view.totalEvents}</small></article>
      <article className="metric-card"><span>통합 발생률</span><strong>{view.pooledRate.toFixed(4)}</strong><small>Phase I 중심 추정</small></article>
      <article className="metric-card"><span>한계 이탈</span><strong>{view.signalCount}</strong><small>{view.signalCount ? "조사 필요" : "신호 없음"}</small></article>
    </section>
    <section className="panel result-chart-panel">
      <header className="panel-heading"><div><span className="eyebrow">BINOMIAL ATTRIBUTE CHART</span><h2>{chartLabel} 관리도</h2></div><span>{view.points.length}개 부분군</span></header>
      <Suspense fallback={<div className="skeleton chart-skeleton" aria-label="속성 관리도 불러오는 중" />}><AttributeControlChart points={view.points} chart={view.chart} /></Suspense>
    </section>
    <section className="panel table-panel">
      <header className="panel-heading"><div><span className="eyebrow">ACCESSIBLE DATA</span><h2>부분군별 관리한계</h2></div></header>
      <div className="table-scroll"><table><thead><tr><th scope="col">부분군</th><th scope="col">{eventLabel}</th><th scope="col">{opportunityLabel}</th><th scope="col">{statisticLabel}</th><th scope="col">LCL</th><th scope="col">CL</th><th scope="col">UCL</th><th scope="col">상태</th></tr></thead><tbody>{view.points.map((point) => <tr key={point.index}><td>{point.index}</td><td>{point.eventCount}</td><td>{point.opportunity}</td><td>{statistic(point.statistic)}</td><td>{statistic(point.lcl)}</td><td>{statistic(point.center)}</td><td>{statistic(point.ucl)}</td><td>{point.signal ? <span className="status-text is-danger"><AlertTriangle aria-hidden="true" /> 3σ 한계 이탈</span> : <span className="status-text is-success"><CheckCircle2 aria-hidden="true" /> 정상</span>}</td></tr>)}</tbody></table></div>
    </section>
  </>;
}

function DoeResult({ doe }: { doe: DoeView }) {
  const effects = doe.coefficients.filter((row) => row.effect !== null);
  const ranked = [...effects].sort((left, right) => Math.abs(right.effect ?? 0) - Math.abs(left.effect ?? 0));
  const maxEffect = Math.max(...ranked.map((row) => Math.abs(row.effect ?? 0)), 1);
  const strongest = ranked[0];
  const factorNames = Array.from(new Set([...doe.predictions, ...doe.optimization].flatMap((row) => Object.keys(row.actual))));
  return <>
    <section className="metric-grid result-metrics" aria-label="DOE 결과 요약">
      <article className="metric-card"><span>응답</span><strong className="metric-text">{doe.responseName}</strong><small>분석 대상</small></article>
      <article className="metric-card"><span>R²</span><strong>{statistic(doe.rSquared, 3)}</strong><small>설명된 변동 비율</small></article>
      <article className="metric-card"><span>수정 R²</span><strong>{statistic(doe.adjustedRSquared, 3)}</strong><small>모델 크기 보정</small></article>
      <article className="metric-card"><span>잔차 표준편차</span><strong>{statistic(doe.residualStandardDeviation, 3)}</strong><small>오차 규모</small></article>
    </section>
    <section className="panel doe-effect-panel">
      <header className="panel-heading"><div><span className="eyebrow">CODED DESIGN EFFECTS</span><h2>효과 크기</h2></div><span>{effects.length}개 항</span></header>
      <div className="effect-bars" role="img" aria-label={strongest ? `가장 큰 절대 효과는 ${strongest.term}, 효과 ${statistic(strongest.effect)}` : "추정된 효과 없음"}>{ranked.map((row) => <div className="effect-bar-row" key={row.term}><strong>{row.term}</strong><span className={Number(row.effect) < 0 ? "effect-track is-negative" : "effect-track"}><i style={{ width: `${Math.abs(Number(row.effect)) / maxEffect * 100}%` }} /></span><span>{statistic(row.effect)}</span></div>)}</div>
      <div className="table-scroll"><table><thead><tr><th scope="col">항</th><th scope="col">차수</th><th scope="col">계수</th><th scope="col">효과</th><th scope="col">F</th><th scope="col">p</th></tr></thead><tbody>{effects.map((row) => <tr key={row.term}><td>{row.term}</td><td>{row.order}</td><td>{statistic(row.coefficient)}</td><td>{statistic(row.effect)}</td><td>{statistic(row.f_value)}</td><td>{statistic(row.p_value)}</td></tr>)}</tbody></table></div>
    </section>
    <section className="panel table-panel"><header className="panel-heading"><div><span className="eyebrow">ANALYSIS OF VARIANCE</span><h2>ANOVA</h2></div></header><div className="table-scroll"><table><thead><tr><th scope="col">변동원</th><th scope="col">DF</th><th scope="col">SS</th><th scope="col">MS</th><th scope="col">F</th><th scope="col">p</th></tr></thead><tbody>{doe.anova.map((row) => <tr key={row.source}><td>{row.source}</td><td>{row.degrees_of_freedom}</td><td>{statistic(row.sum_of_squares)}</td><td>{statistic(row.mean_square)}</td><td>{statistic(row.f_value)}</td><td>{statistic(row.p_value)}</td></tr>)}</tbody></table></div></section>
    <section className="panel table-panel"><header className="panel-heading"><div><span className="eyebrow">RESIDUAL DIAGNOSTICS</span><h2>적합값과 잔차</h2></div></header><div className="table-scroll"><table><thead><tr><th scope="col">실행순서</th><th scope="col">표준순서</th><th scope="col">관측값</th><th scope="col">적합값</th><th scope="col">잔차</th><th scope="col">척도화 잔차</th></tr></thead><tbody>{doe.residuals.map((row) => <tr key={row.run_order}><td>{row.run_order}</td><td>{row.standard_order ?? "중심점"}</td><td>{statistic(row.observed)}</td><td>{statistic(row.fitted)}</td><td>{statistic(row.residual)}</td><td>{statistic(row.scaled_residual)}</td></tr>)}</tbody></table></div></section>
    {doe.predictions.length > 0 && <section className="panel table-panel"><header className="panel-heading"><div><span className="eyebrow">MODEL PREDICTION</span><h2>조건별 예측</h2></div></header><div className="table-scroll"><table><thead><tr><th scope="col">조건</th>{factorNames.map((name) => <th scope="col" key={name}>{name}</th>)}<th scope="col">예측 응답</th></tr></thead><tbody>{doe.predictions.map((row) => <tr key={row.point}><td>{row.point}</td>{factorNames.map((name) => <td key={name}>{statistic(row.actual[name])}</td>)}<td>{statistic(row.predicted_response)}</td></tr>)}</tbody></table></div></section>}
    {doe.optimization.length > 0 && <section className="panel table-panel"><header className="panel-heading"><div><span className="eyebrow">VERTEX OPTIMIZATION</span><h2>최적 설정</h2></div></header><div className="table-scroll"><table><thead><tr><th scope="col">목표</th>{factorNames.map((name) => <th scope="col" key={name}>{name}</th>)}<th scope="col">예측 응답</th><th scope="col">평가 후보</th></tr></thead><tbody>{doe.optimization.map((row) => <tr key={row.goal}><td>{row.goal === "maximize" ? "최대화" : "최소화"}</td>{factorNames.map((name) => <td key={name}>{statistic(row.actual[name])}</td>)}<td>{statistic(row.predicted_response)}</td><td>{row.candidate_count}</td></tr>)}</tbody></table></div></section>}
  </>;
}

function DoeDesirabilityResult({ optimizer }: { optimizer: DoeDesirabilityView }) {
  const factorNames = Object.keys(optimizer.solution.actual);
  const goalLabel = { maximize: "최대화", minimize: "최소화", target: "목표값" };
  return <>
    <section className="metric-grid result-metrics" aria-label="DOE 다중 응답 최적화 요약">
      <article className="metric-card"><span>복합 desirability</span><strong>{statistic(optimizer.solution.composite_desirability, 4)}</strong><small>0–1, 높을수록 바람직</small></article>
      <article className="metric-card"><span>응답 수</span><strong>{optimizer.responses.length}</strong><small>동시 최적화</small></article>
      <article className="metric-card"><span>후보 평가</span><strong>{optimizer.solution.candidate_evaluations}</strong><small>결정론적 탐색</small></article>
      <article className="metric-card"><span>전역 최적 증명</span><strong className="metric-text">{optimizer.globalOptimumProven ? "예" : "아니오"}</strong><small>확인 실험 필요</small></article>
    </section>
    <section className="panel table-panel"><header className="panel-heading"><div><span className="eyebrow">OPTIMAL SETTINGS</span><h2>권장 요인 설정</h2></div></header><div className="table-scroll"><table><thead><tr>{factorNames.map((name) => <th scope="col" key={name}>{name}</th>)}<th scope="col">복합 desirability</th></tr></thead><tbody><tr>{factorNames.map((name) => <td key={name}>{statistic(optimizer.solution.actual[name])}</td>)}<td>{statistic(optimizer.solution.composite_desirability)}</td></tr></tbody></table></div></section>
    <section className="panel table-panel"><header className="panel-heading"><div><span className="eyebrow">INDIVIDUAL DESIRABILITY</span><h2>응답별 예측과 만족도</h2></div></header><div className="table-scroll"><table><thead><tr><th scope="col">응답</th><th scope="col">목표</th><th scope="col">예측</th><th scope="col">개별 desirability</th><th scope="col">Lower</th><th scope="col">Target</th><th scope="col">Upper</th><th scope="col">가중치</th><th scope="col">중요도</th></tr></thead><tbody>{optimizer.responses.map((row) => <tr key={row.response}><td>{row.response}</td><td>{goalLabel[row.goal]}</td><td>{statistic(row.prediction)}</td><td>{statistic(row.desirability)}</td><td>{statistic(row.lower)}</td><td>{statistic(row.target)}</td><td>{statistic(row.upper)}</td><td>{statistic(row.weight, 2)}</td><td>{statistic(row.importance, 2)}</td></tr>)}</tbody></table></div></section>
  </>;
}

function DoeFractionalResult({ design }: { design: DoeFractionalView }) {
  const factorNames = Object.keys(design.design[0]?.coded ?? {});
  return <>
    <section className="metric-grid result-metrics" aria-label="일부요인배치 요약">
      <article className="metric-card"><span>설계</span><strong className="metric-text">{design.designNotation}</strong><small>정규 2수준 일부요인</small></article>
      <article className="metric-card"><span>분수</span><strong>{design.fraction}</strong><small>완전요인 대비</small></article>
      <article className="metric-card"><span>해상도</span><strong>{design.resolutionLabel}</strong><small>최단 정의 단어 {design.resolution}개 요인</small></article>
      <article className="metric-card"><span>실행 수</span><strong>{design.design.length}</strong><small>반복 포함</small></article>
      <article className="metric-card"><span>블록</span><strong>{design.blockCount}</strong><small>{design.blockedResolutionLabel ? `블록 포함 해상도 ${design.blockedResolutionLabel}` : "블록 없음"}</small></article>
    </section>
    {design.automaticSelection && <section className="panel table-panel"><header className="panel-heading"><div><span className="eyebrow">GENERATOR SELECTION AUDIT</span><h2>자동 생성자 선택 근거</h2></div><span>{design.candidateSetsExamined ?? 0}개 후보 집합 검토</span></header><dl className="selection-audit"><div><dt>선택 목적</dt><dd>{design.selectionObjective === "minimum_runs_then_minimum_aberration" ? "최소 실행 수 → 최소 이상률" : "요청 실행 수에서 최소 이상률"}</dd></div><div><dt>단어 길이 패턴</dt><dd>{Object.entries(design.wordLengthPattern).map(([length, count]) => `A${length}=${count}`).join(", ")}</dd></div></dl></section>}
    {design.generators.length > 0 && <section className="panel table-panel"><header className="panel-heading"><div><span className="eyebrow">DESIGN GENERATORS</span><h2>선택된 생성식</h2></div><span>{design.automaticSelection ? "자동 선택" : "사용자 지정"}</span></header><div className="table-scroll"><table><thead><tr><th scope="col">생성 요인</th><th scope="col">기본 요인 곱</th><th scope="col">식</th></tr></thead><tbody>{design.generators.map((generator) => <tr key={generator.factor}><td>{generator.factor}</td><td>{generator.terms.join(" × ")}</td><td>{generator.expression}</td></tr>)}</tbody></table></div></section>}
    {design.blockGenerators.length > 0 && <section className="panel table-panel"><header className="panel-heading"><div><span className="eyebrow">BLOCK CONFOUNDING</span><h2>블록 생성식과 처리효과 별칭</h2></div><span>{design.blockCount}개 블록 · 해상도 {design.blockedResolutionLabel}</span></header><div className="table-scroll"><table><thead><tr><th scope="col">블록 대비</th><th scope="col">생성 처리항</th><th scope="col">교락된 처리효과</th></tr></thead><tbody>{design.blockAliases.map((row) => <tr key={row.contrast}><td>{row.contrast}</td><td>{row.generator_terms}</td><td>{row.treatment_alias_set.join(" = ")}</td></tr>)}</tbody></table></div></section>}
    <section className="panel table-panel"><header className="panel-heading"><div><span className="eyebrow">DEFINING RELATION</span><h2>정의관계</h2></div></header><p className="supporting-copy">{design.definingRelation}</p></section>
    <section className="panel table-panel"><header className="panel-heading"><div><span className="eyebrow">MAIN-EFFECT ALIASES</span><h2>주효과 별칭구조</h2></div></header><div className="table-scroll"><table><thead><tr><th scope="col">효과</th><th scope="col">전체 별칭 집합</th></tr></thead><tbody>{design.mainEffectAliases.map((row) => <tr key={row.effect}><td>{row.effect}</td><td>{row.alias_set.join(" = ")}</td></tr>)}</tbody></table></div></section>
    <section className="panel table-panel"><header className="panel-heading"><div><span className="eyebrow">TWO-FACTOR ALIASES</span><h2>2요인 교호작용 별칭구조</h2></div></header><div className="table-scroll"><table><thead><tr><th scope="col">효과</th><th scope="col">전체 별칭 집합</th></tr></thead><tbody>{design.twoFactorAliases.map((row) => <tr key={row.effect}><td>{row.effect}</td><td>{row.alias_set.join(" = ")}</td></tr>)}</tbody></table></div></section>
    <section className="panel table-panel"><header className="panel-heading"><div><span className="eyebrow">DESIGN MATRIX</span><h2>실행 설계표</h2></div></header><div className="table-scroll"><table><thead><tr><th scope="col">실행순서</th><th scope="col">표준순서</th><th scope="col">반복</th>{design.blockCount > 1 && <th scope="col">블록</th>}{factorNames.map((name) => <th scope="col" key={name}>{name} coded · actual</th>)}</tr></thead><tbody>{design.design.map((row) => <tr key={`${row.run_order}-${row.replicate}`}><td>{row.run_order}</td><td>{row.standard_order}</td><td>{row.replicate}</td>{design.blockCount > 1 && <td>{row.block}</td>}{factorNames.map((name) => <td key={name}>{row.coded[name] > 0 ? "+1" : "−1"} · {statistic(row.actual[name])}</td>)}</tr>)}</tbody></table></div></section>
  </>;
}

function DoeFractionalAnalysisResult({ analysis }: { analysis: DoeFractionalAnalysisView }) {
  const maxValue = Math.max(...analysis.rankedEffects.map((row) => row.display_value), 1);
  const strongest = analysis.rankedEffects[0];
  const method = analysis.inferenceMethod === "lenth_pse" ? "Lenth PSE" : analysis.inferenceMethod === "inference_unavailable_zero_residual" ? "오차 추정 불가" : "모형 잔차";
  return <>
    <section className="metric-grid result-metrics" aria-label="일부요인 응답 분석 요약">
      <article className="metric-card"><span>응답</span><strong className="metric-text">{analysis.responseName}</strong><small>주효과 대표항</small></article>
      <article className="metric-card"><span>가장 큰 효과</span><strong>{strongest?.term ?? "—"}</strong><small>{strongest ? statistic(strongest.effect) : "추정 없음"}</small></article>
      <article className="metric-card"><span>설계 해상도</span><strong>{analysis.foldover ? `${analysis.resolutionLabel} → ${analysis.augmentedResolution}` : analysis.resolutionLabel}</strong><small>{analysis.foldover ? "full foldover" : "원 설계"}</small></article>
      <article className="metric-card"><span>주효과–2FI 분리</span><strong className="metric-text">{analysis.mainEffectsClear ? "분리됨" : "별칭 유지"}</strong><small>{method} · 잔차 DF {analysis.residualDegreesOfFreedom}</small></article>
    </section>
    <section className="panel doe-effect-panel">
      <header className="panel-heading"><div><span className="eyebrow">PARETO OF EFFECTS</span><h2>부분요인 주효과 Pareto</h2></div><span>기준선 {statistic(analysis.referenceLine)}</span></header>
      <div className="effect-bars" role="img" aria-label={strongest ? `가장 큰 절대 효과는 ${strongest.term}, 효과 ${statistic(strongest.effect)}` : "추정된 효과 없음"}>{analysis.rankedEffects.map((row) => <div className="effect-bar-row" key={row.term}><strong>{row.term}</strong><span className={row.effect < 0 ? "effect-track is-negative" : "effect-track"}><i style={{ width: `${row.display_value / maxValue * 100}%` }} /></span><span>{statistic(row.display_value)}</span></div>)}</div>
      <div className="table-scroll"><table><thead><tr><th scope="col">순위</th><th scope="col">대표항</th><th scope="col">효과</th><th scope="col">표준화 효과</th><th scope="col">p</th><th scope="col">별칭 해석</th></tr></thead><tbody>{analysis.rankedEffects.map((row, index) => <tr key={row.term}><td>{index + 1}</td><td>{row.term}</td><td>{statistic(row.effect)}</td><td>{statistic(row.standardized_effect)}</td><td>{statistic(row.p_value)}</td><td>{row.clear_of_two_factor_interactions ? `2FI 분리 · ${row.alias_set.join(" = ")}` : row.alias_set.join(" = ")}</td></tr>)}</tbody></table></div>
    </section>
    {analysis.blockEffects.length > 0 && <section className="panel table-panel"><header className="panel-heading"><div><span className="eyebrow">BLOCK EFFECTS</span><h2>블록 효과와 교락 처리항</h2></div><span>{analysis.blockCount}개 블록</span></header><div className="table-scroll"><table><thead><tr><th scope="col">대비</th><th scope="col">계수</th><th scope="col">효과</th><th scope="col">생성 처리항</th><th scope="col">처리효과 별칭</th></tr></thead><tbody>{analysis.blockEffects.map((row) => <tr key={row.contrast}><td>{row.contrast}</td><td>{statistic(row.coefficient)}</td><td>{statistic(row.effect)}</td><td>{row.generator_terms}</td><td>{row.treatment_alias_set.join(" = ")}</td></tr>)}</tbody></table></div></section>}
    <section className="panel table-panel"><header className="panel-heading"><div><span className="eyebrow">INTERPRETATION BOUNDARY</span><h2>별칭 및 확인 범위</h2></div></header><p className="supporting-copy">{analysis.mainEffectsClear ? "주효과는 2요인 교호작용과 분리되지만 2요인 교호작용끼리의 별칭은 남을 수 있습니다." : "표시 효과는 별칭 집합의 결합 효과입니다. 개별 원인으로 단정하지 말고 후속 실험으로 확인하세요."}</p></section>
  </>;
}

function DoeBoxBehnkenResult({ design }: { design: DoeBoxBehnkenView }) {
  const factorNames = Object.keys(design.design[0]?.coded ?? {});
  return <>
    <section className="metric-grid result-metrics" aria-label="Box-Behnken 설계 요약">
      <article className="metric-card"><span>요인 수</span><strong>{design.factorCount}</strong><small>세 수준 정량 요인</small></article>
      <article className="metric-card"><span>Edge blocks</span><strong>{design.edgeBlocks}</strong><small>요인쌍별 4개 점</small></article>
      <article className="metric-card"><span>총 실행 수</span><strong>{design.design.length}</strong><small>중심점 {design.centerPoints}회</small></article>
      <article className="metric-card"><span>2차 모형</span><strong className="metric-text">{design.quadraticModelEstimable ? "추정 가능" : "추정 불가"}</strong><small>완전 quadratic 항 수 기준</small></article>
    </section>
    <section className="panel table-panel"><header className="panel-heading"><div><span className="eyebrow">DESIGN MATRIX</span><h2>Box–Behnken 실행 설계표</h2></div><span>Edge point {design.edgePoints}개</span></header><div className="table-scroll"><table><thead><tr><th scope="col">실행순서</th><th scope="col">표준순서</th><th scope="col">Block</th><th scope="col">점 유형</th>{factorNames.map((name) => <th scope="col" key={name}>{name} coded · actual</th>)}</tr></thead><tbody>{design.design.map((row) => <tr key={row.run_order}><td>{row.run_order}</td><td>{row.standard_order ?? "중심점"}</td><td>{row.block ?? "—"}</td><td>{row.point_type === "center" ? "중심점" : "Edge midpoint"}</td>{factorNames.map((name) => <td key={name}>{row.coded[name] > 0 ? "+1" : row.coded[name] < 0 ? "−1" : "0"} · {statistic(row.actual[name], 4)}</td>)}</tr>)}</tbody></table></div></section>
  </>;
}

function DoeCentralCompositeResult({ design }: { design: DoeCentralCompositeView }) {
  const factorNames = Object.keys(design.design[0]?.coded ?? {});
  const pointLabel = { factorial: "Factorial", axial: "Axial", center: "Center" };
  return <>
    <section className="metric-grid result-metrics" aria-label="중앙합성설계 요약">
      <article className="metric-card"><span>α</span><strong>{statistic(design.alpha, 4)}</strong><small>{design.rotatable ? "Rotatable" : "Face-centered"}</small></article>
      <article className="metric-card"><span>Factorial points</span><strong>{design.factorialRuns}</strong><small>2수준 cube</small></article>
      <article className="metric-card"><span>Axial points</span><strong>{design.axialRuns}</strong><small>곡률 추정</small></article>
      <article className="metric-card"><span>총 실행 수</span><strong>{design.design.length}</strong><small>중심점 {design.centerPoints}회</small></article>
    </section>
    <section className="panel table-panel"><header className="panel-heading"><div><span className="eyebrow">DESIGN MATRIX</span><h2>중앙합성 실행 설계표</h2></div></header><div className="table-scroll"><table><thead><tr><th scope="col">실행순서</th><th scope="col">표준순서</th><th scope="col">점 유형</th>{factorNames.map((name) => <th scope="col" key={name}>{name} coded · actual</th>)}</tr></thead><tbody>{design.design.map((row) => <tr key={row.run_order}><td>{row.run_order}</td><td>{row.standard_order ?? "중심점"}</td><td>{pointLabel[row.point_type]}</td>{factorNames.map((name) => <td key={name}>{statistic(row.coded[name], 4)} · {statistic(row.actual[name], 4)}</td>)}</tr>)}</tbody></table></div></section>
  </>;
}

function DoeQuadraticAnalysisResult({ analysis, designLabel, methodLabel }: { analysis: DoeQuadraticAnalysisView; designLabel: string; methodLabel: string }) {
  return <>
    <section className="metric-grid result-metrics" aria-label={`${designLabel} 2차 모형 요약`}>
      <article className="metric-card"><span>응답</span><strong className="metric-text">{analysis.responseName}</strong><small>완전 2차 모형</small></article>
      <article className="metric-card"><span>R²</span><strong>{statistic(analysis.rSquared, 4)}</strong><small>수정 R² {statistic(analysis.adjustedRSquared, 4)}</small></article>
      <article className="metric-card"><span>α</span><strong>{statistic(analysis.alpha, 4)}</strong><small>{methodLabel}</small></article>
      <article className="metric-card"><span>잔차 DF</span><strong>{analysis.residualDegreesOfFreedom}</strong><small>LOF DF {analysis.lackOfFitDegreesOfFreedom}</small></article>
    </section>
    <section className="panel table-panel"><header className="panel-heading"><div><span className="eyebrow">QUADRATIC MODEL</span><h2>2차 모형 계수</h2></div></header><div className="table-scroll"><table><thead><tr><th scope="col">항</th><th scope="col">유형</th><th scope="col">계수</th><th scope="col">표준오차</th><th scope="col">t</th><th scope="col">p</th><th scope="col">판정</th></tr></thead><tbody>{analysis.coefficients.map((row) => <tr key={row.term}><td>{row.term}</td><td>{row.kind}</td><td>{statistic(row.coefficient)}</td><td>{statistic(row.standard_error)}</td><td>{statistic(row.t_value)}</td><td>{statistic(row.p_value)}</td><td>{row.significant ? "유의" : "보류"}</td></tr>)}</tbody></table></div></section>
    <section className="panel table-panel"><header className="panel-heading"><div><span className="eyebrow">ANOVA</span><h2>반응표면 분산분석</h2></div></header><div className="table-scroll"><table><thead><tr><th scope="col">변동원</th><th scope="col">DF</th><th scope="col">SS</th><th scope="col">MS</th><th scope="col">F</th><th scope="col">p</th></tr></thead><tbody>{analysis.anova.map((row) => <tr key={row.source}><td>{row.source}</td><td>{row.degrees_of_freedom}</td><td>{statistic(row.sum_of_squares)}</td><td>{statistic(row.mean_square)}</td><td>{statistic(row.f_value)}</td><td>{statistic(row.p_value)}</td></tr>)}</tbody></table></div></section>
    <section className="panel table-panel"><header className="panel-heading"><div><span className="eyebrow">RESIDUALS</span><h2>적합값과 잔차</h2></div></header><div className="table-scroll"><table><thead><tr><th scope="col">실행순서</th><th scope="col">관측</th><th scope="col">적합</th><th scope="col">잔차</th></tr></thead><tbody>{analysis.residuals.map((row) => <tr key={row.run_order}><td>{row.run_order}</td><td>{statistic(row.observed)}</td><td>{statistic(row.fitted)}</td><td>{statistic(row.residual)}</td></tr>)}</tbody></table></div></section>
  </>;
}

function DoeCentralCompositeSurfaceResult({ surface }: { surface: DoeCentralCompositeSurfaceView }) {
  const point = surface.stationary;
  const factorNames = point.coded ? Object.keys(point.coded) : [];
  const classificationLabel = { minimum: "최소점", maximum: "최대점", saddle: "안장점", ridge: "능선/평탄" };
  const contourSummary = `${surface.plotFactors.join("와 ")}의 등고선 ${surface.contourLevels}개 수준, 선분 ${surface.contours.length}개`;
  const wireframe = surfaceWireframePaths(surface.grid, surface.gridSize);
  return <>
    <section className="metric-grid result-metrics" aria-label="응답표면 정상점 분석 요약">
      <article className="metric-card"><span>정상점 분류</span><strong className="metric-text">{classificationLabel[point.classification]}</strong><small>Canonical eigenvalues 기준</small></article>
      <article className="metric-card"><span>예측 응답</span><strong>{statistic(point.predicted_response)}</strong><small>{surface.responseName}</small></article>
      <article className="metric-card"><span>설계영역 내부</span><strong className="metric-text">{point.inside_factorial_cube === null ? "판정 불가" : point.inside_factorial_cube ? "예" : "아니오"}</strong><small>coded factorial cube</small></article>
      <article className="metric-card"><span>등고선 수준</span><strong>{surface.contourLevels}</strong><small>선분 {surface.contours.length}개</small></article>
    </section>
    <section className="panel table-panel"><header className="panel-heading"><div><span className="eyebrow">STATIONARY POINT</span><h2>정상점 분석</h2></div></header>{point.available && point.coded && point.actual ? <div className="table-scroll"><table><thead><tr><th scope="col">요인</th><th scope="col">Coded</th><th scope="col">Actual</th></tr></thead><tbody>{factorNames.map((name) => <tr key={name}><td>{name}</td><td>{statistic(point.coded?.[name] ?? null)}</td><td>{statistic(point.actual?.[name] ?? null)}</td></tr>)}</tbody></table></div> : <p className="supporting-copy">2차 계수 행렬이 특이하여 고유한 정상점을 계산할 수 없습니다.</p>}</section>
    <section className="panel table-panel"><header className="panel-heading"><div><span className="eyebrow">CANONICAL ANALYSIS</span><h2>Canonical eigenvalues</h2></div></header><div className="table-scroll"><table><thead><tr><th scope="col">축</th><th scope="col">고유값</th></tr></thead><tbody>{surface.canonicalAxes.map((row) => <tr key={row.axis}><td>{row.axis}</td><td>{statistic(row.eigenvalue)}</td></tr>)}</tbody></table></div></section>
    <section className="panel table-panel"><header className="panel-heading"><div><span className="eyebrow">BOUNDED SLICE</span><h2>응답표면 구간 극값</h2></div><span>{surface.plotFactors.join(" × ")}</span></header><div className="table-scroll"><table><thead><tr><th scope="col">종류</th><th scope="col">{surface.plotFactors[0]} coded</th><th scope="col">{surface.plotFactors[0]} actual</th><th scope="col">{surface.plotFactors[1]} coded</th><th scope="col">{surface.plotFactors[1]} actual</th><th scope="col">예측 응답</th></tr></thead><tbody>{surface.extrema.map((row) => <tr key={row.kind}><td>{row.kind === "minimum" ? "최소" : "최대"}</td><td>{statistic(row.x_coded)}</td><td>{statistic(row.x_actual)}</td><td>{statistic(row.y_coded)}</td><td>{statistic(row.y_actual)}</td><td>{statistic(row.predicted_response)}</td></tr>)}</tbody></table></div></section>
    <section className="panel result-chart-panel"><header className="panel-heading"><div><span className="eyebrow">ISO-RESPONSE CONTOURS</span><h2>응답표면 등고선</h2></div><span>{surface.gridSize} × {surface.gridSize} 격자</span></header>{surface.contours.length ? <svg className="surface-contour-chart" viewBox="0 0 100 100" role="img" aria-label={contourSummary} preserveAspectRatio="none">{surface.contours.map((segment, index) => <line key={`${segment.level}-${index}`} x1={(segment.x1_coded + 1) * 50} y1={(1 - (segment.y1_coded + 1) / 2) * 100} x2={(segment.x2_coded + 1) * 50} y2={(1 - (segment.y2_coded + 1) / 2) * 100} />)}</svg> : <p className="supporting-copy contour-empty">선택한 표면 구간이 평탄하여 등고선을 생성할 수 없습니다.</p>}</section>
    <section className="panel result-chart-panel"><header className="panel-heading"><div><span className="eyebrow">PROJECTED SURFACE</span><h2>3D 응답표면 와이어프레임</h2></div><span>{surface.responseName}</span></header><svg className="surface-wireframe-chart" viewBox="0 0 100 100" role="img" aria-label={`${surface.plotFactors.join("와 ")}에 따른 ${surface.responseName} 예측 응답의 3D 와이어프레임. 최소 ${statistic(wireframe.minimum)}, 최대 ${statistic(wireframe.maximum)}`} preserveAspectRatio="xMidYMid meet">{wireframe.paths.map((points, index) => <polyline key={index} points={points} />)}</svg></section>
    {surface.contours.length > 0 && <section className="panel table-panel"><header className="panel-heading"><div><span className="eyebrow">ACCESSIBLE CONTOUR DATA</span><h2>등고선 선분 표</h2></div><span>{surface.contours.length}개 선분</span></header><div className="table-scroll"><table><thead><tr><th scope="col">수준</th><th scope="col">X1 actual</th><th scope="col">Y1 actual</th><th scope="col">X2 actual</th><th scope="col">Y2 actual</th></tr></thead><tbody>{surface.contours.map((segment, index) => <tr key={`${segment.level}-${index}`}><td>{statistic(segment.level)}</td><td>{statistic(segment.x1_actual)}</td><td>{statistic(segment.y1_actual)}</td><td>{statistic(segment.x2_actual)}</td><td>{statistic(segment.y2_actual)}</td></tr>)}</tbody></table></div></section>}
    <section className="panel table-panel"><header className="panel-heading"><div><span className="eyebrow">ACCESSIBLE SURFACE DATA</span><h2>응답표면 격자</h2></div><span>{surface.grid.length}개 점</span></header><div className="table-scroll"><table><thead><tr><th scope="col">X index</th><th scope="col">Y index</th><th scope="col">{surface.plotFactors[0]} coded</th><th scope="col">{surface.plotFactors[0]} actual</th><th scope="col">{surface.plotFactors[1]} coded</th><th scope="col">{surface.plotFactors[1]} actual</th><th scope="col">예측 응답</th></tr></thead><tbody>{surface.grid.map((row) => <tr key={`${row.x_index}-${row.y_index}`}><td>{row.x_index}</td><td>{row.y_index}</td><td>{statistic(row.x_coded)}</td><td>{statistic(row.x_actual)}</td><td>{statistic(row.y_coded)}</td><td>{statistic(row.y_actual)}</td><td>{statistic(row.predicted_response)}</td></tr>)}</tbody></table></div></section>
  </>;
}

function surfaceWireframePaths(grid: DoeCentralCompositeSurfaceView["grid"], gridSize: number) {
  const responses = grid.map((point) => point.predicted_response);
  const minimum = Math.min(...responses);
  const maximum = Math.max(...responses);
  const span = maximum - minimum || 1;
  const project = (point: DoeCentralCompositeSurfaceView["grid"][number]) => {
    const height = (point.predicted_response - minimum) / span;
    const horizontal = 50 + (point.x_coded - point.y_coded) * 20;
    const vertical = 70 - (point.x_coded + point.y_coded) * 10 - height * 40;
    return `${horizontal.toFixed(3)},${vertical.toFixed(3)}`;
  };
  const paths: string[] = [];
  for (let row = 0; row < gridSize; row += 1) paths.push(grid.slice(row * gridSize, (row + 1) * gridSize).map(project).join(" "));
  for (let column = 0; column < gridSize; column += 1) {
    const points = Array.from({ length: gridSize }, (_, row) => grid[row * gridSize + column]).filter((point): point is DoeCentralCompositeSurfaceView["grid"][number] => point !== undefined);
    paths.push(points.map(project).join(" "));
  }
  return { paths, minimum, maximum };
}

function DoePlackettBurmanResult({ design }: { design: DoePlackettBurmanView }) {
  const factorNames = Object.keys(design.design[0]?.coded ?? {});
  return <>
    <section className="metric-grid result-metrics" aria-label="Plackett-Burman 설계 요약">
      <article className="metric-card"><span>요인 수</span><strong>{design.factorCount}</strong><small>선별 대상</small></article>
      <article className="metric-card"><span>기본 실행 수</span><strong>{design.baseRunCount}</strong><small>반복 전</small></article>
      <article className="metric-card"><span>해상도</span><strong>{design.resolutionLabel}</strong><small>주효과 선별</small></article>
      <article className="metric-card"><span>총 실행 수</span><strong>{design.totalRunCount}</strong><small>중심점 포함</small></article>
    </section>
    <section className="panel table-panel"><header className="panel-heading"><div><span className="eyebrow">SCREENING DIAGNOSTICS</span><h2>설계 검증</h2></div></header><dl><div><dt>열 균형</dt><dd>{design.balanced ? "통과" : "실패"}</dd></div><div><dt>열쌍 직교</dt><dd>{design.pairwiseOrthogonal ? "통과" : "실패"}</dd></div><div><dt>미사용 열</dt><dd>{design.unusedFactorColumns}</dd></div><div><dt>구성 방식</dt><dd>{design.construction}</dd></div></dl></section>
    <section className="panel table-panel"><header className="panel-heading"><div><span className="eyebrow">DESIGN MATRIX</span><h2>선별 실행 설계표</h2></div></header><div className="table-scroll"><table><thead><tr><th scope="col">실행순서</th><th scope="col">표준순서</th><th scope="col">반복</th><th scope="col">점 유형</th>{factorNames.map((name) => <th scope="col" key={name}>{name} coded · actual</th>)}</tr></thead><tbody>{design.design.map((row) => <tr key={row.run_order}><td>{row.run_order}</td><td>{row.standard_order ?? "중심점"}</td><td>{row.replicate}</td><td>{row.point_type === "center" ? "중심점" : "선별점"}</td>{factorNames.map((name) => <td key={name}>{row.coded[name] === 0 ? "0" : row.coded[name] > 0 ? "+1" : "−1"} · {statistic(row.actual[name])}</td>)}</tr>)}</tbody></table></div></section>
  </>;
}

function DoePlackettBurmanAnalysisResult({ analysis }: { analysis: DoePlackettBurmanAnalysisView }) {
  const maxValue = Math.max(...analysis.rankedEffects.map((row) => row.display_value), 1);
  const strongest = analysis.rankedEffects[0];
  const method = analysis.inferenceMethod === "lenth_pse" ? "Lenth PSE" : "잔차 오차";
  return <>
    <section className="metric-grid result-metrics" aria-label="Plackett-Burman 응답 분석 요약">
      <article className="metric-card"><span>응답</span><strong className="metric-text">{analysis.responseName}</strong><small>선별 분석 대상</small></article>
      <article className="metric-card"><span>가장 큰 효과</span><strong>{strongest?.term ?? "—"}</strong><small>{strongest ? statistic(strongest.effect) : "추정 없음"}</small></article>
      <article className="metric-card"><span>판정 방식</span><strong className="metric-text">{method}</strong><small>잔차 DF {analysis.residualDegreesOfFreedom}</small></article>
      <article className="metric-card"><span>확인 후보</span><strong>{analysis.confirmationCandidates.length}</strong><small>독립 확인실험 필요</small></article>
    </section>
    <section className="panel doe-effect-panel">
      <header className="panel-heading"><div><span className="eyebrow">PARETO OF EFFECTS</span><h2>주효과 Pareto</h2></div><span>기준선 {statistic(analysis.referenceLine)}</span></header>
      <div className="effect-bars" role="img" aria-label={strongest ? `가장 큰 절대 효과는 ${strongest.term}, 효과 ${statistic(strongest.effect)}` : "추정된 효과 없음"}>{analysis.rankedEffects.map((row) => <div className="effect-bar-row" key={row.term}><strong>{row.term}</strong><span className={row.effect < 0 ? "effect-track is-negative" : "effect-track"}><i style={{ width: `${row.display_value / maxValue * 100}%` }} /></span><span>{statistic(row.display_value)}</span></div>)}</div>
      <div className="table-scroll"><table><thead><tr><th scope="col">순위</th><th scope="col">요인</th><th scope="col">효과</th><th scope="col">표준화 효과</th><th scope="col">p</th><th scope="col">선별 판정</th></tr></thead><tbody>{analysis.rankedEffects.map((row, index) => <tr key={row.term}><td>{index + 1}</td><td>{row.term}</td><td>{statistic(row.effect)}</td><td>{statistic(row.standardized_effect)}</td><td>{statistic(row.p_value)}</td><td>{row.significant ? "확인 후보" : "기준 미달"}</td></tr>)}</tbody></table></div>
    </section>
    <section className="panel table-panel"><header className="panel-heading"><div><span className="eyebrow">CONFIRMATION WORKFLOW</span><h2>확인실험 후보</h2></div></header>{analysis.confirmationCandidates.length ? <div className="table-scroll"><table><thead><tr><th scope="col">요인</th><th scope="col">효과</th><th scope="col">응답 증가 방향</th><th scope="col">권장 수준</th><th scope="col">대조 수준</th></tr></thead><tbody>{analysis.confirmationCandidates.map((row) => <tr key={row.factor}><td>{row.factor}</td><td>{statistic(row.effect)}</td><td>{row.direction_for_increase === "high" ? "High" : "Low"}</td><td>{statistic(row.suggested_level)}</td><td>{statistic(row.opposite_level)}</td></tr>)}</tbody></table></div> : <p className="supporting-copy">선택한 기준선을 넘은 요인이 없습니다. 순위만으로 후보를 승격하지 마세요.</p>}</section>
    {analysis.curvature.map((row) => <section className="panel table-panel" key="curvature"><header className="panel-heading"><div><span className="eyebrow">CENTER POINTS</span><h2>기술적 곡률 점검</h2></div></header><dl><div><dt>요인점 평균</dt><dd>{statistic(row.factorial_mean)}</dd></div><div><dt>중심점 평균</dt><dd>{statistic(row.center_mean)}</dd></div><div><dt>차이</dt><dd>{statistic(row.difference)}</dd></div><div><dt>중심점 수</dt><dd>{row.center_point_count}</dd></div></dl></section>)}
  </>;
}
