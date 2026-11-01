import { ArrowRight, BarChart3, FileWarning, FlaskConical, type LucideIcon } from "lucide-react";
import { Link } from "react-router-dom";

type Workspace = {
  title: string;
  description: string;
  workflow: string[];
  action: string;
  to: string;
  icon: LucideIcon;
};

const operatingFlow = [
  { title: "현장 과제 선택", description: "개선할 공정과 품질 특성을 정합니다." },
  { title: "작업공간 설정", description: "DOE, SPC, FMEA 중 업무에 맞는 작업공간을 엽니다." },
  { title: "데이터 연결", description: "작업표와 기준 조건, 추적 대상을 연결합니다." },
  { title: "분석·검토", description: "분석을 실행하고 신호, 위험, 효과를 검토합니다." },
  { title: "표준화·추적", description: "보고서와 관리계획서로 조치와 변경을 이어갑니다." },
];

const coreWorkspaces: Workspace[] = [
  {
    title: "실험계획법(DOE)",
    description: "공정 인자의 효과를 검증하고 목표 품질을 만족하는 조건을 찾습니다.",
    workflow: ["목적·반응 정의", "인자·설계 생성", "실험 데이터 입력", "효과 분석", "조건 최적화·보고"],
    action: "DOE 업무 시작",
    to: "/doe",
    icon: FlaskConical,
  },
  {
    title: "통계적 공정관리(SPC)",
    description: "공정의 안정성을 감시하고 이상 신호를 현장 조치로 연결합니다.",
    workflow: ["관리도 선택", "공정 데이터 입력", "관리한계 설정", "이상 신호 검토", "조치·보고"],
    action: "SPC 업무 시작",
    to: "/spc",
    icon: BarChart3,
  },
  {
    title: "고장 형태 및 영향 분석(FMEA)",
    description: "공정 위험과 예방·검출 관리를 연결하고 조치 이후 위험을 추적합니다.",
    workflow: ["공정·특성 연결", "고장 형태 분석", "위험 우선순위", "예방·검출 조치", "승인·관리계획"],
    action: "FMEA 업무 시작",
    to: "/fmea",
    icon: FileWarning,
  },
];

const dmaic = [
  { title: "정의 (Define)", description: "문제와 고객 요구, 범위를 합의합니다.", tools: "프로젝트 헌장 · VOC · SIPOC" },
  { title: "측정 (Measure)", description: "기준 성과와 측정 신뢰성을 확보합니다.", tools: "데이터 수집 · MSA · 공정능력" },
  { title: "분석 (Analyze)", description: "변동과 결함의 근본원인을 검증합니다.", tools: "파레토 · 특성요인도 · 5 Why" },
  { title: "개선 (Improve)", description: "개선안을 시험하고 최적 조건을 확정합니다.", tools: "DOE · 파일럿 · 개선안 선정" },
  { title: "관리 (Control)", description: "성과를 감시하고 표준과 위험 관리를 유지합니다.", tools: "SPC · FMEA · 관리계획서" },
];

function WorkspaceCard({ workspace }: { workspace: Workspace }) {
  const Icon = workspace.icon;
  return (
    <article className="preview-card home-workspace-card">
      <header><span className="preview-icon"><Icon aria-hidden="true" /></span><span className="utility-label">작업공간 (Workspace)</span></header>
      <h3>{workspace.title}</h3>
      <p>{workspace.description}</p>
      <ol className="workspace-flow" aria-label={`${workspace.title} 업무 흐름`}>
        {workspace.workflow.map((step) => <li key={step}>{step}</li>)}
      </ol>
      <Link className="text-link" to={workspace.to}>{workspace.action} <ArrowRight aria-hidden="true" /></Link>
    </article>
  );
}

export function MenuPreviewPage() {
  return (
    <div className="page menu-preview home-preview" data-density="comfortable">
      <nav className="breadcrumb" aria-label="경로"><Link to="/home">홈 (Home)</Link></nav>
      <section className="preview-hero home-operations-hero" aria-labelledby="home-title">
        <div>
          <span className="eyebrow">현장 분석 운영 흐름</span>
          <h1 id="home-title">공정 문제에서 검증된 조치까지</h1>
          <p>현장 과제를 선택하고 전문 작업공간에서 데이터를 분석한 뒤, 결과를 보고서·관리계획·개선 프로젝트의 후속 조치로 연결합니다.</p>
        </div>
        <ol className="home-operating-flow" aria-label="현장 분석 운영 단계">
          {operatingFlow.map((step, index) => <li key={step.title}><span>{index + 1}</span><div><strong>{step.title}</strong><p>{step.description}</p></div></li>)}
        </ol>
      </section>
      <section className="home-core-panel" aria-labelledby="core-title">
        <header className="preview-section-heading">
          <span className="eyebrow">전문 작업공간 (Core Workspaces)</span>
          <h2 id="core-title">업무에 맞는 작업공간에서 시작합니다</h2>
          <p>각 작업공간은 설정에서 보고까지 동일한 원칙으로 이어지고, 결과는 다음 현장 업무의 입력 근거가 됩니다.</p>
        </header>
        <div className="preview-grid">{coreWorkspaces.map((workspace) => <WorkspaceCard key={workspace.title} workspace={workspace} />)}</div>
      </section>
      <section className="home-dmaic-panel" aria-labelledby="dmaic-title">
        <header className="home-dmaic-heading">
          <div><span className="eyebrow">개선 프로젝트 (Improvement Project)</span><h2 id="dmaic-title">DMAIC로 분석 결과를 개선 과제로 운영합니다</h2><p>개별 분석을 프로젝트 목표·근거·조치·관리 상태와 연결해 정의부터 관리까지 일관되게 추적합니다.</p></div>
          <Link className="text-link" to="/home/dmaic">설명 및 작업공간 열기 <ArrowRight aria-hidden="true" /></Link>
        </header>
        <ol className="home-dmaic-list" aria-label="DMAIC 단계">
          {dmaic.map((item, index) => <li key={item.title}><span>{index + 1}</span><div><strong>{item.title}</strong><p>{item.description}</p><small>{item.tools}</small></div></li>)}
        </ol>
      </section>
    </div>
  );
}
