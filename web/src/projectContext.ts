import type { StoredDmaicProject } from "./types";

export const ACTIVE_PROJECT_ID = "statpro-active-project-id";
export const ACTIVE_PROJECT_TITLE = "statpro-active-project-title";

export function persistActiveProject(project: StoredDmaicProject | null): void {
  if (!project) return;
  localStorage.setItem(ACTIVE_PROJECT_ID, project.project_id);
  localStorage.setItem(ACTIVE_PROJECT_TITLE, project.project.title);
}

export function selectActiveProject(projects: StoredDmaicProject[]): StoredDmaicProject | null {
  const activeId = localStorage.getItem(ACTIVE_PROJECT_ID);
  const selected = projects.find((project) => project.project_id === activeId) ?? projects[0] ?? null;
  persistActiveProject(selected);
  return selected;
}
