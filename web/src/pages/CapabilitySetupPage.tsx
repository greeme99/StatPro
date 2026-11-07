import { AlertTriangle, ArrowLeft, Play } from "lucide-react";
import { FormEvent, useMemo, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { createCapabilityRun } from "../api";
import { Button } from "../components/Button";

function defaultRunId() {
  const timestamp = new Date().toISOString().replace(/[-:TZ.]/g, "").slice(0, 14);
  return `capability-${timestamp}`;
}

export function CapabilitySetupPage() {
  const navigate = useNavigate();
  const [runId, setRunId] = useState(defaultRunId);
  const [model, setModel] = useState<"normal" | "nonnormal">("normal");
  const [values, setValues] = useState("98.7\n99.2\n100.1\n99.5\n100.4\n101.0\n99.8\n100.2");
  const [lsl, setLsl] = useState("95");
  const [usl, setUsl] = useState("105");
  const [target, setTarget] = useState("100");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const valuesRef = useRef<HTMLTextAreaElement>(null);
  const parsed = useMemo(() => values.split(/[\s,;]+/).filter(Boolean).map(Number), [values]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    const lower = lsl.trim() === "" ? undefined : Number(lsl);
    const upper = usl.trim() === "" ? undefined : Number(usl);
    const targetValue = target.trim() === "" ? undefined : Number(target);
    if (parsed.length < 2 || parsed.some((value) => !Number.isFinite(value))) {
      setError("유한한 측정값을 두 개 이상 입력하세요. 줄바꿈, 쉼표 또는 공백으로 구분할 수 있습니다.");
      valuesRef.current?.focus();
      return;
    }
    if ((lower === undefined && upper === undefined) || ![lower, upper, targetValue].every((value) => value === undefined || Number.isFinite(value))) {
      setError("LSL 또는 USL을 하나 이상 입력하고, 규격·목표값은 유한한 숫자로 입력하세요.");
      return;
    }
    if (lower !== undefined && upper !== undefined && lower >= upper) {
      setError("LSL은 USL보다 작아야 합니다.");
      return;
    }
    setError("");
    setLoading(true);
    try {
      await createCapabilityRun({ run_id: runId, values: parsed, model, ...(lower === undefined ? {} : { lsl: lower }), ...(upper === undefined ? {} : { usl: upper }), ...(targetValue === undefined ? {} : { target: targetValue }) });
      navigate(`/runs/${runId}`);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "공정능력 분석을 실행하지 못했습니다.");
      valuesRef.current?.focus();
    } finally {
      setLoading(false);
    }
  }

  return <div className="page form-page" data-density="comfortable">
    <Link className="back-link" to="/spc"><ArrowLeft aria-hidden="true" /> 통계적 공정관리(SPC)</Link>
    <section className="page-heading"><div><span className="eyebrow">SPC / CAPABILITY</span><h1>공정능력 분석 설정</h1><p>안정성이 확인된 공정의 측정값과 공학 규격을 비교해 능력 지수와 관측 불량을 검토합니다.</p></div></section>
    {error && <div className="error-banner" role="alert"><AlertTriangle aria-hidden="true" /><div><strong>입력을 확인하세요</strong><p>{error}</p></div></div>}
    <form className="analysis-form" onSubmit={submit}>
      <section className="form-panel"><header><span className="step-index">01</span><div><h2>분석 방식과 실행 식별자</h2><p>정규 가정은 Cp/Cpk/Pp/Ppk를, 경험적 비정규 방식은 Cnp/Cnpk를 계산합니다.</p></div></header><div className="inline-fields"><label className="field"><span>Run ID</span><input value={runId} onChange={(event) => setRunId(event.target.value)} required pattern="[A-Za-z0-9][A-Za-z0-9._-]{0,127}" /></label><label className="field"><span>분포 방식</span><select value={model} onChange={(event) => setModel(event.target.value as "normal" | "nonnormal")}><option value="normal">정규 공정능력 (Cp/Cpk/Pp/Ppk)</option><option value="nonnormal">경험적 비정규 공정능력 (Cnp/Cnpk)</option></select></label></div></section>
      <section className="form-panel"><header><span className="step-index">02</span><div><h2>시간 순서 측정값</h2><p>같은 공정 모집단에서 수집한 값을 입력하세요. 결측값을 0으로 대체하지 않습니다.</p></div></header><label className="field"><span>측정값 *</span><textarea ref={valuesRef} rows={9} value={values} onChange={(event) => setValues(event.target.value)} aria-invalid={Boolean(error)} /><small>{parsed.filter(Number.isFinite).length}개 값 인식됨</small></label></section>
      <section className="form-panel"><header><span className="step-index">03</span><div><h2>공학 규격</h2><p>관리한계가 아닌 설계·고객 요구 규격을 입력합니다. LSL 또는 USL은 반드시 하나 이상 필요합니다.</p></div></header><div className="inline-fields"><label className="field"><span>LSL (하한 규격)</span><input type="number" step="any" value={lsl} onChange={(event) => setLsl(event.target.value)} placeholder="선택 입력" /></label><label className="field"><span>USL (상한 규격)</span><input type="number" step="any" value={usl} onChange={(event) => setUsl(event.target.value)} placeholder="선택 입력" /></label><label className="field"><span>목표값</span><input type="number" step="any" value={target} onChange={(event) => setTarget(event.target.value)} placeholder="선택 입력" /></label></div></section>
      <aside className="method-note"><strong>해석 전 확인</strong><p>공정능력은 공정 안정성과 단일 모집단을 전제로 합니다. 정규 방식은 약정규 분포를 가정하며, 경험적 비정규 방식은 명명 분포를 적합하지 않습니다. 결과의 경고·가정·NIST 근거를 함께 검토하세요.</p></aside>
      <div className="form-actions"><Button type="submit" variant="primary" loading={loading} icon={<Play />}>공정능력 분석 실행</Button></div>
    </form>
  </div>;
}
