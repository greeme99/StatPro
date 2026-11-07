import { CheckCircle2, CircleDashed, ExternalLink, ShieldAlert } from "lucide-react";
import { Link, useParams } from "react-router-dom";

type Delivery = "구현됨" | "개발 예정" | "외부 정책 필요";
type Item = { name: string; detail: string; status: Delivery; to?: string };
type Catalog = { title: string; description: string; items: Item[] };

const catalogs: Record<string, Catalog> = {
  reports: {
    title: "결과 및 보고서",
    description: "분석 실행의 결과, 입력 근거, 경고와 내보내기 파일을 같은 기록에서 확인합니다.",
    items: [
      { name: "분석 실행 결과", detail: "저장된 분석 실행의 표, 차트, 진단과 근거를 확인합니다.", status: "구현됨", to: "/" },
      { name: "DOE 표준 보고서", detail: "HTML, JSON, CSV ZIP 내보내기를 제공합니다.", status: "구현됨", to: "/analyses/doe/full-factorial" },
      { name: "SPC 보고서 내보내기", detail: "I-MR·Xbar-R·Xbar-S는 PDF 인쇄·Excel·PNG·SVG를, 나머지는 JSON·CSV를 제공합니다.", status: "구현됨", to: "/spc" },
      { name: "DOE 그래프·검토 양식", detail: "지원 Plot의 SVG와 표 CSV·JSON을 묶어 내보내고 표준·고객·규제 검토용 HTML 양식을 선택합니다.", status: "구현됨", to: "/doe" },
      { name: "PDF·조직 승인 양식", detail: "PDF 파일 생성, 조직별 필수 항목 검증과 전자서명 양식은 별도 확장 범위입니다.", status: "개발 예정" },
    ],
  },
  tools: {
    title: "계산 및 도우미",
    description: "독립 계산도 분석 실행과 동일하게 입력, 가정, 결과 근거를 남기는 방식으로 확장합니다.",
    items: [
      { name: "공정능력 분석", detail: "정규 및 경험적 비정규 공정능력 분석을 실행하고 능력지수·불량 PPM·가정을 함께 확인합니다.", status: "구현됨", to: "/analyses/capability" },
      { name: "교차 Gage R&R", detail: "균형 교차 측정 설계에서 반복성·재현성, 분산성분, NDC와 ANOVA를 확인합니다.", status: "구현됨", to: "/analyses/msa/gage-rr" },
      { name: "실험 실행 수·설계 선택", detail: "DOE 설계 화면에서 실행 수와 설계 조건을 확인합니다.", status: "구현됨", to: "/analyses/doe/full-factorial" },
      { name: "SPC·DOE 선택 가이드", detail: "데이터 유형과 업무 목적에 따라 관리도와 실험설계를 선택하고 해당 작업공간으로 이동합니다.", status: "구현됨", to: "/spc" },
      { name: "통합 분석 추천", detail: "모든 통계 모듈을 아우르는 자동 방법 추천과 검정력 기반 비교는 후속 범위입니다.", status: "개발 예정" },
    ],
  },
  help: {
    title: "도움말",
    description: "StatPro는 분석 근거, 가정, 제한사항을 결과와 함께 보존합니다.",
    items: [
      { name: "단계별 설정", detail: "DOE, SPC, FMEA 설정 화면에서 완료 조건과 검증 메시지를 제공합니다.", status: "구현됨", to: "/analyses/doe/full-factorial" },
      { name: "통계 방법·근거", detail: "각 분석 실행의 근거와 제한사항을 결과 화면에서 확인합니다.", status: "구현됨", to: "/" },
      { name: "기업 IdP 승인·직무분리", detail: "검증된 Entra OIDC claims와 조직 권한 마스터를 교차검증하고 MFA·활성 계정·독립 승인을 실패 폐쇄합니다.", status: "구현됨", to: "/fmea" },
      { name: "운영 tenant·계정 수명주기", detail: "운영 tenant 등록, 비밀 관리, 조건부 접근과 SCIM 비활성화 연동은 조직 관리자 설정과 실환경 검증이 필요합니다.", status: "외부 정책 필요" },
    ],
  },
};

const iconFor = (status: Delivery) => status === "구현됨" ? CheckCircle2 : status === "외부 정책 필요" ? ShieldAlert : CircleDashed;

export function FeatureCatalogPage() {
  const { section = "help" } = useParams();
  const catalog = catalogs[section] ?? catalogs.help;
  return (
    <div className="page" data-density="comfortable">
      <section className="page-heading"><div><span className="eyebrow">STATPRO CATALOG</span><h1>{catalog.title}</h1><p>{catalog.description}</p></div></section>
      <section className="feature-catalog" aria-label={`${catalog.title} 기능 목록`}>
        {catalog.items.map((item) => {
          const Icon = iconFor(item.status);
          return <article className="feature-item" key={item.name}>
            <header><Icon aria-hidden="true" /><span className={`delivery-status status-${item.status.replaceAll(" ", "-")}`}>{item.status}</span></header>
            <h2>{item.name}</h2><p>{item.detail}</p>
            {item.to ? <Link className="text-link" to={item.to} aria-label={`${item.name} 기능으로 이동`}>기능으로 이동 <ExternalLink aria-hidden="true" /></Link> : <p className="catalog-note">현재 분석을 실행할 수 없습니다. 제공 범위가 확정되면 이 메뉴에서 시작합니다.</p>}
          </article>;
        })}
      </section>
    </div>
  );
}
