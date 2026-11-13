import { ArrowRight, CheckCircle2, CircleDashed, ExternalLink, ShieldAlert } from "lucide-react";
import { Link } from "react-router-dom";

type Delivery = "구현됨" | "개발 예정" | "외부 정책 필요";
type Goal = { title: string; progress: number; delivery: Delivery; available: string; remaining: string; to?: string };

const goals: Goal[] = [
  { title: "통계적 공정관리(SPC)·공정능력", progress: 92, delivery: "구현됨", available: "계량형·계수형·희귀사건·EWMA·CUSUM 관리도와 정규/경험적 비정규 공정능력 분석을 실행하고, 모든 결과를 식별값·근거 포함 인쇄·JSON·CSV·Excel 호환 표로 출력합니다. EWMA·CUSUM·계수형·희귀사건 및 공정능력은 저장된 ResultBundle 기반 PNG·SVG를 생성합니다.", remaining: "생성형 PDF 파일과 통계적 분포 적합도 검증은 후속 범위입니다.", to: "/spc" },
  { title: "실험계획법(DOE)", progress: 93, delivery: "구현됨", available: "완전·일부요인, Plackett–Burman, 중심합성, Box–Behnken, 반응표면과 다중응답 최적화, HTML·PDF·XLSX·CSV·SVG 보고서를 실행합니다.", remaining: "고급 split-plot·공변량 설계와 조직별 전자승인 양식은 후속 범위입니다.", to: "/doe" },
  { title: "측정시스템 분석(MSA)", progress: 86, delivery: "구현됨", available: "연속 측정은 교차·중첩 Gage R&R과 편의·선형성, 표준 판정 검사는 Attribute Agreement로 실행합니다. 균형 Gage R&R은 ANOVA 분모·F·p 판정과 반복성 분산의 정확 95% 신뢰구간을 실행 근거와 함께 보존합니다.", remaining: "다른 분산성분 신뢰구간, REML·비균형 설계와 측정계획 연계는 아직 시작할 수 없습니다.", to: "/analyses/msa/gage-rr-nested" },
  { title: "FMEA·관리계획 인수인계", progress: 80, delivery: "외부 정책 필요", available: "PFMEA 개정·조치·재평가·승인과 SPC/MSA 실행 근거를 Control Plan에 연결합니다.", remaining: "운영 tenant, SCIM 계정 수명주기, 조건부 접근과 조직별 전자서명 정책은 조직 제공 정책과 실환경 검증이 필요합니다.", to: "/fmea" },
  { title: "DMAIC 개선 프로젝트", progress: 86, delivery: "구현됨", available: "정의·측정·분석·개선·관리 문서와 분석 실행 근거를 프로젝트 단위로 연결합니다. 개선 단계는 개선안·파일럿·비용편익 시나리오·실행계획을 불변 개정으로 저장하고, 실행계획에는 단계별 담당·목표일·완료기준과 소통·품질·교육 계획을 보존합니다.", remaining: "프로젝트 문서의 Word/PDF 출력, 조직별 승인 양식, 실시간 데이터 연동과 실제 롤아웃·교육 이수의 외부 검증은 후속 범위입니다.", to: "/home/dmaic" },
  { title: "AI Copilot 안내", progress: 82, delivery: "외부 정책 필요", available: "Rulebase 기반으로 현상·데이터 구조에 맞는 도구, 메뉴 경로, 체크리스트, 업무절차를 안내합니다. 미적중 질의는 EXAONE 2.5로 전달하고 실패 시 목적별 Ollama 로컬 모델로 대체합니다.", remaining: "EXAONE API 키·전송 정책·운영 감사 기준을 설정한 뒤에만 외부 모델을 활성화할 수 있습니다. 로컬 Ollama 모델 설치·운영 정책도 별도 확인이 필요합니다." },
];

const iconFor = (delivery: Delivery) => delivery === "구현됨" ? CheckCircle2 : delivery === "외부 정책 필요" ? ShieldAlert : CircleDashed;

export function DeliveryProgressPage() {
  const overall = Math.round(goals.reduce((total, goal) => total + goal.progress, 0) / goals.length);
  return <div className="page delivery-progress" data-density="comfortable">
    <nav className="breadcrumb" aria-label="경로"><Link to="/home">홈 (Home)</Link><span aria-hidden="true">/</span><span>개발 목표 현황</span></nav>
    <section className="preview-hero"><div><span className="eyebrow">RELEASE DELIVERY TRACKER</span><h1>현장 분석 흐름의 목표 대비 진척도</h1><p>로컬에서 사용자가 실제로 시작·입력·분석·결과 확인을 할 수 있는 기능만 완료로 계산합니다. 외부 정책이나 미구현 확장은 완료율에 포함하지 않습니다.</p></div><div className="delivery-overall" aria-label="현재 릴리스 목표 가중 진척도"><strong>{overall}%</strong><span>가중 진척도</span><progress value={overall} max="100" aria-label="현재 릴리스 목표 가중 진척도">{overall}%</progress><small>6개 목표 영역의 현재 제공 범위를 동등 가중으로 산정</small></div></section>
    <section className="delivery-rubric panel" aria-labelledby="rubric-title"><header className="panel-heading"><div><span className="eyebrow">MEASUREMENT RULE</span><h2 id="rubric-title">진척도 산정 기준</h2></div></header><ol className="delivery-rubric-list"><li><strong>실행 가능</strong><span>메뉴 경로, 입력 검증, 로컬 분석 실행, 결과 조회가 모두 있어야 합니다.</span></li><li><strong>증적 연결</strong><span>ResultBundle, 경고·가정·근거와 후속 작업공간 연결 여부를 반영합니다.</span></li><li><strong>제외 원칙</strong><span>외부 IdP·SCIM·MES/FDC/APC/R2R, 고객 정책, 미구현 출력 형식은 완료로 계산하지 않습니다.</span></li></ol></section>
    <section className="delivery-goal-grid" aria-label="목표 영역별 진척도">{goals.map((goal) => { const Icon = iconFor(goal.delivery); return <article className="delivery-goal-card" key={goal.title}><header><span className="preview-icon"><Icon aria-hidden="true" /></span><span className={"delivery-status status-" + goal.delivery.replaceAll(" ", "-")}>{goal.delivery}</span></header><h2>{goal.title}</h2><div className="delivery-goal-progress"><strong>{goal.progress}%</strong><progress value={goal.progress} max="100" aria-label={goal.title + " 목표 대비 진척도"}>{goal.progress}%</progress></div><dl><div><dt>현재 제공</dt><dd>{goal.available}</dd></div><div><dt>남은 범위</dt><dd>{goal.remaining}</dd></div></dl>{goal.to ? <Link className="text-link" to={goal.to} aria-label={goal.title + " 작업공간 열기"}>현재 작업공간 열기 <ArrowRight aria-hidden="true" /></Link> : <p className="catalog-note"><ExternalLink aria-hidden="true" /> 운영 정책 확정 후 생성형 AI 보완을 연결합니다.</p>}</article>; })}</section>
    <section className="panel delivery-next" aria-labelledby="next-title"><header className="panel-heading"><div><span className="eyebrow">NEXT DELIVERY</span><h2 id="next-title">다음 개발 우선순위</h2></div></header><ol><li><strong>출력 계약 확장</strong><span>SPC·공정능력·MSA 결과의 형식별 출력 범위와 재현 식별값 보존을 일관화합니다.</span></li><li><strong>MSA 추론 확장</strong><span>신뢰구간·유의성 검정, REML과 비균형 설계는 통계적 가정과 검증 범위를 명시한 뒤 추가합니다.</span></li><li><strong>운영 연계 준비</strong><span>EXAONE과 Ollama 연결, 조직 IdP·SCIM·전자서명은 키·모델·정책·감사 계약이 제공된 범위에서만 활성화합니다.</span></li></ol></section>
  </div>;
}
