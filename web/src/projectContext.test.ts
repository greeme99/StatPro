import { beforeEach, describe, expect, it } from "vitest";
import { ACTIVE_PROJECT_ID, ACTIVE_PROJECT_TITLE, selectActiveProject } from "./projectContext";
import type { StoredDmaicProject } from "./types";

function project(projectId: string, title: string): StoredDmaicProject {
  return { project_id: projectId, project: { project_id: projectId, title } } as StoredDmaicProject;
}

describe("DMAIC active project context", () => {
  beforeEach(() => localStorage.clear());

  it("selects the persisted project across workspaces", () => {
    const projects = [project("DMAIC-001", "첫 프로젝트"), project("DMAIC-002", "현재 프로젝트")];
    localStorage.setItem(ACTIVE_PROJECT_ID, "DMAIC-002");

    expect(selectActiveProject(projects)?.project_id).toBe("DMAIC-002");
    expect(localStorage.getItem(ACTIVE_PROJECT_TITLE)).toBe("현재 프로젝트");
  });

  it("falls back to the first available project and persists it", () => {
    const selected = selectActiveProject([project("DMAIC-001", "첫 프로젝트")]);

    expect(selected?.project_id).toBe("DMAIC-001");
    expect(localStorage.getItem(ACTIVE_PROJECT_ID)).toBe("DMAIC-001");
    expect(localStorage.getItem(ACTIVE_PROJECT_TITLE)).toBe("첫 프로젝트");
  });
});
