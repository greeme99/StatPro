import { useEffect, useRef, useState, type FormEvent, type KeyboardEvent, type PointerEvent as ReactPointerEvent } from "react";
import { Bot, ChevronRight, Database, ExternalLink, FolderKanban, ListChecks, Mic, Plus, RotateCcw, Search, Send, X } from "lucide-react";
import { Link, useLocation } from "react-router-dom";
import { createCopilotRule, getCopilotGuidance, getRun, listCopilotRules, listDmaicProjects, type CopilotRule } from "../api";
import { guideCopilotQuestion, type CopilotAction } from "../copilotGuidance";

type CopilotMessage = {
  id: number;
  role: "assistant" | "user";
  text: string;
  action?: CopilotAction;
  provider?: string;
  sources?: Array<{ title: string; reference: string }>;
  guidanceMode?: "rulebase" | "llm_fallback" | "manual_guidance" | "unmatched";
  recommendedTool?: string;
  menuPath?: string[];
  checklist?: string[];
  workflowSteps?: string[];
  fallbackSteps?: Array<{ stage: string; status: "answered" | "unmatched" | "failed" | "unavailable" | "skipped"; detail: string }>;
  question?: string;
};
type CopilotEvidence = {
  kind: "run" | "project";
  title: string;
  identifier: string;
  revision: string;
  detail: string;
  href: string;
  answerContext: string;
};
type WorkflowSession = {
  messageId: number;
  stepIndex: number;
};
type RuleProposal = {
  messageId: number;
  situation: string;
  answer: string;
  keywords: string;
  recommendedTool: string;
  menuPath: string[];
  checklist: string[];
  workflowSteps: string[];
};
type ModelPreference = "auto" | "rulebase" | "exaone" | "codex";

const commandStarters = [
  { label: "사용법", text: "현재 작업공간의 사용법과 시작 순서를 안내해줘." },
  { label: "검사 조건", text: "이 분석을 실행하기 전에 확인할 검사 조건과 데이터 조건을 알려줘." },
  { label: "Workflow", text: "내 업무 상황에 맞는 단계별 Workflow와 완료 기준을 만들어줘." },
  { label: "메뉴 찾기", text: "이 문제를 해결할 작업공간과 메뉴 경로를 알려줘." },
  { label: "분석 방법", text: "목표와 데이터 구조에 맞는 분석 방법을 추천하고 작업공간을 열어줘." },
] as const;

function conversationContext(messages: CopilotMessage[]) {
  const turns = messages.filter((message) => message.role === "user" || message.workflowSteps?.length).slice(-6)
    .map((message) => `${message.role === "user" ? "사용자" : "AI Assistant"}: ${message.text}`)
    .join("\n");
  return turns.length > 1200 ? turns.slice(-1200) : turns;
}

function guidanceContext(evidence: CopilotEvidence | null, messages: CopilotMessage[]) {
  const parts = [evidence?.answerContext, conversationContext(messages)].filter(Boolean);
  const combined = parts.join("\n대화 문맥: ");
  return combined.length > 1800 ? combined.slice(-1800) : combined || undefined;
}

const workspaceContext = (pathname: string) => {
  if (pathname.startsWith("/analyses/spc") || pathname.startsWith("/spc") || pathname.startsWith("/runs")) {
    return {
      name: "통계적 공정관리 (SPC)",
      suggestions: ["이 관리도는 언제 사용하나요?", "관리한계 설정값을 설명해줘", "이상 신호가 나오면 무엇을 해야 하나요?"],
    };
  }
  if (pathname.startsWith("/analyses/doe") || pathname.startsWith("/doe")) {
    return {
      name: "실험계획법 (DOE)",
      suggestions: ["설계 유형을 어떻게 선택하나요?", "반복·블록·중심점을 설명해줘", "분석 결과의 다음 절차는 무엇인가요?"],
    };
  }
  if (pathname.startsWith("/fmea")) {
    return {
      name: "고장 형태 및 영향 분석 (FMEA)",
      suggestions: ["AIAG/VDA 7단계를 설명해줘", "조치 우선순위는 어떻게 판단하나요?", "관리계획과 SPC 근거를 연결하는 방법은?"],
    };
  }
  if (pathname.startsWith("/home/dmaic")) {
    return {
      name: "개선 프로젝트 (DMAIC)",
      suggestions: ["현재 단계의 완료 기준은 무엇인가요?", "다음 작업공간을 추천해줘", "분석 근거를 프로젝트에 연결하는 방법은?"],
    };
  }
  if (pathname.startsWith("/data")) {
    return {
      name: "작업표 및 데이터 (Worksheet & Data)",
      suggestions: ["분석용 데이터 형식을 알려줘", "결측값은 어떻게 처리하나요?", "데이터 개정과 분석 실행의 관계는?"],
    };
  }
  return {
    name: "홈 (Home)",
    suggestions: ["현장 문제에 맞는 작업공간을 추천해줘", "DOE, SPC, FMEA의 차이는?", "DMAIC 프로젝트는 어디서 시작하나요?"],
  };
};

export function CopilotPanel() {
  const location = useLocation();
  const context = workspaceContext(location.pathname);
  const [open, setOpen] = useState(() => localStorage.getItem("statpro-copilot-open") === "true");
  const [question, setQuestion] = useState("");
  const [modelPreferenceSetting, setModelPreferenceSetting] = useState<ModelPreference>(() => {
    const saved = localStorage.getItem("statpro-copilot-model-preference");
    return saved === "rulebase" || saved === "exaone" || saved === "codex" ? saved : "auto";
  });
  const [commandMenuOpen, setCommandMenuOpen] = useState(false);
  const [showCases, setShowCases] = useState(false);
  const [selectedCaseId, setSelectedCaseId] = useState<string | null>(null);
  const [caseQuery, setCaseQuery] = useState("");
  const [evidence, setEvidence] = useState<CopilotEvidence | null>(null);
  const [evidenceLoading, setEvidenceLoading] = useState(false);
  const [answerLoading, setAnswerLoading] = useState(false);
  const [catalogRules, setCatalogRules] = useState<CopilotRule[]>([]);
  const [catalogLoading, setCatalogLoading] = useState(false);
  const [ruleDraft, setRuleDraft] = useState({ situation: "", keywords: "", source: "직접 작성", content: "" });
  const [ruleSaving, setRuleSaving] = useState(false);
  const [ruleEditorOpen, setRuleEditorOpen] = useState(false);
  const [ruleProposal, setRuleProposal] = useState<RuleProposal | null>(null);
  const [proposalSaving, setProposalSaving] = useState(false);
  const [ruleProposalStatus, setRuleProposalStatus] = useState("");
  const [messages, setMessages] = useState<CopilotMessage[]>([]);
  const [workflowSession, setWorkflowSession] = useState<WorkflowSession | null>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const panelRef = useRef<HTMLElement>(null);
  const [panelSize, setPanelSize] = useState<{ width: number; height: number } | null>(null);
  const defaultSize = useRef<{ width: number; height: number } | null>(null);
  const resizeStart = useRef<{ edge: "left" | "bottom"; x: number; y: number; width: number; height: number } | null>(null);

  const startResize = (edge: "left" | "bottom", event: ReactPointerEvent<HTMLButtonElement>) => {
    if (event.button !== 0 || !panelRef.current) return;
    const bounds = panelRef.current.getBoundingClientRect();
    defaultSize.current ??= { width: bounds.width, height: bounds.height };
    resizeStart.current = { edge, x: event.clientX, y: event.clientY, width: bounds.width, height: bounds.height };
    event.currentTarget.setPointerCapture(event.pointerId);
    event.preventDefault();
  };
  const moveResize = (event: ReactPointerEvent<HTMLButtonElement>) => {
    const start = resizeStart.current;
    const minimum = defaultSize.current;
    if (!start || !minimum) return;
    const sidebar = parseFloat(getComputedStyle(document.documentElement).getPropertyValue("--sidebar-compact-width")) || 0;
    const header = parseFloat(getComputedStyle(document.documentElement).getPropertyValue("--header-height")) || 0;
    setPanelSize((current) => ({
      width: start.edge === "left" ? Math.min(window.innerWidth - sidebar, Math.max(minimum.width, start.width + start.x - event.clientX)) : current?.width ?? start.width,
      height: start.edge === "bottom" ? Math.min(window.innerHeight - header, Math.max(minimum.height, start.height + event.clientY - start.y)) : current?.height ?? start.height,
    }));
  };
  const stopResize = () => { resizeStart.current = null; };
  const resizeWithKeyboard = (edge: "left" | "bottom", key: string) => {
    const direction = edge === "left" ? key === "ArrowLeft" ? 1 : key === "ArrowRight" ? -1 : 0 : key === "ArrowDown" ? 1 : key === "ArrowUp" ? -1 : 0;
    if (!direction || !panelRef.current) return false;
    const bounds = panelRef.current.getBoundingClientRect();
    defaultSize.current ??= { width: bounds.width, height: bounds.height };
    const sidebar = parseFloat(getComputedStyle(document.documentElement).getPropertyValue("--sidebar-compact-width")) || 0;
    const header = parseFloat(getComputedStyle(document.documentElement).getPropertyValue("--header-height")) || 0;
    const step = parseFloat(getComputedStyle(document.documentElement).getPropertyValue("--space-6")) || 24;
    setPanelSize({
      width: edge === "left" ? Math.min(window.innerWidth - sidebar, Math.max(defaultSize.current.width, bounds.width + direction * step)) : bounds.width,
      height: edge === "bottom" ? Math.min(window.innerHeight - header, Math.max(defaultSize.current.height, bounds.height + direction * step)) : bounds.height,
    });
    return true;
  };

  useEffect(() => {
    localStorage.setItem("statpro-copilot-open", String(open));
    if (open) window.requestAnimationFrame(() => inputRef.current?.focus());
    else setShowCases(false);
  }, [open]);

  useEffect(() => {
    localStorage.setItem("statpro-copilot-model-preference", modelPreferenceSetting);
  }, [modelPreferenceSetting]);

  useEffect(() => {
    let active = true;
    setEvidence(null);
    if (!open) return () => { active = false; };

    const runMatch = location.pathname.match(/^\/runs\/([^/]+)$/);
    if (runMatch) {
      setEvidenceLoading(true);
      getRun(decodeURIComponent(runMatch[1]))
        .then((stored) => {
          if (!active) return;
          const warningCount = stored.result.warnings.length;
          const assumptionCount = stored.result.assumptions.length;
          setEvidence({
            kind: "run",
            title: stored.result.analysis_type,
            identifier: stored.run_id,
            revision: `Storage v${stored.storage_version}`,
            detail: `엔진 ${stored.result.engine_version} · 가정 ${assumptionCount}개 · 경고 ${warningCount}개`,
            href: `/runs/${encodeURIComponent(stored.run_id)}`,
            answerContext: `실행 ${stored.run_id}, ${stored.result.analysis_type}, 엔진 ${stored.result.engine_version}, 경고 ${warningCount}개, 입력 digest ${stored.result.input_digest.slice(0, 12)}…`,
          });
        })
        .catch(() => undefined)
        .finally(() => { if (active) setEvidenceLoading(false); });
      return () => { active = false; };
    }

    if (location.pathname.startsWith("/home/dmaic")) {
      setEvidenceLoading(true);
      listDmaicProjects(20)
        .then((page) => {
          if (!active || page.items.length === 0) return;
          const preferredId = localStorage.getItem("statpro-active-project-id");
          const stored = page.items.find((item) => item.project_id === preferredId) ?? page.items[0];
          const completed = [stored.project.charter, stored.project.measurement_plan, stored.project.root_cause_analysis, stored.project.solution_selection, stored.project.pilot_plan, stored.project.control_handoff].filter(Boolean).length;
          localStorage.setItem("statpro-active-project-id", stored.project_id);
          setEvidence({
            kind: "project",
            title: stored.project.title,
            identifier: stored.project_id,
            revision: `Revision ${stored.project.revision}`,
            detail: `${stored.project.status} · 핵심 산출물 ${completed}/6`,
            href: "/home/dmaic/define",
            answerContext: `프로젝트 ${stored.project_id} (${stored.project.title}), 개정 ${stored.project.revision}, 상태 ${stored.project.status}, 핵심 산출물 ${completed}/6`,
          });
        })
        .catch(() => undefined)
        .finally(() => { if (active) setEvidenceLoading(false); });
    }
    return () => { active = false; };
  }, [location.pathname, open]);

  useEffect(() => {
    if (!open) return;
    setCatalogLoading(true);
    listCopilotRules({ limit: 200 }).then(setCatalogRules).catch(() => setCatalogRules([])).finally(() => setCatalogLoading(false));
  }, [open]);

  const ask = async (value: string) => {
    const text = value.trim();
    if (!text || answerLoading) return;
    setShowCases(false);
    const messageId = Date.now();
    setMessages((current) => [...current, { id: messageId, role: "user", text }]);
    setQuestion("");
    setAnswerLoading(true);
    const modelPreference = /(?:^|\s)\/?model\s+(rulebase|exaone|codex)\b/i.exec(text)?.[1]?.toLowerCase()
      ?? (/(?:\bexaone\b|엑사원)/i.test(text) ? "exaone" : /(?:\bcodex\b|\bsdk\b|코덱스|에스디케이)/i.test(text) ? "codex" : modelPreferenceSetting);
    try {
      const guidance = await getCopilotGuidance({
        question: text,
        pathname: location.pathname,
        workspace: context.name,
        evidence_context: guidanceContext(evidence, messages),
        model_preference: modelPreference as "auto" | "rulebase" | "exaone" | "codex",
      });
      const assistantMessage: CopilotMessage = {
        id: messageId + 1,
        role: "assistant",
        text: guidance.answer,
        action: guidance.action ?? undefined,
        provider: guidance.provider,
        sources: guidance.sources,
        guidanceMode: guidance.guidance_mode,
        recommendedTool: guidance.recommended_tool ?? undefined,
        menuPath: guidance.menu_path,
        checklist: guidance.checklist,
        workflowSteps: guidance.workflow_steps,
        fallbackSteps: guidance.fallback_steps,
        question: text,
      };
      setMessages((current) => [...current, assistantMessage]);
      if (guidance.workflow_steps.length > 0) setWorkflowSession({ messageId: assistantMessage.id, stepIndex: 0 });
    } catch {
      const guidance = guideCopilotQuestion({
        question: text,
        contextName: context.name,
        pathname: location.pathname,
        evidenceContext: guidanceContext(evidence, messages),
      });
      const assistantMessage: CopilotMessage = {
        id: messageId + 1,
        role: "assistant",
        text: guidance.text,
        action: guidance.action,
        provider: "브라우저 로컬 폴백",
        guidanceMode: guidance.guidanceMode,
        recommendedTool: guidance.recommendedTool,
        menuPath: guidance.menuPath,
        checklist: guidance.checklist,
        workflowSteps: guidance.workflowSteps,
        question: text,
      };
      setMessages((current) => [...current, assistantMessage]);
      if (guidance.workflowSteps?.length) setWorkflowSession({ messageId: assistantMessage.id, stepIndex: 0 });
    } finally {
      setAnswerLoading(false);
    }
  };

  const submit = (event: FormEvent) => {
    event.preventDefault();
    void ask(question);
  };
  const submitOnEnter = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      void ask(question);
    }
  };

  const selectCommandStarter = (text: string) => {
    setQuestion(text);
    setCommandMenuOpen(false);
    window.requestAnimationFrame(() => inputRef.current?.focus());
  };
  const saveUserRule = async () => {
    const keywords = ruleDraft.keywords.split(",").map((value) => value.trim()).filter(Boolean);
    if (!ruleDraft.situation.trim() || keywords.length === 0 || ruleSaving) return;
    setRuleSaving(true);
    try {
      const rule = await createCopilotRule({ rule_id: `user-rule-${Date.now()}`, domain: "사용자 보완", situation: ruleDraft.situation.trim(), keywords, recommended_tool: "사용자 정의 분석 가이드", menu_path: ["홈 (Home)", "AI Assistant", "분석 Case"], checklist: ["원본 문서와 현장 적용 범위를 검토합니다."], workflow_steps: ["정의 확인", "데이터 기준 검토", "현장 적용 전 검증"], source_reference: ruleDraft.source });
      setCatalogRules((current) => Array.isArray(current) ? [...current, rule] : [rule]);
      setRuleDraft({ situation: "", keywords: "", source: "직접 작성", content: "" });
    } finally { setRuleSaving(false); }
  };
  const openRuleProposal = (message: CopilotMessage) => {
    setRuleProposalStatus("");
    setRuleProposal({
      messageId: message.id,
      situation: message.question ?? message.text,
      answer: message.text,
      keywords: "",
      recommendedTool: message.recommendedTool ?? "AI Assistant 승인 가이드",
      menuPath: message.menuPath?.length ? message.menuPath : ["홈 (Home)", "AI Assistant"],
      checklist: message.checklist?.length ? message.checklist : ["현장 적용 전 근거와 데이터 조건을 검토합니다."],
      workflowSteps: message.workflowSteps?.length ? message.workflowSteps : ["요청 확인", "현장 적용 검토", "분석 실행"],
    });
  };
  const approveRuleProposal = async () => {
    if (!ruleProposal || proposalSaving) return;
    const keywords = ruleProposal.keywords.split(",").map((value) => value.trim()).filter(Boolean);
    if (!ruleProposal.situation.trim() || !ruleProposal.answer.trim() || keywords.length === 0) return;
    setProposalSaving(true);
    try {
      const rule = await createCopilotRule({
        rule_id: `user-rule-${Date.now()}`,
        domain: "AI Assistant 승인 Rule",
        situation: ruleProposal.situation.trim(),
        answer: ruleProposal.answer.trim(),
        keywords,
        recommended_tool: ruleProposal.recommendedTool,
        menu_path: ruleProposal.menuPath,
        checklist: ruleProposal.checklist,
        workflow_steps: ruleProposal.workflowSteps,
        source_reference: "AI Assistant 대화 승인",
      });
      setCatalogRules((current) => Array.isArray(current) ? [...current, rule] : [rule]);
      setRuleProposal(null);
      setRuleProposalStatus("승인한 대화 결과를 로컬 Rulebase에 저장했습니다.");
    } finally { setProposalSaving(false); }
  };

  const latestWorkflow = [...messages].reverse().find((message) => message.role === "assistant" && message.workflowSteps && message.workflowSteps.length > 0);
  const normalizedCaseQuery = caseQuery.trim().toLocaleLowerCase();
  const visibleCases = normalizedCaseQuery
    ? catalogRules.filter((rule) => [rule.domain, rule.situation, rule.recommended_tool, ...(rule.keywords ?? []), ...rule.menu_path, ...rule.checklist, ...rule.workflow_steps].join(" ").toLocaleLowerCase().includes(normalizedCaseQuery))
    : catalogRules;
  const activeWorkflow = workflowSession
    ? messages.find((message) => message.id === workflowSession.messageId && message.workflowSteps && message.workflowSteps.length > 0) ?? latestWorkflow
    : latestWorkflow;
  const activeStepIndex = activeWorkflow && workflowSession?.messageId === activeWorkflow.id ? workflowSession.stepIndex : 0;
  const activeStep = activeWorkflow?.workflowSteps?.[activeStepIndex];
  const finishActiveStep = () => {
    if (!activeWorkflow?.workflowSteps || !workflowSession || workflowSession.messageId !== activeWorkflow.id) return;
    setWorkflowSession((current) => current && current.messageId === activeWorkflow.id
      ? { ...current, stepIndex: Math.min(current.stepIndex + 1, activeWorkflow.workflowSteps!.length) }
      : current);
  };
  const resetConversation = () => {
    if (answerLoading) return;
    setMessages([]);
    setWorkflowSession(null);
    setQuestion("");
    setCommandMenuOpen(false);
    setShowCases(false);
    setSelectedCaseId(null);
    setCaseQuery("");
    setRuleProposal(null);
    setRuleProposalStatus("");
    window.requestAnimationFrame(() => inputRef.current?.focus());
  };

  return (
    <>
      <button className={`copilot-launcher${open ? " is-open" : ""}`} style={open && panelSize ? { insetInlineEnd: panelSize.width } : undefined} type="button" aria-label={open ? "AI Assistant 감추기" : "AI Assistant 보이기"} aria-expanded={open} aria-controls="copilot-panel" onClick={() => setOpen((current) => !current)}>
        <Bot aria-hidden="true" /><span>AI Assistant</span><ChevronRight aria-hidden="true" />
      </button>
      <aside ref={panelRef} id="copilot-panel" className={`copilot-panel${open ? " is-open" : ""}`} style={panelSize ? { width: panelSize.width, height: panelSize.height } : undefined} aria-label="AI Assistant" aria-hidden={!open}>
        <button className="copilot-resize-handle is-left" type="button" aria-label="AI Assistant 너비 조절" onPointerDown={(event) => startResize("left", event)} onPointerMove={moveResize} onPointerUp={stopResize} onPointerCancel={stopResize} onKeyDown={(event) => { if (resizeWithKeyboard("left", event.key)) event.preventDefault(); }} />
        <button className="copilot-resize-handle is-bottom" type="button" aria-label="AI Assistant 높이 조절" onPointerDown={(event) => startResize("bottom", event)} onPointerMove={moveResize} onPointerUp={stopResize} onPointerCancel={stopResize} onKeyDown={(event) => { if (resizeWithKeyboard("bottom", event.key)) event.preventDefault(); }} />
        <header className="copilot-header">
          <div><h2>AI Assistant</h2></div>
          <div className="copilot-header-actions"><button className="button-secondary" type="button" aria-expanded={showCases} onClick={() => setShowCases((current) => !current)}>{showCases ? "대화 보기" : "분석 Case 보기"}</button><button className="icon-button" type="button" aria-label="대화 초기화" disabled={answerLoading} onClick={resetConversation}><RotateCcw aria-hidden="true" /></button><button className="icon-button" type="button" aria-label="AI Assistant 닫기" onClick={() => setOpen(false)}><X aria-hidden="true" /></button></div>
        </header>
        <section className="copilot-route-summary" aria-label="AI 응답 경로 설정"><div><strong>응답 경로</strong><p>기본 순서는 Rulebase → EXAONE → Codex SDK입니다.</p></div><label><span className="sr-only">AI 응답 경로</span><select aria-label="AI 응답 경로" value={modelPreferenceSetting} onChange={(event) => setModelPreferenceSetting(event.target.value as ModelPreference)} disabled={answerLoading}><option value="auto">모델 선택</option><option value="rulebase">Rulebase만</option><option value="exaone">EXAONE만</option><option value="codex">Codex SDK만</option></select></label></section>
        <div className="copilot-content">
        {showCases ? <section className="copilot-catalog" aria-label="등록된 분석 Case">
          <header><div><strong>등록된 분석 Case</strong><small>{visibleCases.length}건 · 검토된 Rulebase</small></div><button type="button" className="button-secondary" aria-expanded={ruleEditorOpen} onClick={() => setRuleEditorOpen((current) => !current)}>{ruleEditorOpen ? "Rule 추가 닫기" : "Rule 추가·보완"}</button></header>
          {ruleEditorOpen && <section className="copilot-rule-editor" aria-label="사용자 Rule 추가"><h3>Rule 추가·보완</h3><p>TXT, MD, CSV 파일을 읽어 초안을 만들고, 키워드와 상황을 검토한 뒤 저장합니다.</p><input type="file" accept=".txt,.md,.csv,text/plain,text/markdown,text/csv" onChange={async (event) => { const file = event.target.files?.[0]; if (!file) return; const content = await file.text(); setRuleDraft((current) => ({ ...current, source: file.name, content, situation: current.situation || file.name.replace(/\.[^.]+$/, "") })); }} /><input value={ruleDraft.situation} onChange={(event) => setRuleDraft((current) => ({ ...current, situation: event.target.value }))} placeholder="Rule 상황·설명" /><input value={ruleDraft.keywords} onChange={(event) => setRuleDraft((current) => ({ ...current, keywords: event.target.value }))} placeholder="매칭 키워드 (쉼표로 구분)" /><textarea value={ruleDraft.content} onChange={(event) => setRuleDraft((current) => ({ ...current, content: event.target.value }))} placeholder="문서 내용 또는 Rule 근거를 붙여넣으세요" rows={4} /><button type="button" className="button-primary" disabled={!ruleDraft.situation.trim() || !ruleDraft.keywords.trim() || ruleSaving} onClick={() => void saveUserRule()}>{ruleSaving ? "저장 중" : "검토 후 Rule 저장"}</button></section>}
          <label className="copilot-case-search"><Search aria-hidden="true" /><input type="search" value={caseQuery} onChange={(event) => setCaseQuery(event.target.value)} placeholder="문제·도구·메뉴·절차 찾기" aria-label="분석 Case 찾기" /></label>
          {catalogLoading ? <p className="copilot-catalog-status">등록된 사례를 불러오고 있습니다.</p> : visibleCases.length > 0 ? <div>{visibleCases.map((rule) => <article className="copilot-catalog-item" key={rule.rule_id}><button type="button" aria-expanded={selectedCaseId === rule.rule_id} onClick={() => setSelectedCaseId((current) => current === rule.rule_id ? null : rule.rule_id)}><strong>{rule.situation}</strong><small>{rule.domain} · {rule.recommended_tool}</small></button>{selectedCaseId === rule.rule_id && <div className="copilot-case-detail"><strong>문제점</strong><p>{rule.situation}</p><strong>분석절차</strong><ol>{rule.workflow_steps.map((item) => <li key={item}>{item}</li>)}</ol><strong>메뉴패스</strong><p>{rule.menu_path.join(" › ")}</p><strong>고려사항</strong><ul>{rule.checklist.map((item) => <li key={item}>{item}</li>)}</ul><Link className="copilot-catalog-action" to={rule.action.href}>{rule.action.label}<ChevronRight aria-hidden="true" /></Link><button type="button" onClick={() => void ask(`${rule.situation} 분석절차와 고려사항을 자세히 안내해줘.`)}>이 Case로 대화하기</button></div>}</article>)}</div> : <p className="copilot-catalog-status">{caseQuery.trim() ? "검색 결과가 없습니다. 다른 단어로 찾거나 아래 대화 입력창에 자연어로 문의하세요." : "등록된 Case를 찾지 못했습니다. 아래 대화 입력창에 현상·목표·데이터 구조를 자연어로 알려주시면 분석절차와 메뉴 경로를 안내합니다."}</p>}
        </section> : <>
        {messages.length > 0 && (evidenceLoading || evidence) && <section className="copilot-evidence" aria-label="현재 근거">
          <header><span>{evidence?.kind === "project" ? <FolderKanban aria-hidden="true" /> : <Database aria-hidden="true" />}</span><div><strong>현재 근거</strong><small>저장된 실행·프로젝트 계약에서 읽음</small></div></header>
          {evidenceLoading && !evidence ? <p>근거를 확인하고 있습니다.</p> : evidence && <><div><strong>{evidence.title}</strong><span>{evidence.identifier}</span><small>{evidence.revision} · {evidence.detail}</small></div><Link to={evidence.href}>근거 열기 <ExternalLink aria-hidden="true" /></Link></>}
        </section>}
        {activeWorkflow && <section className="copilot-evidence copilot-workflow-session" aria-label="현재 대화 워크플로">
          <header><span><ListChecks aria-hidden="true" /></span><div><strong>대화에서 만든 작업 흐름</strong><small>{activeStep ? `현재 단계: ${activeStep}` : "모든 안내 단계를 검토했습니다."}</small></div></header>
          {activeWorkflow.recommendedTool && <div><strong>{activeWorkflow.recommendedTool}</strong><span>{activeWorkflow.text}</span></div>}
          <ol>{activeWorkflow.workflowSteps?.map((step, index) => <li className={index < activeStepIndex ? "is-complete" : index === activeStepIndex ? "is-current" : ""} key={step}><span>{index + 1}</span>{step}</li>)}</ol>
          <div className="copilot-workflow-actions">
            {activeStep && <button type="button" className="button-secondary" onClick={finishActiveStep}>현재 단계 완료</button>}
            {activeWorkflow.action && <Link className="button-primary" to={activeWorkflow.action.href}>{activeStep ? "현재 단계 작업공간 열기" : "작업공간 열기"} <ExternalLink aria-hidden="true" /></Link>}
          </div>
          <small>완료 표시는 이 브라우저 대화에서만 관리됩니다. 분석 설정·결과·프로젝트 문서는 사용자가 작업공간에서 별도로 저장해야 합니다.</small>
        </section>}
        <div className="copilot-messages" role="log" aria-live="polite" aria-relevant="additions">
          {messages.map((message) => <div className={`copilot-message is-${message.role}`} key={message.id}><strong>{message.role === "assistant" ? "AI Assistant" : "사용자"}</strong><p>{message.text}</p>{message.fallbackSteps && message.fallbackSteps.length > 0 && <section className="copilot-guidance-block copilot-fallback-status" aria-label="AI Assistant 답변 생성 단계"><h3>답변 생성 단계</h3><ul>{message.fallbackSteps.map((step) => <li key={step.stage} data-status={step.status}><strong>{step.stage}: {step.status === "answered" ? "답변 생성" : step.status === "unmatched" ? "규칙 없음" : step.status === "failed" ? "오류" : step.status === "unavailable" ? "미설정" : "미호출"}</strong><span>{step.detail}</span></li>)}</ul></section>}{message.guidanceMode === "unmatched" && <section className="copilot-scope-notice" aria-label="StatPro 제공 범위 안내"><h3>StatPro 제공 범위 밖</h3><p>이 요청은 StatPro에서 분석·승인·자동 실행하지 않습니다. 권장 연계 도구와 데이터 계약을 별도로 확인하세요.</p></section>}{message.recommendedTool && <section className="copilot-guidance-block"><h3>{message.guidanceMode === "unmatched" ? "권장 연계 도구" : "추천 도구"}</h3><strong>{message.recommendedTool}</strong></section>}{message.menuPath && message.menuPath.length > 0 && <nav className="copilot-guidance-block" aria-label="추천 메뉴 경로"><h3>메뉴 경로</h3><ol>{message.menuPath.map((item) => <li key={item}>{item}</li>)}</ol></nav>}{message.checklist && message.checklist.length > 0 && <section className="copilot-guidance-block"><h3>실행 전 체크리스트</h3><ul>{message.checklist.map((item) => <li key={item}>{item}</li>)}</ul></section>}{message.workflowSteps && message.workflowSteps.length > 0 && <section className="copilot-guidance-block"><h3>업무절차 (Workflow)</h3><ol>{message.workflowSteps.map((item) => <li key={item}>{item}</li>)}</ol></section>}{message.provider && <small className="copilot-provider">응답 출처: {message.provider}{message.guidanceMode === "llm_fallback" ? " · 생성형 AI 보완" : message.guidanceMode === "rulebase" ? " · 검토된 Rulebase" : ""}</small>}{message.sources && message.sources.length > 0 && <details className="copilot-sources"><summary>근거 {message.sources.length}건</summary><ul>{message.sources.map((source) => <li key={source.reference}><span>{source.title}</span><code>{source.reference}</code></li>)}</ul></details>}{message.action && <Link className="copilot-action" to={message.action.href}>{message.action.label}<ChevronRight aria-hidden="true" /></Link>}{message.role === "assistant" && <button className="copilot-rule-proposal-trigger" type="button" onClick={() => openRuleProposal(message)}>Rule 초안 제안</button>}{ruleProposal?.messageId === message.id && <section className="copilot-rule-proposal" aria-label="Rulebase 업데이트 제안"><h3>Rulebase 업데이트 제안</h3><p>승인할 때만 이 요청과 응답이 로컬 Rulebase에 저장됩니다.</p><label><span>적용 상황</span><textarea aria-label="적용 상황" value={ruleProposal.situation} onChange={(event) => setRuleProposal((current) => current ? { ...current, situation: event.target.value } : current)} rows={2} /></label><label><span>매칭 키워드</span><input aria-label="매칭 키워드" value={ruleProposal.keywords} onChange={(event) => setRuleProposal((current) => current ? { ...current, keywords: event.target.value } : current)} placeholder="쉼표로 구분" /></label><label><span>저장될 답변</span><textarea aria-label="저장될 답변" value={ruleProposal.answer} onChange={(event) => setRuleProposal((current) => current ? { ...current, answer: event.target.value } : current)} rows={4} /></label><div className="copilot-rule-proposal-actions"><button type="button" className="button-primary" disabled={!ruleProposal.situation.trim() || !ruleProposal.answer.trim() || !ruleProposal.keywords.trim() || proposalSaving} onClick={() => void approveRuleProposal()}>{proposalSaving ? "저장 중" : "승인 후 Rulebase 업데이트"}</button><button type="button" className="button-secondary" disabled={proposalSaving} onClick={() => setRuleProposal(null)}>제안 닫기</button></div></section>}</div>)}
          {ruleProposalStatus && <p className="copilot-rule-proposal-status" role="status">{ruleProposalStatus}</p>}
          {answerLoading && <div className="copilot-message is-assistant"><strong>AI Assistant</strong><p>검토된 로컬 근거를 확인하고 있습니다.</p></div>}
        </div>
        </>}
        </div>
        <form className="copilot-composer" onSubmit={submit}>
          <label htmlFor="copilot-question">문의 및 작업 요청 · Text to Work</label>
          <div className="copilot-command-row">
            <button className="copilot-command-icon" type="button" aria-label="명령 추가" aria-expanded={commandMenuOpen} aria-controls="copilot-command-menu" disabled={answerLoading} onClick={() => setCommandMenuOpen((current) => !current)}><Plus aria-hidden="true" /></button>
            <textarea ref={inputRef} id="copilot-question" value={question} onChange={(event) => setQuestion(event.target.value)} onKeyDown={submitOnEnter} placeholder="질문하거나 작업 가이드를 요청하세요 (Shift+Enter 줄바꿈)" rows={2} disabled={answerLoading} />
            <button className="copilot-command-icon" type="button" aria-label="음성 입력은 현재 지원하지 않음" title="음성 입력은 현재 지원하지 않습니다." disabled><Mic aria-hidden="true" /></button>
            <button className="copilot-command-send" type="submit" aria-label="작업 명령 보내기" disabled={!question.trim() || answerLoading}><Send aria-hidden="true" /></button>
          </div>
          {commandMenuOpen && <div id="copilot-command-menu" className="copilot-command-menu" role="group" aria-label="명령 유형 선택">{commandStarters.map((starter) => <button type="button" key={starter.label} onClick={() => selectCommandStarter(starter.text)}>{starter.label}</button>)}</div>}
        </form>
      </aside>
    </>
  );
}
