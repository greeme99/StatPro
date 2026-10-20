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

  it("submits the selected I-MR rule set", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(JSON.stringify({}), { status: 201, headers: { "Content-Type": "application/json" } }));
    render(<MemoryRouter initialEntries={["/analyses/imr/new"]}><App /></MemoryRouter>);

    await userEvent.selectOptions(await screen.findByRole("combobox", { name: "규칙 세트" }), "nelson");
    await userEvent.click(screen.getByRole("button", { name: "분석 실행" }));
    await waitFor(() => expect(fetchMock.mock.calls.some(([, init]) => (init as RequestInit | undefined)?.method === "POST")).toBe(true));
    const post = fetchMock.mock.calls.find(([, init]) => (init as RequestInit | undefined)?.method === "POST");
    expect(JSON.parse(String((post?.[1] as RequestInit).body)).rules).toBe("nelson");
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

  it("renders supplementary I-MR rule identifiers for involved observations", async () => {
    const result = {
      analysis_type: "spc.imr", engine_version: "0.6.0", input_digest: "b".repeat(64),
      warnings: [], assumptions: [], provenance: [], parameters: { rules: "western_electric" }, diagnostics: {},
      tables: { limits: { individuals: { center: 3.5, ucl: 8.82, lcl: -1.82 } } },
      plots: { individuals: { values: [1, 2, 3, 4, 5, 6], signals: [0, 1, 2, 3, 4, 5], rule_signals: [{ rule: "TREND-6", involved_indices: [0, 1, 2, 3, 4, 5] }] } },
    };
    vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(JSON.stringify({ run_id: "run-trend", storage_version: 1, etag: "a".repeat(64), result }), { status: 200, headers: { "Content-Type": "application/json" } }));

    render(<MemoryRouter initialEntries={["/runs/run-trend"]}><App /></MemoryRouter>);
    expect(await screen.findByText("신호 관측값")).toBeInTheDocument();
    expect(screen.getAllByText("TREND-6").length).toBeGreaterThan(0);
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

  it("adds and completes an FMEA action with revised risk ratings", async () => {
    const item = {
      item_id: "FA-001", structure_element: "Connector", function: "Maintain contact", requirement: "Resistance", failure_mode: "Incomplete insertion", effect: "Open circuit", cause: "Fixture drift", prevention_control: "Checklist", detection_control: "Continuity test",
      initial_ratings: { severity: 8, occurrence: 4, detection: 5, rpn: 160 }, current_ratings: { severity: 8, occurrence: 4, detection: 5, rpn: 160 }, action_priority: null, action_priority_reason: "policy_not_supplied",
    };
    const baseStudy = { study_id: "PFMEA-001", name: "Connector Assembly", study_type: "process", standard_version: "customer-standard-2026", status: "draft", revision: 2, parent_digest: "a", digest: "b".repeat(64), items: [item], actions: [], audit_events: [], action_priority_policy_id: null, action_priority_policy_digest: null };
    const openAction = { action_id: "ACT-001", item_id: "FA-001", description: "Add fixture sensor", owner: "process.engineer", due_date: "2026-11-30", status: "open", result: null, evidence_refs: [] };
    const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
      const url = String(input);
      if (url.endsWith("/health")) return new Response(JSON.stringify({ ok: true, engine_version: "0.6.0", local_only: true }), { status: 200 });
      if (url.endsWith("/recommended-actions") && init?.method === "POST") return new Response(JSON.stringify({ study_id: "PFMEA-001", storage_version: 3, etag: "c".repeat(64), study: { ...baseStudy, revision: 3, actions: [openAction] } }), { status: 200 });
      if (url.endsWith("/recommended-actions/ACT-001/complete") && init?.method === "POST") return new Response(JSON.stringify({ study_id: "PFMEA-001", storage_version: 4, etag: "d".repeat(64), study: { ...baseStudy, revision: 4, items: [{ ...item, current_ratings: { severity: 8, occurrence: 2, detection: 2, rpn: 32 } }], actions: [{ ...openAction, status: "complete", result: "Validated", evidence_refs: ["VAL-014"] }] } }), { status: 200 });
      return new Response(JSON.stringify({ study_id: "PFMEA-001", storage_version: 2, etag: "a".repeat(64), study: baseStudy }), { status: 200 });
    });

    render(<MemoryRouter initialEntries={["/fmea/PFMEA-001"]}><App /></MemoryRouter>);
    await userEvent.click(await screen.findByRole("button", { name: "권고조치 추가" }));
    await userEvent.type(screen.getByRole("textbox", { name: "권고조치" }), "Add fixture sensor");
    await userEvent.type(screen.getByRole("textbox", { name: "담당자" }), "process.engineer");
    await userEvent.type(screen.getByLabelText("완료 예정일"), "2026-11-30");
    await userEvent.click(screen.getByRole("button", { name: "권고조치 저장" }));
    expect(await screen.findByText(/ACT-001 · Add fixture sensor/)).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "완료 및 재평가" }));
    await userEvent.type(screen.getByRole("textbox", { name: "실행 결과" }), "Validated");
    await userEvent.type(screen.getByRole("textbox", { name: /증거 참조/ }), "VAL-014");
    const occurrence = screen.getByRole("spinbutton", { name: "재평가 O" });
    const detection = screen.getByRole("spinbutton", { name: "재평가 D" });
    await userEvent.clear(occurrence); await userEvent.type(occurrence, "2");
    await userEvent.clear(detection); await userEvent.type(detection, "2");
    await userEvent.click(screen.getByRole("button", { name: "완료 저장" }));
    expect(await screen.findByText("완료")).toBeInTheDocument();
    expect(await screen.findByText(/결과:/)).toBeInTheDocument();

    const completeCall = fetchMock.mock.calls.find(([url]) => String(url).endsWith("/recommended-actions/ACT-001/complete"));
    expect(JSON.parse(String((completeCall?.[1] as RequestInit).body))).toMatchObject({ expected_storage_version: 3, evidence_refs: ["VAL-014"], revised_ratings: { severity: 8, occurrence: 2, detection: 2 } });
  });

  it("approves an in-review FMEA revision", async () => {
    const study = { study_id: "PFMEA-001", name: "Connector Assembly", study_type: "process", standard_version: "customer-standard-2026", status: "in_review", revision: 5, parent_digest: "a", digest: "b".repeat(64), items: [], actions: [], audit_events: [], action_priority_policy_id: null, action_priority_policy_digest: null };
    const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
      if (String(input).endsWith("/health")) return new Response(JSON.stringify({ ok: true, engine_version: "0.6.0", local_only: true }), { status: 200 });
      if (init?.method === "POST") return new Response(JSON.stringify({ study_id: "PFMEA-001", storage_version: 6, etag: "c".repeat(64), study: { ...study, status: "approved", revision: 6 } }), { status: 200 });
      return new Response(JSON.stringify({ study_id: "PFMEA-001", storage_version: 5, etag: "a".repeat(64), study }), { status: 200 });
    });

    render(<MemoryRouter initialEntries={["/fmea/PFMEA-001"]}><App /></MemoryRouter>);
    await userEvent.click(await screen.findByRole("button", { name: "승인" }));
    expect(await screen.findByText("승인됨")).toBeInTheDocument();
    const approveCall = fetchMock.mock.calls.find(([url, init]) => String(url).endsWith("/approve") && (init as RequestInit | undefined)?.method === "POST");
    expect(JSON.parse(String((approveCall?.[1] as RequestInit).body)).expected_storage_version).toBe(5);
  });

  it("validates the DOE response count before creating an analysis run", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(JSON.stringify({ ok: true, engine_version: "0.6.0", local_only: true }), { status: 200 }));
    render(<MemoryRouter initialEntries={["/analyses/doe/full-factorial"]}><App /></MemoryRouter>);
    const responses = await screen.findByRole("textbox", { name: /^응답값/ });
    await userEvent.clear(responses);
    await userEvent.type(responses, "10 11 12");
    await userEvent.click(screen.getByRole("button", { name: "DOE 분석 실행" }));

    expect(await screen.findByText(/응답값 8개가 필요합니다/)).toBeInTheDocument();
    expect(fetchMock.mock.calls.some(([, init]) => (init as RequestInit | undefined)?.method === "POST")).toBe(false);
    expect(responses).toHaveFocus();
  });

  it("submits DOE prediction settings and a bounded optimization goal", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
      if (String(input).endsWith("/health")) return new Response(JSON.stringify({ ok: true, engine_version: "0.6.0", local_only: true }), { status: 200 });
      return new Response(JSON.stringify({}), { status: init?.method === "POST" ? 201 : 200, headers: { "Content-Type": "application/json" } });
    });
    render(<MemoryRouter initialEntries={["/analyses/doe/full-factorial"]}><App /></MemoryRouter>);

    await userEvent.click(await screen.findByRole("button", { name: "DOE 분석 실행" }));
    await waitFor(() => expect(fetchMock.mock.calls.some(([, init]) => (init as RequestInit | undefined)?.method === "POST")).toBe(true));
    const post = fetchMock.mock.calls.find(([, init]) => (init as RequestInit | undefined)?.method === "POST");
    const body = JSON.parse(String((post?.[1] as RequestInit).body));
    expect(body.prediction_points).toEqual([{ A: 0.75, B: 15 }]);
    expect(body.optimization_goal).toBe("maximize");
  });

  it("renders DOE effects, ANOVA, and residual diagnostics", async () => {
    const result = {
      analysis_type: "doe.full_factorial_2level_analysis", engine_version: "0.6.0", input_digest: "b".repeat(64), warnings: [], assumptions: [], provenance: [], parameters: {},
      diagnostics: { response_name: "Strength", r_squared: 0.94366, adjusted_r_squared: 0.90141, residual_standard_deviation: 1.4142 },
      tables: {
        coefficients: [
          { term: "Constant", order: 0, coefficient: 14.5, effect: null, sum_of_squares: null, f_value: null, p_value: null },
          { term: "A", order: 1, coefficient: 3.5, effect: 7, sum_of_squares: 98, f_value: 49, p_value: 0.002192 },
          { term: "B", order: 1, coefficient: 1.5, effect: 3, sum_of_squares: 18, f_value: 9, p_value: 0.03994 },
          { term: "A:B", order: 2, coefficient: 1.5, effect: 3, sum_of_squares: 18, f_value: 9, p_value: 0.03994 },
        ],
        anova: [{ source: "Model", degrees_of_freedom: 3, sum_of_squares: 134, mean_square: 44.6667, f_value: 22.3333, p_value: 0.0059 }],
        residuals: [{ run_order: 1, standard_order: 1, point_type: "factorial", observed: 10, fitted: 11, residual: -1, scaled_residual: -0.7071 }],
        predictions: [{ point: 1, actual: { A: 0.75, B: 15 }, coded: { A: 0.5, B: 0 }, predicted_response: 16.25 }],
        optimization: [{ goal: "maximize", standard_order: 4, actual: { A: 1, B: 20 }, coded: { A: 1, B: 1 }, predicted_response: 21, candidate_count: 4 }],
      },
      plots: {},
    };
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      if (String(input).endsWith("/health")) return new Response(JSON.stringify({ ok: true, engine_version: "0.6.0", local_only: true }), { status: 200 });
      return new Response(JSON.stringify({ run_id: "doe-001", storage_version: 1, etag: "a".repeat(64), result }), { status: 200 });
    });

    render(<MemoryRouter initialEntries={["/runs/doe-001"]}><App /></MemoryRouter>);
    expect(await screen.findByRole("heading", { name: "효과 크기" })).toBeInTheDocument();
    expect(screen.getByRole("img", { name: /가장 큰 절대 효과는 A/ })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "ANOVA" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "적합값과 잔차" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "조건별 예측" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "최적 설정" })).toBeInTheDocument();
    expect(screen.getAllByText("A:B").length).toBeGreaterThan(0);
  });

  it("submits multiple DOE response objectives with target boundaries", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
      if (String(input).endsWith("/health")) return new Response(JSON.stringify({ ok: true, engine_version: "0.6.0", local_only: true }), { status: 200 });
      return new Response(JSON.stringify({}), { status: init?.method === "POST" ? 201 : 200, headers: { "Content-Type": "application/json" } });
    });
    render(<MemoryRouter initialEntries={["/analyses/doe/response-optimizer"]}><App /></MemoryRouter>);

    const goals = await screen.findAllByRole("combobox", { name: "목표" });
    await userEvent.selectOptions(goals[0], "target");
    const uppers = screen.getAllByRole("spinbutton", { name: "Upper" });
    await userEvent.type(uppers[0], "20");
    await userEvent.click(screen.getByRole("button", { name: "응답 최적화 실행" }));
    await waitFor(() => expect(fetchMock.mock.calls.some(([, init]) => (init as RequestInit | undefined)?.method === "POST")).toBe(true));
    const post = fetchMock.mock.calls.find(([url, init]) => String(url).endsWith("/doe-response-optimizer") && (init as RequestInit | undefined)?.method === "POST");
    const body = JSON.parse(String((post?.[1] as RequestInit).body));
    expect(body.objectives).toHaveLength(2);
    expect(body.objectives[0]).toMatchObject({ name: "Yield", goal: "target", lower: 0, target: 10 });
    expect(body.randomize).toBe(false);
  });

  it("renders DOE composite and individual desirability results", async () => {
    const result = {
      analysis_type: "doe.full_factorial_2level_desirability", engine_version: "0.6.0", input_digest: "c".repeat(64), warnings: [], assumptions: [], provenance: [], parameters: {},
      diagnostics: { global_optimum_proven: false },
      tables: {
        solution: [{ solution: 1, actual: { A: 1, B: 0 }, coded: { A: 1, B: -1 }, composite_desirability: 1, candidate_evaluations: 80, search_method: "deterministic_multistart_pattern" }],
        response_desirabilities: [
          { response: "Yield", goal: "maximize", prediction: 10, desirability: 1, lower: 0, target: 10, upper: null, weight: 1, importance: 1 },
          { response: "Cost", goal: "minimize", prediction: 0, desirability: 1, lower: null, target: 0, upper: 10, weight: 1, importance: 1 },
        ],
        models: [],
      },
      plots: {},
    };
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      if (String(input).endsWith("/health")) return new Response(JSON.stringify({ ok: true, engine_version: "0.6.0", local_only: true }), { status: 200 });
      return new Response(JSON.stringify({ run_id: "doe-opt-001", storage_version: 1, etag: "a".repeat(64), result }), { status: 200 });
    });

    render(<MemoryRouter initialEntries={["/runs/doe-opt-001"]}><App /></MemoryRouter>);
    expect(await screen.findByRole("heading", { name: "권장 요인 설정" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "응답별 예측과 만족도" })).toBeInTheDocument();
    expect(screen.getAllByText("복합 desirability")).toHaveLength(2);
    expect(screen.getByText("Yield")).toBeInTheDocument();
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
