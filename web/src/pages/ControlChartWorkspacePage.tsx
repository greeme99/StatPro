import { ArrowRight, CheckCircle2, Gauge, HelpCircle } from "lucide-react";
import { Link, useSearchParams } from "react-router-dom";
import { controlChartGroups } from "../spcCatalog";

const signalGuide = [
  "관리한계(UCL/LCL)를 벗어난 점",
  "중심선 한쪽에 7점 이상 연속된 런",
  "3점 중 2점이 2σ~3σ 영역에 나타나는 패턴",
  "지속 상승·하락 추세 또는 주기적 변동",
];

export function ControlChartWorkspacePage() {
  const [params, setParams] = useSearchParams();
  const type = params.get("type") === "attributes" ? "attributes" : "variables";
  const selected = controlChartGroups.find((group) => group.id === type) ?? controlChartGroups[0];

  return (
    <div className="page control-chart-workspace" data-density="comfortable">
      <nav className="breadcrumb" aria-label="경로"><Link to="/home">홈 (Home)</Link><Link to="/spc">통계적 공정관리 (SPC)</Link><span>관리도 (Control Chart)</span></nav>
      <section className="page-heading"><div><span className="eyebrow">SPC / CONTROL CHARTS</span><h1>관리도(Control Chart) 작업공간</h1><p>데이터 유형과 표본 구조를 먼저 구분한 뒤 목적에 맞는 관리도를 선택합니다.</p></div></section>
      <section className="control-type-section" aria-labelledby="chart-type-title">
        <header><span className="step-index">01</span><div><h2 id="chart-type-title">데이터 분류 선택</h2><p>연속 측정값은 계량형, 세어서 얻는 부적합·결점 데이터는 계수형입니다.</p></div></header>
        <div className="control-type-selector" role="tablist" aria-label="관리도 데이터 분류">
          {controlChartGroups.map((group) => <button type="button" role="tab" aria-selected={group.id === type} className={group.id === type ? "is-selected" : ""} onClick={() => setParams({ type: group.id })} key={group.id}><Gauge aria-hidden="true" /><span><strong>{group.title} ({group.english})</strong><small>{group.description}</small></span></button>)}
        </div>
      </section>
      <section className="control-chart-selection" aria-labelledby="chart-selection-title">
        <header><span className="step-index">02</span><div><h2 id="chart-selection-title">{selected.title} 관리도 선택</h2><p>{selected.selectionRule}</p></div></header>
        <div className="control-chart-grid">
          {selected.charts.map((chart) => <article className="control-chart-card" key={chart.title}><span className="utility-label">{selected.english}</span><h3>{chart.title}</h3><p>{chart.description}</p><dl><div><dt>적합한 경우</dt><dd>{chart.whenToUse}</dd></div></dl><Link className="text-link" to={chart.route}>{chart.title} 설정 시작 <ArrowRight aria-hidden="true" /></Link></article>)}
        </div>
      </section>
      <section className="spc-guide-grid" aria-label="관리도 선택 및 기능 가이드">
        <article className="spc-guide-panel"><header><HelpCircle aria-hidden="true" /><h2>선택 가이드</h2></header><ol><li><strong>값을 측정합니까, 셉니까?</strong><p>측정값이면 계량형, 부적합·결점 수면 계수형을 선택합니다.</p></li><li><strong>부분군을 만들 수 있습니까?</strong><p>가능하면 Xbar-R/S, 개별 측정이면 I-MR을 고려합니다.</p></li><li><strong>표본 또는 검사 기회가 일정합니까?</strong><p>부적합품은 p/np, 결점은 c/u에서 고정 여부로 구분합니다.</p></li><li><strong>희귀하거나 작은 이동입니까?</strong><p>희귀사건은 G/T, 작은 지속 이동은 EWMA 또는 CUSUM을 사용합니다.</p></li></ol></article>
        <article className="spc-guide-panel"><header><CheckCircle2 aria-hidden="true" /><h2>기능·해석 가이드</h2></header><p><strong>CL</strong>은 공정 중심, <strong>UCL/LCL</strong>은 규격 한계가 아니라 공정 변동으로 계산한 관리한계입니다.</p><ul>{signalGuide.map((signal) => <li key={signal}>{signal}</li>)}</ul><aside><strong>판단 원칙</strong><p>신호가 없으면 공정이 규격을 만족한다는 뜻이 아니라 통계적으로 안정적이라는 뜻입니다. 신호가 있으면 원인·조치·재발 방지 근거를 함께 기록합니다.</p></aside></article>
      </section>
    </div>
  );
}
