import { useEffect, useRef, useState } from "react";
import { Check, ChevronDown, FolderKanban, Plus, X } from "lucide-react";
import { Link } from "react-router-dom";
import { listDmaicProjects } from "../api";
import { ACTIVE_PROJECT_ID, ACTIVE_PROJECT_TITLE, persistActiveProject } from "../projectContext";
import type { StoredDmaicProject } from "../types";

export function ProjectContextMenu() {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [projects, setProjects] = useState<StoredDmaicProject[]>([]);
  const [activeId, setActiveId] = useState(() => localStorage.getItem(ACTIVE_PROJECT_ID) ?? "");
  const [activeTitle, setActiveTitle] = useState(() => localStorage.getItem(ACTIVE_PROJECT_TITLE) ?? "");
  const triggerRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!open || projects.length > 0) return;
    let active = true;
    setLoading(true);
    setError("");
    listDmaicProjects(50)
      .then((page) => { if (active) setProjects(Array.isArray(page.items) ? page.items : []); })
      .catch((reason: Error) => { if (active) setError(reason.message); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [open, projects.length]);

  const selectProject = (stored: StoredDmaicProject) => {
    persistActiveProject(stored);
    setActiveId(stored.project_id);
    setActiveTitle(stored.project.title);
    setOpen(false);
    triggerRef.current?.focus();
  };

  return (
    <div className="project-context">
      <button ref={triggerRef} className="project-context-trigger" type="button" aria-expanded={open} aria-controls="project-context-menu" onClick={() => setOpen((current) => !current)}>
        <FolderKanban aria-hidden="true" />
        <span><small>현재 프로젝트</small><strong>{activeTitle || "프로젝트 선택"}</strong></span>
        <ChevronDown aria-hidden="true" />
      </button>
      {open && <section id="project-context-menu" className="project-context-menu" aria-label="현재 프로젝트 선택">
        <header><div><span className="eyebrow">PROJECT CONTEXT</span><h2>현재 프로젝트</h2></div><button className="icon-button" type="button" aria-label="프로젝트 선택 닫기" onClick={() => setOpen(false)}><X aria-hidden="true" /></button></header>
        <p>선택한 프로젝트는 작업공간을 이동해도 유지되며, 분석 근거 연결의 기본 대상이 됩니다.</p>
        <div className="project-context-list" role="listbox" aria-label="DMAIC 프로젝트">
          {loading && <span className="project-context-state">프로젝트를 불러오고 있습니다.</span>}
          {error && <span className="project-context-state is-error">{error}</span>}
          {!loading && !error && projects.length === 0 && <span className="project-context-state">등록된 프로젝트가 없습니다.</span>}
          {projects.map((stored) => <button type="button" role="option" aria-selected={stored.project_id === activeId} key={stored.project_id} onClick={() => selectProject(stored)}>
            <span><strong>{stored.project.title}</strong><small>{stored.project_id} · Revision {stored.project.revision} · {stored.project.status}</small></span>
            {stored.project_id === activeId && <Check aria-hidden="true" />}
          </button>)}
        </div>
        {activeId && <Link className="button button-primary" to="/home/dmaic/project" onClick={() => setOpen(false)}><FolderKanban aria-hidden="true" /> 현재 프로젝트 현황 열기</Link>}
        <Link className="button button-secondary" to="/home/dmaic/define" onClick={() => setOpen(false)}><Plus aria-hidden="true" /> 프로젝트 만들기·정의 열기</Link>
      </section>}
    </div>
  );
}
