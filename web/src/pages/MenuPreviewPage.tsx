import { ArrowRight, BarChart3, CheckCircle2, FileWarning, FlaskConical, FolderKanban, LayoutDashboard } from "lucide-react";
import { Link } from "react-router-dom";

type Status = "구현됨" | "개발 예정" | "외부 정책 필요";
type MenuItem = { title: string; description: string; status: Status; to?: string };

const coreWorkspaces: MenuItem[] = [
  { title: "실험계획법(DOE)", description: "설계, 실행표, 분석, 최적화, 결과 및 보고서를 하나의 흐름으로 관리합니다.", status: "구현됨", to: "/doe" },
  { title: "통계적 공정관리(SPC)", description: "관리도 종류 선택부터 데이터 입력, 분석 실행, 결과 및 보고서까지 연결합니다.", status: "구현됨", to: "/analyses/spc/attribute" },
  { title: "고장 형태 및 영향 분석(FMEA)", description: "PFMEA, 관리계획서, 조치 및 승인 이력을 추적합니다.", status: "구현됨", to: "/fmea" },
];
const dmaic = [
  { title: "정의 (Define)", description: "문제, 고객 요구사항, 프로젝트 범위를 명확히 합니다." },
  { title: "측정 (Measure)", description: "기준 성과와 측정시스템, 데이터를 확인합니다." },
  { title: "분석 (Analyze)", description: "변동과 근본원인을 검증합니다." },
  { title: "개선 (Improve)", description: "DOE로 개선안을 검증하고 최적 조건을 찾습니다." },
  { title: "관리 (Control)", description: "SPC와 FMEA 관리계획서로 개선을 유지합니다." },
];
const statusClass: Record<Status, string> = { "구현됨": "is-implemented", "개발 예정": "is-planned", "외부 정책 필요": "is-policy" };
function DeliveryBadge({ status }: { status: Status }) { return <span className={`preview-status ${statusClass[status]}`}>{status}</span>; }
function WorkspaceCard({ item, icon: Icon }: { item: MenuItem; icon: typeof FlaskConical }) {
  return <article className="preview-card"><header><span className="preview-icon"><Icon aria-hidden="true" /></span><DeliveryBadge status={item.status} /></header><h3>{item.title}</h3><p>{item.description}</p><Link className="text-link" to={item.to!}>작업공간 열기 <ArrowRight aria-hidden="true" /></Link></article>;
}
export function MenuPreviewPage() {
  return <div className="page menu-preview home-preview" data-density="comfortable">
    <nav className="breadcrumb" aria-label="경로"><Link to="/home">홈 (Home)</Link></nav>
    <section className="preview-hero"><div><span className="eyebrow">HOME / MENU PREVIEW</span><h1>제조·품질 분석의 시작점</h1><p>홈 (Home)에서 현재 사용할 수 있는 DOE, SPC, FMEA 작업공간으로 바로 이동하고, 프로젝트형 개선 흐름은 DMAIC에서 확장합니다.</p></div><div className="preview-legend" aria-label="상태 범례"><DeliveryBadge status="구현됨" /><DeliveryBadge status="개발 예정" /><DeliveryBadge status="외부 정책 필요" /></div></section>
    <section className="home-core-panel" aria-labelledby="core-title"><header className="preview-section-heading"><span className="eyebrow">CORE WORKSPACES</span><h2 id="core-title">핵심 전문 작업공간</h2><p>모든 분석은 `설정 → 데이터 → 분석 → 결과 → 보고서` 순서를 따릅니다.</p></header><div className="preview-grid"><WorkspaceCard item={coreWorkspaces[0]} icon={FlaskConical} /><WorkspaceCard item={coreWorkspaces[1]} icon={BarChart3} /><WorkspaceCard item={coreWorkspaces[2]} icon={FileWarning} /></div></section>
    <section className="home-dmaic-panel" aria-labelledby="dmaic-title"><div><span className="eyebrow">IMPROVEMENT PROJECT</span><h2 id="dmaic-title">개선 프로젝트 (DMAIC)</h2><p>프로젝트 맥락과 기존 분석 실행을 참조로 연결하는 확장 작업공간입니다.</p><div className="preview-legend"><DeliveryBadge status="개발 예정" /></div><Link className="text-link" to="/home/dmaic">DMAIC 알아보기 <ArrowRight aria-hidden="true" /></Link></div><ol className="home-dmaic-list" aria-label="DMAIC 단계">{dmaic.map((item, index) => <li key={item.title}><span>{index + 1}</span><div><strong>{item.title}</strong><p>{item.description}</p></div></li>)}</ol></section>
    <section className="preview-contract" aria-labelledby="ownership-title"><CheckCircle2 aria-hidden="true" /><div><h2 id="ownership-title">데이터와 결과의 소유 경계</h2><p>DOE·SPC 결과는 불변 분석 실행(Analysis Run), FMEA 관리계획서는 FMEA 연구가 소유합니다. DMAIC는 ID·ETag·입력 다이제스트를 참조로만 보관합니다.</p></div></section>
    <section className="home-menu-summary" aria-labelledby="menu-title"><span className="preview-icon"><LayoutDashboard aria-hidden="true" /></span><div><h2 id="menu-title">홈 (Home) 기준 메뉴 분기</h2><p>프로젝트 및 작업공간 (Projects & Workspaces) 아래에서 DOE, SPC, FMEA를 즉시 열고, DMAIC와 조직 정책 연동은 준비 상태를 투명하게 표시합니다.</p></div><FolderKanban aria-hidden="true" /></section>
  </div>;
}
