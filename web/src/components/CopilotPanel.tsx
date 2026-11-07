import { useEffect, useRef, useState, type FormEvent } from "react";
import { Bot, ChevronRight, Database, ExternalLink, FolderKanban, ListChecks, RotateCcw, Send, X } from "lucide-react";
import { Link, useLocation } from "react-router-dom";
import { getCopilotGuidance, getRun, listCopilotRules, listDmaicProjects, type CopilotRule } from "../api";
import { guideCopilotQuestion, type CopilotAction } from "../copilotGuidance";

type CopilotMessage = {
  id: number;
  role: "assistant" | "user";
  text: string;
  action?: CopilotAction;
  provider?: string;
  sources?: Array<{ title: string; reference: string }>;
  guidanceMode?: "rulebase" | "llm_fallback" | "unmatched";
  recommendedTool?: string;
  menuPath?: string[];
  checklist?: string[];
  workflowSteps?: string[];
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

const initialMessage = (): CopilotMessage => ({
  id: Date.now(),
  role: "assistant",
  text: "업무 상황을 대화로 설명하면, 확인한 목표와 데이터 구조를 바탕으로 다음 단계·체크리스트·작업공간을 안내합니다. 답변은 분석 설정을 직접 변경하지 않습니다.",
});

function conversationContext(messages: CopilotMessage[]) {
  const turns = messages.filter((message) => message.role === "user" || message.workflowSteps?.length).slice(-6)
    .map((message) => `${message.role === "user" ? "사용자" : "Copilot"}: ${message.text}`)
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
  const [evidence, setEvidence] = useState<CopilotEvidence | null>(null);
  const [evidenceLoading, setEvidenceLoading] = useState(false);
  const [answerLoading, setAnswerLoading] = useState(false);
  const [catalogRules, setCatalogRules] = useState<CopilotRule[]>([]);
  const [catalogLoading, setCatalogLoading] = useState(false);
  const [messages, setMessages] = useState<CopilotMessage[]>(() => [initialMessage()]);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    localStorage.setItem("statpro-copilot-open", String(open));
    if (open) window.requestAnimationFrame(() => inputRef.current?.focus());
  }, [open]);

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
    const domain = context.name.includes("SPC") ? "SPC" : context.name.includes("DOE") ? "DOE" : context.name.includes("FMEA") ? "FMEA" : context.name.includes("DMAIC") ? "DMAIC" : undefined;
    setCatalogLoading(true);
    listCopilotRules({ domain, limit: 4 }).then(setCatalogRules).catch(() => setCatalogRules([])).finally(() => setCatalogLoading(false));
  }, [context.name, open]);

  const ask = async (value: string) => {
    const text = value.trim();
    if (!text || answerLoading) return;
    const messageId = Date.now();
    setMessages((current) => [...current, { id: messageId, role: "user", text }]);
    setQuestion("");
    setAnswerLoading(true);
    try {
      const guidance = await getCopilotGuidance({
        question: text,
        pathname: location.pathname,
        workspace: context.name,
        evidence_context: guidanceContext(evidence, messages),
      });
      setMessages((current) => [...current, {
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
      }]);
    } catch {
      const guidance = guideCopilotQuestion({
        question: text,
        contextName: context.name,
        pathname: location.pathname,
        evidenceContext: guidanceContext(evidence, messages),
      });
      setMessages((current) => [...current, {
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
      }]);
    } finally {
      setAnswerLoading(false);
    }
  };

  const submit = (event: FormEvent) => {
    event.preventDefault();
    void ask(question);
  };

  const activeWorkflow = [...messages].reverse().find((message) => message.role === "assistant" && message.workflowSteps && message.workflowSteps.length > 0);
  const resetConversation = () => {
    if (answerLoading) return;
    setMessages([initialMessage()]);
    setQuestion("");
    window.requestAnimationFrame(() => inputRef.current?.focus());
  };

  return (
    <>
      <button className={`copilot-launcher${open ? " is-open" : ""}`} type="button" aria-label={open ? "AI Copilot 감추기" : "AI Copilot 보이기"} aria-expanded={open} aria-controls="copilot-panel" onClick={() => setOpen((current) => !current)}>
        <Bot aria-hidden="true" /><span>AI Copilot</span><ChevronRight aria-hidden="true" />
      </button>
      <aside id="copilot-panel" className={`copilot-panel${open ? " is-open" : ""}`} aria-label="AI Copilot" aria-hidden={!open}>
        <header className="copilot-header">
          <div><span className="eyebrow">CONTEXT-AWARE GUIDE</span><h2>AI Copilot</h2><p>{context.name}</p></div>
          <div><button className="icon-button" type="button" aria-label="대화 초기화" disabled={answerLoading} onClick={resetConversation}><RotateCcw aria-hidden="true" /></button><button className="icon-button" type="button" aria-label="AI Copilot 닫기" onClick={() => setOpen(false)}><X aria-hidden="true" /></button></div>
        </header>
        <div className="copilot-suggestions" aria-label="추천 질문">
          {context.suggestions.map((suggestion) => <button type="button" key={suggestion} disabled={answerLoading} onClick={() => void ask(suggestion)}>{suggestion}</button>)}
        </div>
        <section className="copilot-catalog" aria-label="현재 작업공간 Rulebase">
          <header><strong>현장 상황별 시작점</strong><small>검토된 Rulebase</small></header>
          {catalogLoading ? <p className="copilot-catalog-status">현재 작업공간의 Rulebase를 확인하고 있습니다.</p> : catalogRules.length > 0 ? <div>{catalogRules.map((rule) => <article className="copilot-catalog-item" key={rule.rule_id}><button type="button" disabled={answerLoading} onClick={() => void ask(rule.situation)}><strong>{rule.situation}</strong><small>{rule.recommended_tool} · {rule.menu_path.join(" › ")}</small></button><details><summary>체크리스트·업무절차 보기</summary><strong>체크리스트</strong><ul>{rule.checklist.map((item) => <li key={item}>{item}</li>)}</ul><strong>업무절차</strong><ol>{rule.workflow_steps.map((item) => <li key={item}>{item}</li>)}</ol></details><Link className="copilot-catalog-action" to={rule.action.href}>{rule.action.label}<ChevronRight aria-hidden="true" /></Link></article>)}</div> : <p className="copilot-catalog-status">이 작업공간의 시작 규칙이 없습니다. 현장 상황이나 목표를 질문하면 적합한 작업 흐름을 안내합니다.</p>}
        </section>
        {(evidenceLoading || evidence) && <section className="copilot-evidence" aria-label="현재 근거">
          <header><span>{evidence?.kind === "project" ? <FolderKanban aria-hidden="true" /> : <Database aria-hidden="true" />}</span><div><strong>현재 근거</strong><small>저장된 실행·프로젝트 계약에서 읽음</small></div></header>
          {evidenceLoading && !evidence ? <p>근거를 확인하고 있습니다.</p> : evidence && <><div><strong>{evidence.title}</strong><span>{evidence.identifier}</span><small>{evidence.revision} · {evidence.detail}</small></div><Link to={evidence.href}>근거 열기 <ExternalLink aria-hidden="true" /></Link></>}
        </section>}
        {activeWorkflow && <section className="copilot-evidence" aria-label="현재 대화 워크플로">
          <header><span><ListChecks aria-hidden="true" /></span><div><strong>현재 대화 워크플로</strong><small>최근 안내에서 이어갈 다음 행동</small></div></header>
          {activeWorkflow.recommendedTool && <div><strong>{activeWorkflow.recommendedTool}</strong><span>{activeWorkflow.text}</span></div>}
          <ol>{activeWorkflow.workflowSteps?.map((step) => <li key={step}>{step}</li>)}</ol>
          {activeWorkflow.action && <Link to={activeWorkflow.action.href}>작업공간 열기 <ExternalLink aria-hidden="true" /></Link>}
        </section>}
        <div className="copilot-messages" role="log" aria-live="polite" aria-relevant="additions">
          {messages.map((message) => <div className={`copilot-message is-${message.role}`} key={message.id}><strong>{message.role === "assistant" ? "Copilot" : "사용자"}</strong><p>{message.text}</p>{message.guidanceMode === "unmatched" && <section className="copilot-scope-notice" aria-label="StatPro 제공 범위 안내"><h3>StatPro 제공 범위 밖</h3><p>이 요청은 StatPro에서 분석·승인·자동 실행하지 않습니다. 권장 연계 도구와 데이터 계약을 별도로 확인하세요.</p></section>}{message.recommendedTool && <section className="copilot-guidance-block"><h3>{message.guidanceMode === "unmatched" ? "권장 연계 도구" : "추천 도구"}</h3><strong>{message.recommendedTool}</strong></section>}{message.menuPath && message.menuPath.length > 0 && <nav className="copilot-guidance-block" aria-label="추천 메뉴 경로"><h3>메뉴 경로</h3><ol>{message.menuPath.map((item) => <li key={item}>{item}</li>)}</ol></nav>}{message.checklist && message.checklist.length > 0 && <section className="copilot-guidance-block"><h3>실행 전 체크리스트</h3><ul>{message.checklist.map((item) => <li key={item}>{item}</li>)}</ul></section>}{message.workflowSteps && message.workflowSteps.length > 0 && <section className="copilot-guidance-block"><h3>업무절차 (Workflow)</h3><ol>{message.workflowSteps.map((item) => <li key={item}>{item}</li>)}</ol></section>}{message.provider && <small className="copilot-provider">응답 출처: {message.provider}{message.guidanceMode === "llm_fallback" ? " · 생성형 AI 보완" : message.guidanceMode === "rulebase" ? " · 검토된 Rulebase" : ""}</small>}{message.sources && message.sources.length > 0 && <details className="copilot-sources"><summary>근거 {message.sources.length}건</summary><ul>{message.sources.map((source) => <li key={source.reference}><span>{source.title}</span><code>{source.reference}</code></li>)}</ul></details>}{message.action && <Link className="copilot-action" to={message.action.href}>{message.action.label}<ChevronRight aria-hidden="true" /></Link>}</div>)}
          {answerLoading && <div className="copilot-message is-assistant"><strong>Copilot</strong><p>검토된 로컬 근거를 확인하고 있습니다.</p></div>}
        </div>
        <form className="copilot-composer" onSubmit={submit}>
          <label htmlFor="copilot-question">질문</label>
          <div><input ref={inputRef} id="copilot-question" value={question} onChange={(event) => setQuestion(event.target.value)} placeholder="예: 설비 비가동이 늘었는데 어떤 순서로 조사하나요?" autoComplete="off" disabled={answerLoading} /><button className="icon-button" type="submit" aria-label="질문 보내기" disabled={!question.trim() || answerLoading}><Send aria-hidden="true" /></button></div>
          <small>업무 상황 또는 다음 질문을 입력하세요. 최근 대화의 목표·데이터 구조를 다음 안내에 반영하며, 분석 설정 변경은 사용자가 검토 후 직접 실행합니다.</small>
        </form>
      </aside>
    </>
  );
}
