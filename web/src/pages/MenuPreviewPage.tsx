import { ArrowRight, BarChart3, CheckCircle2, ClipboardList, FileWarning, FlaskConical, FolderKanban, LayoutDashboard, LockKeyhole, Wrench } from "lucide-react";
import { Link } from "react-router-dom";

type Status = "구현됨" | "개발 예정" | "외부 정책 필요";
type MenuItem = { title: string; description: string; status: Status; to?: string };

const workspaces: MenuItem[] = [
  { title: "실험계획법(DOE) 작업공간", description: "설계, 실행표, 분석, 최적화, 결과 및 보고서를 하나의 흐름으로 관리합니다.", status: "구현됨", to: "/doe" },
  { title: "통계적 공정관리(SPC) 작업공간", description: "관리도 종류 선택부터 데이터 입력, 분석 실행, 결과 및 보고서까지 연결합니다.", status: "구현됨", to: "/analyses/spc/attribute" },
  { title: "고장 형태 및 영향 분석(FMEA) 작업공간", description: "PFMEA, 관리계획서, 조치 및 승인 이력을 추적합니다.", status: "구현됨", to: "/fmea" },
];

const dmaic: MenuItem[] = [
  { title: "정의", description: "프로젝트 헌장, VOC, SIPOC, 문제 정의 및 이해관계자를 기록합니다.", status: "개발 예정" },
  { title: "측정", description: "데이터 수집 계획과 MSA·SPC·공정능력 실행 근거를 연결합니다.", status: "개발 예정" },
  { title: "분석", description: "근본원인, 특성요인도, 5 Why, 파레토와 검증 실행을 추적합니다.", status: "개발 예정" },
  { title: "개선", description: "기존 실험계획법(DOE) 작업공간과 개선 의사결정을 연결합니다.", status: "개발 예정", to: "/doe" },
  { title: "관리", description: "FMEA 관리계획서, SPC·공정능력 실행, 반응 계획과 검토 주기를 연결합니다.", status: "개발 예정", to: "/fmea" },
];

const statusClass: Record<Status, string> = { "구현됨": "is-implemented", "개발 예정": "is-planned", "외부 정책 필요": "is-policy" };
function DeliveryBadge({ status }: { status: Status }) { return <span className={`preview-status ${statusClass[status]}`}>{status}</span>; }

function WorkspaceCard({ item, icon: Icon }: { item: MenuItem; icon: typeof FlaskConical }) {
  return <article className="preview-card">
    <header><span className="preview-icon"><Icon aria-hidden="true" /></span><DeliveryBadge status={item.status} /></header>
    <h3>{item.title}</h3><p>{item.description}</p>
    {item.to ? <Link className="text-link" to={item.to}>{item.status === "개발 예정" ? "기존 작업공간 열기" : "작업공간 열기"} <ArrowRight aria-hidden="true" /></Link> : <p className="preview-note">설계 범위와 데이터 계약을 확정한 뒤 사용할 수 있습니다.</p>}
  </article>;
}

export function MenuPreviewPage() {
  return <div className="page menu-preview" data-density="comfortable">
    <nav className="breadcrumb" aria-label="경로"><Link to="/">홈</Link><span aria-hidden="true">/</span><span>메뉴 및 UI 미리보기</span></nav>
    <section className="preview-hero">
      <div><span className="eyebrow">INFORMATION ARCHITECTURE PREVIEW</span><h1>StatPro 메뉴와 작업공간 구조</h1><p>제조·품질 분석은 전문 작업공간에서 수행하고, DMAIC는 그 실행 근거를 연결하는 프로젝트 허브로 구성합니다.</p></div>
      <div className="preview-legend" aria-label="상태 범례"><DeliveryBadge status="구현됨" /><DeliveryBadge status="개발 예정" /><DeliveryBadge status="외부 정책 필요" /></div>
    </section>
    <section className="preview-shell" aria-label="재구성된 메뉴 트리">
      <aside className="preview-tree"><h2>전체 메뉴</h2><ul>
        <li><LayoutDashboard aria-hidden="true" />홈</li><li><FolderKanban aria-hidden="true" /><span>프로젝트 및 작업공간</span></li>
        <li className="nested"><ClipboardList aria-hidden="true" /><span>개선 프로젝트(DMAIC)</span><DeliveryBadge status="개발 예정" /></li>
        <li className="nested"><FlaskConical aria-hidden="true" /><span>실험계획법(DOE)</span><DeliveryBadge status="구현됨" /></li>
        <li className="nested"><BarChart3 aria-hidden="true" /><span>통계적 공정관리(SPC)</span><DeliveryBadge status="구현됨" /></li>
        <li className="nested"><FileWarning aria-hidden="true" /><span>고장 형태 및 영향 분석(FMEA)</span><DeliveryBadge status="구현됨" /></li>
        <li><Wrench aria-hidden="true" />작업표 및 데이터</li><li><ClipboardList aria-hidden="true" />결과 및 보고서</li>
        <li><LockKeyhole aria-hidden="true" /><span>조직 정책 연동</span><DeliveryBadge status="외부 정책 필요" /></li>
      </ul></aside>
      <div className="preview-main"><header className="preview-section-heading"><span className="eyebrow">CORE WORKSPACES</span><h2>현재 사용할 수 있는 전문 작업공간</h2><p>분석 흐름은 모두 `설정 → 데이터 → 분석 → 결과 → 보고서` 순서를 따릅니다.</p></header>
        <div className="preview-grid"><WorkspaceCard item={workspaces[0]} icon={FlaskConical} /><WorkspaceCard item={workspaces[1]} icon={BarChart3} /><WorkspaceCard item={workspaces[2]} icon={FileWarning} /></div>
      </div>
    </section>
    <section className="preview-dmaic" aria-labelledby="dmaic-title"><header className="preview-section-heading"><span className="eyebrow">IMPROVEMENT PROJECT</span><h2 id="dmaic-title">개선 프로젝트(DMAIC) — 개발 예정</h2><p>DMAIC는 새 통계 엔진의 사본이 아니라, 프로젝트 단계와 기존 분석 실행·FMEA 연구를 참조로 연결하는 허브입니다.</p></header>
      <ol className="dmaic-rail" aria-label="DMAIC 단계">{dmaic.map((item, index) => <li key={item.title}><span>{index + 1}</span><strong>{item.title}</strong></li>)}</ol>
      <div className="preview-grid preview-grid-dmaic">{dmaic.map((item) => <WorkspaceCard key={item.title} item={item} icon={ClipboardList} />)}</div>
    </section>
    <section className="preview-contract" aria-labelledby="ownership-title"><CheckCircle2 aria-hidden="true" /><div><h2 id="ownership-title">데이터와 결과의 소유 경계</h2><p>DOE·SPC 결과는 불변 분석 실행(Analysis Run), FMEA 관리계획서는 FMEA 연구가 소유합니다. DMAIC는 ID·ETag·입력 다이제스트를 참조로만 보관합니다.</p></div></section>
  </div>;
}
