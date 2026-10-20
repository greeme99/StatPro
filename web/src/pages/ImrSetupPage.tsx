import { AlertTriangle, ArrowLeft, Play } from "lucide-react";
import { FormEvent, useMemo, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { createImrRun } from "../api";
import { Button } from "../components/Button";

function defaultRunId() {
  const timestamp = new Date().toISOString().replace(/[-:TZ.]/g, "").slice(0, 14);
  return `imr-${timestamp}`;
}

export function ImrSetupPage() {
  const navigate = useNavigate();
  const [runId, setRunId] = useState(defaultRunId);
  const [values, setValues] = useState("10.2\n10.4\n10.1\n10.6\n10.3\n10.5\n10.2\n10.4");
  const [target, setTarget] = useState("");
  const [rules, setRules] = useState<"basic" | "western_electric" | "nelson">("western_electric");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const valuesRef = useRef<HTMLTextAreaElement>(null);
  const parsed = useMemo(() => values.split(/[\s,;]+/).filter(Boolean).map(Number), [values]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (parsed.length < 2 || parsed.some((value) => !Number.isFinite(value))) {
      setError("유한한 숫자를 두 개 이상 입력하세요. 줄바꿈, 쉼표 또는 공백으로 구분할 수 있습니다.");
      valuesRef.current?.focus();
      return;
    }
    setError("");
    setLoading(true);
    try {
      await createImrRun({ run_id: runId, values: parsed, rules, ...(target ? { target: Number(target) } : {}) });
      navigate(`/runs/${runId}`);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "분석을 실행하지 못했습니다.");
      valuesRef.current?.focus();
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="page form-page" data-density="comfortable">
      <Link className="back-link" to="/"><ArrowLeft aria-hidden="true" /> 분석 홈</Link>
      <section className="page-heading">
        <div><span className="eyebrow">SPC / INDIVIDUALS</span><h1>I-MR 분석 설정</h1><p>시간 순서가 유지된 개별 관측값으로 공정 중심과 단기 변동을 확인합니다.</p></div>
      </section>
      {error && <div className="error-banner" role="alert"><AlertTriangle aria-hidden="true" /><div><strong>입력을 확인하세요</strong><p>{error}</p></div></div>}
      <form className="analysis-form" onSubmit={submit}>
        <section className="form-panel">
          <header><span className="step-index">01</span><div><h2>실행 식별자</h2><p>저장 후 변경되지 않는 분석 기록의 이름입니다.</p></div></header>
          <label className="field"><span>Run ID</span><input value={runId} onChange={(event) => setRunId(event.target.value)} required pattern="[A-Za-z0-9][A-Za-z0-9._-]{0,127}" /><small>영문, 숫자, 점, 밑줄, 하이픈을 사용할 수 있습니다.</small></label>
        </section>
        <section className="form-panel">
          <header><span className="step-index">02</span><div><h2>관측값</h2><p>측정한 순서 그대로 입력하세요. 결측값은 0으로 입력하지 않습니다.</p></div></header>
          <label className="field"><span>측정값 *</span><textarea ref={valuesRef} rows={9} value={values} onChange={(event) => setValues(event.target.value)} aria-invalid={Boolean(error)} aria-describedby={error ? "values-error" : "values-hint"} /><small id={error ? "values-error" : "values-hint"}>{parsed.filter(Number.isFinite).length}개 값 인식됨</small></label>
        </section>
        <section className="form-panel">
          <header><span className="step-index">03</span><div><h2>선택 옵션</h2><p>목표값은 관리 중심선과 별도로 표시됩니다.</p></div></header>
          <div className="inline-fields">
            <label className="field"><span>목표값</span><input type="number" step="any" value={target} onChange={(event) => setTarget(event.target.value)} placeholder="선택 입력" /></label>
            <label className="field"><span>규칙 세트</span><select value={rules} onChange={(event) => setRules(event.target.value as "basic" | "western_electric" | "nelson")}><option value="western_electric">NIST WECO + 추세 규칙</option><option value="nelson">Nelson 8개 규칙</option><option value="basic">3σ 한계만</option></select></label>
          </div>
        </section>
        <aside className="method-note"><strong>계산 방법</strong><p>연속 두 관측값의 이동범위와 NIST 3-sigma 관리한계를 사용합니다. Western Electric 규칙, Nelson 8개 규칙 또는 3σ 한계만 선택할 수 있습니다. 실행 결과에는 입력 digest, 엔진 버전, 가정과 공개 출처가 함께 저장됩니다.</p></aside>
        <div className="form-actions"><Button type="submit" variant="primary" loading={loading} icon={<Play />}>분석 실행</Button></div>
      </form>
    </div>
  );
}
