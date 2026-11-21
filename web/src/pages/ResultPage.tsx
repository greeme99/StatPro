import { AlertTriangle, BookOpen, CheckCircle2, Download, FileSpreadsheet, FileText, X } from "lucide-react";
import { lazy, Suspense, useEffect, useMemo, useRef, useState } from "react";
import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom";
import { ANALYSIS_REPORT_REGISTRY, analysisReportKind, analysisRunArtifactUrl, getRun, type ReportTemplate } from "../api";
import { toAttributeAgreementView, toAttributeChartView, toCapabilityView, toCusumView, toDoeBoxBehnkenAnalysisView, toDoeBoxBehnkenView, toDoeCentralCompositeAnalysisView, toDoeCentralCompositeSurfaceView, toDoeCentralCompositeView, toDoeDesirabilityView, toDoeFractionalAnalysisView, toDoeFractionalView, toDoePlackettBurmanAnalysisView, toDoePlackettBurmanView, toDoeView, toEwmaView, toGageBiasLinearityView, toGageRrView, toImrView, toNestedGageRrView, toParetoView, toRareEventChartView, toXbarRView, toXbarSView, type AttributeAgreementView, type AttributeChartView, type CapabilityView, type CusumView, type DoeBoxBehnkenView, type DoeCentralCompositeSurfaceView, type DoeCentralCompositeView, type DoeDesirabilityView, type DoeFractionalAnalysisView, type DoeFractionalView, type DoePlackettBurmanAnalysisView, type DoePlackettBurmanView, type DoeQuadraticAnalysisView, type DoeView, type EwmaView, type GageBiasLinearityView, type GageRrView, type NestedGageRrView, type ParetoView, type RareEventChartView, type XbarRView, type XbarSView } from "../analysis";
import { Button } from "../components/Button";
import { ControlChartStatistics, ControlLimitBadges, ControlSignalSummary } from "../components/ControlChartResultSections";
import { ReportPdfDownload } from "../components/ReportPdfDownload";
import { ResultExportMenu } from "../components/ResultExportMenu";
import { SpcEvidenceActionPanel } from "../components/SpcEvidenceActionPanel";
import type { StoredRun } from "../types";

const ProcessRail = lazy(() => import("../components/ProcessRail").then((module) => ({ default: module.ProcessRail })));
const AttributeControlChart = lazy(() => import("../components/AttributeControlChart").then((module) => ({ default: module.AttributeControlChart })));
const EwmaControlChart = lazy(() => import("../components/EwmaControlChart").then((module) => ({ default: module.EwmaControlChart })));
const CusumControlChart = lazy(() => import("../components/CusumControlChart").then((module) => ({ default: module.CusumControlChart })));
const ParetoChart = lazy(() => import("../components/ParetoChart").then((module) => ({ default: module.ParetoChart })));

type WorksheetSource = { worksheet_id: string; worksheet_revision: number; worksheet_digest: string; column_name: string };

function worksheetSourceFrom(parameters: Record<string, unknown>): WorksheetSource | null {
  const source = parameters.worksheet_source;
  if (!source || typeof source !== "object") return null;
  const record = source as Record<string, unknown>;
  return typeof record.worksheet_id === "string" && typeof record.worksheet_revision === "number" && typeof record.worksheet_digest === "string" && typeof record.column_name === "string"
    ? { worksheet_id: record.worksheet_id, worksheet_revision: record.worksheet_revision, worksheet_digest: record.worksheet_digest, column_name: record.column_name }
    : null;
}

export function ResultPage() {
  const { runId = "" } = useParams();
  const [run, setRun] = useState<StoredRun | null>(null);
  const [state, setState] = useState<"loading" | "ready" | "error">("loading");
  const [search, setSearch] = useSearchParams();
  const [reportTemplate, setReportTemplate] = useState<ReportTemplate>("standard");
  const [reportDownloadError, setReportDownloadError] = useState("");
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
  const worksheetSource = result ? worksheetSourceFrom(result.parameters) : null;
  const reportKind = result ? analysisReportKind(result.analysis_type) : null;
  const reportDescriptor = reportKind ? ANALYSIS_REPORT_REGISTRY[reportKind] : null;
  const normality = result?.analysis_type === "normality.jarque_bera";
  const descriptive = result?.analysis_type === "descriptive.univariate";
  const regression = result?.analysis_type === "regression.linear_ols" || result?.analysis_type === "regression.categorical_ols" || result?.analysis_type === "regression.polynomial_ols" || result?.analysis_type === "regression.interaction_ols" || result?.analysis_type === "regression.stepwise_ols" || result?.analysis_type === "regression.logistic" || result?.analysis_type === "regression.poisson" || result?.analysis_type === "regression.negative_binomial" || result?.analysis_type === "regression.regularized_linear" || result?.analysis_type === "regression.ols_validation" || result?.analysis_type === "regression.best_subsets_ols";
  const welchT = result?.analysis_type === "hypothesis.independent_welch_t" || result?.analysis_type === "hypothesis.independent_tost_equivalence";
  const mannWhitney = result?.analysis_type === "hypothesis.mann_whitney_u";
  const pairedT = result?.analysis_type === "hypothesis.paired_t" || result?.analysis_type === "hypothesis.wilcoxon_signed_rank";
  const anova = result?.analysis_type === "hypothesis.one_way_anova" || result?.analysis_type === "hypothesis.chi_square_independence" || result?.analysis_type === "hypothesis.kruskal_wallis";
  const imr = toImrView(result);
  const attributeChart = toAttributeChartView(result);
  const rareEventChart = toRareEventChartView(result);
  const xbarS = toXbarSView(result);
  const xbarR = toXbarRView(result);
  const ewma = toEwmaView(result);
  const cusum = toCusumView(result);
  const pareto = toParetoView(result);
  const capability = toCapabilityView(result);
  const gageRr = toGageRrView(result);
  const attributeAgreement = toAttributeAgreementView(result);
  const biasLinearity = toGageBiasLinearityView(result);
  const nestedGageRr = toNestedGageRrView(result);
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
  const signalCount = useMemo(() => imr ? imr.points.filter((point) => point.signal).length + (imr.movingRangePoints?.filter((point) => point.signal).length ?? 0) : 0, [imr]);
  const closeDrawer = () => { setSearch({}); drawerTrigger.current?.focus(); };

  if (state === "loading") return <div className="page"><div className="skeleton page-skeleton" aria-label="결과 불러오는 중" /></div>;
  if (state === "error" || !run || !result) return <div className="page"><div className="state-message is-error"><AlertTriangle aria-hidden="true" /><h1>결과를 불러오지 못했습니다</h1><p>Run ID를 확인하거나 로컬 API 연결 상태를 점검하세요.</p><Button onClick={() => navigate("/home")}>홈으로 이동</Button></div></div>;

  return (
    <div className="page result-page" data-density="compact">
      <section className="result-header">
        <div><span className="eyebrow">ANALYSIS RUN / {result.analysis_type}</span><h1>{run.run_id}</h1><p className="digest">SHA-256 · {result.input_digest}</p></div>
        <div className="result-actions"><span className="status-badge is-success"><CheckCircle2 aria-hidden="true" /> 완료</span>{reportKind && reportDescriptor && <>{reportDescriptor.supportsTemplates && <label className="report-template-control">보고서 양식<select aria-label="DOE 보고서 양식" value={reportTemplate} onChange={(event) => setReportTemplate(event.target.value as ReportTemplate)}><option value="standard">표준 분석 보고서</option><option value="customer_review">고객 검토용 보고서</option><option value="regulatory_review">규제 검토용 보고서</option></select></label>}{reportDescriptor.artifacts.includes("html") && <a className="button button-secondary" href={analysisRunArtifactUrl(run.run_id, reportKind, "html", reportTemplate)} download><FileText aria-hidden="true" /><span>HTML 보고서</span></a>}{reportDescriptor.artifacts.includes("pdf") && <ReportPdfDownload href={analysisRunArtifactUrl(run.run_id, reportKind, "pdf", reportTemplate)} filename={`${run.run_id}-${reportKind}-report.pdf`} onError={setReportDownloadError}><FileText aria-hidden="true" /><span>PDF 보고서</span></ReportPdfDownload>}{reportDescriptor.artifacts.includes("xlsx") && <a className="button button-secondary" href={analysisRunArtifactUrl(run.run_id, reportKind, "xlsx", reportTemplate)} download><FileSpreadsheet aria-hidden="true" /><span>Excel 보고서</span></a>}{reportDescriptor.artifacts.includes("zip") && <a className="button button-secondary" href={analysisRunArtifactUrl(run.run_id, reportKind, "zip", reportTemplate)} download><Download aria-hidden="true" /><span>그래프·Excel·CSV·JSON 묶음</span></a>}</>}<ResultExportMenu runId={run.run_id} result={result} /><Button ref={drawerTrigger} icon={<BookOpen />} onClick={() => setSearch({ detail: "provenance" })}>계산 근거</Button></div>
      </section>
      {reportDownloadError && <div className="error-banner" role="alert"><AlertTriangle aria-hidden="true" /><p>{reportDownloadError}</p></div>}
      {imr ? <>
      <ControlChartStatistics center={imr.center} ucl={imr.ucl} lcl={imr.lcl} totalPoints={imr.points.length} signalCount={signalCount} />
      <section className="panel result-chart-panel">
        <header className="panel-heading"><div><span className="eyebrow">INDIVIDUALS CHART</span><h2>개별값(I) 관리도</h2><ControlLimitBadges limits={[{ label: "CL", value: imr.center }, { label: "UCL", value: imr.ucl }, { label: "LCL", value: imr.lcl }]} /></div><span className="run-version">ENGINE {result.engine_version}</span></header>
        <Suspense fallback={<div className="skeleton chart-skeleton" aria-label="관리도 불러오는 중" />}><ProcessRail points={imr.points} center={imr.center} ucl={imr.ucl} lcl={imr.lcl} /></Suspense>
      </section>
      {imr.movingRangePoints && imr.movingRange && <section className="panel result-chart-panel">
        <header className="panel-heading"><div><span className="eyebrow">MOVING RANGE CHART</span><h2>이동 범위(MR) 관리도</h2><ControlLimitBadges limits={[{ label: "CL", value: imr.movingRange.center }, { label: "UCL", value: imr.movingRange.ucl }, { label: "LCL", value: imr.movingRange.lcl }]} /></div></header>
        <Suspense fallback={<div className="skeleton chart-skeleton" aria-label="이동 범위 관리도 불러오는 중" />}><ProcessRail points={imr.movingRangePoints} center={imr.movingRange.center} ucl={imr.movingRange.ucl} lcl={imr.movingRange.lcl} /></Suspense>
      </section>}
      <section className="panel table-panel">
        <header className="panel-heading"><div><span className="eyebrow">ACCESSIBLE DATA</span><h2>관리도 원본 표</h2></div></header>
        <div className="table-scroll"><table><thead><tr><th scope="col">순서</th><th scope="col">관측값</th><th scope="col">상태</th></tr></thead><tbody>{imr.points.map((point) => <tr key={point.index}><td>{point.index}</td><td>{point.value.toFixed(4)}</td><td>{point.signal ? <span className="status-text is-danger"><AlertTriangle aria-hidden="true" /> {point.rules.length ? point.rules.join(", ") : "3σ 한계 이탈"}</span> : <span className="status-text is-success"><CheckCircle2 aria-hidden="true" /> 정상</span>}</td></tr>)}</tbody></table></div>
      </section>
      <ControlSignalSummary signalCount={signalCount} />
      </> : normality ? <NormalityResult result={result} /> : descriptive ? <DescriptiveStatisticsResult result={result} /> : regression ? <LinearRegressionResult result={result} /> : welchT ? <WelchTResult result={result} /> : mannWhitney ? <MannWhitneyResult result={result} /> : pairedT ? <PairedTResult result={result} /> : anova ? <OneWayAnovaResult result={result} /> : capability ? <CapabilityResult view={capability} /> : gageRr ? <GageRrResult view={gageRr} /> : nestedGageRr ? <NestedGageRrResult view={nestedGageRr} /> : attributeAgreement ? <AttributeAgreementResult view={attributeAgreement} /> : biasLinearity ? <GageBiasLinearityResult view={biasLinearity} /> : pareto ? <ParetoResult view={pareto} /> : cusum ? <CusumResult view={cusum} /> : ewma ? <EwmaResult view={ewma} /> : xbarR ? <XbarRResult view={xbarR} /> : xbarS ? <XbarSResult view={xbarS} /> : attributeChart ? <AttributeChartResult view={attributeChart} /> : rareEventChart ? <RareEventChartResult view={rareEventChart} /> : doe ? <DoeResult doe={doe} /> : optimizer ? <DoeDesirabilityResult optimizer={optimizer} /> : fractional ? <DoeFractionalResult design={fractional} /> : fractionalAnalysis ? <DoeFractionalAnalysisResult analysis={fractionalAnalysis} /> : boxBehnken ? <DoeBoxBehnkenResult design={boxBehnken} /> : boxBehnkenAnalysis ? <DoeQuadraticAnalysisResult analysis={boxBehnkenAnalysis} designLabel="Box–Behnken" methodLabel="Edge-midpoint design" /> : centralComposite ? <DoeCentralCompositeResult design={centralComposite} /> : centralCompositeAnalysis ? <DoeQuadraticAnalysisResult analysis={centralCompositeAnalysis} designLabel="중앙합성" methodLabel={centralCompositeAnalysis.rotatable ? "Rotatable" : "Face-centered"} /> : centralCompositeSurface ? <DoeCentralCompositeSurfaceResult surface={centralCompositeSurface} /> : plackettBurman ? <DoePlackettBurmanResult design={plackettBurman} /> : plackettBurmanAnalysis ? <DoePlackettBurmanAnalysisResult analysis={plackettBurmanAnalysis} /> : <section className="panel generic-result-panel"><header className="panel-heading"><div><span className="eyebrow">RESULT BUNDLE</span><h2>분석 결과 요약</h2></div></header><dl><div><dt>분석 유형</dt><dd>{result.analysis_type}</dd></div><div><dt>진단 항목</dt><dd>{Object.keys(result.diagnostics).length}개</dd></div><div><dt>결과 표</dt><dd>{Object.keys(result.tables).join(", ") || "없음"}</dd></div></dl></section>}
      {result.analysis_type.startsWith("spc.") && <SpcEvidenceActionPanel runId={run.run_id} result={result} />}
      {result.warnings.length > 0 && <section className="warning-panel"><AlertTriangle aria-hidden="true" /><div><h2>해석 전 확인</h2><ul>{result.warnings.map((warning) => <li key={warning}>{warning}</li>)}</ul></div></section>}
      {drawerOpen && <><button className="drawer-scrim" aria-label="계산 근거 닫기" onClick={closeDrawer} /><aside ref={drawer} className="detail-drawer" role="dialog" aria-modal="true" aria-labelledby="drawer-title"><header><div><span className="eyebrow">EVIDENCE</span><h2 id="drawer-title">계산 근거</h2></div><button ref={closeButton} className="icon-button" aria-label="닫기" onClick={closeDrawer}><X /></button></header>{worksheetSource && <section><h3>작업표 출처</h3><Link className="source-link" to={`/data/${worksheetSource.worksheet_id}`}><strong>{worksheetSource.column_name} · revision {worksheetSource.worksheet_revision}</strong><span>{worksheetSource.worksheet_id}</span></Link><dl><div><dt>작업표 digest</dt><dd className="digest">{worksheetSource.worksheet_digest}</dd></div></dl></section>}<section><h3>분석 가정</h3><ul>{result.assumptions.map((item) => <li key={item}>{item}</li>)}</ul></section><section><h3>공개 출처</h3>{result.provenance.map((source) => <a className="source-link" href={source.url} target="_blank" rel="noreferrer" key={source.url}><strong>{source.title}</strong><span>{source.authority}</span></a>)}</section><section><h3>재현 정보</h3><dl><div><dt>엔진</dt><dd>{result.engine_version}</dd></div><div><dt>Storage version</dt><dd>{run.storage_version}</dd></div><div><dt>ETag</dt><dd className="digest">{run.etag}</dd></div></dl></section></aside></>}
    </div>
  );
}

function statistic(value: number | null, digits = 4) {
  if (value === null) return "—";
  if (!Number.isFinite(value)) return value > 0 ? "∞" : "—";
  return value.toFixed(digits);
}

function NormalityResult({ result }: { result: StoredRun["result"] }) {
  const row = (result.tables.normality as { rows?: Array<Record<string, number>> } | undefined)?.rows?.[0];
  return <section className="panel table-panel"><header className="panel-heading"><div><span className="eyebrow">JARQUE–BERA</span><h2>정규성 검정 결과</h2></div></header><p>{result.diagnostics.reject_normality ? "유의수준에서 정규성 가정을 기각합니다. 공정능력·회귀의 가정과 대체 분석법을 검토하세요." : "유의수준에서 정규성 가정을 기각할 충분한 증거가 없습니다. 표본 크기와 도메인 지식을 함께 검토하세요."}</p>{row && <div className="table-scroll"><table><thead><tr><th>n</th><th>왜도</th><th>첨도</th><th>JB 통계량</th><th>p값</th></tr></thead><tbody><tr><td>{row.n}</td><td>{statistic(row.skewness)}</td><td>{statistic(row.kurtosis)}</td><td>{statistic(row.jb_statistic)}</td><td>{statistic(row.p_value)}</td></tr></tbody></table></div>}</section>;
}

function DescriptiveStatisticsResult({ result }: { result: StoredRun["result"] }) {
  const row = (result.tables.summary as { rows?: Array<Record<string, string | number | null>> } | undefined)?.rows?.[0];
  if (!row) return null;
  return <><section className="metric-grid result-metrics" aria-label="기초통계 요약"><article className="metric-card"><span>관측 수</span><strong>{String(row.n ?? "—")}</strong><small>{String(row.variable ?? "측정값")}</small></article><article className="metric-card"><span>평균</span><strong>{statistic(row.mean as number | null)}</strong><small>표준편차 {statistic(row.standard_deviation as number | null)}</small></article><article className="metric-card"><span>중앙값</span><strong>{statistic(row.median as number | null)}</strong><small>IQR {statistic(row.interquartile_range as number | null)}</small></article><article className="metric-card"><span>평균 95% 신뢰구간</span><strong className="metric-text">{statistic(row.mean_confidence_interval_lower as number | null)} ~ {statistic(row.mean_confidence_interval_upper as number | null)}</strong><small>t 분포 기반</small></article></section><section className="panel table-panel"><header className="panel-heading"><div><span className="eyebrow">DESCRIPTIVE STATISTICS</span><h2>중심과 산포</h2></div><span>{String(result.parameters.confidence_level ? `${Math.round(Number(result.parameters.confidence_level) * 100)}% 신뢰수준` : "—")}</span></header><div className="table-scroll"><table><caption>연속형 측정값의 기초통계</caption><thead><tr><th scope="col">최소</th><th scope="col">Q1</th><th scope="col">중앙값</th><th scope="col">Q3</th><th scope="col">최대</th><th scope="col">범위</th><th scope="col">변동계수</th></tr></thead><tbody><tr><td>{statistic(row.minimum as number | null)}</td><td>{statistic(row.q1 as number | null)}</td><td>{statistic(row.median as number | null)}</td><td>{statistic(row.q3 as number | null)}</td><td>{statistic(row.maximum as number | null)}</td><td>{statistic(row.range as number | null)}</td><td>{statistic(row.coefficient_of_variation as number | null)}</td></tr></tbody></table></div></section><section className="panel table-panel"><header className="panel-heading"><div><span className="eyebrow">DISTRIBUTION SHAPE</span><h2>분포 형태</h2></div></header><p>왜도와 초과첨도는 분포 형태를 요약하는 지표입니다. 정규성 판정이 필요하면 별도의 정규성 검정을 실행하세요.</p><div className="table-scroll"><table><caption>왜도와 초과첨도</caption><thead><tr><th scope="col">왜도</th><th scope="col">초과첨도</th><th scope="col">표준오차</th></tr></thead><tbody><tr><td>{statistic(row.skewness as number | null)}</td><td>{statistic(row.excess_kurtosis as number | null)}</td><td>{statistic(row.standard_error as number | null)}</td></tr></tbody></table></div></section></>;
}

function WelchTResult({ result }: { result: StoredRun["result"] }) { const row = (result.tables.test as { rows?: Array<Record<string, number | boolean>> } | undefined)?.rows?.[0]; const groups = (result.tables.group_summary as { rows?: Array<Record<string, string | number>> } | undefined)?.rows ?? []; if (!row) return null; if (result.analysis_type === "hypothesis.independent_tost_equivalence") return <><section className="metric-grid result-metrics"><article className="metric-card"><span>평균차</span><strong>{statistic(row.difference as number)}</strong></article><article className="metric-card"><span>90% 신뢰구간</span><strong>{statistic(row.confidence_interval_lower as number)} ~ {statistic(row.confidence_interval_upper as number)}</strong></article><article className="metric-card"><span>등가 판정</span><strong>{row.equivalent ? "등가" : "미확인"}</strong></article></section><section className="panel table-panel"><header className="panel-heading"><div><span className="eyebrow">TOST EQUIVALENCE</span><h2>독립 두 집단 등가성</h2></div></header><p>{row.equivalent ? "두 단측 검정이 모두 통과했습니다. 평균차가 사전 정의한 허용차 범위 안에 있다는 통계적 근거가 있습니다." : "두 단측 검정 중 하나 이상이 통과하지 못했습니다. 등가성을 확인할 충분한 근거가 없습니다."}</p><div className="table-scroll"><table><thead><tr><th>하한 허용차</th><th>상한 허용차</th><th>하한 p값</th><th>상한 p값</th><th>90% 신뢰구간</th></tr></thead><tbody><tr><td>{statistic(row.lower_margin as number)}</td><td>{statistic(row.upper_margin as number)}</td><td>{statistic(row.lower_p_value as number)}</td><td>{statistic(row.upper_p_value as number)}</td><td>{statistic(row.confidence_interval_lower as number)} ~ {statistic(row.confidence_interval_upper as number)}</td></tr></tbody></table></div></section></>; return <><section className="metric-grid result-metrics"><article className="metric-card"><span>평균차</span><strong>{statistic(row.difference as number)}</strong></article><article className="metric-card"><span>p값</span><strong>{statistic(row.p_value as number)}</strong></article><article className="metric-card"><span>신뢰구간</span><strong>{statistic(row.confidence_interval_lower as number)} ~ {statistic(row.confidence_interval_upper as number)}</strong></article></section><section className="panel table-panel"><header className="panel-heading"><div><span className="eyebrow">WELCH T-TEST</span><h2>독립표본 평균 비교</h2></div></header><p>{row.significant ? "유의수준에서 두 집단 평균이 같다는 가설을 기각합니다." : "유의수준에서 두 집단 평균이 다르다고 볼 충분한 증거가 없습니다."}</p><div className="table-scroll"><table><thead><tr><th>집단</th><th>n</th><th>평균</th><th>표본분산</th></tr></thead><tbody>{groups.map((group) => <tr key={String(group.group)}><th>{group.group}</th><td>{group.n}</td><td>{statistic(group.mean as number)}</td><td>{statistic(group.sample_variance as number)}</td></tr>)}</tbody></table></div></section></>; }

function MannWhitneyResult({ result }: { result: StoredRun["result"] }) { const row = (result.tables.test as { rows?: Array<Record<string, number | boolean>> } | undefined)?.rows?.[0]; const groups = (result.tables.group_summary as { rows?: Array<Record<string, string | number>> } | undefined)?.rows ?? []; if (!row) return null; return <><section className="metric-grid result-metrics"><article className="metric-card"><span>U 통계량</span><strong>{statistic(row.u as number)}</strong></article><article className="metric-card"><span>z</span><strong>{statistic(row.z_value as number)}</strong></article><article className="metric-card"><span>p값</span><strong>{statistic(row.p_value as number)}</strong></article></section><section className="panel table-panel"><header className="panel-heading"><div><span className="eyebrow">MANN–WHITNEY U</span><h2>독립 두 집단 순위 비교</h2></div></header><p>{row.significant ? "유의수준에서 두 집단의 분포 위치가 같다는 가설을 기각합니다." : "두 집단의 분포 위치가 다르다고 볼 충분한 증거가 없습니다."} 동점·연속성 보정 정규근사 결과입니다.</p><div className="table-scroll"><table><thead><tr><th>집단</th><th>n</th><th>평균 순위</th></tr></thead><tbody>{groups.map((group) => <tr key={String(group.group)}><th>{group.group}</th><td>{group.n}</td><td>{statistic(group.mean_rank as number)}</td></tr>)}</tbody></table></div></section></>; }

function PairedTResult({ result }: { result: StoredRun["result"] }) { const row = (result.tables.test as { rows?: Array<Record<string, number | boolean>> } | undefined)?.rows?.[0]; if (!row) return null; if (result.analysis_type === "hypothesis.wilcoxon_signed_rank") return <><section className="metric-grid result-metrics"><article className="metric-card"><span>W 통계량</span><strong>{statistic(row.w as number)}</strong></article><article className="metric-card"><span>z</span><strong>{statistic(row.z_value as number)}</strong></article><article className="metric-card"><span>p값</span><strong>{statistic(row.p_value as number)}</strong></article></section><section className="panel table-panel"><header className="panel-heading"><div><span className="eyebrow">WILCOXON SIGNED-RANK</span><h2>대응 측정값 순위 비교</h2></div></header><p>{row.significant ? "대응 측정값의 위치가 같다는 가설을 기각합니다." : "위치 차이에 대한 충분한 증거가 없습니다."} 0 차이는 제외한 동점·연속성 보정 정규근사 결과입니다.</p><div className="table-scroll"><table><thead><tr><th>W</th><th>양의 순위합</th><th>음의 순위합</th><th>z</th><th>p값</th></tr></thead><tbody><tr><td>{statistic(row.w as number)}</td><td>{statistic(row.w_plus as number)}</td><td>{statistic(row.w_minus as number)}</td><td>{statistic(row.z_value as number)}</td><td>{statistic(row.p_value as number)}</td></tr></tbody></table></div></section></>; return <><section className="metric-grid result-metrics"><article className="metric-card"><span>평균 차이</span><strong>{statistic(row.difference as number)}</strong></article><article className="metric-card"><span>p값</span><strong>{statistic(row.p_value as number)}</strong></article><article className="metric-card"><span>신뢰구간</span><strong>{statistic(row.confidence_interval_lower as number)} ~ {statistic(row.confidence_interval_upper as number)}</strong></article></section><section className="panel table-panel"><header className="panel-heading"><div><span className="eyebrow">PAIRED T-TEST</span><h2>대응 측정값 차이</h2></div><span>자유도 {row.degrees_of_freedom}</span></header><p>{row.significant ? "유의수준에서 대응 측정값의 평균 차이가 0이라는 가설을 기각합니다." : "유의수준에서 대응 측정값의 평균 차이가 0이 아니라고 볼 충분한 증거가 없습니다."}</p><div className="table-scroll"><table><thead><tr><th>평균 차이</th><th>표준오차</th><th>t</th><th>p값</th><th>신뢰구간</th></tr></thead><tbody><tr><td>{statistic(row.difference as number)}</td><td>{statistic(row.standard_error as number)}</td><td>{statistic(row.t_statistic as number)}</td><td>{statistic(row.p_value as number)}</td><td>{statistic(row.confidence_interval_lower as number)} ~ {statistic(row.confidence_interval_upper as number)}</td></tr></tbody></table></div></section></>; }

function OneWayAnovaResult({ result }: { result: StoredRun["result"] }) { if (result.analysis_type === "hypothesis.chi_square_independence") return <ChiSquareResult result={result} />; const groups = (result.tables.group_summary as { rows?: Array<Record<string, number | string>> } | undefined)?.rows ?? []; const d = result.diagnostics; if (result.analysis_type === "hypothesis.kruskal_wallis") return <><section className="metric-grid result-metrics"><article className="metric-card"><span>H</span><strong>{statistic(d.h_value as number | null)}</strong></article><article className="metric-card"><span>자유도</span><strong>{String(d.degrees_of_freedom ?? "—")}</strong></article><article className="metric-card"><span>p값</span><strong>{statistic(d.p_value as number | null)}</strong></article></section><section className="panel table-panel"><header className="panel-heading"><div><span className="eyebrow">KRUSKAL–WALLIS</span><h2>독립 집단 순위 비교</h2></div></header><p>{d.reject_equal_distributions ? "하나 이상의 집단 분포 위치 차이가 유의합니다. 어떤 집단이 다른지는 사후 비교로 확인하세요." : "집단 분포 위치 차이에 대한 충분한 증거가 없습니다."}</p><div className="table-scroll"><table><thead><tr><th>집단</th><th>n</th><th>평균 순위</th></tr></thead><tbody>{groups.map((group) => <tr key={String(group.group)}><th>{group.group}</th><td>{group.n}</td><td>{statistic(group.mean_rank as number)}</td></tr>)}</tbody></table></div></section></>; const anova = (result.tables.anova as { rows?: Array<Record<string, number | string | null>> } | undefined)?.rows ?? []; return <><section className="metric-grid result-metrics"><article className="metric-card"><span>F</span><strong>{statistic(d.f_statistic as number | null)}</strong></article><article className="metric-card"><span>p값</span><strong>{statistic(d.p_value as number | null)}</strong></article><article className="metric-card"><span>η²</span><strong>{statistic(d.eta_squared as number | null)}</strong></article></section><section className="panel table-panel"><header className="panel-heading"><div><span className="eyebrow">ONE-WAY ANOVA</span><h2>집단 평균 비교</h2></div></header><p>{d.reject_equal_means ? "하나 이상의 집단 평균 차이가 유의합니다. 어떤 집단이 다른지는 별도 사후 비교로 확인하세요." : "집단 평균 차이에 대한 충분한 통계적 증거가 없습니다."}</p><div className="table-scroll"><table><thead><tr><th>집단</th><th>n</th><th>평균</th></tr></thead><tbody>{groups.map((group) => <tr key={String(group.group)}><th>{group.group}</th><td>{group.n}</td><td>{statistic(group.mean as number)}</td></tr>)}</tbody></table></div><div className="table-scroll"><table><caption>분산분석표</caption><thead><tr><th>변동원</th><th>DF</th><th>SS</th><th>MS</th><th>F</th><th>p값</th></tr></thead><tbody>{anova.map((row) => <tr key={String(row.source)}><th>{row.source}</th><td>{row.df}</td><td>{statistic(row.sum_squares as number | null)}</td><td>{statistic(row.mean_square as number | null)}</td><td>{statistic(row.f_value as number | null)}</td><td>{statistic(row.p_value as number | null)}</td></tr>)}</tbody></table></div></section></>; }

function ChiSquareResult({ result }: { result: StoredRun["result"] }) { const d = result.diagnostics; const cells = (result.tables.cells as { rows?: Array<Record<string, string | number>> } | undefined)?.rows ?? []; return <><section className="metric-grid result-metrics"><article className="metric-card"><span>χ²</span><strong>{statistic(d.chi_square as number | null)}</strong></article><article className="metric-card"><span>p값</span><strong>{statistic(d.p_value as number | null)}</strong></article><article className="metric-card"><span>Cramér’s V</span><strong>{statistic(d.cramers_v as number | null)}</strong></article></section><section className="panel table-panel"><header className="panel-heading"><div><span className="eyebrow">CHI-SQUARE</span><h2>범주형 변수 연관성</h2></div><span>자유도 {String(d.degrees_of_freedom ?? "—")}</span></header><p>{d.reject_independence ? "두 범주형 변수는 독립이라는 가설을 기각합니다. 효과크기와 공정 맥락을 함께 검토하세요." : "두 범주형 변수의 연관성에 대한 충분한 통계적 증거가 없습니다."}</p><div className="table-scroll"><table><thead><tr><th>행 범주</th><th>열 범주</th><th>관측도수</th><th>기대도수</th></tr></thead><tbody>{cells.map((cell) => <tr key={`${cell.row}-${cell.column}`}><th>{cell.row}</th><td>{cell.column}</td><td>{cell.observed}</td><td>{statistic(cell.expected as number)}</td></tr>)}</tbody></table></div></section></>; }

function LinearRegressionResult({ result }: { result: StoredRun["result"] }) {
  if (result.analysis_type === "regression.best_subsets_ols") return <BestSubsetsResult result={result} />;
  if (result.analysis_type === "regression.regularized_linear") return <RegularizedRegressionResult result={result} />;
  if (result.analysis_type === "regression.ols_validation") return <OlsValidationResult result={result} />;
  if (result.analysis_type === "regression.logistic") return <LogisticRegressionResult result={result} />;
  if (result.analysis_type === "regression.poisson" || result.analysis_type === "regression.negative_binomial") return <CountRegressionResult result={result} />;
  const categorical = result.analysis_type === "regression.categorical_ols";
  const polynomial = result.analysis_type === "regression.polynomial_ols";
  const interaction = result.analysis_type === "regression.interaction_ols";
  const stepwise = result.analysis_type === "regression.stepwise_ols";
  const coefficients = (result.tables.coefficients as { rows?: Array<Record<string, string | number | boolean | null>> } | undefined)?.rows ?? [];
  const anova = (result.tables.anova as { rows?: Array<Record<string, string | number | null>> } | undefined)?.rows ?? [];
  const collinearity = (result.tables.collinearity as { rows?: Array<Record<string, string | number>> } | undefined)?.rows ?? [];
  const fittedValues = (result.tables.fitted_values as { rows?: Array<Record<string, number | null>> } | undefined)?.rows ?? [];
  const diagnostic = (name: string) => typeof result.diagnostics[name] === "number" ? result.diagnostics[name] as number : null;
  const predictionConfidence = diagnostic("prediction_interval_confidence");
  const influenceRows = fittedValues.filter((row) => typeof row.cooks_distance === "number");
  const influenceThresholds = result.diagnostics.influence_thresholds as Record<string, number> | undefined;
  const normalityStatus = result.diagnostics.residual_normality_status as string | undefined;
  const normalityRejected = result.diagnostics.reject_residual_normality === true;
  const varianceStatus = result.diagnostics.heteroscedasticity_status as string | undefined;
  const varianceRejected = result.diagnostics.reject_constant_variance === true;
  const selectionHistory = (result.tables.selection_history as { rows?: Array<Record<string, string | number>> } | undefined)?.rows ?? [];
  return <>
    <section className="metric-grid result-metrics" aria-label={`${categorical ? "범주형 OLS" : polynomial ? "다항" : interaction ? "교호작용" : "선형"}회귀 모형 적합도`}>
      <article className="metric-card"><span>R²</span><strong>{statistic(diagnostic("r_squared"))}</strong><small>설명된 변동 비율</small></article>
      <article className="metric-card"><span>수정 R²</span><strong>{statistic(diagnostic("adjusted_r_squared"))}</strong><small>변수 수 보정</small></article>
      <article className="metric-card"><span>잔차 표준오차</span><strong>{statistic(diagnostic("residual_standard_error"))}</strong><small>모형 오차의 크기</small></article>
      <article className="metric-card"><span>{stepwise ? "선택 AICc" : "모형 p값"}</span><strong>{statistic(diagnostic(stepwise ? "aicc" : "model_p_value"))}</strong><small>{stepwise ? "자동 선택 비교 기준" : "전체 모형 F 검정"}</small></article>
    </section>
    <section className="panel table-panel"><header className="panel-heading"><div><span className="eyebrow">OLS</span><h2>{categorical ? "범주형 OLS 회귀 결과" : polynomial ? "다항회귀 결과" : interaction ? "교호작용 회귀 결과" : stepwise ? "단계선택 회귀 결과" : "선형회귀 결과"}</h2></div><span>{categorical ? `기준 범주 ${Object.entries((result.parameters.reference_levels as Record<string, string> | undefined) ?? {}).map(([name, level]) => `${name}: ${level}`).join(" · ") || "—"}` : `잔차 자유도 ${diagnostic("residual_degrees_of_freedom") ?? "—"}`}</span></header><p>{categorical ? "각 계수는 표시된 기준 범주와 비교한 평균 차이입니다. 범주별 표본 수와 잔차·공정 조건을 함께 검토한 뒤 운영 설정을 확정하세요." : polynomial ? `차수 ${String(result.parameters.degree ?? "—")}의 항은 관측된 X 범위에서만 해석하세요. 상호작용과 자동 변수선택은 포함하지 않습니다.` : interaction ? "두 설명변수의 곱(X₁×X₂)으로 설정 효과의 결합 변화를 추정합니다. 주효과와 교호작용을 함께 해석하고, 공정 제약·잔차·확인 실험으로 재검증하세요." : stepwise ? "선택된 항은 탐색 결과입니다. 계수의 유의성, 공정 지식, 잔차·공선성·독립 검증을 함께 검토한 뒤 확인 실험으로 재검증하세요." : "계수의 유의성만으로 운영 설정을 확정하지 말고 잔차·공정 제약·확인 실험을 함께 검토하세요."}</p><div className="table-scroll"><table><caption>회귀 계수와 유의성</caption><thead><tr><th>항</th><th>계수</th><th>표준오차</th><th>t</th><th>p값</th><th>판정</th></tr></thead><tbody>{coefficients.map((row) => <tr key={String(row.term)}><th>{row.term}</th><td>{statistic(row.coefficient as number | null)}</td><td>{statistic(row.standard_error as number | null)}</td><td>{statistic(row.t_value as number | null)}</td><td>{statistic(row.p_value as number | null)}</td><td>{row.significant ? "유의" : "비유의"}</td></tr>)}</tbody></table></div></section>
    <section className="panel table-panel"><header className="panel-heading"><div><span className="eyebrow">ANOVA</span><h2>모형 분산분석</h2></div><span>F {statistic(diagnostic("model_f_statistic"))}</span></header><div className="table-scroll"><table><caption>모형·오차·전체 변동</caption><thead><tr><th>변동원</th><th>DF</th><th>SS</th><th>MS</th><th>F</th><th>p값</th></tr></thead><tbody>{anova.map((row) => <tr key={String(row.source)}><th>{row.source}</th><td>{row.degrees_of_freedom}</td><td>{statistic(row.sum_squares as number | null)}</td><td>{statistic(row.mean_square as number | null)}</td><td>{statistic(row.f_value as number | null)}</td><td>{statistic(row.p_value as number | null)}</td></tr>)}</tbody></table></div></section>
    {collinearity.length > 0 && <section className="panel table-panel"><header className="panel-heading"><div><span className="eyebrow">COLLINEARITY</span><h2>공선성 진단</h2></div><span>최대 VIF {statistic(diagnostic("maximum_vif"))}</span></header><p>VIF는 다른 설명변수와의 중복 정보 때문에 계수 추정의 불확실성이 커지는 정도를 보여줍니다. 공정 지식과 함께 중복 X를 검토하세요.</p><div className="table-scroll"><table><caption>설명변수별 분산팽창계수와 허용도</caption><thead><tr><th>설명변수</th><th>VIF</th><th>허용도</th></tr></thead><tbody>{collinearity.map((row) => <tr key={String(row.term)}><th>{row.term}</th><td>{statistic(row.vif as number | null)}</td><td>{statistic(row.tolerance as number | null)}</td></tr>)}</tbody></table></div></section>}
    <section className="panel table-panel"><header className="panel-heading"><div><span className="eyebrow">RESIDUAL REVIEW</span><h2>관측값별 적합과 잔차</h2></div><span>높은 leverage와 큰 잔차를 함께 검토</span></header><p>{predictionConfidence === null ? "예측구간은 현재 결과에 포함되지 않았습니다." : `예측구간은 같은 X 조건에서 새 관측값이 들어올 범위를 ${(predictionConfidence * 100).toFixed(0)}% 수준으로 나타냅니다.`}</p><div className="table-scroll"><table><caption>원 관측값, 모형 적합값과 잔차</caption><thead><tr><th>관측</th><th>실제값</th><th>적합값</th><th>예측구간</th><th>잔차</th><th>Leverage</th></tr></thead><tbody>{fittedValues.map((row) => <tr key={row.observation}><th>{row.observation}</th><td>{statistic(row.actual ?? null)}</td><td>{statistic(row.fitted ?? null)}</td><td>{row.prediction_interval_lower === null || row.prediction_interval_upper === null ? "—" : `${statistic(row.prediction_interval_lower)} ~ ${statistic(row.prediction_interval_upper)}`}</td><td>{statistic(row.residual ?? null)}</td><td>{statistic(row.leverage ?? null)}</td></tr>)}</tbody></table></div></section>
    {influenceRows.length > 0 && <section className="panel table-panel"><header className="panel-heading"><div><span className="eyebrow">INFLUENCE</span><h2>영향 관측치 진단</h2></div><span>Cook's D 기준 {statistic(influenceThresholds?.cooks_distance ?? null)}</span></header><p>큰 Cook's D·DFFITS 또는 학생화 잔차는 회귀식에 과도하게 영향을 주는 관측치일 수 있습니다. 삭제하지 말고 측정·공정 이력을 먼저 검토하세요.</p><div className="table-scroll"><table><caption>관측별 영향도 진단</caption><thead><tr><th>관측</th><th>표준화 잔차</th><th>학생화 잔차</th><th>Cook's D</th><th>DFFITS</th></tr></thead><tbody>{influenceRows.map((row) => <tr key={row.observation}><th>{row.observation}</th><td>{statistic(row.standardized_residual ?? null)}</td><td>{statistic(row.studentized_residual ?? null)}</td><td>{statistic(row.cooks_distance ?? null)}</td><td>{statistic(row.dffits ?? null)}</td></tr>)}</tbody></table></div></section>}
    {(normalityStatus || varianceStatus) && <section className="panel table-panel"><header className="panel-heading"><div><span className="eyebrow">ASSUMPTION DIAGNOSTICS</span><h2>잔차 가정 진단</h2></div><span>α {statistic(result.parameters.alpha as number | null)}</span></header><p>검정 결과만으로 원인을 단정하지 마세요. 이상 관측치·누락 변수·공정 변화·시간 의존성을 함께 확인하고, 필요하면 모형을 재지정하거나 독립 검증하세요.</p><div className="table-scroll"><table><caption>잔차 정규성 및 등분산성 근사 검정</caption><thead><tr><th>가정</th><th>방법</th><th>통계량</th><th>자유도</th><th>p값</th><th>판정</th></tr></thead><tbody><tr><th>정규성</th><td>Jarque–Bera (근사)</td><td>{statistic(diagnostic("residual_normality_statistic"))}</td><td>2</td><td>{statistic(diagnostic("residual_normality_p_value"))}</td><td>{normalityStatus === "unavailable_zero_variation" ? "잔차 변동 없음" : normalityRejected ? "정규성 가정 기각" : "기각할 증거 없음"}</td></tr><tr><th>등분산성</th><td>Breusch–Pagan LM</td><td>{statistic(diagnostic("heteroscedasticity_statistic"))}</td><td>{String(result.diagnostics.heteroscedasticity_degrees_of_freedom ?? "—")}</td><td>{statistic(diagnostic("heteroscedasticity_p_value"))}</td><td>{varianceStatus === "unavailable_zero_variation" ? "잔차 변동 없음" : varianceRejected ? "등분산성 가정 기각" : "기각할 증거 없음"}</td></tr></tbody></table></div></section>}
    {selectionHistory.length > 0 && <section className="panel table-panel"><header className="panel-heading"><div><span className="eyebrow">MODEL SELECTION</span><h2>모형 선택 이력</h2></div><span>AICc·BIC가 낮을수록 적합</span></header><p>자동 선택 결과는 후보 탐색용입니다. 공정 지식·공선성·독립 검증을 함께 검토하세요.</p><div className="table-scroll"><table><caption>단계별 변수 진입과 제거</caption><thead><tr><th>단계</th><th>동작</th><th>항</th><th>AICc</th><th>BIC</th></tr></thead><tbody>{selectionHistory.map((row) => <tr key={`${row.step}-${row.term}`}><th>{row.step}</th><td>{row.action === "enter" ? "진입" : "제거"}</td><td>{row.term}</td><td>{statistic(row.aicc as number)}</td><td>{statistic(row.bic as number)}</td></tr>)}</tbody></table></div></section>}
  </>;
}

function BestSubsetsResult({ result }: { result: StoredRun["result"] }) {
  const rows = (result.tables.model_comparison as { rows?: Array<Record<string, string | number | string[]>> } | undefined)?.rows ?? [];
  return <section className="panel table-panel"><header className="panel-heading"><div><span className="eyebrow">BEST SUBSETS</span><h2>후보 모형 비교</h2></div><span>{String(result.parameters.examined_model_count ?? "—")}개 모형 평가</span></header><p>AICc·BIC·PRESS가 낮은 모형을 우선 검토하되, 공정 지식·검증오차·공선성을 함께 확인하세요.</p><div className="table-scroll"><table><caption>크기별 최적 부분집합 모형</caption><thead><tr><th>항</th><th>개수</th><th>수정 R²</th><th>PRESS</th><th>Cp</th><th>AICc</th><th>BIC</th></tr></thead><tbody>{rows.map((row) => <tr key={String(row.terms)}><th>{Array.isArray(row.terms) ? row.terms.join(", ") : row.terms}</th><td>{row.term_count}</td><td>{statistic(row.adjusted_r_squared as number)}</td><td>{statistic(row.press as number)}</td><td>{statistic(row.mallows_cp as number)}</td><td>{statistic(row.aicc as number)}</td><td>{statistic(row.bic as number)}</td></tr>)}</tbody></table></div></section>;
}

function RegularizedRegressionResult({ result }: { result: StoredRun["result"] }) {
  const coefficients = (result.tables.coefficients as { rows?: Array<Record<string, string | number | boolean>> } | undefined)?.rows ?? [];
  const lambdas = (result.tables.lambda_selection as { rows?: Array<Record<string, number>> } | undefined)?.rows ?? [];
  return <><section className="metric-grid result-metrics"><article className="metric-card"><span>선택 λ</span><strong>{statistic(result.parameters.selected_lambda as number | null)}</strong><small>{String(result.parameters.method ?? "—")}</small></article><article className="metric-card"><span>CV RMSE</span><strong>{statistic(result.diagnostics.cv_rmse as number | null)}</strong><small>{String(result.parameters.fold_count ?? "—")} fold</small></article><article className="metric-card"><span>비영 계수</span><strong>{String(result.diagnostics.nonzero_coefficient_count ?? "—")}</strong><small>Intercept 제외</small></article><article className="metric-card"><span>R²</span><strong>{statistic(result.diagnostics.r_squared as number | null)}</strong><small>학습 데이터 적합도</small></article></section><section className="panel table-panel"><header className="panel-heading"><div><span className="eyebrow">REGULARIZED REGRESSION</span><h2>정규화 계수</h2></div></header><p>선택된 λ는 교차검증 RMSE가 가장 낮은 후보입니다. Lasso의 0 계수는 예측 변수 제외 신호이지만 공정 원인 부재를 뜻하지는 않습니다.</p><div className="table-scroll"><table><thead><tr><th>항</th><th>원 단위 계수</th><th>표준화 계수</th><th>제로화</th></tr></thead><tbody>{coefficients.map((row) => <tr key={String(row.term)}><th>{row.term}</th><td>{statistic(row.coefficient as number)}</td><td>{statistic(row.standardized_coefficient as number)}</td><td>{row.zeroed ? "예" : "아니오"}</td></tr>)}</tbody></table></div></section><section className="panel table-panel"><header className="panel-heading"><div><span className="eyebrow">LAMBDA SELECTION</span><h2>교차검증 λ 비교</h2></div></header><div className="table-scroll"><table><thead><tr><th>λ</th><th>CV RMSE</th></tr></thead><tbody>{lambdas.map((row) => <tr key={row.lambda}><th>{statistic(row.lambda)}</th><td>{statistic(row.cv_rmse)}</td></tr>)}</tbody></table></div></section></>;
}

function OlsValidationResult({ result }: { result: StoredRun["result"] }) {
  const folds = (result.tables.fold_summary as { rows?: Array<Record<string, number>> } | undefined)?.rows ?? [];
  const predictions = (result.tables.held_out_predictions as { rows?: Array<Record<string, number>> } | undefined)?.rows ?? [];
  return <><section className="metric-grid result-metrics" aria-label="회귀 모형 검증 요약"><article className="metric-card"><span>RMSE</span><strong>{statistic(result.diagnostics.rmse as number | null)}</strong><small>홀드아웃 예측 오차</small></article><article className="metric-card"><span>MAE</span><strong>{statistic(result.diagnostics.mae as number | null)}</strong><small>절대오차 평균</small></article><article className="metric-card"><span>예측 R²</span><strong>{statistic(result.diagnostics.r_squared_pred as number | null)}</strong><small>검증 행 설명력</small></article></section><section className="panel table-panel"><header className="panel-heading"><div><span className="eyebrow">MODEL VALIDATION</span><h2>분할별 예측오차</h2></div><span>{String(result.parameters.validation_method ?? "—")} · {String(result.parameters.fold_count ?? "—")}개 분할</span></header><p>각 행은 해당 분할의 학습에 포함되지 않은 예측 결과입니다. 시간 순서·공정 변경·데이터 누출 가능성을 별도로 검토하세요.</p><div className="table-scroll"><table><caption>분할별 학습 및 검증 오차</caption><thead><tr><th>분할</th><th>학습 수</th><th>검증 수</th><th>RMSE</th><th>MAE</th></tr></thead><tbody>{folds.map((row) => <tr key={row.fold}><th>{row.fold}</th><td>{row.train_size}</td><td>{row.test_size}</td><td>{statistic(row.rmse)}</td><td>{statistic(row.mae)}</td></tr>)}</tbody></table></div></section><section className="panel table-panel"><header className="panel-heading"><div><span className="eyebrow">HELD-OUT PREDICTIONS</span><h2>검증 행 예측값</h2></div></header><div className="table-scroll"><table><caption>학습에서 제외된 관측값의 실제·예측값</caption><thead><tr><th>분할</th><th>관측</th><th>실제값</th><th>예측값</th><th>잔차</th></tr></thead><tbody>{predictions.map((row) => <tr key={row.observation}><td>{row.fold}</td><th>{row.observation}</th><td>{statistic(row.actual)}</td><td>{statistic(row.predicted)}</td><td>{statistic(row.residual)}</td></tr>)}</tbody></table></div></section></>;
}

function CountRegressionResult({ result }: { result: StoredRun["result"] }) {
  const coefficients = (result.tables.coefficients as { rows?: Array<Record<string, string | number | boolean | null>> } | undefined)?.rows ?? [];
  const fitted = (result.tables.fitted_values as { rows?: Array<Record<string, number>> } | undefined)?.rows ?? [];
  const negativeBinomial = result.analysis_type === "regression.negative_binomial";
  const dispersionRatio = (negativeBinomial ? result.diagnostics.pearson_dispersion_ratio : result.diagnostics.dispersion_ratio) as number | undefined;
  const dispersionStatus = result.diagnostics.dispersion_status as string | undefined;
  const dispersionLabel = dispersionStatus === "overdispersed" ? "과산포 검토 필요" : dispersionStatus === "underdispersed" ? "과소산포 검토 필요" : "Poisson 가정과 일치";
  return <>
    <section className="metric-grid result-metrics" aria-label={`${negativeBinomial ? "음이항" : "Poisson"} 회귀 적합도 요약`}>
      <article className="metric-card"><span>{negativeBinomial ? "로그우도" : "Deviance"}</span><strong>{statistic((negativeBinomial ? result.diagnostics.log_likelihood : result.diagnostics.deviance) as number | null)}</strong><small>{negativeBinomial ? "NB2 최대우도" : "작을수록 포화모형에 가까움"}</small></article>
      <article className="metric-card"><span>잔차 자유도</span><strong>{String(result.diagnostics.residual_degrees_of_freedom ?? "—")}</strong><small>추정 후 남은 정보</small></article>
      <article className="metric-card"><span>예측 건수 합계</span><strong>{statistic(result.diagnostics.predicted_count_total as number | null)}</strong><small>관측 건수와 비교</small></article>
      <article className="metric-card"><span>{negativeBinomial ? "분산모수 α" : "Pearson 산포비"}</span><strong>{statistic((negativeBinomial ? result.diagnostics.dispersion_alpha : dispersionRatio) as number | null)}</strong><small>{negativeBinomial ? "Var(Y)=μ+αμ²" : dispersionLabel}</small></article>
    </section>
    {!negativeBinomial && <section className="panel table-panel">
      <header className="panel-heading"><div><span className="eyebrow">DISPERSION DIAGNOSTIC</span><h2>Poisson 산포 가정 점검</h2></div><span>{dispersionLabel}</span></header>
      <p>{dispersionStatus === "overdispersed" ? "과산포 신호가 있어 현재 Poisson 표준오차와 p값이 과도하게 낙관적일 수 있습니다. 영과다·군집·누락된 설명변수를 확인하고, 필요하면 음이항 또는 준-Poisson 모형을 별도 검토하세요." : dispersionStatus === "underdispersed" ? "과소산포 신호가 있어 독립 표본과 계수 발생 과정을 재검토하세요." : "Pearson 산포 진단에서 Poisson 평균·분산 가정과 뚜렷하게 다른 증거는 나타나지 않았습니다. 표본 수와 공정 맥락은 별도로 검토하세요."}</p>
      <div className="table-scroll"><table><caption>Pearson χ² 기반 산포 진단</caption><thead><tr><th scope="col">Pearson χ²</th><th scope="col">잔차 자유도</th><th scope="col">산포비</th><th scope="col">근사 p값</th><th scope="col">판정</th></tr></thead><tbody><tr><td>{statistic(result.diagnostics.pearson_chi_square as number | null)}</td><td>{String(result.diagnostics.residual_degrees_of_freedom ?? "—")}</td><td>{statistic(dispersionRatio ?? null)}</td><td>{statistic(result.diagnostics.dispersion_p_value as number | null)}</td><td>{dispersionLabel}</td></tr></tbody></table></div>
    </section>}
    {negativeBinomial && <section className="panel table-panel"><header className="panel-heading"><div><span className="eyebrow">DISPERSION MODEL</span><h2>음이항 과산포 모수</h2></div><span>NB2</span></header><p>α가 양수이면 평균보다 큰 분산을 허용합니다. 이 모형은 과산포를 흡수하지만 영과다·군집·누락 변수를 원인으로 판정하지는 않습니다.</p><div className="table-scroll"><table><caption>추정된 NB2 분산모수와 Pearson 적합도</caption><thead><tr><th scope="col">α</th><th scope="col">α 표준오차</th><th scope="col">Pearson χ²</th><th scope="col">Pearson 산포비</th><th scope="col">AIC</th></tr></thead><tbody><tr><td>{statistic(result.diagnostics.dispersion_alpha as number | null)}</td><td>{statistic(result.diagnostics.dispersion_alpha_standard_error as number | null)}</td><td>{statistic(result.diagnostics.pearson_chi_square as number | null)}</td><td>{statistic(dispersionRatio ?? null)}</td><td>{statistic(result.diagnostics.aic as number | null)}</td></tr></tbody></table></div></section>}
    <section className="panel table-panel">
      <header className="panel-heading"><div><span className="eyebrow">{negativeBinomial ? "NEGATIVE BINOMIAL" : "POISSON"} REGRESSION</span><h2>발생률비와 유의성</h2></div></header>
      <p>발생률비(IRR)는 다른 변수가 고정된 상태에서 X가 1단위 증가할 때 기대 발생 건수가 몇 배로 바뀌는지 나타냅니다. {negativeBinomial ? "NB2는 과산포를 허용하지만 관측의 독립성과 올바른 평균구조는 별도로 검토해야 합니다." : "Poisson의 평균·분산 가정이 맞는지 별도로 검토하세요."}</p>
      <div className="table-scroll"><table><caption>{negativeBinomial ? "음이항" : "Poisson"} 회귀 계수, 발생률비와 95% 신뢰구간</caption><thead><tr><th scope="col">항</th><th scope="col">계수</th><th scope="col">IRR</th><th scope="col">IRR 95% 신뢰구간</th><th scope="col">표준오차</th><th scope="col">z</th><th scope="col">p값</th><th scope="col">판정</th></tr></thead><tbody>{coefficients.map((row) => <tr key={String(row.term)}><th scope="row">{row.term}</th><td>{statistic(row.coefficient as number | null)}</td><td>{statistic(row.incidence_rate_ratio as number | null)}</td><td>{statistic(row.irr_ci_lower as number | null)} ~ {statistic(row.irr_ci_upper as number | null)}</td><td>{statistic(row.standard_error as number | null)}</td><td>{statistic(row.z_value as number | null)}</td><td>{statistic(row.p_value as number | null)}</td><td>{row.significant ? "유의" : "비유의"}</td></tr>)}</tbody></table></div>
    </section>
    <section className="panel table-panel">
      <header className="panel-heading"><div><span className="eyebrow">FITTED COUNTS</span><h2>관측별 예측 건수</h2></div></header>
      <div className="table-scroll"><table><caption>실제 건수와 {negativeBinomial ? "음이항" : "Poisson"} 모형 예측 건수</caption><thead><tr><th scope="col">관측</th><th scope="col">실제 건수</th><th scope="col">예측 건수</th></tr></thead><tbody>{fitted.map((row) => <tr key={row.observation}><th scope="row">{row.observation}</th><td>{statistic(row.actual)}</td><td>{statistic(row.predicted_count)}</td></tr>)}</tbody></table></div>
    </section>
  </>;
}

function LogisticRegressionResult({ result }: { result: StoredRun["result"] }) {
  const coefficients = (result.tables.coefficients as { rows?: Array<Record<string, string | number | boolean | null>> } | undefined)?.rows ?? [];
  const fitted = (result.tables.fitted_values as { rows?: Array<Record<string, number>> } | undefined)?.rows ?? [];
  const threshold = (result.diagnostics.classification_threshold as number | undefined) ?? 0.5;
  const accuracy = result.diagnostics.classification_accuracy as number | undefined;
  const classified = fitted.filter((row) => (row.predicted_probability >= threshold ? 1 : 0) === row.actual).length;
  return <>
    <section className="metric-grid result-metrics" aria-label="로지스틱 회귀 적합도 요약">
      <article className="metric-card"><span>사건 수</span><strong>{String(result.diagnostics.event_count ?? "—")}</strong><small>Y=1 관측</small></article>
      <article className="metric-card"><span>로그우도</span><strong>{statistic(result.diagnostics.log_likelihood as number | null)}</strong><small>값이 클수록 적합</small></article>
      <article className="metric-card"><span>분류 정확도</span><strong>{accuracy === undefined ? "—" : `${(accuracy * 100).toFixed(1)}%`}</strong><small>기준 {threshold.toFixed(2)} · {fitted.length ? `${classified}/${fitted.length}` : "—"}</small></article>
    </section>
    <section className="panel table-panel">
      <header className="panel-heading"><div><span className="eyebrow">LOGISTIC REGRESSION</span><h2>오즈비와 유의성</h2></div></header>
      <p>오즈비는 다른 변수가 고정된 상태에서 X가 1단위 증가할 때 사건(Y=1)의 오즈 변화입니다. 신뢰구간이 1을 포함하면 해당 유의수준에서 효과가 불확실할 수 있습니다.</p>
      <div className="table-scroll"><table><caption>로지스틱 회귀 계수, 오즈비와 95% 신뢰구간</caption><thead><tr><th scope="col">항</th><th scope="col">계수</th><th scope="col">오즈비</th><th scope="col">오즈비 95% 신뢰구간</th><th scope="col">표준오차</th><th scope="col">z</th><th scope="col">p값</th><th scope="col">판정</th></tr></thead><tbody>{coefficients.map((row) => <tr key={String(row.term)}><th scope="row">{row.term}</th><td>{statistic(row.coefficient as number | null)}</td><td>{statistic(row.odds_ratio as number | null)}</td><td>{statistic(row.odds_ratio_ci_lower as number | null)} ~ {statistic(row.odds_ratio_ci_upper as number | null)}</td><td>{statistic(row.standard_error as number | null)}</td><td>{statistic(row.z_value as number | null)}</td><td>{statistic(row.p_value as number | null)}</td><td>{row.significant ? "유의" : "비유의"}</td></tr>)}</tbody></table></div>
    </section>
    <section className="panel table-panel">
      <header className="panel-heading"><div><span className="eyebrow">PREDICTED PROBABILITY</span><h2>관측별 예측확률</h2></div><span>분류 기준 {threshold.toFixed(2)}</span></header>
      <div className="table-scroll"><table><caption>관측별 실제 결과와 로지스틱 예측확률</caption><thead><tr><th scope="col">관측</th><th scope="col">실제 Y</th><th scope="col">예측확률</th><th scope="col">분류</th></tr></thead><tbody>{fitted.map((row) => <tr key={row.observation}><th scope="row">{row.observation}</th><td>{row.actual}</td><td>{statistic(row.predicted_probability)}</td><td>{row.predicted_probability >= threshold ? "사건(1)" : "비사건(0)"}</td></tr>)}</tbody></table></div>
    </section>
  </>;
}

function CapabilityResult({ view }: { view: CapabilityView }) {
  const indexLabel = view.model === "normal" ? "Cp/Cpk · Pp/Ppk" : "Cnp/Cnpk";
  const indexRows = Object.entries(view.indices);
  const defectRows = Object.entries(view.nonconformance);
  return <>
    <section className="metric-grid result-metrics" aria-label="공정능력 분석 요약">
      <article className="metric-card"><span>분석 방식</span><strong className="metric-text">{view.model === "normal" ? "정규" : "경험적 비정규"}</strong><small>{indexLabel}</small></article>
      <article className="metric-card"><span>관측 수</span><strong>{view.count}</strong><small>입력 측정값</small></article>
      <article className="metric-card"><span>{view.model === "normal" ? "평균" : "중앙값"}</span><strong>{statistic(view.location)}</strong><small>공정 중심</small></article>
      <article className="metric-card"><span>{view.model === "normal" ? "전체 σ" : "등가 σ"}</span><strong>{statistic(view.overallSigma)}</strong><small>장기 변동 추정</small></article>
      {view.withinSigma !== null && <article className="metric-card"><span>군내 σ</span><strong>{statistic(view.withinSigma)}</strong><small>이동범위 기반</small></article>}
    </section>
    <section className="panel table-panel"><header className="panel-heading"><div><span className="eyebrow">CAPABILITY INDICES</span><h2>능력 지수</h2></div><span>{view.model === "normal" ? "군내·전체 변동 비교" : "경험적 꼬리 분위수 기반"}</span></header><div className="table-scroll"><table><thead><tr><th scope="col">지수</th><th scope="col">값</th></tr></thead><tbody>{indexRows.map(([name, value]) => <tr key={name}><td>{name.toUpperCase()}</td><td>{statistic(value)}</td></tr>)}</tbody></table></div></section>
    <section className="panel table-panel"><header className="panel-heading"><div><span className="eyebrow">NONCONFORMANCE</span><h2>규격 이탈</h2></div><span>관측값 기준 {view.model === "normal" ? "예측 PPM 포함" : "관측 PPM"}</span></header><div className="table-scroll"><table><thead><tr><th scope="col">항목</th><th scope="col">값</th></tr></thead><tbody>{defectRows.map(([name, value]) => <tr key={name}><td>{name.replaceAll("_", " ")}</td><td>{name.includes("ppm") ? statistic(value, 1) : statistic(value)}</td></tr>)}</tbody></table></div>{view.lowerQuantile !== null && <p className="supporting-copy">경험적 하위 분위수 {statistic(view.lowerQuantile)}, 상위 분위수 {statistic(view.upperQuantile)}를 사용했습니다.</p>}</section>
  </>;
}

function MsaAnovaTable({ rows }: { rows: GageRrView["anova"] }) {
  return <div className="table-scroll"><table><thead><tr><th scope="col">변동원</th><th scope="col">DF</th><th scope="col">SS</th><th scope="col">MS</th><th scope="col">검정 분모</th><th scope="col">F</th><th scope="col">p</th><th scope="col">판정 (α=0.05)</th></tr></thead><tbody>{rows.map((row) => <tr key={row.source}><td>{row.source.replaceAll("_", " ")}</td><td>{row.df}</td><td>{statistic(row.ss)}</td><td>{statistic(row.ms)}</td><td>{row.denominator_source?.replaceAll("_", " ") ?? "—"}</td><td>{statistic(row.f_value ?? null)}</td><td>{statistic(row.p_value ?? null)}</td><td>{row.significant === true ? <span className="status-text is-success"><CheckCircle2 aria-hidden="true" /> 유의</span> : row.significant === false ? "비유의" : "해당없음"}</td></tr>)}</tbody></table></div>;
}

function GageRrResult({ view }: { view: GageRrView }) {
  return <>
    <section className="metric-grid result-metrics" aria-label="교차 Gage R&R 요약">
      <article className="metric-card"><span>측정값</span><strong>{view.study.measurement_count}</strong><small>균형 교차 설계</small></article>
      <article className="metric-card"><span>부품</span><strong>{view.study.part_count}</strong><small>Part-to-part</small></article>
      <article className="metric-card"><span>작업자</span><strong>{view.study.operator_count}</strong><small>재현성 요인</small></article>
      <article className="metric-card"><span>셀당 반복</span><strong>{view.study.replicates_per_cell}</strong><small>모든 셀 동일</small></article>
      <article className="metric-card"><span>구별 범주 수</span><strong>{view.ndc === null ? "∞" : view.ndc}</strong><small>NDC</small></article>
    </section>
    <VarianceComponentTable components={view.components} title="분산성분과 Study variation" />
    <section className="panel table-panel"><header className="panel-heading"><div><span className="eyebrow">ANOVA</span><h2>균형 교차 ANOVA</h2></div><span>전체 평균 {statistic(view.study.grand_mean)} · 비풀링 F 검정</span></header><MsaAnovaTable rows={view.anova} /></section>
  </>;
}

function NestedGageRrResult({ view }: { view: NestedGageRrView }) {
  return <>
    <section className="metric-grid result-metrics" aria-label="중첩 Gage R&R 요약">
      <article className="metric-card"><span>측정값</span><strong>{view.study.measurement_count}</strong><small>균형 중첩 설계</small></article>
      <article className="metric-card"><span>작업자</span><strong>{view.study.operator_count}</strong><small>부품이 작업자에 중첩</small></article>
      <article className="metric-card"><span>작업자당 부품</span><strong>{view.study.parts_per_operator}</strong><small>모든 작업자 동일</small></article>
      <article className="metric-card"><span>부품당 반복</span><strong>{view.study.replicates_per_part}</strong><small>모든 셀 동일</small></article>
    </section>
    <VarianceComponentTable components={view.components} title="중첩 설계 분산성분" />
    <section className="panel table-panel"><header className="panel-heading"><div><span className="eyebrow">NESTED ANOVA</span><h2>작업자 내 부품 ANOVA</h2></div><span>전체 평균 {statistic(view.study.grand_mean)} · 비풀링 F 검정</span></header><MsaAnovaTable rows={view.anova} /></section>
  </>;
}

function VarianceComponentTable({ components, title }: { components: GageRrView["components"]; title: string }) {
  const hasConfidenceInterval = components.some((row) => row.variance_confidence_interval);
  return <section className="panel table-panel"><header className="panel-heading"><div><span className="eyebrow">VARIANCE COMPONENTS</span><h2>{title}</h2></div>{hasConfidenceInterval && <span>반복성 분산 95% 신뢰구간 포함</span>}</header><div className="table-scroll"><table><thead><tr><th scope="col">변동원</th><th scope="col">분산</th>{hasConfidenceInterval && <th scope="col">분산 신뢰구간</th>}<th scope="col">Study variation</th><th scope="col">% Contribution</th><th scope="col">% Study variation</th></tr></thead><tbody>{components.map((row) => <tr key={row.source}><td>{row.source.replaceAll("_", " ")}</td><td>{statistic(row.variance)}</td>{hasConfidenceInterval && <td>{row.variance_confidence_interval ? `${Math.round(row.variance_confidence_interval.confidence_level * 100)}% · ${statistic(row.variance_confidence_interval.lower)} ~ ${statistic(row.variance_confidence_interval.upper)}` : "—"}</td>}<td>{statistic(row.study_variation)}</td><td>{statistic(row.percent_contribution, 2)}</td><td>{statistic(row.percent_study_variation, 2)}</td></tr>)}</tbody></table></div></section>;
}

function AttributeAgreementResult({ view }: { view: AttributeAgreementView }) {
  return <>
    <section className="metric-grid result-metrics" aria-label="Attribute Agreement 분석 요약">
      <article className="metric-card"><span>판정값</span><strong>{view.study.assessment_count}</strong><small>{view.study.categories.join(" · ") || "명목형"}</small></article>
      <article className="metric-card"><span>품목</span><strong>{view.study.item_count}</strong><small>표준 판정 포함</small></article>
      <article className="metric-card"><span>검사자</span><strong>{view.study.appraiser_count}</strong><small>교차 판정 설계</small></article>
      <article className="metric-card"><span>품목당 반복</span><strong>{view.study.trials_per_item}</strong><small>모든 셀 동일</small></article>
      <article className="metric-card"><span>전체 표준 일치</span><strong>{statistic(view.overall.all_appraisers_standard_percent, 1)}%</strong><small>{view.overall.all_appraisers_match_standard}/{view.study.item_count}개 품목</small></article>
      <article className="metric-card"><span>전체 검사자 일치</span><strong>{statistic(view.overall.all_appraisers_agree_percent, 1)}%</strong><small>{view.overall.all_appraisers_agree}/{view.study.item_count}개 품목</small></article>
    </section>
    <section className="panel table-panel"><header className="panel-heading"><div><span className="eyebrow">APPRAISER AGREEMENT</span><h2>검사자별 반복·표준 일치도</h2></div><span>Wilson 95% 구간은 품목 단위 완전 일치율의 불확실성을 표시합니다.</span></header><div className="table-scroll"><table><caption>검사자별 Attribute Agreement 결과</caption><thead><tr><th scope="col">검사자</th><th scope="col">품목</th><th scope="col">반복</th><th scope="col">검사자 내 일치</th><th scope="col">내부 일치 95% 구간</th><th scope="col">표준 대비 일치</th><th scope="col">표준 일치 95% 구간</th><th scope="col">Cohen’s κ</th></tr></thead><tbody>{view.appraisers.map((row) => <tr key={row.appraiser}><th scope="row">{row.appraiser}</th><td>{row.items_inspected}</td><td>{row.trials_per_item}</td><td>{statistic(row.within_percent, 1)}%</td><td>{statistic(row.within_confidence_interval.lower * 100, 1)}% ~ {statistic(row.within_confidence_interval.upper * 100, 1)}%</td><td>{statistic(row.standard_percent, 1)}%</td><td>{statistic(row.standard_confidence_interval.lower * 100, 1)}% ~ {statistic(row.standard_confidence_interval.upper * 100, 1)}%</td><td>{statistic(row.cohen_kappa_vs_standard)}</td></tr>)}</tbody></table></div></section>
  </>;
}

function GageBiasLinearityResult({ view }: { view: GageBiasLinearityView }) {
  return <>
    <section className="metric-grid result-metrics" aria-label="Gage 편의·선형성 분석 요약">
      <article className="metric-card"><span>측정값</span><strong>{view.study.measurement_count}</strong><small>기준값 반복 측정</small></article>
      <article className="metric-card"><span>기준값 수준</span><strong>{view.study.reference_level_count}</strong><small>운영 범위 포함</small></article>
      <article className="metric-card"><span>평균 편의</span><strong>{statistic(view.study.mean_bias)}</strong><small>관측값 − 기준값</small></article>
      <article className="metric-card"><span>편의 기울기</span><strong>{statistic(view.fit.slope)}</strong><small>기준값 1단위당 변화</small></article>
      <article className="metric-card"><span>R²</span><strong>{statistic(view.fit.r_squared)}</strong><small>편의 선형 적합</small></article>
      <article className="metric-card"><span>잔차 표준편차</span><strong>{statistic(view.fit.residual_standard_deviation)}</strong><small>직선 주변 산포</small></article>
    </section>
    <section className="panel table-panel"><header className="panel-heading"><div><span className="eyebrow">BIAS BY REFERENCE</span><h2>기준값별 편의</h2></div><span>양수 편의는 측정기가 높게 읽음을 뜻합니다.</span></header><div className="table-scroll"><table><caption>기준값별 반복 측정과 편의</caption><thead><tr><th scope="col">기준값</th><th scope="col">반복 수</th><th scope="col">평균 측정값</th><th scope="col">평균 편의</th><th scope="col">측정 표준편차</th></tr></thead><tbody>{view.levels.map((row) => <tr key={row.reference}><th scope="row">{statistic(row.reference)}</th><td>{row.measurement_count}</td><td>{statistic(row.mean_measurement)}</td><td>{statistic(row.mean_bias)}</td><td>{statistic(row.measurement_standard_deviation)}</td></tr>)}</tbody></table></div></section>
  </>;
}

function ParetoResult({ view }: { view: ParetoView }) {
  const metricLabels = { frequency: "발생 빈도", cost: "비용", loss: "손실" };
  return <>
    <section className="check-sheet-status" aria-label="파레토 분석 요약">
      <div><span>분석 대상</span><strong className="metric-text">{view.subject}</strong></div>
      <div><span>총 {metricLabels[view.metricKind]}</span><strong>{view.total.toLocaleString()}</strong></div>
      <div><span>분류 수</span><strong>{view.categoryCount}</strong></div>
      <div><span>우선 조사 분류</span><strong>{view.vitalFewCount}</strong></div>
    </section>
    <section className="panel result-chart-panel">
      <header className="panel-heading"><div><span className="eyebrow">PARETO PRIORITIZATION</span><h2>{view.subject} 파레토 차트</h2><p>막대는 분류별 {metricLabels[view.metricKind]}, 선은 누적 기여도입니다. {view.thresholdPercentage}% 기준을 넘는 분류까지 우선 조사 대상으로 표시합니다.</p></div></header>
      <Suspense fallback={<div className="skeleton chart-skeleton" aria-label="파레토 차트 불러오는 중" />}><ParetoChart rows={view.rows} threshold={view.thresholdPercentage} /></Suspense>
    </section>
    <section className="panel table-panel">
      <header className="panel-heading"><div><span className="eyebrow">ACCESSIBLE DATA</span><h2>분류별 순위와 누적 기여도</h2></div>{view.sourceSheetId && <Link className="text-link" to={`/spc/tools/check-sheet`}>원본 체크 시트 작업공간</Link>}</header>
      <div className="table-scroll"><table><caption>파레토 차트의 접근 가능한 원본 표</caption><thead><tr><th scope="col">순위</th><th scope="col">분류</th><th scope="col">값</th><th scope="col">구성비</th><th scope="col">누적 비율</th><th scope="col">판정</th></tr></thead><tbody>{view.rows.map((row) => <tr key={row.category}><td>{row.rank}</td><th scope="row">{row.category}</th><td>{row.value.toLocaleString()}</td><td>{row.percentage.toFixed(1)}%</td><td>{row.cumulative_percentage.toFixed(1)}%</td><td>{row.vital_few ? <span className="status-badge is-warning">우선 조사</span> : "후순위"}</td></tr>)}</tbody></table></div>
    </section>
    <section className="spc-evidence-note"><AlertTriangle aria-hidden="true" /><p><strong>해석 제한:</strong> 순위와 누적률은 조사 순서를 정하는 근거입니다. 근본 원인은 현장 확인, 특성요인도, 5 Why 또는 추가 통계 분석으로 검증해야 합니다.</p></section>
  </>;
}

function EwmaResult({ view }: { view: EwmaView }) {
  const signalCount = view.points.filter((point) => point.signal).length;
  const firstPoint = view.points[0];
  return <>
    <ControlChartStatistics center={firstPoint?.center ?? 0} ucl="시점별 계산" lcl="시점별 계산" totalPoints={view.points.length} signalCount={signalCount} />
    <section className="panel result-chart-panel">
      <header className="panel-heading"><div><span className="eyebrow">TIME-WEIGHTED CONTROL CHART</span><h2>EWMA 관리도</h2><ControlLimitBadges limits={[{ label: "CL", value: firstPoint?.center ?? 0 }, { label: "관리 한계", value: "시점별 계산" }]} /></div><span>평균 {view.meanSource === "historical" ? "과거 기준" : "현재 자료 추정"}</span></header>
      <Suspense fallback={<div className="skeleton chart-skeleton" aria-label="EWMA 관리도 불러오는 중" />}><EwmaControlChart points={view.points} /></Suspense>
    </section>
    <section className="panel table-panel">
      <header className="panel-heading"><div><span className="eyebrow">ACCESSIBLE DATA</span><h2>EWMA 관측값과 관리한계</h2></div></header>
      <div className="table-scroll"><table><thead><tr><th scope="col">순서</th><th scope="col">관측값</th><th scope="col">EWMA</th><th scope="col">LCL</th><th scope="col">CL</th><th scope="col">UCL</th><th scope="col">상태</th></tr></thead><tbody>{view.points.map((point) => <tr key={point.index}><td>{point.index}</td><td>{statistic(point.observation)}</td><td>{statistic(point.ewma)}</td><td>{statistic(point.lcl)}</td><td>{statistic(point.center)}</td><td>{statistic(point.ucl)}</td><td>{point.signal ? <span className="status-text is-danger"><AlertTriangle aria-hidden="true" /> 관리한계 이탈</span> : <span className="status-text is-success"><CheckCircle2 aria-hidden="true" /> 정상</span>}</td></tr>)}</tbody></table></div>
    </section>
    <ControlSignalSummary signalCount={signalCount} />
  </>;
}

function CusumResult({ view }: { view: CusumView }) {
  const signalCount = view.points.filter((point) => point.signal).length;
  return <>
    <ControlChartStatistics center={0} ucl={view.decisionInterval} lcl={-view.decisionInterval} totalPoints={view.points.length} signalCount={signalCount} />
    <section className="panel result-chart-panel">
      <header className="panel-heading"><div><span className="eyebrow">TWO-SIDED TABULAR CUSUM</span><h2>CUSUM 관리도</h2><ControlLimitBadges limits={[{ label: "CL", value: 0 }, { label: "UCL", value: view.decisionInterval }, { label: "LCL", value: -view.decisionInterval }]} /></div><span>FIR {statistic(view.firHeadStart)} · 신호 후 {view.resetAfterSignal ? "재설정" : "누적 유지"}</span></header>
      <Suspense fallback={<div className="skeleton chart-skeleton" aria-label="CUSUM 관리도 불러오는 중" />}><CusumControlChart points={view.points} /></Suspense>
    </section>
    <section className="panel table-panel">
      <header className="panel-heading"><div><span className="eyebrow">ACCESSIBLE DATA</span><h2>CUSUM 관측값과 판정구간</h2></div></header>
      <div className="table-scroll"><table><thead><tr><th scope="col">순서</th><th scope="col">관측값</th><th scope="col">상측 CUSUM</th><th scope="col">하측 CUSUM</th><th scope="col">LCL</th><th scope="col">UCL</th><th scope="col">상태</th></tr></thead><tbody>{view.points.map((point) => <tr key={point.index}><td>{point.index}</td><td>{statistic(point.observation)}</td><td>{statistic(point.upperCusum)}</td><td>{statistic(point.lowerCusum)}</td><td>{statistic(point.lcl)}</td><td>{statistic(point.ucl)}</td><td>{point.signal ? <span className="status-text is-danger"><AlertTriangle aria-hidden="true" /> {point.signalDirection === "upper" ? "상측 이탈" : point.signalDirection === "lower" ? "하측 이탈" : "양측 이탈"}{point.resetApplied ? " · 재설정됨" : ""}</span> : <span className="status-text is-success"><CheckCircle2 aria-hidden="true" /> 정상</span>}</td></tr>)}</tbody></table></div>
    </section>
    <ControlSignalSummary signalCount={signalCount} />
  </>;
}

function XbarSResult({ view }: { view: XbarSView }) {
  const signalCount = view.xbarPoints.filter((point) => point.signal).length + view.sPoints.filter((point) => point.signal).length;
  return <>
    <ControlChartStatistics center={view.xbarLimits.center} ucl={view.xbarLimits.ucl} lcl={view.xbarLimits.lcl} totalPoints={view.xbarPoints.length + view.sPoints.length} signalCount={signalCount} />
    <section className="panel result-chart-panel"><header className="panel-heading"><div><span className="eyebrow">XBAR CHART</span><h2>부분군 평균(Xbar) 관리도</h2><ControlLimitBadges limits={[{ label: "CL", value: view.xbarLimits.center }, { label: "UCL", value: view.xbarLimits.ucl }, { label: "LCL", value: view.xbarLimits.lcl }]} /></div></header><Suspense fallback={<div className="skeleton chart-skeleton" aria-label="Xbar 관리도 불러오는 중" />}><ProcessRail points={view.xbarPoints} center={view.xbarLimits.center} ucl={view.xbarLimits.ucl} lcl={view.xbarLimits.lcl} /></Suspense></section>
    <section className="panel result-chart-panel"><header className="panel-heading"><div><span className="eyebrow">S CHART</span><h2>부분군 표준편차(S) 관리도</h2><ControlLimitBadges limits={[{ label: "CL", value: view.sLimits.center }, { label: "UCL", value: view.sLimits.ucl }, { label: "LCL", value: view.sLimits.lcl }]} /></div></header><Suspense fallback={<div className="skeleton chart-skeleton" aria-label="S 관리도 불러오는 중" />}><ProcessRail points={view.sPoints} center={view.sLimits.center} ucl={view.sLimits.ucl} lcl={view.sLimits.lcl} /></Suspense></section>
    <section className="panel table-panel"><header className="panel-heading"><div><span className="eyebrow">ACCESSIBLE DATA</span><h2>Xbar-S 부분군 표</h2></div></header><div className="table-scroll"><table><thead><tr><th scope="col">부분군</th><th scope="col">평균</th><th scope="col">표준편차</th><th scope="col">상태</th></tr></thead><tbody>{view.xbarPoints.map((point, index) => <tr key={point.index}><td>{point.index}</td><td>{statistic(point.value)}</td><td>{statistic(view.sPoints[index]?.value ?? null)}</td><td>{point.signal || view.sPoints[index]?.signal ? "검토 필요" : "관리상태"}</td></tr>)}</tbody></table></div></section>
    <ControlSignalSummary signalCount={signalCount} />
  </>;
}

function XbarRResult({ view }: { view: XbarRView }) {
  const signalCount = view.xbarPoints.filter((point) => point.signal).length + view.rangePoints.filter((point) => point.signal).length;
  const signalRows = [
    ...view.xbarPoints.filter((point) => point.signal).map((point) => ({ chart: "Xbar", point })),
    ...view.rangePoints.filter((point) => point.signal).map((point) => ({ chart: "R", point })),
  ];
  return <>
    <ControlChartStatistics center={view.xbarLimits.center} ucl={view.xbarLimits.ucl} lcl={view.xbarLimits.lcl} totalPoints={view.xbarPoints.length + view.rangePoints.length} signalCount={signalCount} />
    <section className="metric-grid result-metrics" aria-label="Xbar-R 분석 설정">
      <article className="metric-card"><span>부분군 크기</span><strong>{view.subgroupSize}</strong><small>동일 크기 합리적 부분군</small></article>
      <article className="metric-card"><span>판정 규칙</span><strong className="metric-text">{view.ruleSet === "nelson" ? "Nelson 규칙" : "기본 3σ 규칙"}</strong><small>보조 규칙은 조사 후보를 표시</small></article>
      <article className="metric-card"><span>Xbar 상수 A2</span><strong>{view.constants.a2}</strong><small>평균 관리한계 계산</small></article>
      <article className="metric-card"><span>R 상수 D3 / D4</span><strong className="metric-text">{view.constants.d3} / {view.constants.d4}</strong><small>범위 관리한계 계산</small></article>
    </section>
    <section className="panel result-chart-panel"><header className="panel-heading"><div><span className="eyebrow">XBAR CHART</span><h2>부분군 평균(Xbar) 관리도</h2><ControlLimitBadges limits={[{ label: "CL", value: view.xbarLimits.center }, { label: "UCL", value: view.xbarLimits.ucl }, { label: "LCL", value: view.xbarLimits.lcl }]} /></div></header><Suspense fallback={<div className="skeleton chart-skeleton" aria-label="Xbar 관리도 불러오는 중" />}><ProcessRail points={view.xbarPoints} center={view.xbarLimits.center} ucl={view.xbarLimits.ucl} lcl={view.xbarLimits.lcl} /></Suspense></section>
    <section className="panel result-chart-panel"><header className="panel-heading"><div><span className="eyebrow">R CHART</span><h2>부분군 범위(R) 관리도</h2><ControlLimitBadges limits={[{ label: "CL", value: view.rangeLimits.center }, { label: "UCL", value: view.rangeLimits.ucl }, { label: "LCL", value: view.rangeLimits.lcl }]} /></div></header><Suspense fallback={<div className="skeleton chart-skeleton" aria-label="R 관리도 불러오는 중" />}><ProcessRail points={view.rangePoints} center={view.rangeLimits.center} ucl={view.rangeLimits.ucl} lcl={view.rangeLimits.lcl} /></Suspense></section>
    <section className="panel table-panel"><header className="panel-heading"><div><span className="eyebrow">ACCESSIBLE DATA</span><h2>Xbar-R 부분군 표</h2></div></header><div className="table-scroll"><table><thead><tr><th scope="col">부분군</th><th scope="col">평균</th><th scope="col">범위</th><th scope="col">상태</th><th scope="col">판정 규칙</th></tr></thead><tbody>{view.xbarPoints.map((point, index) => { const rangePoint = view.rangePoints[index]; const rules = [...new Set([...point.rules, ...(rangePoint?.rules ?? [])])]; return <tr key={point.index}><td>{point.index}</td><td>{statistic(point.value)}</td><td>{statistic(rangePoint?.value ?? null)}</td><td>{point.signal || rangePoint?.signal ? <span className="status-text is-danger"><AlertTriangle aria-hidden="true" /> 검토 필요</span> : <span className="status-text is-success"><CheckCircle2 aria-hidden="true" /> 관리상태</span>}</td><td>{rules.join(", ") || "—"}</td></tr>; })}</tbody></table></div></section>
    <section className="panel table-panel"><header className="panel-heading"><div><span className="eyebrow">SIGNAL INVESTIGATION</span><h2>관리이탈 지점 분석</h2></div><span>{signalRows.length}개 지점</span></header>{signalRows.length ? <div className="table-scroll"><table><thead><tr><th scope="col">관리도</th><th scope="col">부분군</th><th scope="col">값</th><th scope="col">위반 규칙</th><th scope="col">권장 조치</th></tr></thead><tbody>{signalRows.map(({ chart, point }) => <tr key={`${chart}-${point.index}`}><td>{chart}</td><td>#{point.index}</td><td>{statistic(point.value)}</td><td>{point.rules.join(", ") || "관리한계 이탈"}</td><td>측정·자재·설비·작업 조건의 특별원인을 확인하고 조치 근거를 기록하세요.</td></tr>)}</tbody></table></div> : <div className="state-message is-success"><CheckCircle2 aria-hidden="true" /><h3>관리이탈 신호가 없습니다</h3><p>현재 부분군은 선택한 규칙에서 관리상태로 판정되었습니다.</p></div>}</section>
    <ControlSignalSummary signalCount={signalCount} />
  </>;
}

function AttributeChartResult({ view }: { view: AttributeChartView }) {
  const chartLabel = { p: "p · 부적합률", np: "np · 부적합품 수", c: "c · 결점 수", u: "u · 단위당 결점 수", p_prime: "Laney P′ · 보정 부적합률", u_prime: "Laney U′ · 보정 결점률" }[view.chart];
  const statisticLabel = { p: "부적합률", np: "부적합품 수", c: "결점 수", u: "단위당 결점 수", p_prime: "부적합률", u_prime: "단위당 결점 수" }[view.chart];
  const eventLabel = view.chart === "p" || view.chart === "np" || view.chart === "p_prime" ? "부적합품" : "결점";
  const opportunityLabel = view.chart === "p" || view.chart === "np" || view.chart === "p_prime" ? "표본 크기" : "검사 단위";
  const hasUniformLimits = view.points.length > 0 && view.points.every((point) => point.center === view.points[0]?.center && point.ucl === view.points[0]?.ucl && point.lcl === view.points[0]?.lcl);
  return <>
    <ControlChartStatistics center={view.points[0]?.center ?? 0} ucl={hasUniformLimits ? view.points[0]?.ucl ?? 0 : "부분군별 계산"} lcl={hasUniformLimits ? view.points[0]?.lcl ?? 0 : "부분군별 계산"} totalPoints={view.points.length} signalCount={view.signalCount} />
    <section className="panel result-chart-panel">
      <header className="panel-heading"><div><span className="eyebrow">ATTRIBUTE CHART</span><h2>{chartLabel} 관리도</h2><ControlLimitBadges limits={hasUniformLimits ? [{ label: "CL", value: view.points[0].center }, { label: "UCL", value: view.points[0].ucl }, { label: "LCL", value: view.points[0].lcl }] : [{ label: "관리 한계", value: "부분군별 계산" }]} /></div><span>{view.points.length}개 부분군</span></header>
      <Suspense fallback={<div className="skeleton chart-skeleton" aria-label="속성 관리도 불러오는 중" />}><AttributeControlChart points={view.points} chart={view.chart} /></Suspense>
    </section>
    <section className="panel table-panel">
      <header className="panel-heading"><div><span className="eyebrow">ACCESSIBLE DATA</span><h2>부분군별 관리한계</h2></div></header>
      <div className="table-scroll"><table><thead><tr><th scope="col">부분군</th><th scope="col">{eventLabel}</th><th scope="col">{opportunityLabel}</th><th scope="col">{statisticLabel}</th><th scope="col">LCL</th><th scope="col">CL</th><th scope="col">UCL</th><th scope="col">상태</th></tr></thead><tbody>{view.points.map((point) => <tr key={point.index}><td>{point.index}</td><td>{point.eventCount}</td><td>{point.opportunity}</td><td>{statistic(point.statistic)}</td><td>{statistic(point.lcl)}</td><td>{statistic(point.center)}</td><td>{statistic(point.ucl)}</td><td>{point.signal ? <span className="status-text is-danger"><AlertTriangle aria-hidden="true" /> 3σ 한계 이탈</span> : <span className="status-text is-success"><CheckCircle2 aria-hidden="true" /> 정상</span>}</td></tr>)}</tbody></table></div>
    </section>
    <ControlSignalSummary signalCount={view.signalCount} />
  </>;
}

function RareEventChartResult({ view }: { view: RareEventChartView }) {
  const title = view.chart === "g" ? "G 관리도 · 사건 간 기회 수" : "T 관리도 · 사건 간 시간";
  const intervalLabel = view.chart === "g" ? "사건 간 기회 수" : "사건 간 시간";
  const firstPoint = view.points[0];
  return <>
    <ControlChartStatistics center={firstPoint?.center ?? 0} ucl={firstPoint?.ucl ?? 0} lcl={firstPoint?.lcl ?? 0} totalPoints={view.points.length} signalCount={view.signalCount} centerLabel="중앙값" upperLabel="확률 상한(UPL)" lowerLabel="확률 하한(LPL)" />
    <section className="panel result-chart-panel">
      <header className="panel-heading"><div><span className="eyebrow">RARE EVENT CONTROL CHART</span><h2>{title}</h2><ControlLimitBadges limits={[{ label: "중앙값", value: firstPoint?.center ?? 0 }, { label: "UPL", value: firstPoint?.ucl ?? 0 }, { label: "LPL", value: firstPoint?.lcl ?? 0 }]} /></div><span>{view.parameterSource === "phase_2_historical" ? "2단계 감시(Phase II) · 검증된 기준선" : "1단계 기준선(Phase I) · 현재 자료 추정"} · {view.distribution === "geometric" ? "기하분포" : "지수분포"}</span></header>
      <Suspense fallback={<div className="skeleton chart-skeleton" aria-label="희귀사건 관리도 불러오는 중" />}><ProcessRail points={view.points.map((point) => ({ index: point.index, value: point.interval, signal: point.signal, rules: [] }))} center={firstPoint?.center ?? 0} ucl={firstPoint?.ucl ?? 0} lcl={firstPoint?.lcl ?? 0} centerLabel="중앙값" upperLabel="UPL" lowerLabel="LPL" /></Suspense>
    </section>
    <section className="panel table-panel">
      <header className="panel-heading"><div><span className="eyebrow">ACCESSIBLE DATA</span><h2>사건 간 간격과 확률 한계</h2></div><span>기준선 평균 간격 {statistic(view.meanInterval)} · 현재 입력 평균 {statistic(view.observedMeanInterval)}</span></header>
      <div className="table-scroll"><table><thead><tr><th scope="col">순서</th><th scope="col">{intervalLabel}</th><th scope="col">LPL</th><th scope="col">중앙값</th><th scope="col">UPL</th><th scope="col">상태</th></tr></thead><tbody>{view.points.map((point) => <tr key={point.index}><td>{point.index}</td><td>{statistic(point.interval)}</td><td>{statistic(point.lcl)}</td><td>{statistic(point.center)}</td><td>{statistic(point.ucl)}</td><td>{point.signal ? <span className="status-text is-danger"><AlertTriangle aria-hidden="true" /> 확률 한계 이탈</span> : <span className="status-text is-success"><CheckCircle2 aria-hidden="true" /> 정상</span>}</td></tr>)}</tbody></table></div>
    </section>
    <ControlSignalSummary signalCount={view.signalCount} detail={view.signalCount ? `${view.signalCount}개 간격이 확률 한계를 벗어났습니다. 드문 사건의 간격 변화와 수집 조건을 조사하세요.` : undefined} />
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
      <article className="metric-card"><span>블록</span><strong>{doe.blockCount}</strong><small>{doe.blockedResolutionLabel ? `블록 포함 해상도 ${doe.blockedResolutionLabel}` : "블록 없음"}</small></article>
    </section>
    {doe.blockEffects.length > 0 && <section className="panel table-panel"><header className="panel-heading"><div><span className="eyebrow">BLOCK NUISANCE EFFECTS</span><h2>블록 효과와 처리효과 교락</h2></div><span>{doe.blockCount}개 블록</span></header><div className="table-scroll"><table><thead><tr><th scope="col">대비</th><th scope="col">계수</th><th scope="col">효과</th><th scope="col">교락 처리항</th></tr></thead><tbody>{doe.blockEffects.map((row) => <tr key={row.contrast}><td>{row.contrast}</td><td>{statistic(row.coefficient)}</td><td>{statistic(row.effect)}</td><td>{row.treatment_alias_set.join(" = ")}</td></tr>)}</tbody></table></div>{doe.confoundedTerms.length > 0 && <p className="supporting-copy">처리 모형에서 제외된 블록 교락 항: {doe.confoundedTerms.map((row) => row.term).join(", ")}</p>}</section>}
    <section className="panel doe-effect-panel">
      <header className="panel-heading"><div><span className="eyebrow">CODED DESIGN EFFECTS</span><h2>효과 크기</h2></div><span>{effects.length}개 항</span></header>
      <div className="effect-bars" role="img" aria-label={strongest ? `가장 큰 절대 효과는 ${strongest.term}, 효과 ${statistic(strongest.effect)}` : "추정된 효과 없음"}>{ranked.map((row) => <div className="effect-bar-row" key={row.term}><strong>{row.term}</strong><span className={Number(row.effect) < 0 ? "effect-track is-negative" : "effect-track"}><i style={{ width: `${Math.abs(Number(row.effect)) / maxEffect * 100}%` }} /></span><span>{statistic(row.effect)}</span></div>)}</div>
      <div className="table-scroll"><table><thead><tr><th scope="col">항</th><th scope="col">차수</th><th scope="col">계수</th><th scope="col">효과</th><th scope="col">F</th><th scope="col">p</th></tr></thead><tbody>{effects.map((row) => <tr key={row.term}><td>{row.term}</td><td>{row.order}</td><td>{statistic(row.coefficient)}</td><td>{statistic(row.effect)}</td><td>{statistic(row.f_value)}</td><td>{statistic(row.p_value)}</td></tr>)}</tbody></table></div>
    </section>
    <section className="panel table-panel"><header className="panel-heading"><div><span className="eyebrow">ANALYSIS OF VARIANCE</span><h2>ANOVA</h2></div></header><div className="table-scroll"><table><thead><tr><th scope="col">변동원</th><th scope="col">DF</th><th scope="col">SS</th><th scope="col">MS</th><th scope="col">F</th><th scope="col">p</th></tr></thead><tbody>{doe.anova.map((row) => <tr key={row.source}><td>{row.source}</td><td>{row.degrees_of_freedom}</td><td>{statistic(row.sum_of_squares)}</td><td>{statistic(row.mean_square)}</td><td>{statistic(row.f_value)}</td><td>{statistic(row.p_value)}</td></tr>)}</tbody></table></div></section>
    <section className="panel table-panel"><header className="panel-heading"><div><span className="eyebrow">RESIDUAL DIAGNOSTICS</span><h2>적합값과 잔차</h2></div></header><div className="table-scroll"><table><thead><tr><th scope="col">실행순서</th><th scope="col">표준순서</th>{doe.blockCount > 1 && <th scope="col">블록</th>}<th scope="col">관측값</th><th scope="col">적합값</th><th scope="col">잔차</th><th scope="col">척도화 잔차</th></tr></thead><tbody>{doe.residuals.map((row) => <tr key={row.run_order}><td>{row.run_order}</td><td>{row.standard_order ?? "중심점"}</td>{doe.blockCount > 1 && <td>{row.block}</td>}<td>{statistic(row.observed)}</td><td>{statistic(row.fitted)}</td><td>{statistic(row.residual)}</td><td>{statistic(row.scaled_residual)}</td></tr>)}</tbody></table></div></section>
    {doe.predictions.length > 0 && <section className="panel table-panel"><header className="panel-heading"><div><span className="eyebrow">MODEL PREDICTION</span><h2>조건별 예측</h2></div></header><div className="table-scroll"><table><thead><tr><th scope="col">조건</th>{factorNames.map((name) => <th scope="col" key={name}>{name}</th>)}<th scope="col">예측 응답</th></tr></thead><tbody>{doe.predictions.map((row) => <tr key={row.point}><td>{row.point}</td>{factorNames.map((name) => <td key={name}>{statistic(row.actual[name])}</td>)}<td>{statistic(row.predicted_response)}</td></tr>)}</tbody></table></div></section>}
    {doe.optimization.length > 0 && <section className="panel table-panel"><header className="panel-heading"><div><span className="eyebrow">VERTEX OPTIMIZATION</span><h2>최적 설정</h2></div></header><div className="table-scroll"><table><thead><tr><th scope="col">목표</th>{factorNames.map((name) => <th scope="col" key={name}>{name}</th>)}<th scope="col">예측 응답</th><th scope="col">평가 후보</th></tr></thead><tbody>{doe.optimization.map((row) => <tr key={row.goal}><td>{row.goal === "maximize" ? "최대화" : "최소화"}</td>{factorNames.map((name) => <td key={name}>{statistic(row.actual[name])}</td>)}<td>{statistic(row.predicted_response)}</td><td>{row.candidate_count}</td></tr>)}</tbody></table></div></section>}
  </>;
}

function DoeDesirabilityResult({ optimizer }: { optimizer: DoeDesirabilityView }) {
  const factorNames = Object.keys(optimizer.solution.actual);
  const constraints = Object.entries(optimizer.factorConstraints);
  const goalLabel = { maximize: "최대화", minimize: "최소화", target: "목표값" };
  return <>
    <section className="metric-grid result-metrics" aria-label="DOE 다중 응답 최적화 요약">
      <article className="metric-card"><span>복합 desirability</span><strong>{statistic(optimizer.solution.composite_desirability, 4)}</strong><small>0–1, 높을수록 바람직</small></article>
      <article className="metric-card"><span>응답 수</span><strong>{optimizer.responses.length}</strong><small>동시 최적화</small></article>
      <article className="metric-card"><span>후보 평가</span><strong>{optimizer.solution.candidate_evaluations}</strong><small>결정론적 탐색</small></article>
      <article className="metric-card"><span>전역 최적 증명</span><strong className="metric-text">{optimizer.globalOptimumProven ? "예" : "아니오"}</strong><small>확인 실험 필요</small></article>
    </section>
    <section className="panel table-panel"><header className="panel-heading"><div><span className="eyebrow">OPTIMAL SETTINGS</span><h2>권장 요인 설정</h2></div></header><div className="table-scroll"><table><thead><tr>{factorNames.map((name) => <th scope="col" key={name}>{name}</th>)}<th scope="col">복합 desirability</th></tr></thead><tbody><tr>{factorNames.map((name) => <td key={name}>{statistic(optimizer.solution.actual[name])}</td>)}<td>{statistic(optimizer.solution.composite_desirability)}</td></tr></tbody></table></div></section>
    {constraints.length > 0 && <section className="panel table-panel"><header className="panel-heading"><div><span className="eyebrow">SEARCH CONSTRAINTS</span><h2>적용된 요인 탐색 제약</h2></div><span>{constraints.length}개 요인</span></header><div className="table-scroll"><table><thead><tr><th scope="col">요인</th><th scope="col">Lower</th><th scope="col">Upper</th><th scope="col">방식</th></tr></thead><tbody>{constraints.map(([name, bounds]) => <tr key={name}><td>{name}</td><td>{statistic(bounds.lower)}</td><td>{statistic(bounds.upper)}</td><td>{bounds.lower === bounds.upper ? "고정" : "범위"}</td></tr>)}</tbody></table></div></section>}
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
      <article className="metric-card"><span>설계 해상도</span><strong>{analysis.foldoverMode !== "none" ? `${analysis.resolutionLabel} → ${analysis.augmentedResolution}` : analysis.resolutionLabel}</strong><small>{analysis.foldoverMode === "all_factors" ? "전체 foldover" : analysis.foldoverMode === "single_factor" ? `${analysis.foldoverFactor} 단일요인 fold` : "원 설계"}</small></article>
      <article className="metric-card"><span>주효과–2FI 분리</span><strong className="metric-text">{analysis.mainEffectsClear ? "분리됨" : "별칭 유지"}</strong><small>{method} · 잔차 DF {analysis.residualDegreesOfFreedom}</small></article>
    </section>
    {analysis.foldoverMode === "single_factor" && <section className="panel table-panel"><header className="panel-heading"><div><span className="eyebrow">PARTIAL FOLDOVER</span><h2>단일요인 fold 별칭 분리 범위</h2></div><span>{analysis.clearedMainEffects.length}개 주효과 분리</span></header><p className="supporting-copy">선택 요인 {analysis.foldoverFactor}의 부호만 반전했습니다. 2요인 교호작용에서 분리된 주효과: {analysis.clearedMainEffects.join(", ") || "없음"}</p></section>}
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
