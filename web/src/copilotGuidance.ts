export type CopilotAction = {
  label: string;
  href: string;
};

export type CopilotGuidance = {
  text: string;
  action?: CopilotAction;
  recommendedTool?: string;
  menuPath?: string[];
  checklist?: string[];
  workflowSteps?: string[];
  guidanceMode?: "rulebase" | "unmatched";
};

type GuidanceInput = {
  question: string;
  contextName: string;
  pathname: string;
  evidenceContext?: string;
};

const withEvidence = (text: string, evidenceContext?: string) =>
  evidenceContext ? `${text} 현재 근거: ${evidenceContext}` : text;

const response = (
  text: string,
  action?: CopilotAction,
  evidenceContext?: string,
  structured: Omit<CopilotGuidance, "text" | "action"> = {},
): CopilotGuidance => ({
  text: withEvidence(text, evidenceContext),
  action,
  guidanceMode: "rulebase",
  ...structured,
});

/**
 * Offline-first decision guidance. The rules explain their required inputs and
 * never mutate analysis settings. A future model adapter can enrich the prose,
 * but navigation and safety-critical method selection stay deterministic.
 */
export function guideCopilotQuestion({ question, contextName, pathname, evidenceContext }: GuidanceInput): CopilotGuidance {
  const normalized = question.replace(/\s+/g, " ").trim();

  if (/(수율|yield|반응값|y값)/i.test(normalized) && /(온도|압력|시간|인자|요인|xs)/i.test(normalized) && /(실험|최적|개선|조건)/i.test(normalized)) {
    return response(
      "수율(Y)에 영향을 주는 인자(Xs)를 동시에 검증하고 최적 조건을 찾는 문제이므로 실험계획법(DOE)이 적합합니다. 설계된 실행표로 주효과와 상호작용을 추정하고 최적 조건은 확인 실험으로 검증하세요.",
      { label: "DOE 절차 시작", href: "/doe" },
      evidenceContext,
      {
        recommendedTool: "실험계획법 (DOE)",
        menuPath: ["홈 (Home)", "실험계획법 (DOE)", "설계 및 생성"],
        checklist: ["반응값(Y)과 목표 수율 정의", "인자(Xs)와 안전 범위 확인", "측정시스템과 잡음 요인 점검", "확인 실험 자원 확보"],
        workflowSteps: ["목표와 반응 정의", "인자·수준·제약조건 정의", "실험설계 생성", "무작위 순서로 실행", "모형 분석과 확인 실험"],
      },
    );
  }

  if (/(설비|장비|기계)/i.test(normalized) && /(비가동|다운타임|정지|고장시간)/i.test(normalized) && /(원인|개선|감소|줄)/i.test(normalized)) {
    return response(
      "설비 비가동은 손실 범위와 데이터 기준을 먼저 고정하고 원인을 검증해야 하므로 DMAIC 개선 프로젝트가 적합합니다.",
      { label: "DMAIC 정의 단계 시작", href: "/home/dmaic/define" },
      evidenceContext,
      {
        recommendedTool: "개선 프로젝트 (DMAIC)",
        menuPath: ["홈 (Home)", "개선 프로젝트 (DMAIC)", "정의 (Define)"],
        checklist: ["비가동 정의 합의", "고장·정비 이력 확보", "MTBF·MTTR 기준선 확인", "목표·범위·책임자 지정"],
        workflowSteps: ["정의: 손실과 범위 확정", "측정: 기준선 확보", "분석: 원인 검증", "개선: 대책 파일럿", "관리: SPC·FMEA·관리계획 연결"],
      },
    );
  }

  if (/nelson|넬슨/i.test(normalized) && (/x[ -]?bar.?r|xbar.?r|평균.?범위/i.test(normalized) || pathname.endsWith("/xbar-r"))) {
    return response(
      "Nelson 규칙은 3σ 한계 밖 점뿐 아니라 연속, 추세, 교대와 중심선 주변의 비무작위 패턴을 검토합니다. Xbar-R에서는 Xbar 규칙 1–8과 R 규칙 1–4를 평가하므로 경보가 늘 수 있습니다. 링크는 검토용 초안만 열며 사용자가 확인해야 적용됩니다.",
      { label: "Nelson 규칙 초안 검토", href: "/analyses/spc/xbar-r?draft=nelson" },
      evidenceContext,
    );
  }

  if (/x[ -]?bar.?r|xbar.?r|평균.?범위/i.test(normalized) || (pathname.endsWith("/xbar-r") && /설정|관리한계|파라미터/i.test(normalized))) {
    return response(
      "Xbar-R 관리도는 연속형 측정값을 합리적 부분군으로 묶고, 부분군 크기가 보통 2~10개일 때 사용합니다. 시간순 부분군마다 동일한 측정 조건을 유지하고 먼저 R 관리도의 산포 안정성을 확인한 뒤 Xbar 관리도의 평균 신호를 해석하세요. 부분군을 만들 수 없으면 I-MR을, 큰 부분군이면 Xbar-S를 검토합니다.",
      { label: "Xbar-R 분석 설정 열기", href: "/analyses/spc/xbar-r" },
      evidenceContext,
    );
  }

  if (/x[ -]?bar.?s|xbar.?s|평균.?표준편차/i.test(normalized)) {
    return response(
      "Xbar-S 관리도는 연속형 측정값의 부분군이 비교적 클 때 표준편차로 군내 산포를 추정합니다. 부분군별 표본 수와 시간 순서를 확인하고 S 관리도의 안정성을 먼저 판단한 다음 Xbar 신호를 검토하세요. 작은 부분군은 Xbar-R이 더 단순합니다.",
      { label: "Xbar-S 분석 설정 열기", href: "/analyses/spc/xbar-s" },
      evidenceContext,
    );
  }

  if (/i.?mr|개별.?이동범위|개별값/i.test(normalized)) {
    return response(
      "I-MR 관리도는 한 시점에 측정값이 하나뿐이라 합리적 부분군을 구성할 수 없을 때 사용합니다. 관측 순서를 보존하고 연속 관측 간 이동범위가 공정 변동을 대표하는지 확인하세요. 자기상관이나 계절성이 강하면 관리한계 해석 전에 시간 구조를 별도로 검토해야 합니다.",
      { label: "I-MR 분석 설정 열기", href: "/analyses/imr/new" },
      evidenceContext,
    );
  }

  if (/p.?관리도|불량률|부적합품.*비율/i.test(normalized)) {
    return response(
      "p 관리도는 검사 수가 달라질 수 있는 각 표본의 부적합품 비율을 감시합니다. 행마다 부적합품 수와 검사 수가 필요하며 부적합품 수는 검사 수를 넘을 수 없습니다. 표본 크기가 고정되고 개수 자체를 관리하려면 np 관리도를 선택합니다. 과산포가 확인되면 Laney P′를 검토하세요.",
      { label: "p 관리도 설정 열기", href: "/analyses/spc/attribute?chart=p" },
      evidenceContext,
    );
  }

  if (/np.?관리도|불량품.*개수|부적합품.*개수/i.test(normalized)) {
    return response(
      "np 관리도는 표본 크기가 일정할 때 부적합품 개수를 감시합니다. 모든 행에 같은 검사 수를 적용할 수 있는지 먼저 확인하세요. 검사 수가 달라지면 p 관리도를 사용해야 합니다.",
      { label: "np 관리도 설정 열기", href: "/analyses/spc/attribute?chart=np" },
      evidenceContext,
    );
  }

  if (/c.?관리도|결점.*개수|결함.*개수/i.test(normalized)) {
    return response(
      "c 관리도는 검사 면적·시간·기회가 일정할 때 한 단위에서 발견되는 결점 수를 감시합니다. 검사 기회가 행마다 달라지면 단위당 결점률을 사용하는 u 관리도로 전환하세요.",
      { label: "c 관리도 설정 열기", href: "/analyses/spc/attribute?chart=c" },
      evidenceContext,
    );
  }

  if (/u.?관리도|단위당.*결점|결함률/i.test(normalized)) {
    return response(
      "u 관리도는 검사 단위 또는 기회 수가 달라질 때 단위당 결점 수를 감시합니다. 행마다 결점 수와 검사 단위 수가 필요합니다. 과산포 또는 과소산포가 반복되면 Laney U′를 검토하세요.",
      { label: "u 관리도 설정 열기", href: "/analyses/spc/attribute?chart=u" },
      evidenceContext,
    );
  }

  if (/ewma|람다|lambda/i.test(normalized)) {
    return response(
      "EWMA는 작고 지속적인 평균 이동을 조기에 탐지합니다. λ가 작을수록 과거 관측의 영향이 오래 유지되고, λ가 클수록 최근 변화에 민감합니다. 기준 평균과 sigma의 출처, λ와 관리한계 배수를 기록한 뒤 과거 안정 구간과 새 실행을 비교하세요. 초기값으로 λ=0.2를 검토하되 공정의 탐지 목적에 맞게 검증해야 합니다.",
      { label: "EWMA 분석 설정 열기", href: "/analyses/spc/ewma" },
      evidenceContext,
    );
  }

  if (/cusum|누적합|결정구간|참조값|\bk\b|\bh\b/i.test(normalized)) {
    return response(
      "양측 tabular CUSUM은 목표 평균에서 작은 지속 이동을 탐지합니다. k는 탐지하려는 이동 크기의 절반 수준을 sigma 단위로 정하고, h는 오경보와 탐지 지연의 균형을 조정합니다. 기준 평균·sigma·k·h의 출처를 함께 보존하고, 변경 전후 실행을 별도 근거로 비교하세요.",
      { label: "CUSUM 분석 설정 열기", href: "/analyses/spc/cusum" },
      evidenceContext,
    );
  }

  if (/희귀|g.?관리도|t.?관리도|사건.*사이/i.test(normalized)) {
    return response(
      "희귀사건 관리도는 사건 사이의 기회 수(G) 또는 경과 시간(T)을 감시합니다. 단순 불량률 대신 사건 간 간격이 데이터여야 하며, 0보다 큰 정수 기회 수는 G, 양의 연속 시간은 T를 선택합니다. 수집 단위와 사건 정의를 고정한 뒤 해석하세요.",
      { label: "G/T 관리도 설정 열기", href: "/analyses/spc/rare-events" },
      evidenceContext,
    );
  }

  if (/관리도|spc|공정.*안정|이상.*신호|관리한계/i.test(normalized)) {
    return response(
      "관리도는 데이터 유형과 부분군 구조로 선택합니다. 연속형은 I-MR·Xbar-R·Xbar-S, 부적합품은 p·np, 결점은 c·u, 작은 평균 이동은 EWMA·CUSUM, 희귀사건 간격은 G·T를 검토하세요. 분석 전에 시간 순서, 합리적 부분군, 기준 구간과 측정시스템 적합성을 확인합니다.",
      { label: "관리도 선택 가이드 열기", href: "/spc/control-charts" },
      evidenceContext,
    );
  }

  if (/부분요인|선별|plackett|플라켓|요인.*많/i.test(normalized)) {
    return response(
      "요인이 많고 주효과 선별이 목적이면 Plackett-Burman 또는 정규 일부요인 설계를 검토합니다. 일부요인은 별칭 구조와 해상도를 명시할 수 있고, Plackett-Burman은 빠른 선별에 적합하지만 상호작용 분리가 제한됩니다. 중요한 요인이 좁혀지면 완전요인 또는 반응표면 설계로 후속 검증하세요.",
      { label: "DOE 선별설계 작업공간 열기", href: "/doe" },
    );
  }

  if (/반응표면|box.?behnken|박스|중심합성|central composite|최적화/i.test(normalized)) {
    return response(
      "곡률을 추정하고 최적 조건을 찾으려면 반응표면 설계를 사용합니다. Box-Behnken은 요인 극단 조합을 피하는 데 유리하고, 중심합성설계는 축점을 통해 넓은 곡률 정보를 제공합니다. 안전 제약, 중심점, 블록, 반복과 응답 목표를 설계 전에 고정하세요.",
      { label: "DOE 반응표면 작업공간 열기", href: "/doe" },
    );
  }

  if (/doe|실험계획|설계.*유형|반복|블록|중심점/i.test(normalized)) {
    return response(
      "DOE는 목적을 먼저 구분합니다. 모든 주효과·상호작용 검증은 완전요인, 적은 실행으로 선별은 일부요인·Plackett-Burman, 곡률과 최적화는 중심합성·Box-Behnken을 선택합니다. 잡음 요인은 블록으로 분리하고, 순수오차와 곡률 확인이 필요하면 반복과 중심점을 계획하세요.",
      { label: "실험계획법 작업공간 열기", href: "/doe" },
    );
  }

  if (/fmea|고장.*형태|ap|조치.*우선|관리계획/i.test(normalized)) {
    return response(
      "FMEA는 공정 흐름과 특성 ID를 기준으로 기능·고장형태·영향·원인·예방·검출 관리를 추적합니다. S/O/D와 조치 우선순위 정책의 버전을 보존하고, 조치 후에는 연결된 SPC·MSA 실행을 재검증한 뒤 승인 개정을 남기세요. 점수만으로 조치를 자동 확정하지 않습니다.",
      { label: "FMEA 작업공간 열기", href: "/fmea" },
      evidenceContext,
    );
  }

  if (/dmaic|개선.*프로젝트|프로젝트.*시작|현재.*단계|완료.*기준/i.test(normalized)) {
    return response(
      "DMAIC는 정의에서 문제·고객 요구·범위를 고정하고, 측정에서 데이터와 측정시스템 근거를 확보한 뒤, 분석에서 원인을 검증합니다. 개선에서는 DOE·파일럿으로 해법을 확인하고, 관리에서는 SPC·FMEA·관리계획으로 유지합니다. 각 단계 산출물과 분석 실행 ID를 프로젝트 개정에 연결하세요.",
      { label: "DMAIC 프로젝트 작업공간 열기", href: "/home/dmaic/project" },
      evidenceContext,
    );
  }

  if (/설정|파라미터|값.*조정/i.test(normalized)) {
    return response(
      `${contextName}의 설정값은 데이터 구조와 탐지 목적에 따라 달라집니다. 기본값을 먼저 실행한 뒤 가정, 표본 크기, 관리한계와 경고를 함께 검토하세요. 값을 변경할 때는 변경 이유와 기대 효과를 기록하고 새 분석 실행으로 비교해야 합니다. 구체적인 분석명과 조정하려는 값을 알려주면 해당 계약으로 좁혀 안내할 수 있습니다.`,
      undefined,
      evidenceContext,
    );
  }

  if (/이상|신호|조치|다음|절차/i.test(normalized)) {
    return response(
      `${contextName} 결과는 신호 확인 → 데이터·측정 오류 배제 → 현장 원인 확인 → 책임자와 조치 기록 → 재분석 및 관리계획 반영 순으로 사용하세요. 결과 화면의 분석 실행 ID와 데이터 개정을 보존하면 조치 전후 근거를 추적할 수 있습니다.`,
      pathname.startsWith("/home/dmaic") ? { label: "프로젝트 근거 검토", href: "/home/dmaic/project" } : undefined,
      evidenceContext,
    );
  }

  if (/근거|연결|개정|실행|보고서/i.test(normalized)) {
    return response(
      `${contextName}의 결과는 분석 실행 ID, 입력 데이터 개정, 설정값, 엔진 버전과 함께 보존해야 합니다. DMAIC 문서나 FMEA 관리계획에는 해당 실행을 링크하고, 재분석 시 기존 근거를 덮어쓰지 말고 새 개정으로 남기세요.`,
      { label: "결과 및 보고서 보기", href: "/catalog/reports" },
      evidenceContext,
    );
  }

  if (/언제|선택|추천|차이|유형|방법/i.test(normalized)) {
    return response(
      `${contextName}에서는 먼저 판단 목적, 데이터 유형, 표본 구성과 시간 순서를 구분합니다. 공정 안정성은 SPC, 원인·효과 검증과 최적화는 DOE, 위험과 관리 추적은 FMEA, 여러 산출물을 하나의 개선 과제로 묶을 때는 DMAIC를 선택하세요. 데이터 구조를 알려주면 분석법까지 좁힐 수 있습니다.`,
      { label: "분석 선택 도우미 열기", href: "/analyses" },
    );
  }

  return response(
    `${contextName} 문맥에서 질문을 확인했습니다. 데이터 유형, 부분군 크기, 현재 단계와 기대하는 판단을 함께 알려주면 사용 절차·분석 방법·설정값·후속 조치 중 필요한 내용을 구체적으로 안내하겠습니다.`,
  );
}
