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
  it("renders the Korean reports catalog with truthful delivery status", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      if (String(input).endsWith("/health")) return new Response(JSON.stringify({ ok: true, engine_version: "0.6.0", local_only: true }), { status: 200 });
      return new Response(JSON.stringify({ items: [] }), { status: 200 });
    });
    render(<MemoryRouter initialEntries={["/catalog/reports"]}><App /></MemoryRouter>);
    expect(await screen.findByRole("heading", { name: "결과 및 보고서" })).toBeInTheDocument();
    expect(screen.getAllByText("구현됨")).toHaveLength(2);
    expect(screen.getByText("부분 구현")).toBeInTheDocument();
    expect(screen.getByText("개발 예정")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "실험계획법(DOE)" })).toBeInTheDocument();
  });

  it("submits a standardized two-sided CUSUM plan", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
      if (String(input).endsWith("/health")) return new Response(JSON.stringify({ ok: true, engine_version: "0.6.0", local_only: true }), { status: 200 });
      return new Response(JSON.stringify({}), { status: init?.method === "POST" ? 201 : 200, headers: { "Content-Type": "application/json" } });
    });
    render(<MemoryRouter initialEntries={["/analyses/spc/cusum"]}><App /></MemoryRouter>);
    expect(await screen.findByRole("heading", { name: "CUSUM 관리도" })).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "CUSUM 실행" }));
    await waitFor(() => expect(fetchMock.mock.calls.some(([url, init]) => String(url).endsWith("/cusum") && (init as RequestInit | undefined)?.method === "POST")).toBe(true));
    const post = fetchMock.mock.calls.find(([url, init]) => String(url).endsWith("/cusum") && (init as RequestInit | undefined)?.method === "POST");
    expect(JSON.parse(String((post?.[1] as RequestInit).body))).toMatchObject({ target: 50, sigma: 1, reference_value: 0.5, decision_interval: 4 });
  });

  it("renders two-sided CUSUM signals with an accessible table", async () => {
    const points = [
      { index: 0, observation: 1, standardized_observation: 1, upper_cusum: 0.5, lower_cusum: 0, center: 0, lcl: -4, ucl: 4, signal: false, signal_direction: null },
      { index: 1, observation: 1, standardized_observation: 1, upper_cusum: 4.5, lower_cusum: 0, center: 0, lcl: -4, ucl: 4, signal: true, signal_direction: "upper" },
    ];
    const result = {
      analysis_type: "spc.cusum", engine_version: "0.6.0", input_digest: "c".repeat(64), warnings: [], assumptions: [], provenance: [],
      parameters: { target: 0, process_sigma: 1, mean_source: "historical", sigma_source: "historical", reference_value: 0.5, decision_interval: 4, standardized: true, initial_cusum: 0 },
      diagnostics: { signal_indices: [1] }, tables: { chart_points: points }, plots: { cusum: { upper_values: [0.5, 4.5], lower_values: [0, 0], signal_indices: [1] } },
    };
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      if (String(input).endsWith("/health")) return new Response(JSON.stringify({ ok: true, engine_version: "0.6.0", local_only: true }), { status: 200 });
      return new Response(JSON.stringify({ run_id: "cusum-001", storage_version: 1, etag: "a".repeat(64), result }), { status: 200 });
    });
    render(<MemoryRouter initialEntries={["/runs/cusum-001"]}><App /></MemoryRouter>);
    expect(await screen.findByRole("heading", { name: "CUSUM 관리도" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "CUSUM 관측값과 판정구간" })).toBeInTheDocument();
    expect(screen.getByText("상측 이탈")).toBeInTheDocument();
  });

  it("submits EWMA observations with historical parameters", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
      if (String(input).endsWith("/health")) return new Response(JSON.stringify({ ok: true, engine_version: "0.6.0", local_only: true }), { status: 200 });
      return new Response(JSON.stringify({}), { status: init?.method === "POST" ? 201 : 200, headers: { "Content-Type": "application/json" } });
    });
    render(<MemoryRouter initialEntries={["/analyses/spc/ewma"]}><App /></MemoryRouter>);
    expect(await screen.findByRole("heading", { name: "EWMA 관리도" })).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "EWMA 실행" }));
    await waitFor(() => expect(fetchMock.mock.calls.some(([url, init]) => String(url).endsWith("/ewma") && (init as RequestInit | undefined)?.method === "POST")).toBe(true));
    const post = fetchMock.mock.calls.find(([url, init]) => String(url).endsWith("/ewma") && (init as RequestInit | undefined)?.method === "POST");
    expect(JSON.parse(String((post?.[1] as RequestInit).body))).toMatchObject({
      values: [50, 50, 50, 50, 50, 51, 51, 52, 52, 52, 52, 52],
      target: 50,
      sigma: 1,
      weight: 0.2,
      limit_width: 3,
    });
  });

  it("renders startup-adjusted EWMA limits with an accessible table", async () => {
    const points = [
      { index: 0, observation: 50, ewma: 50, center: 50, lcl: 49.4, ucl: 50.6, standard_error: 0.2, signal: false },
      { index: 1, observation: 55, ewma: 51, center: 50, lcl: 49.23, ucl: 50.77, standard_error: 0.256, signal: true },
    ];
    const result = {
      analysis_type: "spc.ewma", engine_version: "0.6.0", input_digest: "e".repeat(64), warnings: [], assumptions: [], provenance: [],
      parameters: { weight: 0.2, limit_width: 3, target: 50, process_sigma: 1, mean_source: "historical", sigma_source: "historical", startup_adjusted_limits: true },
      diagnostics: { signal_indices: [1] }, tables: { chart_points: points }, plots: { ewma: { points, signal_indices: [1] } },
    };
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      if (String(input).endsWith("/health")) return new Response(JSON.stringify({ ok: true, engine_version: "0.6.0", local_only: true }), { status: 200 });
      return new Response(JSON.stringify({ run_id: "ewma-001", storage_version: 1, etag: "a".repeat(64), result }), { status: 200 });
    });
    render(<MemoryRouter initialEntries={["/runs/ewma-001"]}><App /></MemoryRouter>);
    expect(await screen.findByRole("heading", { name: "EWMA 관리도" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "EWMA 관측값과 관리한계" })).toBeInTheDocument();
    expect(screen.getByText("관리한계 이탈")).toBeInTheDocument();
  });

  it("submits equal-sized rational subgroups for Xbar-S", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
      if (String(input).endsWith("/health")) return new Response(JSON.stringify({ ok: true, engine_version: "0.6.0", local_only: true }), { status: 200 });
      return new Response(JSON.stringify({}), { status: init?.method === "POST" ? 201 : 200, headers: { "Content-Type": "application/json" } });
    });
    render(<MemoryRouter initialEntries={["/analyses/spc/xbar-s"]}><App /></MemoryRouter>);
    expect(await screen.findByRole("heading", { name: "Xbar-S 관리도" })).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Xbar-S 실행" }));
    await waitFor(() => expect(fetchMock.mock.calls.some(([, init]) => (init as RequestInit | undefined)?.method === "POST")).toBe(true));
    const post = fetchMock.mock.calls.find(([url, init]) => String(url).endsWith("/xbar-s") && (init as RequestInit | undefined)?.method === "POST");
    const body = JSON.parse(String((post?.[1] as RequestInit).body));
    expect(body.subgroups).toHaveLength(3);
    expect(body.subgroups[0]).toHaveLength(10);
    expect(body.rules).toBe("basic");
  });

  it("renders Xbar-S mean and standard-deviation charts with an accessible table", async () => {
    const result = {
      analysis_type: "spc.xbar_s", engine_version: "0.6.0", input_digest: "f".repeat(64), warnings: [], assumptions: [], provenance: [],
      parameters: { subgroup_size: 10, c4: 0.9727, rules: "basic" }, diagnostics: { estimated_sigma: 1.25 },
      tables: { limits: { xbar: { center: 10, lcl: 8, ucl: 12 }, standard_deviation: { center: 1.2, lcl: 0.3, ucl: 2.1 } } },
      plots: { xbar: { values: [9.8, 10.2], signals: [] }, standard_deviation: { values: [1.1, 1.3], signals: [1] } },
    };
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      if (String(input).endsWith("/health")) return new Response(JSON.stringify({ ok: true, engine_version: "0.6.0", local_only: true }), { status: 200 });
      return new Response(JSON.stringify({ run_id: "xbar-s-001", storage_version: 1, etag: "a".repeat(64), result }), { status: 200 });
    });
    render(<MemoryRouter initialEntries={["/runs/xbar-s-001"]}><App /></MemoryRouter>);
    expect(await screen.findByRole("heading", { name: "부분군 평균 관리도" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "부분군 표준편차 관리도" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Xbar-S 부분군 표" })).toBeInTheDocument();
    expect(screen.getByText("검토 필요")).toBeInTheDocument();
  });

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

  it("submits a p chart with subgroup counts and sample sizes", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
      if (String(input).endsWith("/health")) return new Response(JSON.stringify({ ok: true, engine_version: "0.6.0", local_only: true }), { status: 200 });
      return new Response(JSON.stringify({}), { status: init?.method === "POST" ? 201 : 200, headers: { "Content-Type": "application/json" } });
    });
    render(<MemoryRouter initialEntries={["/analyses/spc/attribute"]}><App /></MemoryRouter>);

    await userEvent.click(await screen.findByRole("button", { name: "관리도 실행" }));
    await waitFor(() => expect(fetchMock.mock.calls.some(([url, init]) => String(url).endsWith("/p-chart") && (init as RequestInit | undefined)?.method === "POST")).toBe(true));
    const post = fetchMock.mock.calls.find(([url, init]) => String(url).endsWith("/p-chart") && (init as RequestInit | undefined)?.method === "POST");
    expect(JSON.parse(String((post?.[1] as RequestInit).body))).toMatchObject({
      nonconforming: [2, 3, 2, 3, 25],
      sample_sizes: [100, 100, 100, 100, 100],
    });
  });

  it("submits and renders a Laney P-prime chart", async () => {
    const points = [
      { index: 0, event_count: 2, opportunity: 100, statistic: 0.02, center: 0.04, lcl: 0, ucl: 0.09, signal: false, z_score: -1, theoretical_sigma: 0.02, adjusted_sigma: 0.016 },
      { index: 1, event_count: 10, opportunity: 100, statistic: 0.1, center: 0.04, lcl: 0, ucl: 0.09, signal: true, z_score: 3, theoretical_sigma: 0.02, adjusted_sigma: 0.016 },
    ];
    const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
      const url = String(input);
      if (url.endsWith("/health")) return new Response(JSON.stringify({ ok: true, engine_version: "0.6.0", local_only: true }), { status: 200 });
      if (init?.method === "POST") return new Response(JSON.stringify({}), { status: 201, headers: { "Content-Type": "application/json" } });
      const result = { analysis_type: "spc.laney_p_prime", engine_version: "0.6.0", input_digest: "l".repeat(64), warnings: [], assumptions: [], provenance: [], parameters: { chart: "p_prime", sigma_z: 0.8 }, diagnostics: { signal_indices: [1] }, tables: { chart_points: points, summary: { total_events: 12, total_opportunity: 200, pooled_rate: 0.06 } }, plots: { attribute_chart: { points, signal_indices: [1] } } };
      return new Response(JSON.stringify({ run_id: "laney-p-result", storage_version: 1, etag: "a".repeat(64), result }), { status: 200 });
    });
    const { unmount } = render(<MemoryRouter initialEntries={["/analyses/spc/attribute"]}><App /></MemoryRouter>);
    await userEvent.selectOptions(await screen.findByRole("combobox", { name: "관리도" }), "p_prime");
    await userEvent.click(screen.getByRole("button", { name: "관리도 실행" }));
    await waitFor(() => expect(fetchMock.mock.calls.some(([url, init]) => String(url).endsWith("/laney-p-prime") && (init as RequestInit | undefined)?.method === "POST")).toBe(true));
    unmount();
    render(<MemoryRouter initialEntries={["/runs/laney-p-result"]}><App /></MemoryRouter>);
    expect(await screen.findByRole("heading", { name: "Laney P′ · 보정 부적합률 관리도" })).toBeInTheDocument();
    expect(screen.getAllByText("3σ 한계 이탈").length).toBeGreaterThan(0);
  });

  it("rejects variable sample sizes for an np chart before calling the API", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch");
    render(<MemoryRouter initialEntries={["/analyses/spc/attribute"]}><App /></MemoryRouter>);
    await userEvent.selectOptions(await screen.findByRole("combobox", { name: "관리도" }), "np");
    const sizes = screen.getByRole("textbox", { name: /^표본 크기/ });
    await userEvent.clear(sizes);
    await userEvent.type(sizes, "100 120 100 100 100");
    await userEvent.click(screen.getByRole("button", { name: "관리도 실행" }));

    expect(await screen.findByText(/np 관리도는 모든 부분군의 검사 기회가 같아야 합니다/)).toBeInTheDocument();
    expect(fetchMock.mock.calls.some(([, init]) => (init as RequestInit | undefined)?.method === "POST")).toBe(false);
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

  it("renders a p chart with varying subgroup limits and an accessible table", async () => {
    const points = [
      { index: 0, event_count: 2, opportunity: 100, nonconforming: 2, sample_size: 100, statistic: 0.02, center: 0.07, lcl: 0, ucl: 0.1465, signal: false },
      { index: 1, event_count: 25, opportunity: 100, nonconforming: 25, sample_size: 100, statistic: 0.25, center: 0.07, lcl: 0, ucl: 0.1465, signal: true },
    ];
    const result = {
      analysis_type: "spc.p_chart", engine_version: "0.6.0", input_digest: "b".repeat(64),
      warnings: [], assumptions: [], provenance: [], parameters: { chart: "p" },
      diagnostics: { signal_indices: [1] },
      tables: { chart_points: points, summary: { total_nonconforming: 27, total_inspected: 200, pooled_proportion: 0.135 } },
      plots: { attribute_chart: { points, signal_indices: [1] } },
    };
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      if (String(input).endsWith("/health")) return new Response(JSON.stringify({ ok: true, engine_version: "0.6.0", local_only: true }), { status: 200 });
      return new Response(JSON.stringify({ run_id: "p-chart-001", storage_version: 1, etag: "a".repeat(64), result }), { status: 200 });
    });

    render(<MemoryRouter initialEntries={["/runs/p-chart-001"]}><App /></MemoryRouter>);
    expect(await screen.findByRole("heading", { name: "p · 부적합률 관리도" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "부분군별 관리한계" })).toBeInTheDocument();
    expect(screen.getAllByText("3σ 한계 이탈").length).toBeGreaterThan(0);
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
    const sevenStepProgress = [
      ["planning_and_preparation", "Planning and Preparation"], ["structure_analysis", "Structure Analysis"],
      ["function_analysis", "Function Analysis"], ["failure_analysis", "Failure Analysis"],
      ["risk_analysis", "Risk Analysis"], ["optimization", "Optimization"],
      ["results_documentation", "Results Documentation"],
    ].map(([step_id, title], index) => ({ step_number: index + 1, step_id, title, status: index < 5 ? "complete" : "not_started", evidence_count: index < 5 ? 1 : 0, gaps: index < 5 ? [] : ["required_evidence"] }));
    const study = { study_id: "PFMEA-001", name: "Connector Assembly", study_type: "process", standard_version: "customer-standard-2026", status: "draft", revision: 2, parent_digest: "a", digest: "b".repeat(64), items: [item], actions: [], audit_events: [], action_priority_policy_id: null, action_priority_policy_digest: null, seven_step_progress: sevenStepProgress };
    const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
      const url = String(input);
      if (url.endsWith("/health")) return new Response(JSON.stringify({ ok: true, engine_version: "0.6.0", local_only: true }), { status: 200 });
      if (init?.method === "POST") return new Response(JSON.stringify({ study_id: "PFMEA-001", storage_version: 3, etag: "c".repeat(64), study: { ...study, status: "in_review", revision: 3 } }), { status: 200 });
      return new Response(JSON.stringify({ study_id: "PFMEA-001", storage_version: 2, etag: "a".repeat(64), study }), { status: 200 });
    });

    render(<MemoryRouter initialEntries={["/fmea/PFMEA-001"]}><App /></MemoryRouter>);
    expect(await screen.findByRole("heading", { name: "FMEA 7단계 진행" })).toBeInTheDocument();
    expect(screen.getByText("기획 및 준비")).toBeInTheDocument();
    await userEvent.click(await screen.findByRole("button", { name: "검토 요청" }));
    expect(await screen.findByText("검토 중")).toBeInTheDocument();
    const reviewCall = fetchMock.mock.calls.find(([url, init]) => String(url).includes("submit-review") && (init as RequestInit | undefined)?.method === "POST");
    expect(JSON.parse(String((reviewCall?.[1] as RequestInit).body)).expected_storage_version).toBe(2);
  });

  it("imports and attaches an external Action Priority policy", async () => {
    const policy = {
      policy_key: `ap-${"d".repeat(64)}`, policy_id: "customer-ap-matrix", standard_version: "customer-standard-2026", digest: "d".repeat(64),
      entries: [{ severity: 8, occurrence: 4, detection: 5, priority: "H" }],
    };
    const study = { study_id: "PFMEA-POLICY", name: "Policy Lifecycle", study_type: "process", standard_version: "customer-standard-2026", status: "draft", revision: 1, parent_digest: null, digest: "b".repeat(64), items: [], actions: [], audit_events: [], action_priority_policy_id: null, action_priority_policy_digest: null, action_priority_policy_key: null };
    const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
      const url = String(input);
      if (url.endsWith("/health")) return new Response(JSON.stringify({ ok: true, engine_version: "0.6.0", local_only: true }), { status: 200 });
      if (url.includes("/fmea-action-priority-policies") && init?.method === "POST") return new Response(JSON.stringify({ policy_key: policy.policy_key, storage_version: 1, etag: "e".repeat(64), policy }), { status: 201 });
      if (url.endsWith("/fmea-studies/PFMEA-POLICY/action-priority-policy") && init?.method === "POST") return new Response(JSON.stringify({ study_id: study.study_id, storage_version: 2, etag: "f".repeat(64), study: { ...study, revision: 2, action_priority_policy_id: policy.policy_id, action_priority_policy_digest: policy.digest, action_priority_policy_key: policy.policy_key } }), { status: 200 });
      if (url.includes("/fmea-action-priority-policies")) return new Response(JSON.stringify({ items: [], next_after: null }), { status: 200 });
      return new Response(JSON.stringify({ study_id: study.study_id, storage_version: 1, etag: "a".repeat(64), study }), { status: 200 });
    });

    render(<MemoryRouter initialEntries={["/fmea/PFMEA-POLICY"]}><App /></MemoryRouter>);
    expect(await screen.findByRole("heading", { name: "Action Priority 정책" })).toBeInTheDocument();
    await userEvent.type(screen.getByRole("textbox", { name: "정책 ID" }), "customer-ap-matrix");
    await userEvent.type(screen.getByRole("textbox", { name: /S,O,D,우선순위/ }), "8,4,5,H");
    await userEvent.click(screen.getByRole("button", { name: "불변 정책으로 가져오기" }));
    await userEvent.selectOptions(await screen.findByRole("combobox", { name: /호환 정책/ }), policy.policy_key);
    await userEvent.click(screen.getByRole("button", { name: "정책 연결" }));

    expect(await screen.findByText("customer-ap-matrix")).toBeInTheDocument();
    const attachCall = fetchMock.mock.calls.find(([url, init]) => String(url).endsWith("/action-priority-policy") && (init as RequestInit | undefined)?.method === "POST");
    expect(JSON.parse(String((attachCall?.[1] as RequestInit).body)).policy_key).toBe(policy.policy_key);
  });

  it("adds a PFMEA process step and renders the traceability chain", async () => {
    const study = {
      study_id: "PFMEA-TRACE", name: "Connector Assembly", study_type: "process", standard_version: "customer-standard-2026", status: "draft", revision: 1, parent_digest: null, digest: "b".repeat(64),
      items: [], actions: [], audit_events: [], action_priority_policy_id: null, action_priority_policy_digest: null, action_priority_policy_key: null,
      process_steps: [], characteristics: [], control_plan_items: [],
    };
    const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
      const url = String(input);
      if (url.endsWith("/health")) return new Response(JSON.stringify({ ok: true, engine_version: "0.6.0", local_only: true }), { status: 200 });
      if (url.includes("/fmea-action-priority-policies")) return new Response(JSON.stringify({ items: [], next_after: null }), { status: 200 });
      if (url.endsWith("/process-steps") && init?.method === "POST") {
        return new Response(JSON.stringify({
          study_id: study.study_id,
          storage_version: 2,
          etag: "c".repeat(64),
          study: { ...study, revision: 2, process_steps: [{ step_id: "STEP-010", sequence: 10, name: "Connector insertion", operation: "Seat connector" }] },
        }), { status: 200 });
      }
      return new Response(JSON.stringify({ study_id: study.study_id, storage_version: 1, etag: "a".repeat(64), study }), { status: 200 });
    });

    render(<MemoryRouter initialEntries={["/fmea/PFMEA-TRACE"]}><App /></MemoryRouter>);
    await userEvent.click(await screen.findByRole("button", { name: "공정 단계" }));
    await userEvent.type(screen.getByRole("textbox", { name: "단계명" }), "Connector insertion");
    await userEvent.type(screen.getByRole("textbox", { name: "작업 내용" }), "Seat connector");
    await userEvent.click(screen.getByRole("button", { name: "공정 단계 저장" }));

    expect(await screen.findByText("STEP-010")).toBeInTheDocument();
    const stepCall = fetchMock.mock.calls.find(([url, init]) => String(url).endsWith("/process-steps") && (init as RequestInit | undefined)?.method === "POST");
    expect(JSON.parse(String((stepCall?.[1] as RequestInit).body))).toMatchObject({ expected_storage_version: 1, step_id: "STEP-010", sequence: 10, name: "Connector insertion" });
  });

  it("links a stored SPC Run to a Control Plan item and shows the reference", async () => {
    const control = {
      control_id: "CP-001", phase: "production", characteristic_id: "CHAR-001", failure_item_ids: [],
      measurement_method: "Caliper", sample_size: 5, frequency: "Each lot", control_method: "I-MR",
      reaction_plan: "Stop line", reaction_owner: "quality.engineer", analysis_evidence: [],
    };
    const study = {
      study_id: "PFMEA-EVIDENCE", name: "Connector Assembly", study_type: "process", standard_version: "customer-standard-2026", status: "draft", revision: 3, parent_digest: null, digest: "b".repeat(64),
      items: [], actions: [], audit_events: [], action_priority_policy_id: null, action_priority_policy_digest: null, action_priority_policy_key: null,
      process_steps: [{ step_id: "STEP-001", sequence: 1, name: "Assembly", operation: "Seat connector" }],
      characteristics: [{ characteristic_id: "CHAR-001", process_step_id: "STEP-001", name: "Depth", specification: "10 ± 1", characteristic_type: "process", special_classification: null }],
      control_plan_items: [control],
    };
    const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
      const url = String(input);
      if (url.endsWith("/health")) return new Response(JSON.stringify({ ok: true, engine_version: "0.6.0", local_only: true }), { status: 200 });
      if (url.includes("/fmea-action-priority-policies")) return new Response(JSON.stringify({ items: [], next_after: null }), { status: 200 });
      if (url.endsWith("/control-plan-items/CP-001/analysis-evidence") && init?.method === "POST") {
        return new Response(JSON.stringify({ study_id: study.study_id, storage_version: 4, etag: "c".repeat(64), study: { ...study, revision: 4, control_plan_items: [{ ...control, analysis_evidence: [{ run_id: "RUN-SPC-001", analysis_type: "spc.imr", run_etag: "d".repeat(64), input_digest: "e".repeat(64) }] }] } }), { status: 200 });
      }
      return new Response(JSON.stringify({ study_id: study.study_id, storage_version: 3, etag: "a".repeat(64), study }), { status: 200 });
    });

    render(<MemoryRouter initialEntries={["/fmea/PFMEA-EVIDENCE"]}><App /></MemoryRouter>);
    await userEvent.click(await screen.findByRole("button", { name: "SPC/MSA 결과 연결" }));
    await userEvent.selectOptions(screen.getByRole("combobox", { name: "Control Plan 항목" }), "CP-001");
    await userEvent.type(screen.getByRole("textbox", { name: "저장된 SPC/MSA Run ID" }), "RUN-SPC-001");
    await userEvent.click(screen.getByRole("button", { name: "실행 결과 연결" }));

    expect(await screen.findByText(/실행 RUN-SPC-001/)).toBeInTheDocument();
    const post = fetchMock.mock.calls.find(([url, init]) => String(url).endsWith("/control-plan-items/CP-001/analysis-evidence") && (init as RequestInit | undefined)?.method === "POST");
    expect(JSON.parse(String((post?.[1] as RequestInit).body))).toMatchObject({ expected_storage_version: 3, run_id: "RUN-SPC-001", actor: "quality.engineer" });
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
    await userEvent.click(await screen.findByRole("button", { name: "승인 서명" }));
    await userEvent.type(screen.getByRole("textbox", { name: "승인자 ID" }), "quality.approver");
    await userEvent.type(screen.getByLabelText("비밀번호"), "correct horse battery staple");
    await userEvent.click(screen.getByRole("button", { name: "재인증 후 승인" }));
    expect(await screen.findByText("승인됨")).toBeInTheDocument();
    const approveCall = fetchMock.mock.calls.find(([url, init]) => String(url).endsWith("/approve") && (init as RequestInit | undefined)?.method === "POST");
    expect(JSON.parse(String((approveCall?.[1] as RequestInit).body))).toEqual({ expected_storage_version: 5, user_id: "quality.approver", password: "correct horse battery staple", meaning: "approval" });
  });

  it("shows the report for the current FMEA revision", async () => {
    const digest = "b".repeat(64);
    const study = { study_id: "PFMEA-REPORT", name: "Report Study", study_type: "process", standard_version: "customer-standard-2026", status: "draft", revision: 1, parent_digest: null, digest, items: [], actions: [], audit_events: [], action_priority_policy_id: null, action_priority_policy_digest: null, process_steps: [], characteristics: [], control_plan_items: [] };
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      const url = String(input);
      if (url.endsWith("/health")) return new Response(JSON.stringify({ ok: true, engine_version: "0.6.0", local_only: true }), { status: 200 });
      if (url.endsWith("/report")) return new Response(JSON.stringify({ report_type: "statpro.fmea.study_review.v1", study_id: study.study_id, study_name: study.name, study_type: "process", standard_version: study.standard_version, revision: 1, snapshot_digest: digest, status: "draft", action_priority_policy: { policy_id: null, policy_digest: null }, seven_step_progress: [], rows: [], approval_record: null, audit_events: [], analysis_evidence_checks: [{ control_id: "CP-001", run_id: "RUN-SPC-001", status: "mismatch" }], limitations: ["Actor names are self-reported workflow fields."] }), { status: 200 });
      if (url.includes("/fmea-action-priority-policies")) return new Response(JSON.stringify({ items: [], next_after: null }), { status: 200 });
      return new Response(JSON.stringify({ study_id: study.study_id, storage_version: 1, etag: "a".repeat(64), study }), { status: 200 });
    });
    render(<MemoryRouter initialEntries={["/fmea/PFMEA-REPORT"]}><App /></MemoryRouter>);
    await userEvent.click(await screen.findByRole("button", { name: "현재 revision 보기" }));
    expect(await screen.findByText("보고할 고장 분석 항목이 없습니다.")).toBeInTheDocument();
    expect(screen.getByText("승인 기록 없음")).toBeInTheDocument();
    expect(screen.getByRole("table", { name: "보고서 조회 시 SPC/MSA Run 식별값 재검증" })).toBeInTheDocument();
    expect(screen.getByText("내용 불일치")).toBeInTheDocument();
    expect(screen.getByText("연결된 SPC/MSA Run 중 재검증되지 않은 결과가 있습니다.").closest('[role="alert"]')).toBeInTheDocument();
    expect(screen.getByText("Actor names are self-reported workflow fields.")).toBeInTheDocument();
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

    await userEvent.selectOptions(await screen.findByRole("combobox", { name: "블록 수" }), "2");
    await userEvent.click(await screen.findByRole("button", { name: "DOE 분석 실행" }));
    await waitFor(() => expect(fetchMock.mock.calls.some(([, init]) => (init as RequestInit | undefined)?.method === "POST")).toBe(true));
    const post = fetchMock.mock.calls.find(([, init]) => (init as RequestInit | undefined)?.method === "POST");
    const body = JSON.parse(String((post?.[1] as RequestInit).body));
    expect(body.prediction_points).toEqual([{ A: 0.75, B: 15 }]);
    expect(body.optimization_goal).toBe("maximize");
    expect(body.blocks).toBe(2);
  });

  it("renders DOE effects, ANOVA, and residual diagnostics", async () => {
    const result = {
      analysis_type: "doe.full_factorial_2level_analysis", engine_version: "0.6.0", input_digest: "b".repeat(64), warnings: [], assumptions: [], provenance: [], parameters: {},
      diagnostics: { response_name: "Strength", r_squared: 0.94366, adjusted_r_squared: 0.90141, residual_standard_deviation: 1.4142, block_count: 2, blocked_resolution_label: "III" },
      tables: {
        coefficients: [
          { term: "Constant", order: 0, coefficient: 14.5, effect: null, sum_of_squares: null, f_value: null, p_value: null },
          { term: "A", order: 1, coefficient: 3.5, effect: 7, sum_of_squares: 98, f_value: 49, p_value: 0.002192 },
          { term: "B", order: 1, coefficient: 1.5, effect: 3, sum_of_squares: 18, f_value: 9, p_value: 0.03994 },
          { term: "A:B", order: 2, coefficient: 1.5, effect: 3, sum_of_squares: 18, f_value: 9, p_value: 0.03994 },
        ],
        anova: [{ source: "Model", degrees_of_freedom: 3, sum_of_squares: 134, mean_square: 44.6667, f_value: 22.3333, p_value: 0.0059 }],
        block_generators: [{ contrast: "Blk1", terms: ["A", "B"], expression: "Blk1=A*B" }],
        block_aliases: [{ contrast: "Blk1", generator_terms: "A*B", treatment_alias_set: ["A*B"] }],
        block_effects: [{ contrast: "Blk1", coefficient: 2, effect: 4, generator_terms: "A*B", treatment_alias_set: ["A*B"] }],
        confounded_terms: [{ term: "A:B", reason: "confounded_with_block" }],
        residuals: [{ run_order: 1, standard_order: 1, point_type: "factorial", block: 1, observed: 10, fitted: 11, residual: -1, scaled_residual: -0.7071 }],
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
    expect(screen.getByRole("link", { name: "HTML 보고서" })).toHaveAttribute("href", "/api/v1/analysis-runs/doe-001/report.html");
    expect(screen.getByRole("link", { name: "CSV·JSON 묶음" })).toHaveAttribute("href", "/api/v1/analysis-runs/doe-001/export");
    expect(screen.getByRole("img", { name: /가장 큰 절대 효과는 A/ })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "ANOVA" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "적합값과 잔차" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "블록 효과와 처리효과 교락" })).toBeInTheDocument();
    expect(screen.getByText(/처리 모형에서 제외된 블록 교락 항: A:B/)).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "조건별 예측" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "최적 설정" })).toBeInTheDocument();
    expect(screen.getAllByText("A:B").length).toBeGreaterThan(0);
  });

  it("submits a regular fractional factorial generator", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
      if (String(input).endsWith("/health")) return new Response(JSON.stringify({ ok: true, engine_version: "0.6.0", local_only: true }), { status: 200 });
      return new Response(JSON.stringify({}), { status: init?.method === "POST" ? 201 : 200, headers: { "Content-Type": "application/json" } });
    });
    render(<MemoryRouter initialEntries={["/analyses/doe/fractional-factorial"]}><App /></MemoryRouter>);

    await userEvent.click(await screen.findByRole("button", { name: "일부요인배치 생성" }));
    await waitFor(() => expect(fetchMock.mock.calls.some(([, init]) => (init as RequestInit | undefined)?.method === "POST")).toBe(true));
    const post = fetchMock.mock.calls.find(([url, init]) => String(url).endsWith("/doe-fractional-factorial") && (init as RequestInit | undefined)?.method === "POST");
    const body = JSON.parse(String((post?.[1] as RequestInit).body));
    expect(body.generators).toEqual([{ factor: "D", terms: ["A", "B", "C"] }]);
    expect(body.factors).toHaveLength(4);
    expect(body.foldover).toBe(false);
  });

  it("submits automatic minimum-aberration fractional selection", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
      if (String(input).endsWith("/health")) return new Response(JSON.stringify({ ok: true, engine_version: "0.6.0", local_only: true }), { status: 200 });
      return new Response(JSON.stringify({}), { status: init?.method === "POST" ? 201 : 200, headers: { "Content-Type": "application/json" } });
    });
    render(<MemoryRouter initialEntries={["/analyses/doe/fractional-factorial"]}><App /></MemoryRouter>);

    await userEvent.click(await screen.findByRole("radio", { name: "자동 선택 · 최소 이상률" }));
    expect(screen.getByRole("combobox", { name: "Foldover 방식" })).toBeEnabled();
    await userEvent.click(screen.getByRole("button", { name: "일부요인배치 생성" }));
    await waitFor(() => expect(fetchMock.mock.calls.some(([, init]) => (init as RequestInit | undefined)?.method === "POST")).toBe(true));
    const post = fetchMock.mock.calls.find(([url, init]) => String(url).endsWith("/doe-fractional-factorial-auto") && (init as RequestInit | undefined)?.method === "POST");
    const body = JSON.parse(String((post?.[1] as RequestInit).body));
    expect(body).toMatchObject({ runs: 8, minimum_resolution: 3, foldover: false });
    expect(body.block_generators).toEqual([]);
    expect(body.generators).toBeUndefined();
  });

  it("submits fractional block generators with a single-factor foldover", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
      if (String(input).endsWith("/health")) return new Response(JSON.stringify({ ok: true, engine_version: "0.6.0", local_only: true }), { status: 200 });
      return new Response(JSON.stringify({}), { status: init?.method === "POST" ? 201 : 200, headers: { "Content-Type": "application/json" } });
    });
    render(<MemoryRouter initialEntries={["/analyses/doe/fractional-factorial"]}><App /></MemoryRouter>);

    await userEvent.type(await screen.findByRole("textbox", { name: "블록 생성식 (선택, 줄마다 하나)" }), "A B");
    await userEvent.selectOptions(screen.getByRole("combobox", { name: "Foldover 방식" }), "factor");
    await userEvent.selectOptions(screen.getByRole("combobox", { name: "반전 요인" }), "D");
    await userEvent.click(screen.getByRole("button", { name: "일부요인배치 생성" }));
    await waitFor(() => expect(fetchMock.mock.calls.some(([, init]) => (init as RequestInit | undefined)?.method === "POST")).toBe(true));
    const post = fetchMock.mock.calls.find(([url, init]) => String(url).endsWith("/doe-fractional-factorial") && (init as RequestInit | undefined)?.method === "POST");
    const body = JSON.parse(String((post?.[1] as RequestInit).body));
    expect(body.block_generators).toEqual([["A", "B"]]);
    expect(body.foldover).toBe(false);
    expect(body.foldover_factor).toBe("D");
  });

  it("submits fractional responses for main-effect analysis", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
      if (String(input).endsWith("/health")) return new Response(JSON.stringify({ ok: true, engine_version: "0.6.0", local_only: true }), { status: 200 });
      return new Response(JSON.stringify({}), { status: init?.method === "POST" ? 201 : 200, headers: { "Content-Type": "application/json" } });
    });
    render(<MemoryRouter initialEntries={["/analyses/doe/fractional-factorial"]}><App /></MemoryRouter>);

    await userEvent.click(await screen.findByRole("checkbox", { name: "응답을 함께 분석" }));
    await userEvent.type(screen.getByRole("textbox", { name: /실행순서 응답/ }), "5 9 11 15 5 9 11 15");
    await userEvent.click(screen.getByRole("button", { name: "일부요인 응답 분석" }));
    await waitFor(() => expect(fetchMock.mock.calls.some(([, init]) => (init as RequestInit | undefined)?.method === "POST")).toBe(true));
    const post = fetchMock.mock.calls.find(([url, init]) => String(url).endsWith("/doe-fractional-factorial-analysis") && (init as RequestInit | undefined)?.method === "POST");
    const body = JSON.parse(String((post?.[1] as RequestInit).body));
    expect(body.responses).toHaveLength(8);
    expect(body).toMatchObject({ response_name: "Response", foldover: false, alpha: 0.05 });
  });

  it("renders fractional defining relation, aliases, and design matrix", async () => {
    const result = {
      analysis_type: "doe.fractional_factorial_2level", engine_version: "0.6.0", input_digest: "d".repeat(64), warnings: [], assumptions: [], provenance: [], parameters: {}, plots: {},
      diagnostics: { resolution: 4, resolution_label: "IV", fraction: "1/2", design_notation: "2^(4-1)", generator_selection_mode: "automatic", selection_objective: "minimum_aberration_at_requested_runs", candidate_sets_examined: 4, word_length_pattern: { "3": 0, "4": 1 }, block_count: 2, blocked_resolution_label: "III" },
      tables: {
        generators: [{ factor: "D", terms: ["A", "B", "C"], expression: "D=A*B*C" }],
        block_generators: [{ contrast: "Blk1", terms: ["A", "B"], expression: "Blk1=A*B" }],
        block_aliases: [{ contrast: "Blk1", generator_terms: "A*B", treatment_alias_set: ["A*B", "C*D"] }],
        defining_relation: [{ identity: "I", words: ["A*B*C*D"], expression: "I = A*B*C*D" }],
        main_effect_aliases: [{ effect: "A", alias_set: ["A", "B*C*D"] }],
        two_factor_aliases: [{ effect: "A*B", alias_set: ["A*B", "C*D"] }],
        design: [{ run_order: 1, standard_order: 1, replicate: 1, block: 1, coded: { A: -1, B: -1, C: -1, D: -1 }, actual: { A: 0, B: 0, C: 0, D: 0 } }],
      },
    };
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      if (String(input).endsWith("/health")) return new Response(JSON.stringify({ ok: true, engine_version: "0.6.0", local_only: true }), { status: 200 });
      return new Response(JSON.stringify({ run_id: "doe-frac-001", storage_version: 1, etag: "a".repeat(64), result }), { status: 200 });
    });

    render(<MemoryRouter initialEntries={["/runs/doe-frac-001"]}><App /></MemoryRouter>);
    expect(await screen.findByRole("heading", { name: "정의관계" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "블록 생성식과 처리효과 별칭" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "자동 생성자 선택 근거" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "선택된 생성식" })).toBeInTheDocument();
    expect(screen.getByText("I = A*B*C*D")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "주효과 별칭구조" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "실행 설계표" })).toBeInTheDocument();
  });

  it("renders fractional effects with alias interpretation", async () => {
    const effect = { term: "A", coefficient: 2, effect: 4, sum_of_squares: 32, standard_error: 1, standardized_effect: 4, p_value: 0.01, significant: true, alias_set: ["A", "B*C*D"], clear_of_two_factor_interactions: false, absolute_effect: 4, display_value: 4 };
    const result = {
      analysis_type: "doe.fractional_factorial_2level_analysis", engine_version: "0.6.0", input_digest: "f".repeat(64), warnings: [], assumptions: [], provenance: [], parameters: { foldover: false, foldover_factor: "D" },
      diagnostics: { response_name: "Yield", inference_method: "residual_error", pareto_reference_line: 2.4, residual_degrees_of_freedom: 2, r_squared: 0.9, resolution_label: "III", augmented_resolution: 3, foldover_mode: "single_factor", foldover_factor: "D", cleared_main_effects: ["D"], main_effects_clear_of_two_factor_interactions: false },
      tables: { coefficients: [effect], ranked_effects: [effect], residuals: [], defining_relation: [], main_effect_aliases: [] },
      plots: {},
    };
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      if (String(input).endsWith("/health")) return new Response(JSON.stringify({ ok: true, engine_version: "0.6.0", local_only: true }), { status: 200 });
      return new Response(JSON.stringify({ run_id: "doe-frac-analysis", storage_version: 1, etag: "a".repeat(64), result }), { status: 200 });
    });

    render(<MemoryRouter initialEntries={["/runs/doe-frac-analysis"]}><App /></MemoryRouter>);
    expect(await screen.findByRole("heading", { name: "부분요인 주효과 Pareto" })).toBeInTheDocument();
    expect(screen.getByRole("img", { name: /가장 큰 절대 효과는 A/ })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "별칭 및 확인 범위" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "단일요인 fold 별칭 분리 범위" })).toBeInTheDocument();
    expect(screen.getByText(/선택 요인 D의 부호만 반전했습니다/)).toBeInTheDocument();
  });

  it("submits central composite responses for quadratic analysis", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
      if (String(input).endsWith("/health")) return new Response(JSON.stringify({ ok: true, engine_version: "0.6.0", local_only: true }), { status: 200 });
      return new Response(JSON.stringify({}), { status: init?.method === "POST" ? 201 : 200, headers: { "Content-Type": "application/json" } });
    });
    render(<MemoryRouter initialEntries={["/analyses/doe/central-composite"]}><App /></MemoryRouter>);

    await userEvent.click(await screen.findByRole("checkbox", { name: "응답을 함께 분석" }));
    await userEvent.type(screen.getByRole("textbox", { name: /실행순서 응답/ }), "4 0 8 20 20 12 4 16 10 10 10 10 10");
    await userEvent.click(screen.getByRole("button", { name: "2차 모형 분석" }));
    await waitFor(() => expect(fetchMock.mock.calls.some(([, init]) => (init as RequestInit | undefined)?.method === "POST")).toBe(true));
    const post = fetchMock.mock.calls.find(([url, init]) => String(url).endsWith("/doe-central-composite-analysis") && (init as RequestInit | undefined)?.method === "POST");
    const body = JSON.parse(String((post?.[1] as RequestInit).body));
    expect(body.responses).toHaveLength(13);
    expect(body).toMatchObject({ design_type: "rotatable", center_points: 5, response_name: "Response" });
  });

  it("submits a Box-Behnken design with automatic center points", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
      if (String(input).endsWith("/health")) return new Response(JSON.stringify({ ok: true, engine_version: "0.6.0", local_only: true }), { status: 200 });
      return new Response(JSON.stringify({}), { status: init?.method === "POST" ? 201 : 200, headers: { "Content-Type": "application/json" } });
    });
    render(<MemoryRouter initialEntries={["/analyses/doe/box-behnken"]}><App /></MemoryRouter>);

    expect(await screen.findByText("예상 실행 수: 15회 · 중심점 3회")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Box–Behnken 설계 생성" }));
    await waitFor(() => expect(fetchMock.mock.calls.some(([, init]) => (init as RequestInit | undefined)?.method === "POST")).toBe(true));
    const post = fetchMock.mock.calls.find(([url, init]) => String(url).endsWith("/doe-box-behnken") && (init as RequestInit | undefined)?.method === "POST");
    const body = JSON.parse(String((post?.[1] as RequestInit).body));
    expect(body.factors).toHaveLength(3);
    expect(body.center_points).toBeUndefined();
    expect(body).toMatchObject({ replicates: 1, randomize: true, seed: 0 });
  });

  it("renders a Box-Behnken design matrix and estimability summary", async () => {
    const result = {
      analysis_type: "doe.box_behnken", engine_version: "0.6.0", input_digest: "b".repeat(64), warnings: [], assumptions: [], provenance: [], parameters: {}, plots: {},
      diagnostics: { factor_count: 3, edge_block_count: 3, edge_point_count: 12, center_point_count: 3, total_run_count: 15, quadratic_model_estimable: true },
      tables: { design: [{ run_order: 1, standard_order: 1, replicate: 1, block: 1, point_type: "edge_midpoint", coded: { A: -1, B: -1, C: 0 }, actual: { A: 0, B: 0, C: 15 } }] },
    };
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      if (String(input).endsWith("/health")) return new Response(JSON.stringify({ ok: true, engine_version: "0.6.0", local_only: true }), { status: 200 });
      return new Response(JSON.stringify({ run_id: "doe-bbd-001", storage_version: 1, etag: "a".repeat(64), result }), { status: 200 });
    });

    render(<MemoryRouter initialEntries={["/runs/doe-bbd-001"]}><App /></MemoryRouter>);
    expect(await screen.findByRole("heading", { name: "Box–Behnken 실행 설계표" })).toBeInTheDocument();
    expect(screen.getByText("추정 가능")).toBeInTheDocument();
    expect(screen.getByText("Edge midpoint")).toBeInTheDocument();
  });

  it("submits Box-Behnken responses for quadratic analysis", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
      if (String(input).endsWith("/health")) return new Response(JSON.stringify({ ok: true, engine_version: "0.6.0", local_only: true }), { status: 200 });
      return new Response(JSON.stringify({}), { status: init?.method === "POST" ? 201 : 200, headers: { "Content-Type": "application/json" } });
    });
    render(<MemoryRouter initialEntries={["/analyses/doe/box-behnken"]}><App /></MemoryRouter>);

    await userEvent.click(await screen.findByRole("checkbox", { name: "응답을 함께 분석" }));
    await userEvent.type(screen.getByRole("textbox", { name: /실행순서 응답/ }), "58 52 42 56 52 56 60 64 47 41 55 49 50 50 50");
    await userEvent.click(screen.getByRole("button", { name: "2차 모형 분석" }));
    await waitFor(() => expect(fetchMock.mock.calls.some(([, init]) => (init as RequestInit | undefined)?.method === "POST")).toBe(true));
    const post = fetchMock.mock.calls.find(([url, init]) => String(url).endsWith("/doe-box-behnken-analysis") && (init as RequestInit | undefined)?.method === "POST");
    const body = JSON.parse(String((post?.[1] as RequestInit).body));
    expect(body.responses).toHaveLength(15);
    expect(body.center_points).toBeUndefined();
    expect(body).toMatchObject({ response_name: "Response", alpha: 0.05 });
  });

  it("submits Box-Behnken responses for stationary-point surface exploration", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
      if (String(input).endsWith("/health")) return new Response(JSON.stringify({ ok: true, engine_version: "0.6.0", local_only: true }), { status: 200 });
      return new Response(JSON.stringify({}), { status: init?.method === "POST" ? 201 : 200, headers: { "Content-Type": "application/json" } });
    });
    render(<MemoryRouter initialEntries={["/analyses/doe/box-behnken"]}><App /></MemoryRouter>);

    await userEvent.click(await screen.findByRole("checkbox", { name: "응답을 함께 분석" }));
    await userEvent.type(screen.getByRole("textbox", { name: /실행순서 응답/ }), "58 52 42 56 52 56 60 64 47 41 55 49 50 50 50");
    await userEvent.click(screen.getByRole("checkbox", { name: "정상점과 2요인 응답표면 격자 탐색" }));
    const gridSize = screen.getByRole("spinbutton", { name: "격자 크기" });
    await userEvent.clear(gridSize);
    await userEvent.type(gridSize, "11");
    await userEvent.click(screen.getByRole("button", { name: "응답표면 탐색" }));
    await waitFor(() => expect(fetchMock.mock.calls.some(([, init]) => (init as RequestInit | undefined)?.method === "POST")).toBe(true));
    const post = fetchMock.mock.calls.find(([url, init]) => String(url).endsWith("/doe-box-behnken-surface") && (init as RequestInit | undefined)?.method === "POST");
    const body = JSON.parse(String((post?.[1] as RequestInit).body));
    expect(body.responses).toHaveLength(15);
    expect(body.center_points).toBeUndefined();
    expect(body).toMatchObject({ plot_factors: ["A", "B"], hold_values: {}, grid_size: 11, contour_levels: 7 });
  });

  it("renders Box-Behnken quadratic coefficients and ANOVA", async () => {
    const result = {
      analysis_type: "doe.box_behnken_analysis", engine_version: "0.6.0", input_digest: "d".repeat(64), warnings: [], assumptions: [], provenance: [], parameters: {}, plots: {},
      diagnostics: { response_name: "Yield", alpha: 0.05, r_squared: 0.99, adjusted_r_squared: 0.98, residual_degrees_of_freedom: 5, lack_of_fit_degrees_of_freedom: 3 },
      tables: {
        coefficients: [{ term: "A^2", kind: "square", coefficient: 6, standard_error: 0.5, t_value: 12, p_value: 0.001, significant: true }],
        anova: [{ source: "Model", degrees_of_freedom: 9, sum_of_squares: 100, mean_square: 11.1, f_value: 10, p_value: 0.01 }],
        residuals: [{ run_order: 1, observed: 58, fitted: 57.9, residual: 0.1 }],
        design: [],
      },
    };
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      if (String(input).endsWith("/health")) return new Response(JSON.stringify({ ok: true, engine_version: "0.6.0", local_only: true }), { status: 200 });
      return new Response(JSON.stringify({ run_id: "doe-bbd-analysis-001", storage_version: 1, etag: "a".repeat(64), result }), { status: 200 });
    });

    render(<MemoryRouter initialEntries={["/runs/doe-bbd-analysis-001"]}><App /></MemoryRouter>);
    expect(await screen.findByRole("heading", { name: "2차 모형 계수" })).toBeInTheDocument();
    expect(screen.getByRole("region", { name: "Box–Behnken 2차 모형 요약" })).toBeInTheDocument();
    expect(screen.getByText("Edge-midpoint design")).toBeInTheDocument();
  });

  it("submits central composite responses for stationary-point surface exploration", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
      if (String(input).endsWith("/health")) return new Response(JSON.stringify({ ok: true, engine_version: "0.6.0", local_only: true }), { status: 200 });
      return new Response(JSON.stringify({}), { status: init?.method === "POST" ? 201 : 200, headers: { "Content-Type": "application/json" } });
    });
    render(<MemoryRouter initialEntries={["/analyses/doe/central-composite"]}><App /></MemoryRouter>);

    await userEvent.click(await screen.findByRole("checkbox", { name: "응답을 함께 분석" }));
    await userEvent.type(screen.getByRole("textbox", { name: /실행순서 응답/ }), "8 8 8 8 8 8 8 8 10 10 10 10 10");
    await userEvent.click(screen.getByRole("checkbox", { name: "정상점과 2요인 응답표면 격자 탐색" }));
    const gridSize = screen.getByRole("spinbutton", { name: "격자 크기" });
    await userEvent.clear(gridSize);
    await userEvent.type(gridSize, "11");
    await userEvent.click(screen.getByRole("button", { name: "응답표면 탐색" }));
    await waitFor(() => expect(fetchMock.mock.calls.some(([, init]) => (init as RequestInit | undefined)?.method === "POST")).toBe(true));
    const post = fetchMock.mock.calls.find(([url, init]) => String(url).endsWith("/doe-central-composite-surface") && (init as RequestInit | undefined)?.method === "POST");
    const body = JSON.parse(String((post?.[1] as RequestInit).body));
    expect(body.responses).toHaveLength(13);
    expect(body).toMatchObject({ plot_factors: ["A", "B"], hold_values: {}, grid_size: 11, contour_levels: 7 });
  });

  it("renders central composite quadratic coefficients and ANOVA", async () => {
    const result = {
      analysis_type: "doe.central_composite_analysis", engine_version: "0.6.0", input_digest: "c".repeat(64), warnings: [], assumptions: [], provenance: [], parameters: {}, plots: {},
      diagnostics: { response_name: "Yield", alpha: 1.4142, rotatable: true, r_squared: 0.95, adjusted_r_squared: 0.9, residual_degrees_of_freedom: 7, lack_of_fit_degrees_of_freedom: 3 },
      tables: {
        coefficients: [{ term: "A^2", kind: "square", coefficient: 5, standard_error: 0.5, t_value: 10, p_value: 0.001, significant: true }],
        anova: [{ source: "Model", degrees_of_freedom: 5, sum_of_squares: 100, mean_square: 20, f_value: 10, p_value: 0.01 }],
        residuals: [{ run_order: 1, observed: 4, fitted: 4.1, residual: -0.1 }],
        design: [],
      },
    };
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      if (String(input).endsWith("/health")) return new Response(JSON.stringify({ ok: true, engine_version: "0.6.0", local_only: true }), { status: 200 });
      return new Response(JSON.stringify({ run_id: "doe-ccd-analysis", storage_version: 1, etag: "a".repeat(64), result }), { status: 200 });
    });

    render(<MemoryRouter initialEntries={["/runs/doe-ccd-analysis"]}><App /></MemoryRouter>);
    expect(await screen.findByRole("heading", { name: "2차 모형 계수" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "반응표면 분산분석" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "적합값과 잔차" })).toBeInTheDocument();
    expect(screen.getByText("A^2")).toBeInTheDocument();
  });

  it("renders stationary-point classification and accessible surface grid", async () => {
    const result = {
      analysis_type: "doe.central_composite_surface", engine_version: "0.6.0", input_digest: "d".repeat(64), warnings: [], assumptions: [], provenance: [], parameters: {}, plots: {},
      diagnostics: { response_name: "Yield", plot_factors: ["A", "B"], surface_grid_size: 3, contour_level_count: 1 },
      tables: {
        stationary_point: [{ classification: "maximum", available: true, coded: { A: 0.25, B: -0.5 }, actual: { A: 6.25, B: 5 }, predicted_response: 100, inside_factorial_cube: true }],
        canonical_axes: [{ axis: 1, eigenvalue: -4 }, { axis: 2, eigenvalue: -2 }],
        surface_grid: [{ x_index: 0, y_index: 0, x_coded: -1, y_coded: -1, x_actual: 0, y_actual: 0, predicted_response: 92 }],
        surface_slice_extrema: [{ kind: "minimum", x_index: 0, y_index: 0, x_coded: -1, y_coded: -1, x_actual: 0, y_actual: 0, predicted_response: 92 }, { kind: "maximum", x_index: 1, y_index: 1, x_coded: 0, y_coded: 0, x_actual: 5, y_actual: 10, predicted_response: 100 }],
        surface_contours: [{ level: 96, x1_coded: -1, y1_coded: 0, x2_coded: 1, y2_coded: 0, x1_actual: 0, y1_actual: 10, x2_actual: 10, y2_actual: 10 }],
      },
    };
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      if (String(input).endsWith("/health")) return new Response(JSON.stringify({ ok: true, engine_version: "0.6.0", local_only: true }), { status: 200 });
      return new Response(JSON.stringify({ run_id: "doe-surface", storage_version: 1, etag: "a".repeat(64), result }), { status: 200 });
    });

    render(<MemoryRouter initialEntries={["/runs/doe-surface"]}><App /></MemoryRouter>);
    expect(await screen.findByRole("heading", { name: "정상점 분석" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Canonical eigenvalues" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "응답표면 격자" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "응답표면 등고선" })).toBeInTheDocument();
    expect(screen.getByRole("img", { name: /등고선 1개 수준, 선분 1개/ })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "3D 응답표면 와이어프레임" })).toBeInTheDocument();
    expect(screen.getByRole("img", { name: /예측 응답의 3D 와이어프레임/ })).toBeInTheDocument();
    expect(screen.getByText("최대점")).toBeInTheDocument();
  });

  it("renders Box-Behnken surface results through the shared surface view", async () => {
    const result = {
      analysis_type: "doe.box_behnken_surface", engine_version: "0.6.0", input_digest: "e".repeat(64), warnings: [], assumptions: [], provenance: [], parameters: {}, plots: {},
      diagnostics: { response_name: "Yield", plot_factors: ["A", "B"], surface_grid_size: 1, contour_level_count: 0 },
      tables: {
        stationary_point: [{ classification: "maximum", available: true, coded: { A: 0.25, B: -0.5, C: 0.1 }, actual: { A: 6.25, B: 5, C: 16.5 }, predicted_response: 100, inside_factorial_cube: true }],
        canonical_axes: [{ axis: 1, eigenvalue: -4 }, { axis: 2, eigenvalue: -3 }, { axis: 3, eigenvalue: -2 }],
        surface_grid: [{ x_index: 0, y_index: 0, x_coded: 0, y_coded: 0, x_actual: 5, y_actual: 10, predicted_response: 99 }],
        surface_slice_extrema: [{ kind: "minimum", x_index: 0, y_index: 0, x_coded: 0, y_coded: 0, x_actual: 5, y_actual: 10, predicted_response: 99 }, { kind: "maximum", x_index: 0, y_index: 0, x_coded: 0, y_coded: 0, x_actual: 5, y_actual: 10, predicted_response: 99 }],
        surface_contours: [],
      },
    };
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      if (String(input).endsWith("/health")) return new Response(JSON.stringify({ ok: true, engine_version: "0.6.0", local_only: true }), { status: 200 });
      return new Response(JSON.stringify({ run_id: "doe-bbd-surface", storage_version: 1, etag: "a".repeat(64), result }), { status: 200 });
    });

    render(<MemoryRouter initialEntries={["/runs/doe-bbd-surface"]}><App /></MemoryRouter>);
    expect(await screen.findByRole("heading", { name: "정상점 분석" })).toBeInTheDocument();
    expect(screen.getByText("최대점")).toBeInTheDocument();
    expect(screen.getByText("C")).toBeInTheDocument();
  });

  it("submits a Plackett-Burman screening design", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
      if (String(input).endsWith("/health")) return new Response(JSON.stringify({ ok: true, engine_version: "0.6.0", local_only: true }), { status: 200 });
      return new Response(JSON.stringify({}), { status: init?.method === "POST" ? 201 : 200, headers: { "Content-Type": "application/json" } });
    });
    render(<MemoryRouter initialEntries={["/analyses/doe/plackett-burman"]}><App /></MemoryRouter>);

    await userEvent.click(await screen.findByRole("button", { name: "선별설계 생성" }));
    await waitFor(() => expect(fetchMock.mock.calls.some(([, init]) => (init as RequestInit | undefined)?.method === "POST")).toBe(true));
    const post = fetchMock.mock.calls.find(([url, init]) => String(url).endsWith("/doe-plackett-burman") && (init as RequestInit | undefined)?.method === "POST");
    const body = JSON.parse(String((post?.[1] as RequestInit).body));
    expect(body.factors).toHaveLength(4);
    expect(body.runs).toBeUndefined();
    expect(body).toMatchObject({ replicates: 1, center_points: 0, randomize: true, seed: 0 });
  });

  it("renders Plackett-Burman diagnostics and design matrix", async () => {
    const result = {
      analysis_type: "doe.plackett_burman", engine_version: "0.6.0", input_digest: "e".repeat(64), warnings: ["Confirm selected factors."], assumptions: [], provenance: [], parameters: {}, plots: {},
      diagnostics: { factor_count: 2, base_run_count: 12, total_run_count: 12, unused_factor_columns: 9, resolution_label: "III", balanced: true, pairwise_orthogonal: true, construction: "published-cyclic-seed" },
      tables: { design: [{ run_order: 1, standard_order: 1, replicate: 1, point_type: "factorial", coded: { A: 1, B: 1 }, actual: { A: 10, B: 20 } }] },
    };
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      if (String(input).endsWith("/health")) return new Response(JSON.stringify({ ok: true, engine_version: "0.6.0", local_only: true }), { status: 200 });
      return new Response(JSON.stringify({ run_id: "doe-pb-001", storage_version: 1, etag: "a".repeat(64), result }), { status: 200 });
    });

    render(<MemoryRouter initialEntries={["/runs/doe-pb-001"]}><App /></MemoryRouter>);
    expect(await screen.findByRole("heading", { name: "설계 검증" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "선별 실행 설계표" })).toBeInTheDocument();
    expect(screen.getByText("published-cyclic-seed")).toBeInTheDocument();
    expect(screen.getAllByText("통과")).toHaveLength(2);
  });

  it("submits Plackett-Burman responses for screening analysis", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
      if (String(input).endsWith("/health")) return new Response(JSON.stringify({ ok: true, engine_version: "0.6.0", local_only: true }), { status: 200 });
      return new Response(JSON.stringify({}), { status: init?.method === "POST" ? 201 : 200, headers: { "Content-Type": "application/json" } });
    });
    render(<MemoryRouter initialEntries={["/analyses/doe/plackett-burman"]}><App /></MemoryRouter>);

    await userEvent.click(await screen.findByRole("checkbox", { name: "응답을 함께 분석" }));
    await userEvent.clear(screen.getByRole("textbox", { name: "응답 이름" }));
    await userEvent.type(screen.getByRole("textbox", { name: "응답 이름" }), "Yield");
    await userEvent.type(screen.getByRole("textbox", { name: /응답값/ }), "1,2,3,4,5,6,7,8,9,10,11,12");
    await userEvent.click(screen.getByRole("button", { name: "응답 분석 실행" }));

    await waitFor(() => expect(fetchMock.mock.calls.some(([, init]) => (init as RequestInit | undefined)?.method === "POST")).toBe(true));
    const post = fetchMock.mock.calls.find(([url, init]) => String(url).endsWith("/doe-plackett-burman-analysis") && (init as RequestInit | undefined)?.method === "POST");
    const body = JSON.parse(String((post?.[1] as RequestInit).body));
    expect(body.responses).toHaveLength(12);
    expect(body).toMatchObject({ response_name: "Yield", alpha: 0.05, replicates: 1, center_points: 0 });
  });

  it("renders Plackett-Burman Pareto and confirmation workflow", async () => {
    const result = {
      analysis_type: "doe.plackett_burman_analysis", engine_version: "0.6.0", input_digest: "f".repeat(64), warnings: ["Confirm selected factors."], assumptions: [], provenance: [], parameters: {},
      diagnostics: { response_name: "Yield", inference_method: "lenth_pse", residual_degrees_of_freedom: 0, pareto_reference_line: 1.2, r_squared: 0.95 },
      plots: { pareto: { terms: ["A", "B"], values: [8, 2], scale: "effect", reference_line: 1.2 } },
      tables: {
        coefficients: [
          { term: "A", coefficient: 4, effect: 8, standard_error: null, standardized_effect: null, p_value: null, significant: true },
          { term: "B", coefficient: 1, effect: 2, standard_error: null, standardized_effect: null, p_value: null, significant: false },
        ],
        ranked_effects: [
          { term: "A", coefficient: 4, effect: 8, absolute_effect: 8, display_value: 8, standard_error: null, standardized_effect: null, p_value: null, significant: true },
          { term: "B", coefficient: 1, effect: 2, absolute_effect: 2, display_value: 2, standard_error: null, standardized_effect: null, p_value: null, significant: false },
        ],
        confirmation_candidates: [{ factor: "A", effect: 8, direction_for_increase: "high", suggested_level: 10, opposite_level: 0, selection_method: "lenth_pse" }],
        curvature: [],
      },
    };
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      if (String(input).endsWith("/health")) return new Response(JSON.stringify({ ok: true, engine_version: "0.6.0", local_only: true }), { status: 200 });
      return new Response(JSON.stringify({ run_id: "doe-pb-analysis-001", storage_version: 1, etag: "a".repeat(64), result }), { status: 200 });
    });

    render(<MemoryRouter initialEntries={["/runs/doe-pb-analysis-001"]}><App /></MemoryRouter>);
    expect(await screen.findByRole("heading", { name: "주효과 Pareto" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "확인실험 후보" })).toBeInTheDocument();
    expect(screen.getByText("Lenth PSE")).toBeInTheDocument();
    expect(screen.getAllByText("확인 후보")).toHaveLength(2);
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
    await userEvent.type(screen.getByRole("textbox", { name: "요인 탐색 제약 (선택)" }), "A 0.2 0.6\nB 0.4 0.4");
    await userEvent.click(screen.getByRole("button", { name: "응답 최적화 실행" }));
    await waitFor(() => expect(fetchMock.mock.calls.some(([, init]) => (init as RequestInit | undefined)?.method === "POST")).toBe(true));
    const post = fetchMock.mock.calls.find(([url, init]) => String(url).endsWith("/doe-response-optimizer") && (init as RequestInit | undefined)?.method === "POST");
    const body = JSON.parse(String((post?.[1] as RequestInit).body));
    expect(body.objectives).toHaveLength(2);
    expect(body.objectives[0]).toMatchObject({ name: "Yield", goal: "target", lower: 0, target: 10 });
    expect(body.factor_constraints).toEqual({ A: { lower: 0.2, upper: 0.6 }, B: { lower: 0.4, upper: 0.4 } });
    expect(body.randomize).toBe(false);
  });

  it("renders DOE composite and individual desirability results", async () => {
    const result = {
      analysis_type: "doe.full_factorial_2level_desirability", engine_version: "0.6.0", input_digest: "c".repeat(64), warnings: [], assumptions: [], provenance: [], parameters: { factor_constraints: { A: { lower: 0.2, upper: 0.6 } } },
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
    expect(screen.getByRole("heading", { name: "적용된 요인 탐색 제약" })).toBeInTheDocument();
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
