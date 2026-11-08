import { FormEvent, useEffect, useState } from "react";
import { ArrowRight, BadgeDollarSign, CheckCircle2, ClipboardCheck } from "lucide-react";
import { Link } from "react-router-dom";
import { getDmaicCostBenefitAnalysis, listDmaicProjects, saveDmaicCostBenefitAnalysis } from "../api";
import { persistActiveProject, selectActiveProject } from "../projectContext";
import type { StoredDmaicCostBenefitAnalysis, StoredDmaicProject } from "../types";

type Item = { name: string; amount: string; recurrence: "one_time" | "monthly" | "annual" };
const blankItem = (): Item => ({ name: "", amount: "", recurrence: "one_time" });
const asLines = (value: string) => value.split("\n").map((item) => item.trim()).filter(Boolean);
const asItem = (item: Item) => ({ name: item.name, amount: Number(item.amount), recurrence: item.recurrence });
const formatMoney = (value: number, currency: string) => new Intl.NumberFormat("ko-KR", { style: "currency", currency, maximumFractionDigits: 0 }).format(value);

export function DmaicCostBenefitWorkspacePage() {
  const [projects, setProjects] = useState<StoredDmaicProject[]>([]);
  const [selected, setSelected] = useState<StoredDmaicProject | null>(null);
  const [currency, setCurrency] = useState("KRW");
  const [months, setMonths] = useState("12");
  const [costs, setCosts] = useState<Item[]>([blankItem()]);
  const [benefits, setBenefits] = useState<Item[]>([blankItem()]);
  const [assumptions, setAssumptions] = useState("");
  const [actor, setActor] = useState("local-operator");
  const [saved, setSaved] = useState<StoredDmaicCostBenefitAnalysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => { void (async () => {
    try { const page = await listDmaicProjects(); setProjects(page.items); setSelected(selectActiveProject(page.items)); }
    catch (cause) { setError(cause instanceof Error ? cause.message : "개선 프로젝트를 불러오지 못했습니다."); }
    finally { setLoading(false); }
  })(); }, []);

  const updateItem = (kind: "cost" | "benefit", index: number, key: keyof Item, value: string) => {
    const setter = kind === "cost" ? setCosts : setBenefits;
    setter((items) => items.map((item, itemIndex) => itemIndex === index ? { ...item, [key]: value } : item));
  };
  const addItem = (kind: "cost" | "benefit") => (kind === "cost" ? setCosts : setBenefits)((items) => [...items, blankItem()]);
  const removeItem = (kind: "cost" | "benefit", index: number) => (kind === "cost" ? setCosts : setBenefits)((items) => items.length === 1 ? items : items.filter((_, itemIndex) => itemIndex !== index));

  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); if (!selected) return;
    try {
      const project = await saveDmaicCostBenefitAnalysis(selected.project_id, {
        expected_storage_version: selected.storage_version, currency, analysis_months: Number(months),
        costs: costs.map(asItem), benefits: benefits.map(asItem), assumptions: asLines(assumptions), actor, occurred_at: new Date().toISOString(),
      });
      const reference = project.project.cost_benefit_analysis;
      if (!reference) throw new Error("저장된 비용-편익 분석 참조를 확인하지 못했습니다.");
      const document = await getDmaicCostBenefitAnalysis(project.project_id, reference.document_id);
      setSaved(document); setSelected(project); persistActiveProject(project);
      setProjects((items) => items.map((item) => item.project_id === project.project_id ? project : item)); setError("");
    } catch (cause) { setError(cause instanceof Error ? cause.message : "비용-편익 분석을 저장하지 못했습니다."); }
  }

  const itemForm = (kind: "cost" | "benefit", title: string, items: Item[]) => <section className="dmaic-evidence-section"><header><BadgeDollarSign aria-hidden="true" /><div><h3>{title}</h3><p>금액과 발생 주기를 입력합니다. 회계 실현·할인율·세금 판정은 포함하지 않습니다.</p></div></header><div className="check-sheet-form">{items.map((item, index) => <div className="check-sheet-wide" key={`${kind}-${index}`}><label>항목명<input value={item.name} onChange={(event) => updateItem(kind, index, "name", event.target.value)} required /></label><label>금액<input inputMode="decimal" min="0" type="number" value={item.amount} onChange={(event) => updateItem(kind, index, "amount", event.target.value)} required /></label><label>발생 주기<select value={item.recurrence} onChange={(event) => updateItem(kind, index, "recurrence", event.target.value)}><option value="one_time">일회성</option><option value="monthly">월간</option><option value="annual">연간</option></select></label><button className="button button-secondary" type="button" onClick={() => removeItem(kind, index)} disabled={items.length === 1}>항목 제거</button></div>)}</div><button className="button button-secondary" type="button" onClick={() => addItem(kind)}>항목 추가</button></section>;

  return <div className="page dmaic-measure-workspace" data-density="comfortable">
    <nav className="breadcrumb" aria-label="경로"><Link to="/home">홈 (Home)</Link><span>/</span><Link to="/home/dmaic">개선 프로젝트 (DMAIC)</Link><span>/</span><span>비용-편익 분석</span></nav>
    <section className="spc-tool-hero"><span className="preview-icon"><BadgeDollarSign aria-hidden="true" /></span><div><span className="eyebrow">IMPROVE · SCENARIO · DECISION</span><h1>비용-편익 분석 (Cost-Benefit Analysis)</h1><p>선정한 개선안의 비용·편익 시나리오를 투명한 가정과 함께 프로젝트 개정으로 보존합니다.</p></div></section>
    {loading ? <p className="method-note">로컬 개선 프로젝트를 불러오는 중입니다.</p> : <><section className="tool-workspace-panel"><header><h2>1. 개선 프로젝트 선택</h2><p>프로젝트의 개선안·파일럿·근본원인 문서가 저장 시점의 근거로 연결됩니다.</p></header><label>프로젝트<select value={selected?.project_id ?? ""} onChange={(event) => { const project = projects.find((item) => item.project_id === event.target.value) ?? null; setSelected(project); persistActiveProject(project); setSaved(null); }}><option value="">프로젝트를 선택하세요</option>{projects.map((item) => <option key={item.project_id} value={item.project_id}>{item.project.title} ({item.project_id})</option>)}</select></label></section>
      {selected ? <form className="tool-workspace-panel dmaic-measure-form" onSubmit={save}><header><h2>2. 시나리오 입력</h2><p><strong>{selected.project.title}</strong> · 현재 프로젝트 개정 {selected.project.revision}</p></header><div className="check-sheet-form"><label>통화 코드<input value={currency} maxLength={8} onChange={(event) => setCurrency(event.target.value.toUpperCase())} required /></label><label>분석 기간(개월)<input type="number" min="1" max="600" value={months} onChange={(event) => setMonths(event.target.value)} required /></label><label className="check-sheet-wide">시나리오 가정 (한 줄에 하나)<textarea value={assumptions} onChange={(event) => setAssumptions(event.target.value)} placeholder="예: 월간 절감액은 분석 기간 동안 유지됩니다." required /></label><label>저장 담당자<input value={actor} onChange={(event) => setActor(event.target.value)} required /></label></div>{itemForm("cost", "비용", costs)}{itemForm("benefit", "편익", benefits)}<p className="method-note"><strong>한계:</strong> 이 결과는 입력값을 합산한 의사결정 시나리오이며, 재무 실현·투자 승인·할인 현금흐름을 자동 판정하지 않습니다.</p><button className="primary-button" type="submit">비용-편익 분석 저장 <ArrowRight aria-hidden="true" /></button></form> : <section className="tool-workspace-panel"><p className="method-note">비용-편익 분석을 시작하려면 먼저 개선 프로젝트를 선택하세요.</p></section>}
      {saved && <section className="dmaic-save-confirmation" aria-live="polite"><CheckCircle2 aria-hidden="true" /><div><h2>비용-편익 시나리오를 새 개정으로 저장했습니다</h2><p>순편익 {formatMoney(saved.cost_benefit_analysis.summary.net_benefit, saved.cost_benefit_analysis.currency)} · ROI {saved.cost_benefit_analysis.summary.roi_percent === null ? "해당 없음" : `${saved.cost_benefit_analysis.summary.roi_percent.toFixed(1)}%`} · 근거 문서 {saved.cost_benefit_analysis.source_documents.length}건</p></div></section>}
      <section className="tool-next-actions"><article><ClipboardCheck aria-hidden="true" /><div><h2>개선안 선정 확인</h2><p>시나리오의 편익 가정이 개선안 선정 근거와 일치하는지 검토합니다.</p><Link className="text-link" to="/home/dmaic/improve/solution-selection">개선안 선정 열기 <ArrowRight aria-hidden="true" /></Link></div></article></section></>}
    {error && <p className="error" role="alert">{error}</p>}
  </div>;
}
