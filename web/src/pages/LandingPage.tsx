import { BarChart3, ClipboardCheck, FlaskConical, Gauge, LockKeyhole, ShieldCheck } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { authenticate } from "../auth";

const capabilities = [
  { icon: Gauge, title: "통계적 공정관리(SPC)·공정능력", description: "관리도 신호와 규격 충족성을 함께 진단합니다." },
  { icon: BarChart3, title: "측정시스템 분석(MSA)", description: "Gage R&R과 측정 신뢰성을 검토합니다." },
  { icon: FlaskConical, title: "실험계획법(DOE)·최적화", description: "요인 설계와 반응표면으로 개선 조건을 탐색합니다." },
  { icon: ClipboardCheck, title: "FMEA·DMAIC", description: "위험 조치와 개선 근거를 하나의 흐름으로 관리합니다." },
];

type LandingVariant = "A" | "B";
const LANDING_NEXT_VARIANT_KEY = "statpro-landing-next-variant";

function nextVariant(variant: LandingVariant): LandingVariant {
  return variant === "A" ? "B" : "A";
}

function readLandingVariant(): LandingVariant {
  return localStorage.getItem(LANDING_NEXT_VARIANT_KEY) === "B" ? "B" : "A";
}

export function LandingPage() {
  const navigate = useNavigate();
  const [variant] = useState<LandingVariant>(readLandingVariant);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    localStorage.setItem(LANDING_NEXT_VARIANT_KEY, nextVariant(variant));
  }, [variant]);

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!authenticate(username, password)) {
      setError("아이디 또는 비밀번호를 확인하세요.");
      return;
    }
    navigate("/home", { replace: true });
  }

  return (
    <main className={`landing-page landing-variant-${variant.toLowerCase()}`}>
      <section className="landing-story" aria-labelledby="landing-title">
        <div className="landing-brand"><span aria-hidden="true">S</span>StatPro</div>
        <p className="landing-kicker">{variant === "A" ? "STATISTICS · SIX SIGMA · TRACEABILITY" : "INHOUSE QUALITY INTELLIGENCE"}</p>
        <h1 id="landing-title">{variant === "A" ? <>현장 데이터가<br />개선 실행이 되는<br />순간.</> : <>통계 분석과<br />6 Sigma 실행을<br />한 화면에서.</>}</h1>
        <p className="landing-lead">제조 현장의 데이터와 개선 과제를 연결하는 <strong>Inhouse 통계 및 6 Sigma 품질관리 솔루션 패키지</strong>입니다. 분석 결과를 보고서와 실행 근거로 남기며, 팀이 같은 기준으로 판단하도록 돕습니다.</p>
        <ol className="landing-flow" aria-label="품질 개선 흐름"><li>데이터</li><li>분석</li><li>개선</li><li>관리</li></ol>
        <div className="landing-insights" aria-label="분석 기능 미리보기">
          <article className="landing-capability-card landing-capability-chart"><span>공정능력 / Assembly line 02</span><strong>Cpk 1.33</strong><em>규격 충족 상태 · 기준선 저장됨</em><div className="landing-chart" aria-hidden="true"><i /><i /><i /><i /><i /><i /><i /></div></article>
          <div className="landing-mini-stack"><article className="landing-capability-card"><span>측정시스템 분석</span><strong>GR&amp;R 8.7%</strong><em>측정 신뢰성 검토 완료</em></article><article className="landing-capability-card"><span>개선 프로젝트</span><strong>DMAIC 04</strong><em>근거 연결 · 보고서 준비</em></article></div>
        </div>
        <section className="landing-capabilities" aria-label="StatPro 핵심 기능">{capabilities.map(({ icon: Icon, title, description }) => <article key={title}><Icon aria-hidden="true" /><div><h2>{title}</h2><p>{description}</p></div></article>)}</section>
      </section>
      <aside className="landing-auth" aria-label="사내 계정 로그인">
        <form className="landing-auth-form" onSubmit={submit}>
          <div className="landing-brand"><span aria-hidden="true">S</span>StatPro</div>
          <h2>사내 계정 로그인</h2>
          <p>담당 프로젝트와 분석 이력을 이어서 확인하세요.</p>
          <label>아이디 (ID)<input value={username} onChange={(event) => setUsername(event.target.value)} autoComplete="username" placeholder="admin" aria-describedby={error ? "login-error" : undefined} autoFocus /></label>
          <label>비밀번호 (Password)<input value={password} onChange={(event) => setPassword(event.target.value)} type="password" autoComplete="current-password" placeholder="admin123" aria-describedby={error ? "login-error" : undefined} /></label>
          {error && <p className="landing-login-error" id="login-error" role="alert">{error}</p>}
          <button className="landing-login-button" type="submit">로그인</button>
          <div className="landing-demo-note"><ShieldCheck aria-hidden="true" /><div><strong>개발·테스트 계정</strong><span><code>admin</code> / <code>admin123</code>로 로그인할 수 있습니다.</span></div></div>
          <p className="landing-auth-foot"><LockKeyhole aria-hidden="true" /> 이 데모 인증 상태는 현재 브라우저 세션에만 보관됩니다.</p>
        </form>
      </aside>
    </main>
  );
}
