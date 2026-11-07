import { AlertTriangle, ArrowLeft, Play } from "lucide-react";
import { FormEvent, useMemo, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { createAttributeAgreementRun } from "../api";
import { Button } from "../components/Button";

type Assessment = { item: string; appraiser: string; trial: number; rating: string; standard: string };

function defaultRunId() {
  return "attribute-agreement-" + new Date().toISOString().replace(/[-:TZ.]/g, "").slice(0, 14);
}

function parseRecords(source: string): Assessment[] | null {
  const rows = source.trim().split(/\r?\n/).filter(Boolean);
  const parsed = rows.map((row) => row.split(/[,\t;]/).map((cell) => cell.trim()));
  if (parsed[0]?.[0]?.toLowerCase() === "item") parsed.shift();
  if (!parsed.length || parsed.some((row) => row.length !== 5 || !row[0] || !row[1] || !row[3] || !row[4] || !Number.isInteger(Number(row[2])) || Number(row[2]) < 1)) return null;
  return parsed.map(([item, appraiser, trial, rating, standard]) => ({ item, appraiser, trial: Number(trial), rating, standard }));
}

export function AttributeAgreementSetupPage() {
  const navigate = useNavigate();
  const [runId, setRunId] = useState(defaultRunId);
  const [recordsText, setRecordsText] = useState("item,appraiser,trial,rating,standard\nI1,A,1,양품,양품\nI1,A,2,양품,양품\nI1,B,1,양품,양품\nI1,B,2,불량,양품\nI2,A,1,불량,불량\nI2,A,2,불량,불량\nI2,B,1,불량,불량\nI2,B,2,불량,불량");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const textarea = useRef<HTMLTextAreaElement>(null);
  const records = useMemo(() => parseRecords(recordsText), [recordsText]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!records) {
      setError("각 행을 품목, 검사자, 반복, 판정, 표준 판정의 다섯 열로 입력하세요. 헤더 행은 선택사항입니다.");
      textarea.current?.focus();
      return;
    }
    setError("");
    setLoading(true);
    try {
      await createAttributeAgreementRun({ run_id: runId, records });
      navigate("/runs/" + runId);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Attribute Agreement 분석을 실행하지 못했습니다.");
      textarea.current?.focus();
    } finally {
      setLoading(false);
    }
  }

  return <div className="page form-page" data-density="comfortable">
    <Link className="back-link" to="/home/dmaic/measure"><ArrowLeft aria-hidden="true" /> DMAIC 측정(Measure)</Link>
    <section className="page-heading"><div><span className="eyebrow">MSA / ATTRIBUTE AGREEMENT</span><h1>Attribute Agreement 분석 설정</h1><p>AOI·ICT·FCT 같은 명목형 검사에서 반복 판정, 표준 대비 정확도, 검사자 간 일치도를 확인합니다.</p></div></section>
    {error && <div className="error-banner" role="alert"><AlertTriangle aria-hidden="true" /><div><strong>입력을 확인하세요</strong><p>{error}</p></div></div>}
    <form className="analysis-form" onSubmit={submit}>
      <section className="form-panel"><header><span className="step-index">01</span><div><h2>분석 실행 식별자</h2><p>실행 결과는 불변 Run ID로 저장되어 FMEA·관리계획의 검사 근거로 연결할 수 있습니다.</p></div></header><label className="field"><span>Run ID</span><input value={runId} onChange={(event) => setRunId(event.target.value)} required pattern="[A-Za-z0-9][A-Za-z0-9._-]{0,127}" /></label></section>
      <section className="form-panel"><header><span className="step-index">02</span><div><h2>반복 검사 판정 데이터</h2><p>CSV, 탭 또는 세미콜론 구분값을 붙여넣습니다. 모든 검사자가 모든 품목을 동일한 횟수로 판정하고, 품목별 표준 판정은 하나여야 합니다.</p></div></header><label className="field"><span>item, appraiser, trial, rating, standard *</span><textarea ref={textarea} rows={12} value={recordsText} onChange={(event) => setRecordsText(event.target.value)} aria-invalid={Boolean(error)} /><small>{records ? records.length + "개 판정값 인식됨" : "형식 확인 필요"}</small></label></section>
      <aside className="method-note"><strong>선택 가이드</strong><p>합격·불합격, 결함 분류처럼 명목형 판정과 알려진 표준이 있을 때 사용합니다. 연속 측정값의 반복성·재현성은 교차 Gage R&R을 사용하세요. 결과는 검사자 내 일치, 표준 대비 일치, 전체 일치와 Cohen’s κ를 제공합니다.</p></aside>
      <div className="form-actions"><Button type="submit" variant="primary" loading={loading} icon={<Play />}>일치도 분석 실행</Button></div>
    </form>
  </div>;
}
