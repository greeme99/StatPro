import { useEffect, useRef, useState, type FormEvent } from "react";
import { Bot, ChevronRight, Database, ExternalLink, FolderKanban, Send, X } from "lucide-react";
import { Link, useLocation } from "react-router-dom";
import { getRun, listDmaicProjects } from "../api";

type CopilotMessage = { id: number; role: "assistant" | "user"; text: string };
type CopilotEvidence = {
  kind: "run" | "project";
  title: string;
  identifier: string;
  revision: string;
  detail: string;
  href: string;
  answerContext: string;
};

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

function guideAnswer(question: string, contextName: string, evidence: CopilotEvidence | null) {
  const normalized = question.replace(/\s+/g, " ").trim();
  const grounded = evidence ? ` 현재 근거: ${evidence.answerContext}` : "";
  if (/설정|한계|파라미터|k|h|람다|lambda/i.test(normalized)) {
    return `${contextName}의 설정값은 데이터 구조와 탐지 목적에 따라 달라집니다. 기본값을 먼저 실행한 뒤 가정, 표본 크기, 관리한계와 경고를 함께 검토하세요. 값을 변경할 때는 변경 이유와 기대 효과를 기록하고, 새 분석 실행으로 비교하는 것이 안전합니다.${grounded}`;
  }
  if (/언제|선택|추천|차이|유형/i.test(normalized)) {
    return `${contextName}에서는 먼저 데이터 유형, 표본 구성, 확인하려는 질문을 구분합니다. 계량값인지 계수값인지, 부분군이 있는지, 원인 탐색인지 효과 검증인지 확인한 뒤 도구를 선택하세요. 현재 화면의 선택 가이드와 입력 검증을 우선 기준으로 사용합니다.`;
  }
  if (/이상|신호|조치|다음|절차|완료/i.test(normalized)) {
    return `${contextName} 결과는 신호 확인 → 데이터·측정 오류 배제 → 현장 원인 확인 → 책임자와 조치 기록 → 재분석 및 관리계획 반영 순으로 사용하세요. 결과 화면의 분석 실행 ID와 데이터 개정을 보존하면 조치 전후 근거를 추적할 수 있습니다.${grounded}`;
  }
  if (/근거|연결|프로젝트|개정|실행/i.test(normalized)) {
    return `${contextName}의 결과는 분석 실행 ID, 입력 데이터 개정, 설정값, 엔진 버전과 함께 보존해야 합니다. DMAIC 문서나 FMEA 관리계획에는 해당 실행을 링크하고, 재분석 시 기존 근거를 덮어쓰지 말고 새 개정으로 남기세요.${grounded}`;
  }
  if (/사용|방법|어떻게|도움/i.test(normalized)) {
    return `${contextName}에서 작업 대상을 선택하고 필수 입력을 확인한 다음 분석을 실행하세요. 결과의 가정·경고·관리한계·이상 신호를 검토한 뒤 보고서 또는 프로젝트 근거로 연결합니다. 구체적인 데이터 유형이나 목표를 알려주면 다음 단계를 좁혀 안내할 수 있습니다.`;
  }
  return `${contextName} 문맥에서 질문을 확인했습니다. 데이터 유형, 현재 단계, 기대하는 판단을 함께 알려주면 사용 절차·분석 방법·설정값·후속 조치 중 필요한 내용을 구체적으로 안내하겠습니다.`;
}

export function CopilotPanel() {
  const location = useLocation();
  const context = workspaceContext(location.pathname);
  const [open, setOpen] = useState(() => localStorage.getItem("statpro-copilot-open") === "true");
  const [question, setQuestion] = useState("");
  const [evidence, setEvidence] = useState<CopilotEvidence | null>(null);
  const [evidenceLoading, setEvidenceLoading] = useState(false);
  const [messages, setMessages] = useState<CopilotMessage[]>([
    { id: 1, role: "assistant", text: "현재 작업공간의 사용법, 업무절차, 분석 방법과 설정값을 질문하세요. 답변은 화면의 분석값을 직접 변경하지 않습니다." },
  ]);
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

  const ask = (value: string) => {
    const text = value.trim();
    if (!text) return;
    setMessages((current) => [
      ...current,
      { id: Date.now(), role: "user", text },
      { id: Date.now() + 1, role: "assistant", text: guideAnswer(text, context.name, evidence) },
    ]);
    setQuestion("");
  };

  const submit = (event: FormEvent) => {
    event.preventDefault();
    ask(question);
  };

  return (
    <>
      <button className={`copilot-launcher${open ? " is-open" : ""}`} type="button" aria-label={open ? "AI Copilot 감추기" : "AI Copilot 보이기"} aria-expanded={open} aria-controls="copilot-panel" onClick={() => setOpen((current) => !current)}>
        <Bot aria-hidden="true" /><span>AI Copilot</span><ChevronRight aria-hidden="true" />
      </button>
      <aside id="copilot-panel" className={`copilot-panel${open ? " is-open" : ""}`} aria-label="AI Copilot" aria-hidden={!open}>
        <header className="copilot-header">
          <div><span className="eyebrow">CONTEXT-AWARE GUIDE</span><h2>AI Copilot</h2><p>{context.name}</p></div>
          <button className="icon-button" type="button" aria-label="AI Copilot 닫기" onClick={() => setOpen(false)}><X aria-hidden="true" /></button>
        </header>
        <div className="copilot-suggestions" aria-label="추천 질문">
          {context.suggestions.map((suggestion) => <button type="button" key={suggestion} onClick={() => ask(suggestion)}>{suggestion}</button>)}
        </div>
        {(evidenceLoading || evidence) && <section className="copilot-evidence" aria-label="현재 근거">
          <header><span>{evidence?.kind === "project" ? <FolderKanban aria-hidden="true" /> : <Database aria-hidden="true" />}</span><div><strong>현재 근거</strong><small>저장된 실행·프로젝트 계약에서 읽음</small></div></header>
          {evidenceLoading && !evidence ? <p>근거를 확인하고 있습니다.</p> : evidence && <><div><strong>{evidence.title}</strong><span>{evidence.identifier}</span><small>{evidence.revision} · {evidence.detail}</small></div><Link to={evidence.href}>근거 열기 <ExternalLink aria-hidden="true" /></Link></>}
        </section>}
        <div className="copilot-messages" role="log" aria-live="polite" aria-relevant="additions">
          {messages.map((message) => <div className={`copilot-message is-${message.role}`} key={message.id}><strong>{message.role === "assistant" ? "Copilot" : "사용자"}</strong><p>{message.text}</p></div>)}
        </div>
        <form className="copilot-composer" onSubmit={submit}>
          <label htmlFor="copilot-question">질문</label>
          <div><input ref={inputRef} id="copilot-question" value={question} onChange={(event) => setQuestion(event.target.value)} placeholder="예: Xbar-R 설정값을 설명해줘" autoComplete="off" /><button className="icon-button" type="submit" aria-label="질문 보내기" disabled={!question.trim()}><Send aria-hidden="true" /></button></div>
          <small>안내 답변입니다. 분석 설정 변경은 사용자가 검토 후 직접 실행합니다.</small>
        </form>
      </aside>
    </>
  );
}
