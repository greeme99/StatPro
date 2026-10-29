import { ArrowRight, BarChart3, BookOpenCheck, ClipboardList, FlaskConical, Search, ShieldCheck, Wrench } from "lucide-react";
import { Link } from "react-router-dom";

type Resource = { title: string; description: string; status: "구현됨" | "개발 예정"; to?: string; icon: typeof BarChart3 };

const phases = [
  { title: "정의 (Define)", description: "문제와 범위, 고객 요구사항을 명확히 하는 단계입니다.", topics: "프로젝트 헌장 · VOC · SIPOC" },
  { title: "측정 (Measure)", description: "기준 성과와 측정 신뢰성을 확인하는 단계입니다.", topics: "데이터 수집 · Gage R&R · MSA" },
  { title: "분석 (Analyze)", description: "변동과 근본 원인을 분석해 개선 우선순위를 정합니다.", topics: "파레토 · 특성요인도 · 5 Why" },
  { title: "개선 (Improve)", description: "개선안을 실험으로 검증하고 실행 계획을 세웁니다.", topics: "실험계획법(DOE) · 시범 운영" },
  { title: "관리 (Control)", description: "성과를 유지하도록 공정과 위험을 모니터링합니다.", topics: "통계적 공정관리(SPC) · FMEA" },
];

const resources: Resource[] = [
  { title: "통계적 공정관리(SPC) 시작하기", description: "관리도 선택, 데이터 입력, 신호 해석의 기본 흐름을 학습합니다.", status: "구현됨", to: "/analyses/spc/attribute", icon: BarChart3 },
  { title: "실험계획법(DOE) 설계하기", description: "인자와 반응을 정의하고 실행표와 분석 결과를 연결하는 방법을 안내합니다.", status: "구현됨", to: "/doe", icon: FlaskConical },
  { title: "고장 형태 및 영향 분석(FMEA) 활용하기", description: "공정 흐름, 위험 기록, 관리계획서와 승인 근거의 연결을 다룹니다.", status: "구현됨", to: "/fmea", icon: ShieldCheck },
  { title: "측정시스템 분석(MSA) 기초", description: "측정값을 분석하기 전에 반복성·재현성을 확인하는 학습 자료입니다.", status: "개발 예정", icon: Wrench },
  { title: "근본원인 분석 실습", description: "파레토와 특성요인도를 사용해 조사 범위를 좁히는 방법을 다룹니다.", status: "개발 예정", icon: Search },
  { title: "개선 프로젝트 운영", description: "DMAIC 단계별 산출물을 하나의 개선 과제로 연결하는 학습 자료입니다.", status: "개발 예정", icon: ClipboardList },
];

function Status({ value }: { value: Resource["status"] }) { return <span className={`preview-status ${value === "구현됨" ? "is-implemented" : "is-planned"}`}>{value}</span>; }

export function LearningResourcesPreviewPage() {
  return <div className="page learning-resources" data-density="comfortable">
    <nav className="breadcrumb" aria-label="경로"><Link to="/">홈 (Home)</Link><span aria-hidden="true">/</span><Link to="/ui-preview/dmaic">DMAIC 알아보기</Link><span aria-hidden="true">/</span><span>학습 리소스</span></nav>
    <section className="preview-hero"><div><span className="eyebrow">LEARNING RESOURCES</span><h1>품질 개선을 위한 학습 리소스</h1><p>DMAIC 방법론과 현재 이용 가능한 전문 분석 작업공간을 연결해, 개선 과제의 다음 단계를 선택할 수 있도록 돕습니다.</p></div><Link className="button button-secondary" to="/ui-preview/dmaic">DMAIC 안내로 돌아가기</Link></section>
    <section aria-labelledby="method-title"><header className="dmaic-guide-heading"><span className="eyebrow">DMAIC METHODOLOGY</span><h2 id="method-title">DMAIC 방법론 개요</h2><p>단계별 목적과 산출물은 프로젝트의 맥락을 만들고, DOE·SPC·FMEA는 검증 가능한 분석 근거를 제공합니다.</p></header><div className="learning-phase-grid">{phases.map((phase) => <article className="learning-phase-card" key={phase.title}><h3>{phase.title}</h3><p>{phase.description}</p><small>{phase.topics}</small></article>)}</div></section>
    <section aria-labelledby="resource-title"><header className="dmaic-guide-heading"><span className="eyebrow">CHOOSE A LEARNING PATH</span><h2 id="resource-title">도구 중심 학습 경로</h2><p>구현된 분석은 바로 열어 볼 수 있으며, 개발 예정 자료는 제공 전까지 실행 도구로 오해되지 않도록 표시합니다.</p></header><div className="learning-resource-grid">{resources.map((resource) => { const Icon = resource.icon; return <article className="learning-resource-card" key={resource.title}><header><span className="preview-icon"><Icon aria-hidden="true" /></span><Status value={resource.status} /></header><h3>{resource.title}</h3><p>{resource.description}</p>{resource.to ? <Link className="text-link" to={resource.to}>작업공간 열기 <ArrowRight aria-hidden="true" /></Link> : <div className="preview-note"><BookOpenCheck aria-hidden="true" /> 학습 자료를 준비 중입니다.</div>}</article>; })}</div></section>
    <section className="learning-guides" aria-labelledby="guide-title"><header className="dmaic-guide-heading"><span className="eyebrow">STEP-BY-STEP LEARNING</span><h2 id="guide-title">학습을 시작하는 순서</h2><p>처음에는 문제와 측정 목적을 정한 다음, 공정 데이터와 위험 정보를 토대로 적합한 분석 작업공간을 선택합니다.</p></header><ol><li><strong>문제 정의</strong><span>개선하려는 공정, 고객 영향, 목표를 간단히 정리합니다.</span></li><li><strong>측정 계획</strong><span>수집할 데이터와 측정 단위, 필요한 표본 구조를 확인합니다.</span></li><li><strong>분석 실행</strong><span>SPC로 공정 신호를 확인하거나 DOE로 인자 효과를 검증합니다.</span></li><li><strong>위험과 조치 연결</strong><span>FMEA의 위험 기록과 관리계획서로 결과를 후속 조치에 연결합니다.</span></li></ol></section>
  </div>;
}
