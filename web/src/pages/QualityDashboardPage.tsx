import { useEffect, useMemo, useState, type FormEvent } from "react";
import { Activity, AlertTriangle, CheckCircle2, Database, Gauge, ShieldAlert } from "lucide-react";
import { Link } from "react-router-dom";
import { createQualityMetric, listQualityMetrics, listRuns } from "../api";
import type { StoredQualityMetric, StoredRun } from "../types";

type MetricForm = {
  metricId: string;
  name: string;
  unit: string;
  runId: string;
  valuePath: string;
  refreshCycle: string;
  ownerRef: string;
  lowerWarning: string;
  lowerCritical: string;
  upperWarning: string;
  upperCritical: string;
};

const initialForm: MetricForm = {
  metricId: "",
  name: "",
  unit: "",
  runId: "",
  valuePath: "tables.summary.center_line",
  refreshCycle: "교대 종료 후",
  ownerRef: "quality.team",
  lowerWarning: "",
  lowerCritical: "",
  upperWarning: "",
  upperCritical: "",
};

const statusLabels = { good: "정상", warning: "주의", critical: "위험" } as const;

function optionalNumber(value: string): number | null {
  return value.trim() === "" ? null : Number(value);
}

export function QualityDashboardPage() {
  const [metrics, setMetrics] = useState<StoredQualityMetric[]>([]);
  const [runs, setRuns] = useState<StoredRun[]>([]);
  const [form, setForm] = useState<MetricForm>(initialForm);
  const [state, setState] = useState<"loading" | "ready" | "saving" | "error">("loading");
  const [message, setMessage] = useState("");

  useEffect(() => {
    Promise.all([listQualityMetrics(100), listRuns(100)])
      .then(([metricPage, runPage]) => {
        setMetrics(metricPage.items);
        setRuns(runPage.items);
        setState("ready");
      })
      .catch((error: Error) => {
        setMessage(error.message);
        setState("error");
      });
  }, []);

  const summary = useMemo(() => ({
    total: metrics.length,
    good: metrics.filter((item) => item.metric.status === "good").length,
    warning: metrics.filter((item) => item.metric.status === "warning").length,
    critical: metrics.filter((item) => item.metric.status === "critical").length,
  }), [metrics]);

  const update = (field: keyof MetricForm, value: string) => {
    setForm((current) => ({ ...current, [field]: value }));
  };

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setState("saving");
    setMessage("");
    try {
      const created = await createQualityMetric({
        metric_id: form.metricId,
        name: form.name,
        unit: form.unit,
        run_id: form.runId,
        value_path: form.valuePath,
        refresh_cycle: form.refreshCycle,
        owner_ref: form.ownerRef,
        lower_warning: optionalNumber(form.lowerWarning),
        lower_critical: optionalNumber(form.lowerCritical),
        upper_warning: optionalNumber(form.upperWarning),
        upper_critical: optionalNumber(form.upperCritical),
      });
      setMetrics((current) => [...current, created]);
      setForm(initialForm);
      setMessage("저장된 분석 결과에서 품질 지표 스냅샷을 생성했습니다.");
      setState("ready");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "품질 지표를 생성하지 못했습니다.");
      setState("error");
    }
  };

  return (
    <div className="page quality-dashboard">
      <nav className="breadcrumbs" aria-label="현재 위치"><Link to="/home">홈 (Home)</Link><span>/</span><span>품질 대시보드 (Quality Dashboard)</span></nav>
      <header className="page-heading">
        <div><span className="eyebrow">RESULT-BASED QUALITY MONITORING</span><h1>품질 대시보드 (Quality Dashboard)</h1><p>검증·저장된 분석 결과의 수치만 지표로 투영하여 현장 판단 근거와 원본 분석 이력을 함께 확인합니다.</p></div>
      </header>

      <ol className="quality-process-rail" aria-label="품질 지표 운영 흐름">
        <li><strong>분석 실행</strong><span>DOE·SPC·FMEA 결과 저장</span></li>
        <li><strong>지표 연결</strong><span>허용된 수치 경로 선택</span></li>
        <li><strong>상태 판정</strong><span>명시적 주의·위험 기준 적용</span></li>
        <li><strong>현장 검토</strong><span>원본 Run 증거로 이동</span></li>
      </ol>

      {message && <div className={state === "error" ? "error-banner" : "quality-confirmation"} role={state === "error" ? "alert" : "status"}>{state === "error" ? <AlertTriangle /> : <CheckCircle2 />}<p>{message}</p></div>}

      <section className="quality-summary-grid" aria-label="지표 상태 요약">
        <article><Gauge /><span>전체 지표</span><strong>{summary.total}</strong></article>
        <article className="is-good"><CheckCircle2 /><span>정상</span><strong>{summary.good}</strong></article>
        <article className="is-warning"><AlertTriangle /><span>주의</span><strong>{summary.warning}</strong></article>
        <article className="is-critical"><ShieldAlert /><span>위험</span><strong>{summary.critical}</strong></article>
      </section>

      <div className="quality-layout">
        <section className="workspace-section">
          <header><span className="eyebrow">CURRENT SNAPSHOTS</span><h2>현장 품질 지표</h2><p>자동 갱신값이 아니라 생성 시점의 불변 스냅샷입니다. 새 분석 결과는 새 지표로 명시적으로 연결합니다.</p></header>
          {state === "loading" ? <div className="state-message"><Activity /><p>저장된 지표를 불러오는 중입니다.</p></div> : metrics.length === 0 ? <div className="state-message"><Database /><h3>연결된 지표가 없습니다</h3><p>오른쪽에서 저장된 분석 Run과 수치 경로를 선택해 첫 지표를 만드세요.</p></div> : (
            <div className="quality-metric-grid">
              {metrics.map(({ metric }) => (
                <article className={`quality-metric-card is-${metric.status}`} key={metric.metric_id}>
                  <header><span className={`quality-status is-${metric.status}`}>{statusLabels[metric.status]}</span><small>{metric.refresh_cycle}</small></header>
                  <h3>{metric.name}</h3><strong>{metric.value.toLocaleString("ko-KR")} <small>{metric.unit}</small></strong>
                  <dl><div><dt>분석</dt><dd>{metric.source.analysis_type}</dd></div><div><dt>담당</dt><dd>{metric.owner_ref}</dd></div><div><dt>경로</dt><dd className="digest">{metric.source.value_path}</dd></div></dl>
                  <Link className="text-link" to={`/runs/${metric.source.run_id}`}>원본 분석 결과 열기 →</Link>
                  <details><summary>증거 식별자</summary><p className="digest">Run ETag: {metric.source.run_etag}</p><p className="digest">Input: {metric.source.input_digest}</p><p className="digest">Metric: {metric.digest}</p></details>
                </article>
              ))}
            </div>
          )}
        </section>

        <form className="workspace-section quality-source-form" onSubmit={submit}>
          <header><span className="eyebrow">SOURCE CONTRACT</span><h2>분석 결과 지표 연결</h2><p>ResultBundle의 tables, diagnostics, parameters 아래에 있는 유한 수치 하나만 연결할 수 있습니다.</p></header>
          <label className="field">저장된 분석 Run<select required value={form.runId} onChange={(event) => update("runId", event.target.value)}><option value="">Run 선택</option>{runs.map((run) => <option value={run.run_id} key={run.run_id}>{run.run_id} · {run.result.analysis_type}</option>)}</select></label>
          <label className="field">지표 ID<input required pattern="[A-Za-z0-9][A-Za-z0-9._-]*" value={form.metricId} onChange={(event) => update("metricId", event.target.value)} placeholder="line-1-yield" /></label>
          <label className="field">지표 이름<input required value={form.name} onChange={(event) => update("name", event.target.value)} placeholder="1라인 수율" /></label>
          <div className="quality-inline-fields"><label className="field">단위<input value={form.unit} onChange={(event) => update("unit", event.target.value)} placeholder="%" /></label><label className="field">검토 주기<input required value={form.refreshCycle} onChange={(event) => update("refreshCycle", event.target.value)} /></label></div>
          <label className="field">수치 경로<input required value={form.valuePath} onChange={(event) => update("valuePath", event.target.value)} /><small>예: tables.summary.center_line, diagnostics.in_control_percentage</small></label>
          <label className="field">담당 조직·역할<input required value={form.ownerRef} onChange={(event) => update("ownerRef", event.target.value)} /></label>
          <fieldset className="quality-thresholds"><legend>상태 판정 기준 (선택)</legend><label className="field">하한 위험<input type="number" step="any" value={form.lowerCritical} onChange={(event) => update("lowerCritical", event.target.value)} /></label><label className="field">하한 주의<input type="number" step="any" value={form.lowerWarning} onChange={(event) => update("lowerWarning", event.target.value)} /></label><label className="field">상한 주의<input type="number" step="any" value={form.upperWarning} onChange={(event) => update("upperWarning", event.target.value)} /></label><label className="field">상한 위험<input type="number" step="any" value={form.upperCritical} onChange={(event) => update("upperCritical", event.target.value)} /></label></fieldset>
          <button className="primary-button" type="submit" disabled={state === "saving" || runs.length === 0}>{state === "saving" ? "지표 생성 중…" : "지표 스냅샷 생성"}</button>
        </form>
      </div>
    </div>
  );
}
