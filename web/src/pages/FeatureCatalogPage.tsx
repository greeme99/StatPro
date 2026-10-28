import { CheckCircle2, CircleDashed, ExternalLink, ShieldAlert } from "lucide-react";
import { Link, useParams } from "react-router-dom";

type Delivery = "구현됨" | "부분 구현" | "개발 예정" | "외부 정책 필요";
type Item = { name: string; detail: string; status: Delivery; to?: string };
type Catalog = { title: string; description: string; items: Item[] };

const catalogs: Record<string, Catalog> = {
  reports: {
    title: "결과 및 보고서",
    description: "분석 실행의 결과, 입력 근거, 경고와 내보내기 파일을 같은 기록에서 확인합니다.",
    items: [
      { name: "분석 실행 결과", detail: "저장된 분석 실행의 표, 차트, 진단과 근거를 확인합니다.", status: "구현됨", to: "/" },
      { name: "DOE 표준 보고서", detail: "HTML, JSON, CSV ZIP 내보내기를 제공합니다.", status: "구현됨", to: "/analyses/doe/full-factorial" },
      { name: "SPC 보고서 내보내기", detail: "현재 각 실행 결과에서 표와 근거를 확인할 수 있습니다.", status: "부분 구현", to: "/analyses/spc/attribute" },
      { name: "그래프 이미지·PDF·고객 양식", detail: "규제 또는 고객별 템플릿 요구를 분리해 지원할 예정입니다.", status: "개발 예정" },
    ],
  },
  tools: {
    title: "계산 및 도우미",
    description: "독립 계산도 분석 실행과 동일하게 입력, 가정, 결과 근거를 남기는 방식으로 확장합니다.",
    items: [
      { name: "공정능력 분석", detail: "정규 및 경험적 비정규 공정능력 분석을 제공합니다.", status: "구현됨", to: "/analyses/spc/attribute" },
      { name: "실험 실행 수·설계 선택", detail: "DOE 설계 화면에서 실행 수와 설계 조건을 확인합니다.", status: "구현됨", to: "/analyses/doe/full-factorial" },
      { name: "분석 선택 가이드", detail: "입력 데이터 특성과 업무 목적에 따라 방법을 안내할 예정입니다.", status: "개발 예정" },
    ],
  },
  help: {
    title: "도움말",
    description: "StatPro는 분석 근거, 가정, 제한사항을 결과와 함께 보존합니다.",
    items: [
      { name: "단계별 설정", detail: "DOE, SPC, FMEA 설정 화면에서 완료 조건과 검증 메시지를 제공합니다.", status: "구현됨", to: "/analyses/doe/full-factorial" },
      { name: "통계 방법·근거", detail: "각 분석 실행의 근거와 제한사항을 결과 화면에서 확인합니다.", status: "구현됨", to: "/" },
      { name: "기업 계정 연동·직무분리", detail: "조직의 IdP와 권한 정책이 제공될 때 연동 범위를 확정합니다.", status: "외부 정책 필요" },
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
            {item.to ? <Link className="text-link" to={item.to}>기능으로 이동 <ExternalLink aria-hidden="true" /></Link> : <p className="catalog-note">현재 분석을 실행할 수 없습니다. 제공 범위가 확정되면 이 메뉴에서 시작합니다.</p>}
          </article>;
        })}
      </section>
    </div>
  );
}
