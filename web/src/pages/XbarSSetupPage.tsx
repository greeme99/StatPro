import { AlertTriangle, ArrowLeft, Play } from "lucide-react";
import { type FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { createXbarSRun } from "../api";
import { Button } from "../components/Button";

function defaultRunId() {
  const timestamp = new Date().toISOString().replace(/[-:TZ.]/g, "").slice(0, 14);
  return `xbar-s-${timestamp}`;
}

function parseSubgroups(text: string) {
  return text.split(/\r?\n/).map((line) => line.trim()).filter(Boolean)
    .map((line) => line.split(/[\s,;]+/).filter(Boolean).map(Number));
}

export function XbarSSetupPage() {
  const navigate = useNavigate();
  const [runId, setRunId] = useState(defaultRunId);
  const [subgroupsText, setSubgroupsText] = useState(
    "1 2 3 4 5 6 7 8 9 10\n2 3 4 5 6 7 8 9 10 11\n3 4 5 6 7 8 9 10 11 12",
  );
  const [rules, setRules] = useState<"basic" | "nelson">("basic");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    const subgroups = parseSubgroups(subgroupsText);
    const size = subgroups[0]?.length ?? 0;
    if (subgroups.length < 2 || size < 2 || size > 100 || subgroups.some((group) => group.length !== size || group.some((value) => !Number.isFinite(value)))) {
      setError("두 개 이상의 부분군을 입력하고, 각 줄에 같은 개수의 유한 측정값 2–100개를 입력하세요.");
      return;
    }
    setError("");
    setLoading(true);
    try {
      await createXbarSRun({ run_id: runId, subgroups, rules });
      navigate(`/runs/${runId}`);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Xbar-S 분석을 실행하지 못했습니다.");
    } finally {
      setLoading(false);
    }
  }

  return <div className="page form-page" data-density="comfortable">
    <Link className="back-link" to="/"><ArrowLeft aria-hidden="true" /> 분석 홈</Link>
    <section className="page-heading"><div><span className="eyebrow">SPC / VARIABLES CHART</span><h1>Xbar-S 관리도</h1><p>합리적 부분군의 평균과 표준편차를 함께 감시합니다. 부분군 크기 9 이상에 특히 적합합니다.</p></div></section>
    {error && <div className="error-banner" role="alert"><AlertTriangle aria-hidden="true" /><div><strong>입력을 확인하세요</strong><p>{error}</p></div></div>}
    <form className="analysis-form" onSubmit={submit}>
      <section className="form-panel"><header><span className="step-index">01</span><div><h2>실행 식별자</h2><p>불변 Analysis Run ID를 지정합니다.</p></div></header><label className="field"><span>Run ID</span><input value={runId} onChange={(event) => setRunId(event.target.value)} required pattern="[A-Za-z0-9][A-Za-z0-9._-]{0,127}" /></label></section>
      <section className="form-panel"><header><span className="step-index">02</span><div><h2>합리적 부분군</h2><p>한 줄이 한 부분군입니다. 모든 부분군은 같은 크기여야 합니다.</p></div></header><label className="field"><span>부분군 측정값</span><textarea rows={10} value={subgroupsText} onChange={(event) => setSubgroupsText(event.target.value)} required /></label></section>
      <section className="form-panel"><header><span className="step-index">03</span><div><h2>특별원인 규칙</h2><p>Basic은 3σ 한계만, Nelson은 Xbar 1–8과 S 1–4를 평가합니다.</p></div></header><label className="field"><span>규칙 세트</span><select value={rules} onChange={(event) => setRules(event.target.value as "basic" | "nelson")}><option value="basic">Basic · 3σ</option><option value="nelson">Nelson</option></select></label></section>
      <aside className="method-note"><strong>해석 순서</strong><p>S 관리도의 변동 안정성을 먼저 확인한 뒤 Xbar 관리도의 공정 중심을 해석하세요. 신호는 원인 확정이 아니라 조사 후보입니다.</p></aside>
      <div className="form-actions"><Button type="submit" variant="primary" loading={loading} icon={<Play />}>Xbar-S 실행</Button></div>
    </form>
  </div>;
}
