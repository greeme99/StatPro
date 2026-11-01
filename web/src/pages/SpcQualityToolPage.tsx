import { ArrowLeft, ArrowRight, Database, Workflow } from "lucide-react";
import { Link, Navigate, useParams } from "react-router-dom";
import { spcTools } from "../spcCatalog";

export function SpcQualityToolPage() {
  const { toolId } = useParams();
  const tool = spcTools.find((item) => item.id === toolId);
  if (!tool) return <Navigate to="/spc" replace />;
  const Icon = tool.icon;

  return (
    <div className="page spc-tool-workspace" data-density="comfortable">
      <Link className="back-link" to="/spc"><ArrowLeft aria-hidden="true" /> SPC 작업공간</Link>
      <section className="spc-tool-hero"><span className="preview-icon"><Icon aria-hidden="true" /></span><div><span className="eyebrow">SPC QUALITY TOOL</span><h1>{tool.title} ({tool.english}) 작업공간</h1><p>{tool.purpose}</p></div></section>
      <section className="tool-workspace-panel"><header><h2>현장 적용 Workflow</h2><p>{tool.fieldUse}</p></header><ol className="tool-workspace-flow">{tool.workflow.map((step, index) => <li key={step}><span>{index + 1}</span><strong>{step}</strong></li>)}</ol></section>
      <section className="tool-next-actions"><article><Database aria-hidden="true" /><div><h2>작업표에서 데이터 준비</h2><p>분석 대상 열과 층별 변수를 정리하고 누락값·시간 순서를 확인합니다.</p><Link className="text-link" to="/data">작업표 및 데이터 열기 <ArrowRight aria-hidden="true" /></Link></div></article><article><Workflow aria-hidden="true" /><div><h2>후속 도구 연결</h2><p>원인과 우선순위를 확인한 뒤 시간 변동을 관리도에서 지속 감시합니다.</p><Link className="text-link" to="/spc/control-charts">관리도 작업공간 열기 <ArrowRight aria-hidden="true" /></Link></div></article></section>
    </div>
  );
}
