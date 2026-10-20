import { AlertTriangle, ArrowLeft, BookOpen, CheckCircle2, X } from "lucide-react";
import { lazy, Suspense, useEffect, useMemo, useRef, useState } from "react";
import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom";
import { getRun } from "../api";
import { toDoeView, toImrView, type DoeView } from "../analysis";
import { Button } from "../components/Button";
import type { StoredRun } from "../types";

const ProcessRail = lazy(() => import("../components/ProcessRail").then((module) => ({ default: module.ProcessRail })));

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
  const doe = toDoeView(result);
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
      </> : doe ? <DoeResult doe={doe} /> : <section className="panel generic-result-panel"><header className="panel-heading"><div><span className="eyebrow">RESULT BUNDLE</span><h2>분석 결과 요약</h2></div></header><dl><div><dt>분석 유형</dt><dd>{result.analysis_type}</dd></div><div><dt>진단 항목</dt><dd>{Object.keys(result.diagnostics).length}개</dd></div><div><dt>결과 표</dt><dd>{Object.keys(result.tables).join(", ") || "없음"}</dd></div></dl><p>이 분석의 전용 시각화는 다음 개발 증분에서 제공됩니다. 계산 근거와 원본 ResultBundle은 보존되어 있습니다.</p></section>}
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
