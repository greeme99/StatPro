import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import App from "./App";

afterEach(() => {
  vi.restoreAllMocks();
  localStorage.clear();
  delete document.documentElement.dataset.theme;
});

describe("StatPro UI", () => {
  it("renders recent analysis runs from the local API", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(JSON.stringify({
      items: [{ run_id: "run-001", storage_version: 1, etag: "a".repeat(64), result: { analysis_type: "capability.normal_individuals", engine_version: "0.6.0", input_digest: "b".repeat(64), warnings: [], assumptions: [], provenance: [], parameters: {}, diagnostics: {}, tables: {}, plots: {} } }],
      next_after: null,
    }), { status: 200, headers: { "Content-Type": "application/json" } }));

    render(<MemoryRouter><App /></MemoryRouter>);
    expect(await screen.findByRole("heading", { name: "공정 판단을 한 화면에서" })).toBeInTheDocument();
    expect(await screen.findByText("run-001")).toBeInTheDocument();
  });

  it("validates I-MR values before calling the API", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch");
    render(<MemoryRouter initialEntries={["/analyses/imr/new"]}><App /></MemoryRouter>);
    const values = await screen.findByRole("textbox", { name: /^측정값/ });
    await userEvent.clear(values);
    await userEvent.type(values, "one value");
    await userEvent.click(screen.getByRole("button", { name: "분석 실행" }));

    expect(await screen.findByText(/유한한 숫자를 두 개 이상 입력하세요/)).toBeInTheDocument();
    expect(fetchMock.mock.calls.some(([, init]) => (init as RequestInit | undefined)?.method === "POST")).toBe(false);
    await waitFor(() => expect(values).toHaveFocus());
  });

  it("toggles dark theme with an accessible control", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(JSON.stringify({ items: [], next_after: null }), { status: 200, headers: { "Content-Type": "application/json" } }));
    render(<MemoryRouter><App /></MemoryRouter>);
    await userEvent.click(screen.getByRole("button", { name: "다크 테마로 전환" }));
    expect(document.documentElement.dataset.theme).toBe("dark");
  });

  it("opens evidence as a modal and restores focus on Escape", async () => {
    const result = {
      analysis_type: "spc.imr", engine_version: "0.6.0", input_digest: "b".repeat(64),
      warnings: [], assumptions: ["시간 순서를 유지합니다."],
      provenance: [{ title: "NIST", url: "https://example.test/nist", authority: "public" }],
      parameters: {}, diagnostics: {},
      tables: { limits: { individuals: { center: 10.3, ucl: 11.0, lcl: 9.6 } } },
      plots: { individuals: { values: [10.2, 10.4], signals: [] } },
    };
    vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(JSON.stringify({ run_id: "run-imr", storage_version: 1, etag: "a".repeat(64), result }), { status: 200, headers: { "Content-Type": "application/json" } }));

    render(<MemoryRouter initialEntries={["/runs/run-imr"]}><App /></MemoryRouter>);
    const trigger = await screen.findByRole("button", { name: "계산 근거" });
    await userEvent.click(trigger);
    expect(screen.getByRole("dialog", { name: "계산 근거" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "닫기" })).toHaveFocus();
    await userEvent.keyboard("{Escape}");
    expect(screen.queryByRole("dialog", { name: "계산 근거" })).not.toBeInTheDocument();
    expect(trigger).toHaveFocus();
  });

  it("renders persisted FMEA studies in the risk workbench", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      const url = String(input);
      const payload = url.endsWith("/health")
        ? { ok: true, engine_version: "0.6.0", local_only: true }
        : {
            items: [{
              study_id: "PFMEA-001", storage_version: 1, etag: "a".repeat(64),
              study: { study_id: "PFMEA-001", name: "Connector Assembly", study_type: "process", standard_version: "customer-standard-2026", status: "draft", revision: 1, parent_digest: null, digest: "b".repeat(64), items: [], actions: [], audit_events: [], action_priority_policy_id: null, action_priority_policy_digest: null },
            }],
            next_after: null,
          };
      return new Response(JSON.stringify(payload), { status: 200, headers: { "Content-Type": "application/json" } });
    });

    render(<MemoryRouter initialEntries={["/fmea"]}><App /></MemoryRouter>);
    expect(await screen.findByRole("heading", { name: "FMEA Study" })).toBeInTheDocument();
    expect(await screen.findByText("Connector Assembly")).toBeInTheDocument();
    expect(screen.getByText("작성 중")).toBeInTheDocument();
  });

  it("submits the current FMEA revision for review", async () => {
    const item = {
      item_id: "FA-001", structure_element: "Connector", function: "Maintain contact", requirement: "Resistance", failure_mode: "Incomplete insertion", effect: "Open circuit", cause: "Fixture drift", prevention_control: "Checklist", detection_control: "Continuity test",
      initial_ratings: { severity: 8, occurrence: 4, detection: 5, rpn: 160 }, current_ratings: { severity: 8, occurrence: 4, detection: 5, rpn: 160 }, action_priority: null, action_priority_reason: "policy_not_supplied",
    };
    const study = { study_id: "PFMEA-001", name: "Connector Assembly", study_type: "process", standard_version: "customer-standard-2026", status: "draft", revision: 2, parent_digest: "a", digest: "b".repeat(64), items: [item], actions: [], audit_events: [], action_priority_policy_id: null, action_priority_policy_digest: null };
    const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
      const url = String(input);
      if (url.endsWith("/health")) return new Response(JSON.stringify({ ok: true, engine_version: "0.6.0", local_only: true }), { status: 200 });
      if (init?.method === "POST") return new Response(JSON.stringify({ study_id: "PFMEA-001", storage_version: 3, etag: "c".repeat(64), study: { ...study, status: "in_review", revision: 3 } }), { status: 200 });
      return new Response(JSON.stringify({ study_id: "PFMEA-001", storage_version: 2, etag: "a".repeat(64), study }), { status: 200 });
    });

    render(<MemoryRouter initialEntries={["/fmea/PFMEA-001"]}><App /></MemoryRouter>);
    await userEvent.click(await screen.findByRole("button", { name: "검토 요청" }));
    expect(await screen.findByText("검토 중")).toBeInTheDocument();
    const reviewCall = fetchMock.mock.calls.find(([url, init]) => String(url).includes("submit-review") && (init as RequestInit | undefined)?.method === "POST");
    expect(JSON.parse(String((reviewCall?.[1] as RequestInit).body)).expected_storage_version).toBe(2);
  });

  it("renders persisted worksheets with typed shape metadata", async () => {
    const worksheet = { worksheet_id: "ws-001", name: "Process Measurements", base_dataset_digest: "d".repeat(64), digest: "e".repeat(64), revision: 1, parent_digest: null, row_count: 2, columns: [{ name: "value", data_type: "numeric", nullable: true, missing_count: 1, values: [10.5, null] }], transformations: [] };
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      const payload = String(input).endsWith("/health")
        ? { ok: true, engine_version: "0.6.0", local_only: true }
        : { items: [{ worksheet_id: "ws-001", storage_version: 1, etag: "a".repeat(64), worksheet, dataset: null }], next_after: null };
      return new Response(JSON.stringify(payload), { status: 200 });
    });

    render(<MemoryRouter initialEntries={["/data"]}><App /></MemoryRouter>);
    expect(await screen.findByRole("heading", { name: "워크시트" })).toBeInTheDocument();
    expect(await screen.findByText("Process Measurements")).toBeInTheDocument();
    expect(screen.getByText("ws-001")).toBeInTheDocument();
  });

  it("imports a CSV file and opens its worksheet", async () => {
    const worksheet = { worksheet_id: "ws-new", name: "Incoming Data", base_dataset_digest: "d".repeat(64), digest: "e".repeat(64), revision: 1, parent_digest: null, row_count: 1, columns: [{ name: "value", data_type: "numeric", nullable: false, missing_count: 0, values: [10.5] }], transformations: [] };
    const stored = { worksheet_id: "ws-new", storage_version: 1, etag: "a".repeat(64), worksheet, dataset: null };
    const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
      const url = String(input);
      if (url.endsWith("/health")) return new Response(JSON.stringify({ ok: true, engine_version: "0.6.0", local_only: true }), { status: 200 });
      if (init?.method === "POST") return new Response(JSON.stringify(stored), { status: 201 });
      if (url.includes("/v1/worksheets/ws-new")) return new Response(JSON.stringify(stored), { status: 200 });
      return new Response(JSON.stringify({ items: [], next_after: null }), { status: 200 });
    });

    render(<MemoryRouter initialEntries={["/data"]}><App /></MemoryRouter>);
    await userEvent.clear(await screen.findByRole("textbox", { name: "워크시트 이름" }));
    await userEvent.type(screen.getByRole("textbox", { name: "워크시트 이름" }), "Incoming Data");
    await userEvent.upload(screen.getByLabelText(/CSV 파일/), new File(["value\n10.5\n"], "incoming.csv", { type: "text/csv" }));
    await userEvent.click(screen.getByRole("button", { name: "가져오기" }));

    expect(await screen.findByRole("heading", { name: "Incoming Data" })).toBeInTheDocument();
    const importCall = fetchMock.mock.calls.find(([url, init]) => String(url).endsWith("/v1/worksheets/import-csv") && (init as RequestInit | undefined)?.method === "POST");
    const body = JSON.parse(String((importCall?.[1] as RequestInit).body));
    expect(body.file_name).toBe("incoming.csv");
    expect(atob(body.content_base64)).toBe("value\n10.5\n");
  });

  it("edits a worksheet cell as a new revision", async () => {
    const column = { name: "value", data_type: "numeric", nullable: false, missing_count: 0, values: [10.5] };
    const worksheet = { worksheet_id: "ws-001", name: "Process Measurements", base_dataset_digest: "d".repeat(64), digest: "e".repeat(64), revision: 1, parent_digest: null, row_count: 1, columns: [column], transformations: [] };
    const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
      if (String(input).endsWith("/health")) return new Response(JSON.stringify({ ok: true, engine_version: "0.6.0", local_only: true }), { status: 200 });
      if (init?.method === "PATCH") return new Response(JSON.stringify({ worksheet_id: "ws-001", storage_version: 2, etag: "b".repeat(64), worksheet: { ...worksheet, revision: 2, parent_digest: worksheet.digest, columns: [{ ...column, values: [11.25] }] }, dataset: null }), { status: 200 });
      return new Response(JSON.stringify({ worksheet_id: "ws-001", storage_version: 1, etag: "a".repeat(64), worksheet, dataset: null }), { status: 200 });
    });

    render(<MemoryRouter initialEntries={["/data/ws-001"]}><App /></MemoryRouter>);
    const trigger = await screen.findByRole("button", { name: /행 1, 열 value, 값 10.5 편집/ });
    await userEvent.click(trigger);
    const editor = screen.getByRole("textbox", { name: /^새 값/ });
    expect(editor).toHaveFocus();
    await userEvent.clear(editor);
    await userEvent.type(editor, "11.25");
    await userEvent.click(screen.getByRole("button", { name: "새 revision으로 저장" }));

    expect(await screen.findByText(/revision 2/)).toBeInTheDocument();
    const patchCall = fetchMock.mock.calls.find(([, init]) => (init as RequestInit | undefined)?.method === "PATCH");
    const body = JSON.parse(String((patchCall?.[1] as RequestInit).body));
    expect(body).toMatchObject({ expected_storage_version: 1, row_index: 0, column_name: "value", value: "11.25" });
  });
});
