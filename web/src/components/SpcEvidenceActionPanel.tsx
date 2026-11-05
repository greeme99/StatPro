import { CheckCircle2, ClipboardCheck, Copy, ShieldCheck, TriangleAlert } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";
import type { ResultBundle } from "../types";

type Props = {
  runId: string;
  result: ResultBundle;
};

export function SpcEvidenceActionPanel({ runId, result }: Props) {
  const [copied, setCopied] = useState(false);
  const hasSignals = signalCount(result) > 0;
  const digest = result.input_digest;

  async function copyReference() {
    const reference = `run_id=${runId}\nanalysis_type=${result.analysis_type}\ninput_digest=${digest}\nengine_version=${result.engine_version}`;
    try {
      await navigator.clipboard.writeText(reference);
      setCopied(true);
    } catch {
      setCopied(false);
    }
  }

  return (
    <section className={hasSignals ? "spc-evidence-action is-alert" : "spc-evidence-action"} aria-labelledby="spc-evidence-action-title">
      <header>
        {hasSignals ? <TriangleAlert aria-hidden="true" /> : <CheckCircle2 aria-hidden="true" />}
        <div>
          <span className="eyebrow">현장 이관 (FIELD HANDOFF)</span>
          <h2 id="spc-evidence-action-title">현장 조치와 증적 연결</h2>
          <p>{hasSignals ? "이상 신호는 원인을 확정하지 않습니다. 현장 조건을 확인하고, 선택한 작업공간에서 조사·조치 근거로 이 실행을 연결하세요." : "현재 관리 한계 이탈 신호는 없습니다. 기준선·수집 조건을 유지하고 필요하면 이 실행을 관리계획 검토의 근거로 연결하세요."}</p>
        </div>
      </header>
      <dl className="spc-evidence-reference">
        <div><dt>분석 실행</dt><dd>{runId}</dd></div>
        <div><dt>입력 다이제스트</dt><dd className="digest">{digest}</dd></div>
        <div><dt>계산 엔진</dt><dd>{result.engine_version}</dd></div>
      </dl>
      <div className="spc-evidence-actions">
        <Link className="button button-primary" to={`/fmea?analysisRunId=${encodeURIComponent(runId)}&inputDigest=${encodeURIComponent(digest)}`}><ShieldCheck aria-hidden="true" />FMEA 관리계획 연결</Link>
        <Link className="button button-secondary" to={`/home/dmaic/measure?analysisRunId=${encodeURIComponent(runId)}`}><ClipboardCheck aria-hidden="true" />DMAIC 측정 근거 연결</Link>
        <button className="button button-ghost" type="button" onClick={copyReference}><Copy aria-hidden="true" />{copied ? "증적 참조를 복사했습니다" : "증적 참조 복사"}</button>
      </div>
      <p className="spc-evidence-action-note">연결 대상은 저장 시 실행 ID와 입력 다이제스트를 서버에서 재검증합니다. 이 화면의 이동·복사는 승인 또는 조치 완료를 의미하지 않습니다.</p>
    </section>
  );
}

function signalCount(result: ResultBundle) {
  const diagnostics = result.diagnostics as Record<string, unknown>;
  return Object.entries(diagnostics)
    .filter(([key, value]) => key.includes("signal") && Array.isArray(value))
    .reduce((count, [, value]) => count + (value as unknown[]).length, 0);
}
