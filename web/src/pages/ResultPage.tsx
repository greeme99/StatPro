import { AlertTriangle, ArrowLeft, BookOpen, CheckCircle2, X } from "lucide-react";
import { lazy, Suspense, useEffect, useMemo, useRef, useState } from "react";
import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom";
import { getRun } from "../api";
import { toImrView } from "../analysis";
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
        <article className="metric-card"><span>한계 이탈</span><strong>{signalCount}</strong><small>{signalCount ? "검토 필요" : "신호 없음"}</small></article>
      </section>
      <section className="panel result-chart-panel">
        <header className="panel-heading"><div><span className="eyebrow">INDIVIDUALS CHART</span><h2>개별값 관리도</h2></div><span className="run-version">ENGINE {result.engine_version}</span></header>
        <Suspense fallback={<div className="skeleton chart-skeleton" aria-label="관리도 불러오는 중" />}><ProcessRail points={imr.points} center={imr.center} ucl={imr.ucl} lcl={imr.lcl} /></Suspense>
      </section>
      <section className="panel table-panel">
        <header className="panel-heading"><div><span className="eyebrow">ACCESSIBLE DATA</span><h2>관리도 원본 표</h2></div></header>
        <div className="table-scroll"><table><thead><tr><th scope="col">순서</th><th scope="col">관측값</th><th scope="col">상태</th></tr></thead><tbody>{imr.points.map((point) => <tr key={point.index}><td>{point.index}</td><td>{point.value.toFixed(4)}</td><td>{point.signal ? <span className="status-text is-danger"><AlertTriangle aria-hidden="true" /> 한계 이탈</span> : <span className="status-text is-success"><CheckCircle2 aria-hidden="true" /> 정상</span>}</td></tr>)}</tbody></table></div>
      </section>
      </> : <section className="panel generic-result-panel"><header className="panel-heading"><div><span className="eyebrow">RESULT BUNDLE</span><h2>분석 결과 요약</h2></div></header><dl><div><dt>분석 유형</dt><dd>{result.analysis_type}</dd></div><div><dt>진단 항목</dt><dd>{Object.keys(result.diagnostics).length}개</dd></div><div><dt>결과 표</dt><dd>{Object.keys(result.tables).join(", ") || "없음"}</dd></div></dl><p>이 분석의 전용 시각화는 다음 개발 증분에서 제공됩니다. 계산 근거와 원본 ResultBundle은 보존되어 있습니다.</p></section>}
      {result.warnings.length > 0 && <section className="warning-panel"><AlertTriangle aria-hidden="true" /><div><h2>해석 전 확인</h2><ul>{result.warnings.map((warning) => <li key={warning}>{warning}</li>)}</ul></div></section>}
      {drawerOpen && <><button className="drawer-scrim" aria-label="계산 근거 닫기" onClick={closeDrawer} /><aside ref={drawer} className="detail-drawer" role="dialog" aria-modal="true" aria-labelledby="drawer-title"><header><div><span className="eyebrow">EVIDENCE</span><h2 id="drawer-title">계산 근거</h2></div><button ref={closeButton} className="icon-button" aria-label="닫기" onClick={closeDrawer}><X /></button></header><section><h3>분석 가정</h3><ul>{result.assumptions.map((item) => <li key={item}>{item}</li>)}</ul></section><section><h3>공개 출처</h3>{result.provenance.map((source) => <a className="source-link" href={source.url} target="_blank" rel="noreferrer" key={source.url}><strong>{source.title}</strong><span>{source.authority}</span></a>)}</section><section><h3>재현 정보</h3><dl><div><dt>엔진</dt><dd>{result.engine_version}</dd></div><div><dt>Storage version</dt><dd>{run.storage_version}</dd></div><div><dt>ETag</dt><dd className="digest">{run.etag}</dd></div></dl></section></aside></>}
    </div>
  );
}
