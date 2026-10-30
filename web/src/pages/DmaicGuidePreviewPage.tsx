import { ArrowRight, BarChart3, ClipboardList, FlaskConical, Gauge, Search, ShieldCheck, Wrench } from "lucide-react";
import { Link } from "react-router-dom";

type ToolCard = { title: string; description: string; status: "구현됨" | "개발 예정"; to?: string; icon: typeof BarChart3 };

const phases = [
  { title: "정의 (Define)", description: "문제, 고객 요구사항, 프로젝트 범위를 명확히 합니다.", tools: "프로젝트 헌장 · VOC · SIPOC · 이해관계자 분석" },
  { title: "측정 (Measure)", description: "기준 성과를 만들고 측정 품질을 확인합니다.", tools: "데이터 수집 · Gage R&R · 측정시스템 분석" },
  { title: "분석 (Analyze)", description: "변동을 조사하고 집중할 원인을 검증합니다.", tools: "파레토 · 특성요인도 · 5 Why · 근본원인 분석" },
  { title: "개선 (Improve)", description: "개선안을 비교하고 실험으로 효과를 확인합니다.", tools: "실험계획법(DOE) · 개선안 선정 · 시범 운영" },
  { title: "관리 (Control)", description: "성과를 모니터링하고 개선 상태를 유지합니다.", tools: "통계적 공정관리(SPC) · 관리계획서 · FMEA" },
];

const tools: ToolCard[] = [
  { title: "공정 변동 이해", description: "통계적 공정관리(SPC) 관리도로 공정을 모니터링하고 이상 신호를 확인합니다.", status: "구현됨", to: "/analyses/spc/attribute", icon: BarChart3 },
  { title: "공정능력 평가", description: "규격 한계를 기준으로 공정 성과를 비교하는 공정능력 분석은 개발 예정입니다.", status: "개발 예정", icon: Gauge },
  { title: "측정 품질 확인", description: "Gage R&R과 측정시스템 분석(MSA)은 측정값을 신뢰하기 전에 검토할 예정입니다.", status: "개발 예정", icon: Wrench },
  { title: "근본원인 조사", description: "특성요인도, 파레토, 5 Why 기반의 근본원인 분석은 개발 예정입니다.", status: "개발 예정", icon: Search },
  { title: "개선 실험 설계", description: "실험계획법(DOE)으로 공정 반응에 영향을 주는 인자를 설계하고 분석합니다.", status: "구현됨", to: "/doe", icon: FlaskConical },
  { title: "결과를 조치로 전환", description: "고장 형태 및 영향 분석(FMEA)에서 관리계획서와 조치·승인 이력을 연결합니다.", status: "구현됨", to: "/fmea", icon: ShieldCheck },
];

function Status({ value }: { value: ToolCard["status"] }) { return <span className={`preview-status ${value === "구현됨" ? "is-implemented" : "is-planned"}`}>{value}</span>; }

export function DmaicGuidePreviewPage() {
  return <div className="page dmaic-guide" data-density="comfortable">
    <nav className="breadcrumb" aria-label="경로"><Link to="/home">홈 (Home)</Link><span aria-hidden="true">/</span><span>DMAIC 알아보기</span></nav>
    <section className="preview-hero"><div><span className="eyebrow">HOW DMAIC WORKS</span><h1>DMAIC를 따라 개선 과제를 구조화합니다</h1><p>프로젝트와 맞는 단계를 확인하고, 현재 사용할 수 있는 전문 작업공간과 앞으로 추가될 도구를 구분해 봅니다.</p></div><div className="preview-hero-actions"><Link className="button button-secondary" to="/home/learning">학습 리소스</Link><Link className="button button-secondary" to="/home">홈으로 돌아가기</Link></div></section>
    <section aria-labelledby="phase-title"><header className="dmaic-guide-heading"><span className="eyebrow">IMPROVEMENT PATH</span><h2 id="phase-title">DMAIC 단계별 안내</h2><p>단계는 프로젝트의 순서이며, 전문 분석 작업공간은 해당 단계의 근거를 만듭니다.</p></header><div className="dmaic-phase-grid">{phases.map((phase, index) => <article className="dmaic-phase-card" key={phase.title}><span>{index + 1}</span><h3>{phase.title}</h3><p>{phase.description}</p><small>{phase.tools}</small></article>)}</div></section>
    <section aria-labelledby="tool-title"><header className="dmaic-guide-heading"><span className="eyebrow">BUILT FOR IMPROVEMENT</span><h2 id="tool-title">분석 근거와 실행 의사결정 연결</h2><p>현재 구현된 도구는 바로 열 수 있으며, 나머지 항목은 필요한 데이터 계약과 업무 흐름을 정한 뒤 제공됩니다.</p></header><div className="dmaic-tool-grid">{tools.map((tool) => { const Icon = tool.icon; return <article className="dmaic-tool-card" key={tool.title}><header><span className="preview-icon"><Icon aria-hidden="true" /></span><Status value={tool.status} /></header><h3>{tool.title}</h3><p>{tool.description}</p>{tool.to ? <Link className="text-link" to={tool.to}>작업공간 열기 <ArrowRight aria-hidden="true" /></Link> : <div className="preview-note"><ClipboardList aria-hidden="true" /> 개발 범위와 데이터 계약을 확정 중입니다.</div>}</article>; })}</div></section>
    <section className="dmaic-faq" aria-labelledby="faq-title"><header className="dmaic-guide-heading"><span className="eyebrow">QUESTIONS ANSWERED</span><h2 id="faq-title">시작 전 확인</h2><p>개선 과제의 출발점을 선택하기 위한 간단한 안내입니다.</p></header><details open><summary>DMAIC에는 무엇이 포함되나요?</summary><p>DMAIC는 정의, 측정, 분석, 개선, 관리 단계로 프로젝트를 구조화합니다. StatPro에서는 각 단계가 DOE·SPC·FMEA와 같은 전문 작업공간의 실행 근거를 참조하도록 설계합니다.</p></details><details><summary>시작하려면 데이터가 필요한가요?</summary><p>아닙니다. 문제 정의와 프로젝트 범위는 데이터 없이 시작할 수 있습니다. 다만 통계적 공정관리(SPC), 공정능력, 측정시스템 분석은 목적에 맞는 측정 데이터가 필요합니다.</p></details><details><summary>특정 DMAIC 단계를 어떻게 열 수 있나요?</summary><p>현재는 홈 (Home)에서 DOE, SPC, FMEA 전문 작업공간을 바로 열 수 있습니다. DMAIC 프로젝트 허브와 단계별 도구는 개발 예정이며, 준비 상태는 메뉴에서 명확히 표시합니다.</p></details><details><summary>모든 단계를 완료해야 개별 도구를 사용할 수 있나요?</summary><p>아닙니다. 현재 구현된 전문 작업공간은 프로젝트 단계와 관계없이 직접 사용할 수 있습니다. DMAIC는 이러한 실행을 프로젝트 맥락 안에서 연결하기 위한 확장 구조입니다.</p></details></section>
  </div>;
}
