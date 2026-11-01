import { ArrowRight, BookOpenCheck, Workflow } from "lucide-react";
import { Link } from "react-router-dom";
import { spcTools } from "../spcCatalog";

const fieldWorkflow = [
  { title: "데이터 수집", detail: "체크 시트로 공정·결함 정보를 같은 기준으로 기록합니다.", tools: "체크 시트" },
  { title: "분포·층별 확인", detail: "분포를 보고 설비·작업자·로트별 차이를 분리합니다.", tools: "히스토그램 · 계층화" },
  { title: "관계·원인 탐색", detail: "변수 관계와 잠재 원인을 구조화해 검증 대상을 좁힙니다.", tools: "산점도 · 특성요인도" },
  { title: "우선순위 결정", detail: "빈도와 손실이 큰 핵심 소수에 개선 자원을 집중합니다.", tools: "파레토 차트" },
  { title: "공정 감시", detail: "시간 순서의 이상 신호를 확인하고 조치 후 안정성을 추적합니다.", tools: "관리도" },
];

export function SpcWorkspacePage() {
  return (
    <div className="page spc-workspace" data-density="comfortable">
      <nav className="breadcrumb" aria-label="경로"><Link to="/home">홈 (Home)</Link><span>통계적 공정관리 (SPC)</span></nav>
      <section className="spc-workspace-hero">
        <div><span className="eyebrow">현장 품질 Workflow</span><h1>통계적 공정관리(SPC) 작업공간</h1><p>품질 문제를 기록하고, 분포와 원인을 확인한 뒤, 우선순위와 관리도로 이어지는 7대 품질 도구 흐름입니다.</p></div>
        <Link className="primary-link" to="/spc/control-charts"><Workflow aria-hidden="true" /> 관리도 작업공간 열기 <ArrowRight aria-hidden="true" /></Link>
      </section>
      <section className="spc-workflow-panel" aria-labelledby="spc-workflow-title">
        <header><span className="eyebrow">Workspace → Workflow</span><h2 id="spc-workflow-title">현장 문제를 다음 판단 단계로 연결합니다</h2><p>현재 문제의 위치에서 시작하고, 필요한 도구만 선택해 사용할 수 있습니다.</p></header>
        <ol className="spc-process-rail">
          {fieldWorkflow.map((step, index) => <li key={step.title}><span>{index + 1}</span><div><strong>{step.title}</strong><p>{step.detail}</p><small>{step.tools}</small></div></li>)}
        </ol>
      </section>
      <section aria-labelledby="spc-tools-title">
        <header className="preview-section-heading"><span className="eyebrow">핵심 품질 도구 7가지</span><h2 id="spc-tools-title">목적에 맞는 도구 작업공간을 선택합니다</h2><p>각 카드에서 적용 시점과 업무 흐름을 확인한 뒤 해당 작업공간으로 이동합니다.</p></header>
        <div className="spc-tool-grid">
          {spcTools.map((tool) => {
            const Icon = tool.icon;
            return <article className="spc-tool-card" key={tool.id}><header><span className="preview-icon"><Icon aria-hidden="true" /></span><span className="utility-label">{tool.english}</span></header><h3>{tool.title} ({tool.english})</h3><p>{tool.purpose}</p><dl><div><dt>사용 시점</dt><dd>{tool.fieldUse}</dd></div></dl><ol aria-label={`${tool.title} 업무 흐름`}>{tool.workflow.map((step) => <li key={step}>{step}</li>)}</ol><Link className="text-link" to={tool.route}>{tool.title} 작업공간 열기 <ArrowRight aria-hidden="true" /></Link></article>;
          })}
        </div>
      </section>
      <aside className="spc-evidence-note"><BookOpenCheck aria-hidden="true" /><div><strong>도구 선택 원칙</strong><p>하나의 도구로 결론을 내리지 않습니다. 수집 기준, 분포, 층별 차이, 원인 가설, 우선순위와 시간 변동을 연결해 판단 근거를 보존합니다.</p></div></aside>
    </div>
  );
}
