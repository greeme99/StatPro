import { AlertTriangle, ArrowLeft, Play } from "lucide-react";
import { FormEvent, useMemo, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { createRareEventChartRun } from "../api";
import { Button } from "../components/Button";

type RareEventChartKind = "g" | "t";

function defaultRunId(chart: RareEventChartKind) {
  const timestamp = new Date().toISOString().replace(/[-:TZ.]/g, "").slice(0, 14);
  return `${chart}-rare-event-${timestamp}`;
}

function parseValues(text: string) {
  return text.split(/[\s,;]+/).filter(Boolean).map(Number);
}

export function RareEventChartSetupPage() {
  const navigate = useNavigate();
  const [chart, setChart] = useState<RareEventChartKind>("g");
  const [runId, setRunId] = useState(() => defaultRunId("g"));
  const [intervalText, setIntervalText] = useState("8\n10\n12\n9\n11\n14\n10\n13");
  const [alpha, setAlpha] = useState("0.005");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const intervalRef = useRef<HTMLTextAreaElement>(null);
  const intervals = useMemo(() => parseValues(intervalText), [intervalText]);

  function selectChart(next: RareEventChartKind) {
    setChart(next);
    setRunId(defaultRunId(next));
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    const tailAlpha = Number(alpha);
    const invalidIntervals = intervals.some((value) => !Number.isFinite(value) || value < 0 || (chart === "g" && !Number.isInteger(value)) || (chart === "t" && value <= 0));
    if (intervals.length < 2 || invalidIntervals) {
      setError(chart === "g" ? "G 관리도에는 0 이상 정수인 사건 간 기회 수를 두 개 이상 입력하세요." : "T 관리도에는 0보다 큰 사건 간 시간을 두 개 이상 입력하세요.");
      intervalRef.current?.focus();
      return;
    }
    if (!Number.isFinite(tailAlpha) || tailAlpha <= 0 || tailAlpha >= 0.5) {
      setError("양쪽 꼬리 확률은 0보다 크고 0.5보다 작은 값이어야 합니다.");
      return;
    }
    setError("");
    setLoading(true);
    try {
      await createRareEventChartRun({ run_id: runId, chart, intervals, alpha: tailAlpha });
      navigate(`/runs/${runId}`);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "분석을 실행하지 못했습니다.");
      intervalRef.current?.focus();
    } finally {
      setLoading(false);
    }
  }

  const intervalLabel = chart === "g" ? "사건 간 기회 수" : "사건 간 시간";
  return (
    <div className="page form-page" data-density="comfortable">
      <Link className="back-link" to="/"><ArrowLeft aria-hidden="true" /> 분석 홈</Link>
      <section className="page-heading"><div><span className="eyebrow">SPC / RARE EVENTS</span><h1>희귀사건 G/T 관리도 설정</h1><p>드물게 발생하는 사건의 간격을 기하 또는 지수 확률모형으로 점검합니다.</p></div></section>
      {error && <div className="error-banner" role="alert"><AlertTriangle aria-hidden="true" /><div><strong>입력을 확인하세요</strong><p>{error}</p></div></div>}
      <form className="analysis-form" onSubmit={submit}>
        <section className="form-panel">
          <header><span className="step-index">01</span><div><h2>관리도 종류 선택</h2><p>사건 사이의 기회 수는 G, 시간·거리·사용량 같은 연속 간격은 T를 선택합니다.</p></div></header>
          <div className="inline-fields">
            <label className="field"><span>관리도</span><select value={chart} onChange={(event) => selectChart(event.target.value as RareEventChartKind)}><option value="g">G · 사건 간 기회 수</option><option value="t">T · 사건 간 시간</option></select></label>
            <label className="field"><span>Run ID</span><input value={runId} onChange={(event) => setRunId(event.target.value)} required pattern="[A-Za-z0-9][A-Za-z0-9._-]{0,127}" /></label>
          </div>
        </section>
        <section className="form-panel">
          <header><span className="step-index">02</span><div><h2>간격 데이터 입력</h2><p>한 행이 하나의 사건 간 간격입니다. 발생 순서를 유지하세요.</p></div></header>
          <div className="inline-fields">
            <label className="field"><span>{intervalLabel} *</span><textarea ref={intervalRef} rows={9} value={intervalText} onChange={(event) => setIntervalText(event.target.value)} aria-invalid={Boolean(error)} /><small>{intervals.filter(Number.isFinite).length}개 간격 인식됨</small></label>
            <label className="field"><span>양쪽 꼬리 확률 α</span><input inputMode="decimal" value={alpha} onChange={(event) => setAlpha(event.target.value)} /><small>기본값 0.005. 상·하한 각각에 적용합니다.</small></label>
          </div>
        </section>
        <aside className="method-note"><strong>계산 방법</strong><p>{chart === "g" ? "G 관리도는 사건 자체를 제외한 기회 수(0 포함)를 기하분포로 모델링합니다." : "T 관리도는 사건 간 양의 시간·거리·사용량을 지수분포로 모델링합니다."} 입력 자료에서 Phase I 모수를 추정하고, 지정한 꼬리 확률의 확률 한계와 중앙값을 표시합니다.</p></aside>
        <div className="form-actions"><Button type="submit" variant="primary" loading={loading} icon={<Play />}>관리도 실행</Button></div>
      </form>
    </div>
  );
}
