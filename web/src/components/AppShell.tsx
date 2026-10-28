import { useEffect, useState, type ReactNode } from "react";
import { Activity, BarChart3, Calculator, Database, FileText, FileWarning, FlaskConical, HelpCircle, Home, Moon, Sun } from "lucide-react";
import { NavLink } from "react-router-dom";
import { getHealth } from "../api";

const navigation = [
  { to: "/", label: "홈", icon: Home },
  { to: "/data", label: "작업표 및 데이터", icon: Database },
  { to: "/analyses/doe/full-factorial", label: "실험계획법(DOE)", icon: FlaskConical },
  { to: "/analyses/spc/attribute", label: "통계적 공정관리(SPC)", icon: BarChart3 },
  { to: "/fmea", label: "고장 형태 및 영향 분석(FMEA)", icon: FileWarning },
  { to: "/catalog/reports", label: "결과 및 보고서", icon: FileText },
  { to: "/catalog/tools", label: "계산 및 도우미", icon: Calculator },
  { to: "/catalog/help", label: "도움말", icon: HelpCircle },
];

export function AppShell({ children }: { children: ReactNode }) {
  const [engine, setEngine] = useState<{ state: "loading" | "ready" | "error"; version: string }>({ state: "loading", version: "0.6.0" });
  const [theme, setTheme] = useState<"light" | "dark">(() => {
    const stored = localStorage.getItem("statpro-theme");
    return stored === "dark" ? "dark" : "light";
  });

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem("statpro-theme", theme);
  }, [theme]);

  useEffect(() => {
    let active = true;
    getHealth()
      .then((health) => { if (active) setEngine({ state: "ready", version: health.engine_version ?? "0.6.0" }); })
      .catch(() => { if (active) setEngine((current) => ({ ...current, state: "error" })); });
    return () => { active = false; };
  }, []);

  return (
    <div className="app-frame">
      <a className="skip-link" href="#main-content">본문 바로가기</a>
      <header className="app-header">
        <div className="brand-lockup" aria-label="StatPro 홈">
          <span className="brand-mark" aria-hidden="true"><Activity /></span>
          <span>StatPro</span>
          <span className="environment-badge">LOCAL</span>
        </div>
        <div className="header-meta">
          <span className={`connection-state${engine.state === "error" ? " is-error" : ""}`}><span aria-hidden="true">●</span> {engine.state === "ready" ? "엔진 연결됨" : engine.state === "error" ? "엔진 연결 오류" : "엔진 확인 중"}</span>
          <button
            className="icon-button"
            type="button"
            aria-label={theme === "light" ? "다크 테마로 전환" : "라이트 테마로 전환"}
            onClick={() => setTheme(theme === "light" ? "dark" : "light")}
          >
            {theme === "light" ? <Moon /> : <Sun />}
          </button>
        </div>
      </header>
      <aside className="sidebar" aria-label="주 메뉴">
        <nav>
          {navigation.map(({ to, label, icon: Icon }) => (
            <NavLink
              className={({ isActive }) => `nav-item${isActive ? " is-active" : ""}`}
              to={to}
              key={to}
            >
              <Icon aria-hidden="true" /><span>{label}</span>
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-foot">
          <span className="utility-label">ENGINE</span>
          <strong>{engine.version}</strong>
        </div>
      </aside>
      <main id="main-content" className="main-content">{children}</main>
      <div className="viewport-warning" role="alert">
        <Activity aria-hidden="true" />
        <h1>더 넓은 화면이 필요합니다</h1>
        <p>StatPro는 정확한 표와 차트 판독을 위해 768px 이상의 화면을 지원합니다.</p>
      </div>
    </div>
  );
}
