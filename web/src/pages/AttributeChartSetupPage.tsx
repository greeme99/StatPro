import { AlertTriangle, ArrowLeft, Play } from "lucide-react";
import { FormEvent, useMemo, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { createAttributeChartRun } from "../api";
import { Button } from "../components/Button";

function defaultRunId(chart: "p" | "np") {
  const timestamp = new Date().toISOString().replace(/[-:TZ.]/g, "").slice(0, 14);
  return `${chart}-chart-${timestamp}`;
}

function parseValues(text: string) {
  return text.split(/[\s,;]+/).filter(Boolean).map(Number);
}

export function AttributeChartSetupPage() {
  const navigate = useNavigate();
  const [chart, setChart] = useState<"p" | "np">("p");
  const [runId, setRunId] = useState(() => defaultRunId("p"));
  const [nonconforming, setNonconforming] = useState("2\n3\n2\n3\n25");
  const [sampleSizes, setSampleSizes] = useState("100\n100\n100\n100\n100");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const countsRef = useRef<HTMLTextAreaElement>(null);
  const counts = useMemo(() => parseValues(nonconforming), [nonconforming]);
  const sizes = useMemo(() => parseValues(sampleSizes), [sampleSizes]);

  function selectChart(next: "p" | "np") {
    setChart(next);
    setRunId(defaultRunId(next));
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    const invalidCounts = counts.some((value) => !Number.isInteger(value) || value < 0);
    const invalidSizes = sizes.some((value) => !Number.isInteger(value) || value <= 0);
    if (counts.length < 2 || counts.length !== sizes.length || invalidCounts || invalidSizes) {
      setError("부적합품 수와 표본 크기를 같은 개수의 0 이상 정수로 입력하세요. 표본 크기는 1 이상이어야 합니다.");
      countsRef.current?.focus();
      return;
    }
    if (counts.some((count, index) => count > sizes[index])) {
      setError("부적합품 수는 같은 부분군의 표본 크기를 초과할 수 없습니다.");
      countsRef.current?.focus();
      return;
    }
    if (chart === "np" && sizes.some((size) => size !== sizes[0])) {
      setError("np 관리도는 모든 부분군의 표본 크기가 같아야 합니다. 크기가 다르면 p 관리도를 선택하세요.");
      countsRef.current?.focus();
      return;
    }
    setError("");
    setLoading(true);
    try {
      await createAttributeChartRun({
        run_id: runId,
        chart,
        nonconforming: counts,
        sample_sizes: sizes,
      });
      navigate(`/runs/${runId}`);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "분석을 실행하지 못했습니다.");
      countsRef.current?.focus();
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="page form-page" data-density="comfortable">
      <Link className="back-link" to="/"><ArrowLeft aria-hidden="true" /> 분석 홈</Link>
      <section className="page-heading">
        <div><span className="eyebrow">SPC / ATTRIBUTES</span><h1>p · np 관리도 설정</h1><p>부분군별 부적합품 수로 비율 또는 개수의 공정 안정성을 확인합니다.</p></div>
      </section>
      {error && <div className="error-banner" role="alert"><AlertTriangle aria-hidden="true" /><div><strong>입력을 확인하세요</strong><p>{error}</p></div></div>}
      <form className="analysis-form" onSubmit={submit}>
        <section className="form-panel">
          <header><span className="step-index">01</span><div><h2>관리도 선택</h2><p>표본 크기가 다르면 p, 모두 같으면 np를 사용할 수 있습니다.</p></div></header>
          <div className="inline-fields">
            <label className="field"><span>관리도</span><select value={chart} onChange={(event) => selectChart(event.target.value as "p" | "np")}><option value="p">p · 부적합률</option><option value="np">np · 부적합품 수</option></select></label>
            <label className="field"><span>Run ID</span><input value={runId} onChange={(event) => setRunId(event.target.value)} required pattern="[A-Za-z0-9][A-Za-z0-9._-]{0,127}" /></label>
          </div>
        </section>
        <section className="form-panel">
          <header><span className="step-index">02</span><div><h2>부분군 데이터</h2><p>두 열의 같은 행이 하나의 부분군입니다. 시간 순서를 유지하세요.</p></div></header>
          <div className="inline-fields">
            <label className="field"><span>부적합품 수 *</span><textarea ref={countsRef} rows={9} value={nonconforming} onChange={(event) => setNonconforming(event.target.value)} aria-invalid={Boolean(error)} /><small>{counts.filter(Number.isFinite).length}개 부분군 인식됨</small></label>
            <label className="field"><span>표본 크기 *</span><textarea rows={9} value={sampleSizes} onChange={(event) => setSampleSizes(event.target.value)} /><small>{sizes.filter(Number.isFinite).length}개 표본 크기 인식됨</small></label>
          </div>
        </section>
        <aside className="method-note"><strong>계산 방법</strong><p>NIST의 이항분포 기반 3σ 근사식을 사용합니다. p 관리도는 부분군별 표본 크기에 맞춰 한계를 계산하고, np 관리도는 일정한 표본 크기를 요구합니다. 한계 이탈은 조사 신호이지 특별원인의 확정 판정이 아닙니다.</p></aside>
        <div className="form-actions"><Button type="submit" variant="primary" loading={loading} icon={<Play />}>관리도 실행</Button></div>
      </form>
    </div>
  );
}
