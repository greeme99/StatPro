import { AlertTriangle, ArrowRight, CheckCircle2, FlaskConical, Gauge, Server } from "lucide-react";
import { lazy, Suspense, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { listRuns } from "../api";
import { toImrView } from "../analysis";
import { Button } from "../components/Button";
import type { StoredRun } from "../types";

const ProcessRail = lazy(() => import("../components/ProcessRail").then((module) => ({ default: module.ProcessRail })));

const labels: Record<string, string> = {
  "spc.imr": "I-MR 관리도",
  "spc.xbar_r": "Xbar-R 관리도",
  "capability.normal_individuals": "정규 공정능력",
  "doe.full_factorial_2level": "2수준 완전요인 DOE",
  "doe.full_factorial_2level_analysis": "2수준 완전요인 DOE 분석",
  "doe.full_factorial_2level_desirability": "DOE 다중 응답 최적화",
  "doe.fractional_factorial_2level": "2수준 일부요인 DOE",
  "doe.fractional_factorial_2level_analysis": "2수준 일부요인 DOE 분석",
  "doe.central_composite": "중앙합성 반응표면 DOE",
  "doe.box_behnken": "Box–Behnken 반응표면 DOE",
  "doe.central_composite_analysis": "중앙합성 2차 모형 분석",
  "doe.central_composite_surface": "반응표면 정상점·격자 탐색",
  "doe.plackett_burman": "Plackett–Burman 선별 DOE",
  "msa.gage_rr_crossed": "교차 Gage R&R",
};

export function DashboardPage() {
  const [runs, setRuns] = useState<StoredRun[]>([]);
  const [state, setState] = useState<"loading" | "ready" | "error">("loading");

  useEffect(() => {
    let active = true;
    listRuns(20)
      .then((page) => { if (active) { setRuns(page.items); setState("ready"); } })
      .catch(() => { if (active) setState("error"); });
    return () => { active = false; };
  }, []);

  const latest = runs.at(-1);
  const warningCount = useMemo(() => runs.reduce((sum, run) => sum + run.result.warnings.length, 0), [runs]);
  const imr = toImrView(latest?.result);

  return (
    <div className="page" data-density="comfortable">
      <section className="page-heading">
        <div>
          <span className="eyebrow">QUALITY WORKBENCH</span>
          <h1>공정 판단을 한 화면에서</h1>
          <p>분석 실행부터 관리한계, 경고, 계산 근거까지 같은 기록으로 확인합니다.</p>
        </div>
        <div className="page-actions"><Link to="/analyses/doe/box-behnken"><Button icon={<FlaskConical />}>DOE Box–Behnken</Button></Link><Link to="/analyses/doe/central-composite"><Button icon={<FlaskConical />}>DOE 반응표면</Button></Link><Link to="/analyses/doe/plackett-burman"><Button icon={<FlaskConical />}>DOE 선별설계</Button></Link><Link to="/analyses/doe/fractional-factorial"><Button icon={<FlaskConical />}>DOE 일부요인</Button></Link><Link to="/analyses/doe/response-optimizer"><Button icon={<FlaskConical />}>DOE 응답 최적화</Button></Link><Link to="/analyses/doe/full-factorial"><Button icon={<FlaskConical />}>새 DOE 분석</Button></Link><Link to="/analyses/imr/new"><Button variant="primary" icon={<FlaskConical />}>새 I-MR 분석</Button></Link></div>
      </section>

      <section className="metric-grid" aria-label="분석 현황">
        <article className="metric-card"><Server aria-hidden="true" /><span>저장된 실행</span><strong>{runs.length}</strong><small>불변 Analysis Run</small></article>
        <article className="metric-card"><Gauge aria-hidden="true" /><span>최근 분석</span><strong className="metric-text">{latest ? labels[latest.result.analysis_type] ?? latest.result.analysis_type : "없음"}</strong><small>{latest?.result.engine_version ?? "엔진 0.6.0"}</small></article>
        <article className="metric-card"><AlertTriangle aria-hidden="true" /><span>검토할 경고</span><strong>{warningCount}</strong><small>가정과 제한 포함</small></article>
        <article className="metric-card"><CheckCircle2 aria-hidden="true" /><span>API 상태</span><strong className={state === "error" ? "status-metric is-error" : "status-metric"}>{state === "ready" ? "정상" : state === "error" ? "연결 오류" : "확인 중"}</strong><small>Loopback 연결</small></article>
      </section>

      <section className="dashboard-grid">
        <article className="panel process-panel">
          <header className="panel-heading">
            <div><span className="eyebrow">PROCESS RAIL</span><h2>최근 공정 판독</h2></div>
            {latest && <Link className="text-link" to={`/runs/${latest.run_id}`}>결과 열기 <ArrowRight aria-hidden="true" /></Link>}
          </header>
          {state === "loading" && <div className="skeleton chart-skeleton" aria-label="최근 분석 불러오는 중" />}
          {state === "error" && <div className="state-message is-error"><AlertTriangle aria-hidden="true" /><h3>분석 서버에 연결하지 못했습니다</h3><p>로컬 API가 127.0.0.1:8765에서 실행 중인지 확인하세요.</p></div>}
          {state === "ready" && !imr && <div className="state-message"><FlaskConical aria-hidden="true" /><h3>판독할 I-MR 결과가 없습니다</h3><p>첫 측정값 묶음을 실행하면 관리한계 레일이 여기에 표시됩니다.</p></div>}
          {imr && <Suspense fallback={<div className="skeleton chart-skeleton" aria-label="관리도 불러오는 중" />}><ProcessRail points={imr.points} center={imr.center} ucl={imr.ucl} lcl={imr.lcl} /></Suspense>}
        </article>

        <article className="panel recent-panel">
          <header className="panel-heading"><div><span className="eyebrow">RUN LOG</span><h2>최근 실행</h2></div></header>
          {state === "ready" && runs.length === 0 ? (
            <div className="state-message"><Server aria-hidden="true" /><h3>저장된 실행이 없습니다</h3><p>새 분석을 실행하면 재현 가능한 기록이 쌓입니다.</p></div>
          ) : (
            <ul className="run-list">
              {[...runs].reverse().slice(0, 6).map((run) => (
                <li key={run.run_id}>
                  <Link to={`/runs/${run.run_id}`}>
                    <span><strong>{run.run_id}</strong><small>{labels[run.result.analysis_type] ?? run.result.analysis_type}</small></span>
                    <span className="run-version">v{run.result.engine_version}</span>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </article>
      </section>
    </div>
  );
}
