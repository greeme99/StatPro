import { BarChart3, CheckCircle2, ClipboardList, FileOutput, FlaskConical, Grid3X3, Info, Route, SlidersHorizontal } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";
import { Button } from "../components/Button";

type Tab = "plan" | "data" | "analysis" | "results" | "optimize" | "evidence";

const tabs: Array<{ id: Tab; label: string }> = [
  { id: "plan", label: "설계 및 계획" }, { id: "data", label: "실행 데이터" },
  { id: "analysis", label: "분석" }, { id: "results", label: "결과" },
  { id: "optimize", label: "최적화" }, { id: "evidence", label: "근거" },
];

const designs = [
  { title: "2수준 완전요인", detail: "요인 효과와 교호작용을 추정합니다.", to: "/analyses/doe/full-factorial" },
  { title: "2수준 일부요인", detail: "실행 수를 줄이고 별칭 구조를 함께 검토합니다.", to: "/analyses/doe/fractional-factorial" },
  { title: "Plackett–Burman 선별설계", detail: "중요 요인 후보를 빠르게 좁힙니다.", to: "/analyses/doe/plackett-burman" },
  { title: "중앙합성설계", detail: "곡률과 반응표면을 추정합니다.", to: "/analyses/doe/central-composite" },
  { title: "Box–Behnken 설계", detail: "세 수준 반응표면 설계를 만듭니다.", to: "/analyses/doe/box-behnken" },
];

const progress = ["실험 목적", "인자·반응", "설계·블록", "실행표", "분석·최적화"];

export function DoeWorkspacePage() {
  const [tab, setTab] = useState<Tab>("plan");
  return <div className="page doe-workspace" data-density="comfortable">
    <nav className="breadcrumb" aria-label="현재 위치">홈 <span aria-hidden="true">/</span> 실험계획법(DOE)</nav>
    <section className="page-heading">
      <div><span className="eyebrow">DOE WORKSPACE</span><h1>실험계획법(DOE) 작업공간</h1><p>실험 목적부터 실행표, 분석, 최적화와 보고서까지 하나의 흐름으로 관리합니다.</p></div>
      <Link to="/analyses/doe/full-factorial"><Button variant="primary" icon={<FlaskConical />}>새 실험 설계</Button></Link>
    </section>
    <section className="doe-overview panel" aria-labelledby="doe-progress-title">
      <div><span className="eyebrow">설계 진행 상태</span><h2 id="doe-progress-title">실험을 시작하기 전에 설계 조건을 확인하세요</h2></div>
      <ol className="doe-progress">{progress.map((label, index) => <li key={label}><span>{index + 1}</span><strong>{label}</strong></li>)}</ol>
      <aside className="doe-readiness"><Info aria-hidden="true" /><div><h3>시작 전 확인</h3><ul><li>측정 가능한 반응과 최적화 목표를 정합니다.</li><li>제어 가능한 인자와 안전한 운전 범위를 정합니다.</li><li>반복, 무작위화, 블록과 확인 실험을 계획합니다.</li></ul></div></aside>
    </section>
    <div className="workspace-tabs" role="tablist" aria-label="DOE 작업 단계">
      {tabs.map((item) => <button type="button" role="tab" aria-selected={tab === item.id} className={tab === item.id ? "is-active" : ""} onClick={() => setTab(item.id)} key={item.id}>{item.label}</button>)}
    </div>
    {tab === "plan" && <section className="workspace-section" aria-labelledby="design-selection-title">
      <header><div><span className="eyebrow">01 · 설계 및 계획</span><h2 id="design-selection-title">설계 유형을 선택하세요</h2><p>현재 제공하는 설계만 바로 시작할 수 있습니다. 설계별 화면에서 인자, 반응, 반복과 블록을 설정합니다.</p></div></header>
      <div className="doe-design-grid">{designs.map((design) => <article className="doe-design-card" key={design.title}><Grid3X3 aria-hidden="true" /><h3>{design.title}</h3><p>{design.detail}</p><Link className="text-link" to={design.to} aria-label={`${design.title} 설계 시작`}>설계 시작</Link></article>)}</div>
    </section>}
    {tab === "data" && <section className="workspace-section workspace-guidance"><ClipboardList aria-hidden="true" /><div><span className="eyebrow">02 · 실행 데이터</span><h2>실행 순서에 맞춰 반응을 입력합니다</h2><p>각 설계 화면은 실행 수를 계산하고, 응답값 수가 일치할 때만 분석을 실행합니다. 데이터가 준비되면 선택한 설계의 설정 화면에서 계속합니다.</p><Link className="text-link" to="/analyses/doe/full-factorial">완전요인 설계에서 응답 입력</Link></div></section>}
    {tab === "analysis" && <section className="workspace-section workspace-guidance"><BarChart3 aria-hidden="true" /><div><span className="eyebrow">03 · 분석</span><h2>효과, ANOVA, 잔차와 별칭 한계를 검토합니다</h2><p>설계에 따라 주효과·교호작용, Pareto, 완전 2차 모형, 정상점 및 표면 탐색 결과가 분석 실행에 보존됩니다.</p><Link className="text-link" to="/analyses/doe/fractional-factorial">일부요인 설계 분석</Link></div></section>}
    {tab === "results" && <section className="workspace-section workspace-guidance"><Route aria-hidden="true" /><div><span className="eyebrow">04 · 결과</span><h2>분석 실행 결과를 검토하고 추적합니다</h2><p>각 결과는 입력 digest, 엔진 버전, 가정, 경고와 근거를 포함하는 불변 분석 실행으로 저장됩니다.</p><Link className="text-link" to="/catalog/reports">결과 및 보고서 보기</Link></div></section>}
    {tab === "optimize" && <section className="workspace-section workspace-guidance"><SlidersHorizontal aria-hidden="true" /><div><span className="eyebrow">05 · 최적화</span><h2>여러 응답 목표를 함께 최적화합니다</h2><p>요인 제약 안에서 최대화, 최소화, 목표값 기준을 결합하고 응답별 만족도와 권장 설정을 확인합니다.</p><Link className="text-link" to="/analyses/doe/response-optimizer">다중 응답 최적화 시작</Link></div></section>}
    {tab === "evidence" && <section className="workspace-section workspace-guidance"><FileOutput aria-hidden="true" /><div><span className="eyebrow">근거 및 보고서</span><h2>분석 결과를 재현 가능한 형식으로 내보냅니다</h2><p>DOE 분석 실행은 HTML, JSON, CSV와 지원 Plot의 SVG 그래프를 ZIP으로 제공합니다. 고객·규제 검토용 양식은 검토 시작점이며 승인·준수·전자서명을 주장하지 않습니다. PDF와 조직별 승인 양식은 개발 예정입니다.</p><span className="delivery-status status-구현됨"><CheckCircle2 aria-hidden="true" /> SVG 그래프·검토용 양식 구현됨</span></div></section>}
  </div>;
}
