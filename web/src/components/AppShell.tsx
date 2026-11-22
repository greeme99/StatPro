import { useEffect, useRef, useState, type CSSProperties, type KeyboardEvent, type PointerEvent, type ReactNode } from "react";
import { Activity, ArrowLeft, ArrowRight, BarChart3, Bug, Calculator, Database, FileText, FileWarning, FlaskConical, Gauge, HelpCircle, Home, ListChecks, LogOut, Moon, PanelLeftClose, PanelLeftOpen, Sun } from "lucide-react";
import { Link, NavLink, useNavigate } from "react-router-dom";
import { signOut } from "../auth";
import { getHealth } from "../api";
import { CopilotPanel } from "./CopilotPanel";
import { FavoriteMenu } from "./FavoriteMenu";
import { ProjectContextMenu } from "./ProjectContextMenu";

const navigation = [
  { to: "/home", label: "홈 (Home)", icon: Home },
  { to: "/analyses", label: "분석 선택 (Analysis Selection)", icon: ListChecks },
  { to: "/data", label: "작업표 및 데이터 (Worksheet & Data)", icon: Database },
  { to: "/doe", label: "실험계획법 (DOE)", icon: FlaskConical },
  { to: "/spc", label: "통계적 공정관리 (SPC)", icon: BarChart3 },
  { to: "/fmea", label: "고장 형태 및 영향 분석 (FMEA)", icon: FileWarning },
  { to: "/quality", label: "품질 대시보드 (Quality Dashboard)", icon: Gauge },
  { to: "/defects", label: "결함 분석 (Defect Analysis)", icon: Bug },
  { to: "/catalog/reports", label: "결과 및 보고서 (Results & Reports)", icon: FileText },
  { to: "/catalog/tools", label: "계산 및 도우미 (Calculators & Helpers)", icon: Calculator },
];

const SIDEBAR_DEFAULT_WIDTH = 360;
const SIDEBAR_MIN_WIDTH = 260;
const SIDEBAR_MAX_WIDTH = 480;
const SIDEBAR_COLLAPSE_THRESHOLD = 180;
const ENGINE_HEALTH_RECHECK_MS = 10_000;

function WorkspaceNavigation() {
  const navigate = useNavigate();
  const canGoBack = typeof window !== "undefined" && Number(window.history.state?.idx) > 0;
  const goPrevious = () => {
    if (canGoBack) navigate(-1);
    else navigate("/home");
  };

  return <nav className="workspace-navigation" aria-label="화면 이동">
    <button className="workspace-navigation-button" type="button" onClick={goPrevious} title={canGoBack ? "이전 방문 화면으로 이동" : "분석 홈으로 이동"}>
      <ArrowLeft aria-hidden="true" /> 이전
    </button>
    <Link className="workspace-navigation-home" to="/home"><Home aria-hidden="true" /> 분석 홈</Link>
    <button className="workspace-navigation-button" type="button" onClick={() => navigate(1)} title="다음 방문 화면으로 이동">
      다음 <ArrowRight aria-hidden="true" />
    </button>
  </nav>;
}

export function AppShell({ children }: { children: ReactNode }) {
  const navigate = useNavigate();
  const resizeStart = useRef<{ x: number; width: number } | null>(null);
  const [engine, setEngine] = useState<{ state: "loading" | "ready" | "error"; version: string }>({ state: "loading", version: "0.6.0" });
  const [theme, setTheme] = useState<"light" | "dark">(() => {
    const stored = localStorage.getItem("statpro-theme");
    return stored === "dark" ? "dark" : "light";
  });
  const [sidebarCollapsed, setSidebarCollapsed] = useState(() => {
    const stored = localStorage.getItem("statpro-sidebar-collapsed");
    if (stored !== null) return stored === "true";
    return typeof window.matchMedia === "function" && window.matchMedia("(max-width: 1023px)").matches;
  });
  const [sidebarWidth, setSidebarWidth] = useState(() => {
    const stored = Number(localStorage.getItem("statpro-sidebar-width"));
    return Number.isFinite(stored) && stored >= SIDEBAR_MIN_WIDTH && stored <= SIDEBAR_MAX_WIDTH ? stored : SIDEBAR_DEFAULT_WIDTH;
  });
  const [isResizingSidebar, setIsResizingSidebar] = useState(false);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem("statpro-theme", theme);
  }, [theme]);

  useEffect(() => {
    localStorage.setItem("statpro-sidebar-collapsed", String(sidebarCollapsed));
  }, [sidebarCollapsed]);

  useEffect(() => {
    localStorage.setItem("statpro-sidebar-width", String(sidebarWidth));
  }, [sidebarWidth]);

  useEffect(() => {
    let active = true;
    let retryTimer: ReturnType<typeof setTimeout> | undefined;
    const checkEngine = () => {
      getHealth()
        .then((health) => {
          if (active) setEngine({ state: "ready", version: health.engine_version ?? "0.6.0" });
        })
        .catch(() => {
          if (active) setEngine((current) => ({ ...current, state: "error" }));
        })
        .finally(() => {
          if (active) retryTimer = setTimeout(checkEngine, ENGINE_HEALTH_RECHECK_MS);
        });
    };
    checkEngine();
    return () => {
      active = false;
      if (retryTimer !== undefined) clearTimeout(retryTimer);
    };
  }, []);

  function startSidebarResize(event: PointerEvent<HTMLButtonElement>) {
    event.preventDefault();
    resizeStart.current = { x: event.clientX, width: sidebarCollapsed ? SIDEBAR_MIN_WIDTH : sidebarWidth };
    if (typeof event.currentTarget.setPointerCapture === "function") event.currentTarget.setPointerCapture(event.pointerId);
    setIsResizingSidebar(true);
  }

  function resizeSidebar(event: PointerEvent<HTMLButtonElement>) {
    if (!resizeStart.current) return;
    const requestedWidth = resizeStart.current.width + event.clientX - resizeStart.current.x;
    if (requestedWidth <= SIDEBAR_COLLAPSE_THRESHOLD) {
      setSidebarCollapsed(true);
      return;
    }
    setSidebarCollapsed(false);
    setSidebarWidth(Math.min(SIDEBAR_MAX_WIDTH, Math.max(SIDEBAR_MIN_WIDTH, requestedWidth)));
  }

  function finishSidebarResize(event: PointerEvent<HTMLButtonElement>) {
    resizeStart.current = null;
    if (typeof event.currentTarget.hasPointerCapture === "function" && typeof event.currentTarget.releasePointerCapture === "function" && event.currentTarget.hasPointerCapture(event.pointerId)) event.currentTarget.releasePointerCapture(event.pointerId);
    setIsResizingSidebar(false);
  }

  function resizeSidebarWithKeyboard(event: KeyboardEvent<HTMLButtonElement>) {
    const step = 20;
    if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return;
    event.preventDefault();
    if (event.key === "Home" || (event.key === "ArrowLeft" && (sidebarCollapsed || sidebarWidth <= SIDEBAR_MIN_WIDTH))) {
      setSidebarCollapsed(true);
      return;
    }
    const nextWidth = event.key === "End"
      ? SIDEBAR_MAX_WIDTH
      : sidebarCollapsed
        ? SIDEBAR_MIN_WIDTH
        : Math.min(SIDEBAR_MAX_WIDTH, Math.max(SIDEBAR_MIN_WIDTH, sidebarWidth + (event.key === "ArrowRight" ? step : -step)));
    setSidebarCollapsed(false);
    setSidebarWidth(nextWidth);
  }

  return (
    <div className={`app-frame${sidebarCollapsed ? " is-sidebar-collapsed" : ""}${isResizingSidebar ? " is-sidebar-resizing" : ""}`} style={{ "--sidebar-current-width": `${sidebarWidth}px` } as CSSProperties}>
      <a className="skip-link" href="#main-content">본문 바로가기</a>
      <header className="app-header">
        <div className="brand-lockup" aria-label="StatPro 홈">
          <span className="brand-mark" aria-hidden="true"><Activity /></span>
          <span>StatPro</span>
          <span className="environment-badge">LOCAL</span>
        </div>
        <ProjectContextMenu />
        <div className="header-meta">
          <FavoriteMenu />
          <span className={`connection-state${engine.state === "error" ? " is-error" : ""}`}><span aria-hidden="true">●</span> {engine.state === "ready" ? "엔진 연결됨" : engine.state === "error" ? "엔진 연결 오류" : "엔진 확인 중"}</span>
          <button
            className="icon-button"
            type="button"
            aria-label={theme === "light" ? "다크 테마로 전환" : "라이트 테마로 전환"}
            onClick={() => setTheme(theme === "light" ? "dark" : "light")}
          >
            {theme === "light" ? <Moon /> : <Sun />}
          </button>
          <button className="icon-button" type="button" aria-label="도움말 열기" onClick={() => navigate("/catalog/help")}><HelpCircle /></button>
        </div>
      </header>
      <aside className={`sidebar${sidebarCollapsed ? " is-collapsed" : ""}`} aria-label="주 메뉴">
        <div className="sidebar-controls">
          <button
            className="sidebar-toggle"
            type="button"
            aria-label={sidebarCollapsed ? "사이드 메뉴 보이기" : "사이드 메뉴 감추기"}
            aria-expanded={!sidebarCollapsed}
            data-tooltip={sidebarCollapsed ? "메뉴 보이기" : undefined}
            onClick={() => setSidebarCollapsed((collapsed) => !collapsed)}
          >
            {sidebarCollapsed ? <PanelLeftOpen aria-hidden="true" /> : <PanelLeftClose aria-hidden="true" />}
            <span>메뉴 감추기</span>
          </button>
        </div>
        <nav>
          {navigation.map(({ to, label, icon: Icon }) => (
            <NavLink
              className={({ isActive }) => `nav-item${isActive ? " is-active" : ""}`}
              to={to}
              key={to}
              aria-label={label}
              data-tooltip={label}
            >
              <Icon aria-hidden="true" /><span className="nav-label">{label}</span>
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-foot">
          <div className="sidebar-engine"><span className="utility-label">ENGINE</span><strong>{engine.version}</strong></div>
          <button className="nav-item nav-logout" type="button" onClick={() => { signOut(); navigate("/", { replace: true }); }} aria-label="로그아웃" data-tooltip="로그아웃">
            <LogOut aria-hidden="true" /><span className="nav-label">로그아웃</span>
          </button>
        </div>
        <button className="sidebar-resize-handle" type="button" role="slider" aria-label="사이드 메뉴 너비 조절" aria-orientation="horizontal" aria-valuemin={0} aria-valuemax={SIDEBAR_MAX_WIDTH} aria-valuenow={sidebarCollapsed ? 0 : sidebarWidth} aria-valuetext={sidebarCollapsed ? "접힘" : `${sidebarWidth}px`} onKeyDown={resizeSidebarWithKeyboard} onPointerDown={startSidebarResize} onPointerMove={resizeSidebar} onPointerUp={finishSidebarResize} onPointerCancel={finishSidebarResize} />
      </aside>
      <main id="main-content" className="main-content"><WorkspaceNavigation />{children}</main>
      <CopilotPanel />
      <div className="viewport-warning" role="alert">
        <Activity aria-hidden="true" />
        <h1>더 넓은 화면이 필요합니다</h1>
        <p>StatPro는 정확한 표와 차트 판독을 위해 768px 이상의 화면을 지원합니다.</p>
      </div>
    </div>
  );
}
