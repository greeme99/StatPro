"""Generate high-quality .excalidraw scene files for StatPro workflows."""

import json
import random
import time
from pathlib import Path


class ExcalidrawBuilder:

  def __init__(self):
    self.elements = []
    self._seed_gen = 1000

  def _next_seed(self):
    self._seed_gen += 1
    return self._seed_gen

  def add_box(
      self,
      elem_id,
      x,
      y,
      w,
      h,
      title,
      subtitle='',
      bg='#ffffff',
      stroke='#1e293b',
      stroke_width=2,
      roundness=3,
      is_container=False,
  ):
    # Box rectangle
    rect = {
        'id': elem_id,
        'type': 'rectangle',
        'x': x,
        'y': y,
        'width': w,
        'height': h,
        'angle': 0,
        'strokeColor': stroke,
        'backgroundColor': bg,
        'fillStyle': 'solid',
        'strokeWidth': stroke_width,
        'strokeStyle': 'solid',
        'roughness': 1,
        'opacity': 100,
        'groupIds': [],
        'frameId': None,
        'roundness': {'type': roundness} if roundness else None,
        'seed': self._next_seed(),
        'version': 1,
        'versionNonce': random.randint(1000, 999999),
        'isDeleted': False,
        'boundElements': [],
        'updated': int(time.time() * 1000),
        'link': None,
        'locked': False,
    }
    self.elements.append(rect)

    if title:
      text_content = f'{title}\n{subtitle}' if subtitle else title
      text_elem = {
          'id': f'{elem_id}_txt',
          'type': 'text',
          'x': x + 10,
          'y': y + (12 if is_container else (h / 2 - (18 if subtitle else 10))),
          'width': w - 20,
          'height': h,
          'angle': 0,
          'strokeColor': stroke,
          'backgroundColor': 'transparent',
          'fillStyle': 'solid',
          'strokeWidth': 1,
          'strokeStyle': 'solid',
          'roughness': 0,
          'opacity': 100,
          'groupIds': [],
          'frameId': None,
          'roundness': None,
          'seed': self._next_seed(),
          'version': 1,
          'versionNonce': random.randint(1000, 999999),
          'isDeleted': False,
          'boundElements': [],
          'updated': int(time.time() * 1000),
          'link': None,
          'locked': False,
          'text': text_content,
          'fontSize': 16 if is_container else 14,
          'fontFamily': 1,
          'textAlign': 'center',
          'verticalAlign': 'top' if is_container else 'middle',
          'baseline': 14,
          'containerId': elem_id if not is_container else None,
          'originalText': text_content,
          'lineHeight': 1.3,
      }
      self.elements.append(text_elem)
      if not is_container:
        rect['boundElements'].append({'type': 'text', 'id': f'{elem_id}_txt'})
    return elem_id

  def add_arrow(
      self,
      start_id,
      end_id,
      x1,
      y1,
      x2,
      y2,
      label='',
      stroke='#64748b',
      dashed=False,
      stroke_width=2,
  ):
    arrow_id = f'arr_{start_id}_{end_id}_{random.randint(100, 999)}'
    dx = x2 - x1
    dy = y2 - y1

    arrow = {
        'id': arrow_id,
        'type': 'arrow',
        'x': x1,
        'y': y1,
        'width': abs(dx),
        'height': abs(dy),
        'angle': 0,
        'strokeColor': stroke,
        'backgroundColor': 'transparent',
        'fillStyle': 'solid',
        'strokeWidth': stroke_width,
        'strokeStyle': 'dashed' if dashed else 'solid',
        'roughness': 1,
        'opacity': 100,
        'groupIds': [],
        'frameId': None,
        'roundness': {'type': 2},
        'seed': self._next_seed(),
        'version': 1,
        'versionNonce': random.randint(1000, 999999),
        'isDeleted': False,
        'boundElements': [],
        'updated': int(time.time() * 1000),
        'link': None,
        'locked': False,
        'points': [[0, 0], [dx, dy]],
        'lastCommittedPoint': None,
        'startBinding': {'elementId': start_id, 'focus': 0, 'gap': 6},
        'endBinding': {'elementId': end_id, 'focus': 0, 'gap': 6},
        'startArrowhead': None,
        'endArrowhead': 'arrow',
    }
    self.elements.append(arrow)

    if label:
      mx = x1 + dx / 2 - 40
      my = y1 + dy / 2 - 16
      lbl = {
          'id': f'{arrow_id}_lbl',
          'type': 'text',
          'x': mx,
          'y': my,
          'width': 100,
          'height': 20,
          'angle': 0,
          'strokeColor': stroke,
          'backgroundColor': 'transparent',
          'fillStyle': 'solid',
          'strokeWidth': 1,
          'strokeStyle': 'solid',
          'roughness': 0,
          'opacity': 100,
          'groupIds': [],
          'frameId': None,
          'roundness': None,
          'seed': self._next_seed(),
          'version': 1,
          'versionNonce': random.randint(1000, 999999),
          'isDeleted': False,
          'boundElements': [],
          'updated': int(time.time() * 1000),
          'link': None,
          'locked': False,
          'text': label,
          'fontSize': 12,
          'fontFamily': 1,
          'textAlign': 'center',
          'verticalAlign': 'middle',
          'baseline': 10,
          'containerId': None,
          'originalText': label,
          'lineHeight': 1.2,
      }
      self.elements.append(lbl)

    return arrow_id

  def to_json(self):
    return {
        'type': 'excalidraw',
        'version': 2,
        'source': 'https://excalidraw.com',
        'elements': self.elements,
        'appState': {
            'gridSize': 20,
            'viewBackgroundColor': '#f8fafc',
            'theme': 'light',
        },
        'files': {},
    }


def build_overall_workflow():
  b = ExcalidrawBuilder()

  # Main Title
  b.add_box(
      'main_title',
      40,
      20,
      1420,
      50,
      'StatPro 전체 표준 워크플로우 (End-to-End Workflow)',
      '홈 → 작업공간 → 데이터 준비 → 분석 실행 → 결과 검토 → 리포트'
      ' 출력/보존',
      bg='#1e293b',
      stroke='#0f172a',
      stroke_width=2,
      roundness=3,
  )

  # Columns / Phases
  col_w = 260
  gap = 35
  top_y = 90
  col_h = 580

  phases = [
      (
          'p1',
          '1. 진입 & 작업공간',
          '홈 / 작업공간 선택',
          '#e0f2fe',
          '#0284c7',
      ),  # Light Sky
      (
          'p2',
          '2. 데이터 수집 & 정제',
          'CSV / Worksheet',
          '#f1f5f9',
          '#475569',
      ),  # Slate
      (
          'p3',
          '3. 분석 구성 & 실행',
          '통계 코어 엔진',
          '#ede9fe',
          '#6366f1',
      ),  # Indigo
      (
          'p4',
          '4. 결과 검토 & 진단',
          'ResultBundle & 차트',
          '#dcfce7',
          '#10b981',
      ),  # Green
      (
          'p5',
          '5. 출력 & 증거 연계',
          '보고서 / Handoff',
          '#fef3c7',
          '#f59e0b',
      ),  # Amber
  ]

  for i, (pid, ptitle, psub, pbg, pstroke) in enumerate(phases):
    col_x = 40 + i * (col_w + gap)
    b.add_box(
        pid,
        col_x,
        top_y,
        col_w,
        col_h,
        ptitle,
        psub,
        bg=pbg,
        stroke=pstroke,
        stroke_width=2,
        is_container=True,
    )

  # Phase 1: Entry & Workspaces
  b.add_box(
      'node_home',
      60,
      160,
      220,
      60,
      '홈 대시보드 (Home)',
      '최근 실행 / DMAIC 프로젝트 진입',
      bg='#ffffff',
      stroke='#0284c7',
  )
  b.add_box(
      'ws_spc',
      60,
      240,
      220,
      50,
      'SPC 작업공간 (/spc)',
      '7대 도구 / 관리도 / 공정능력',
      bg='#ffffff',
      stroke='#0284c7',
  )
  b.add_box(
      'ws_doe',
      60,
      310,
      220,
      50,
      'DOE 작업공간 (/doe)',
      '실험 설계 / 반응표면 / 최적화',
      bg='#ffffff',
      stroke='#0284c7',
  )
  b.add_box(
      'ws_fmea',
      60,
      380,
      220,
      50,
      'FMEA 작업공간 (/fmea)',
      'PFMEA 7단계 / 관리계획서',
      bg='#ffffff',
      stroke='#0284c7',
  )
  b.add_box(
      'ws_dmaic',
      60,
      450,
      220,
      50,
      'DMAIC 작업공간 (/home/dmaic)',
      '헌장 / VOC / SIPOC / 원인분석',
      bg='#ffffff',
      stroke='#0284c7',
  )
  b.add_box(
      'ws_data',
      60,
      520,
      220,
      50,
      '데이터 작업공간 (/data)',
      'Dataset 스냅샷 & Worksheet 편집',
      bg='#ffffff',
      stroke='#0284c7',
  )

  # Phase 2: Data Ingestion & Input
  b.add_box(
      'n_csv',
      355,
      170,
      220,
      60,
      'CSV 가져오기 / 입력',
      'UTF-8 인코딩 / 결측치 명시 보존',
      bg='#ffffff',
      stroke='#475569',
  )
  b.add_box(
      'n_snapshot',
      355,
      270,
      220,
      70,
      'Dataset Snapshot',
      '불변 원천 데이터\nSHA-256 Digest 고정',
      bg='#ffffff',
      stroke='#475569',
  )
  b.add_box(
      'n_worksheet',
      355,
      380,
      220,
      80,
      'Worksheet Revision',
      '타입 프로파일링 (수치/범주)\n낙관적 동시성 (ETag)',
      bg='#ffffff',
      stroke='#475569',
  )
  b.add_box(
      'n_bindings',
      355,
      490,
      220,
      60,
      'Input Bindings',
      '요인(X)·반응(Y) 컬럼 매핑',
      bg='#ffffff',
      stroke='#475569',
  )

  # Phase 3: Configuration & Execution
  b.add_box(
      'n_params',
      650,
      170,
      220,
      70,
      '분석 파라미터 구성',
      '알파 위험, 부분군 크기(n)\n관리한계 및 목표 규격 설정',
      bg='#ffffff',
      stroke='#6366f1',
  )
  b.add_box(
      'n_run_req',
      650,
      280,
      220,
      70,
      'Analysis Run 생성',
      'Engine Version 고정\n입력 데이터 Digest 바인딩',
      bg='#ffffff',
      stroke='#6366f1',
  )
  b.add_box(
      'n_stat_core',
      650,
      400,
      220,
      90,
      'StatPro 통계 코어 엔진',
      'DOE ANOVA / 회귀모형\nSPC 한계선 & Nelson 신호\nMSA 교차 Gage R&R',
      bg='#4f46e5',
      stroke='#3730a3',
  )

  # Phase 4: Review & Diagnostics
  b.add_box(
      'n_bundle',
      945,
      170,
      220,
      80,
      'ResultBundle 경계 통과',
      '완전한 재현 가능 객체\n수치 표 + 진단 + 경고 + Digest',
      bg='#ffffff',
      stroke='#10b981',
  )
  b.add_box(
      'n_charts',
      945,
      285,
      220,
      75,
      '시각화 대시보드',
      'Recharts 기반 반응형 차트\nI-MR / Xbar-R / 파레토 / 표면',
      bg='#ffffff',
      stroke='#10b981',
  )
  b.add_box(
      'n_diagnostics',
      945,
      395,
      220,
      80,
      '통계 진단 & 신호 감지',
      'Nelson Rule 1~8 이상 신호\n정규/비정규 공정능력(Cp/Cpk)\n적합도 R² / 잔차 분석',
      bg='#ffffff',
      stroke='#10b981',
  )
  b.add_box(
      'n_next_action',
      945,
      505,
      220,
      55,
      '다음 조치 가이드',
      '원인 조사 권고 / 파라미터 조정',
      bg='#ffffff',
      stroke='#10b981',
  )

  # Phase 5: Export & Governance
  b.add_box(
      'n_exp_zip',
      1240,
      165,
      220,
      60,
      'DOE ZIP 내보내기',
      '결정론적 JSON + HTML + CSV',
      bg='#ffffff',
      stroke='#f59e0b',
  )
  b.add_box(
      'n_exp_html',
      1240,
      245,
      220,
      60,
      '브라우저 인쇄 HTML/PDF',
      'I-MR, Xbar-R, Xbar-S 인쇄',
      bg='#ffffff',
      stroke='#f59e0b',
  )
  b.add_box(
      'n_exp_csv',
      1240,
      325,
      220,
      60,
      '수치 데이터 CSV / Excel',
      'SpreadsheetML 호환 원천 필드',
      bg='#ffffff',
      stroke='#f59e0b',
  )
  b.add_box(
      'n_metric_snap',
      1240,
      405,
      220,
      65,
      '품질 지표 스냅샷 (/quality)',
      '불변 경로 연결 지표 보존\n담당자·검토주기·임계치 추적',
      bg='#ffffff',
      stroke='#f59e0b',
  )
  b.add_box(
      'n_evidence',
      1240,
      490,
      220,
      70,
      '불변 증거 참조 (Evidence Ref)',
      'FMEA 조치 근거 연결\nDMAIC 인수인계 문서 보존',
      bg='#f59e0b',
      stroke='#b45309',
  )

  # Connectors (Inter-phase)
  b.add_arrow(
      'node_home',
      'ws_data',
      170,
      220,
      170,
      520,
      label='데이터 준비',
      stroke='#0284c7',
  )
  b.add_arrow(
      'ws_data', 'n_csv', 280, 540, 355, 200, label='가져오기', stroke='#0284c7'
  )
  b.add_arrow(
      'n_csv', 'n_snapshot', 465, 230, 465, 270, label='동결', stroke='#475569'
  )
  b.add_arrow(
      'n_snapshot',
      'n_worksheet',
      465,
      340,
      465,
      380,
      label='개정',
      stroke='#475569',
  )
  b.add_arrow(
      'n_worksheet',
      'n_bindings',
      465,
      460,
      465,
      490,
      label='바인딩',
      stroke='#475569',
  )

  b.add_arrow(
      'n_bindings',
      'n_params',
      575,
      520,
      650,
      205,
      label='입력 데이터 전달',
      stroke='#475569',
  )
  b.add_arrow(
      'n_params',
      'n_run_req',
      760,
      240,
      760,
      280,
      label='옵션 확정',
      stroke='#6366f1',
  )
  b.add_arrow(
      'n_run_req',
      'n_stat_core',
      760,
      350,
      760,
      400,
      label='실행 호출',
      stroke='#6366f1',
  )

  b.add_arrow(
      'n_stat_core',
      'n_bundle',
      870,
      445,
      945,
      210,
      label='결과 생성',
      stroke='#6366f1',
  )
  b.add_arrow(
      'n_bundle',
      'n_charts',
      1055,
      250,
      1055,
      285,
      label='렌더링',
      stroke='#10b981',
  )
  b.add_arrow(
      'n_charts',
      'n_diagnostics',
      1055,
      360,
      1055,
      395,
      label='진단',
      stroke='#10b981',
  )
  b.add_arrow(
      'n_diagnostics',
      'n_next_action',
      1055,
      475,
      1055,
      505,
      label='권고',
      stroke='#10b981',
  )

  b.add_arrow(
      'n_charts',
      'n_exp_html',
      1165,
      320,
      1240,
      275,
      label='인쇄',
      stroke='#10b981',
  )
  b.add_arrow(
      'n_bundle',
      'n_exp_zip',
      1165,
      210,
      1240,
      195,
      label='패키징',
      stroke='#10b981',
  )
  b.add_arrow(
      'n_bundle',
      'n_metric_snap',
      1165,
      240,
      1240,
      435,
      label='스냅샷',
      stroke='#10b981',
  )
  b.add_arrow(
      'n_bundle',
      'n_evidence',
      1165,
      250,
      1240,
      525,
      label='증거 참조',
      stroke='#10b981',
  )

  return b.to_json()


def build_integrated_workflow():
  b = ExcalidrawBuilder()

  # Main Title
  b.add_box(
      'main_title_int',
      40,
      20,
      1450,
      50,
      'StatPro 도메인 간 연계 워크플로우 (Cross-Domain & DMAIC Integration)',
      'DMAIC 품질 혁신 단계를 중심으로 한 DOE · SPC · MSA · FMEA 증거 참조'
      ' 연계 체계',
      bg='#0f172a',
      stroke='#020617',
      stroke_width=2,
      roundness=3,
  )

  col_w = 265
  gap = 30
  top_y = 90
  col_h = 600

  steps = [
      (
          's1',
          '1. 정의 (Define)',
          '프로젝트 방향 & 고객 가치',
          '#f0f9ff',
          '#0284c7',
      ),  # Blue
      (
          's2',
          '2. 측정 (Measure)',
          '측정시스템 & 기준선 분석',
          '#fefce8',
          '#ca8a04',
      ),  # Yellow
      (
          's3',
          '3. 분석 (Analyze)',
          '원인 분석 & 핵심 인자 선별',
          '#fdf2f8',
          '#db2777',
      ),  # Pink
      (
          's4',
          '4. 개선 (Improve)',
          '실험계획 & 최적화 조건',
          '#f0fdf4',
          '#16a34a',
      ),  # Green
      (
          's5',
          '5. 관리 (Control)',
          'FMEA 관리계획 & 실시간 모니터링',
          '#faf5ff',
          '#9333ea',
      ),  # Purple
  ]

  for i, (sid, stitle, ssub, sbg, sstroke) in enumerate(steps):
    col_x = 40 + i * (col_w + gap)
    b.add_box(
        sid,
        col_x,
        top_y,
        col_w,
        col_h,
        stitle,
        ssub,
        bg=sbg,
        stroke=sstroke,
        stroke_width=2,
        is_container=True,
    )

  # Column 1: Define
  b.add_box(
      'd_charter',
      60,
      160,
      225,
      70,
      '프로젝트 헌장 (Charter)',
      '사업 타당성 / 문제 기술서\n목표 수준 / 팀 구성 / 일정',
      bg='#ffffff',
      stroke='#0284c7',
  )
  b.add_box(
      'd_voc',
      60,
      250,
      225,
      70,
      '고객의 소리 (VOC)',
      '요구사항 / 페인포인트 / 기회\n핵심품질특성(CTQ) 도출',
      bg='#ffffff',
      stroke='#0284c7',
  )
  b.add_box(
      'd_sipoc',
      60,
      340,
      225,
      75,
      'SIPOC 공정 맵',
      '공급자-입력-공정-출력-고객\n공정 시작/종료 경계 정의',
      bg='#ffffff',
      stroke='#0284c7',
  )
  b.add_box(
      'd_problem',
      60,
      435,
      225,
      70,
      '문제 정의서',
      '현재 상태 vs 목표 상태 격차\n심각도 / 긴급도 / 업무 영향',
      bg='#ffffff',
      stroke='#0284c7',
  )
  b.add_box(
      'd_stakeholder',
      60,
      525,
      225,
      60,
      '이해관계자 분석',
      '영향도·관심도 매트릭스\n소통 계획 / 우려사항 관리',
      bg='#ffffff',
      stroke='#0284c7',
  )

  # Column 2: Measure
  b.add_box(
      'm_plan',
      355,
      160,
      225,
      75,
      '데이터 수집 계획',
      '핵심 지표 / 표본추출 전략\n측정 방법 / 수집 양식 / 주기',
      bg='#ffffff',
      stroke='#ca8a04',
  )
  b.add_box(
      'm_msa',
      355,
      265,
      225,
      95,
      'MSA: 균형 교차 Gage R&R',
      '측정시스템 변동 평가\n%Study Var / %Tolerance\n측정기 신뢰성 검증',
      bg='#fef08a',
      stroke='#a16207',
      stroke_width=2,
  )
  b.add_box(
      'm_baseline_spc',
      355,
      390,
      225,
      90,
      '기준선 SPC 관리도 실행',
      'I-MR, Xbar-R, Xbar-S\n안정 상태 공정 기준선 확립\n(Analysis Run 바인딩)',
      bg='#ffffff',
      stroke='#ca8a04',
  )
  b.add_box(
      'm_capability',
      355,
      505,
      225,
      80,
      '공정능력 분석 (Cp/Cpk)',
      '정규 / 비정규 공정능력\n기준선 결함률(PPM/Z값)',
      bg='#ffffff',
      stroke='#ca8a04',
  )

  # Column 3: Analyze
  b.add_box(
      'a_pareto',
      650,
      160,
      225,
      80,
      '일반 파레토 분석 (/spc)',
      '80/20 법칙 불량 항목 선별\n누적 기여도 / 손실 비용 순위\n(Analysis Run 기반)',
      bg='#ffffff',
      stroke='#db2777',
  )
  b.add_box(
      'a_fishbone',
      650,
      270,
      225,
      95,
      '6M 특성요인도 (Fishbone)',
      'Man·Machine·Material·\nMethod·Measurement·Mother Nature\n원인 가설 & 증거 참조',
      bg='#ffffff',
      stroke='#db2777',
  )
  b.add_box(
      'a_rca',
      650,
      395,
      225,
      85,
      '근본원인 분석 (RCA)',
      '잠재원인 검증 & 근거 대조\n검증된 핵심 인자(Critical X)\n시정조치 대상 도출',
      bg='#ffffff',
      stroke='#db2777',
  )
  b.add_box(
      'a_defects',
      650,
      510,
      225,
      75,
      '일반 결함 분석 (/defects)',
      '체크 시트 연계 / DPMO 산출\n단위 손실 & 위험 우선순위',
      bg='#ffffff',
      stroke='#db2777',
  )

  # Column 4: Improve
  b.add_box(
      'i_doe_design',
      945,
      160,
      225,
      85,
      '실험계획법 (DOE 설계)',
      '완전요인 (Full Factorial)\n일부요인 (Fractional 2-level)\nPlackett-Burman 선별 설계',
      bg='#ffffff',
      stroke='#16a34a',
  )
  b.add_box(
      'i_doe_analysis',
      945,
      275,
      225,
      85,
      '실험 데이터 분석 & 모형화',
      '주효과 & 교호작용 ANOVA\n효과 파레토 차트 / 잔차 검정\n중심합성(CCD) / Box-Behnken',
      bg='#ffffff',
      stroke='#16a34a',
  )
  b.add_box(
      'i_optimizer',
      945,
      390,
      225,
      95,
      '반응표면 & 다중응답 최적화',
      '2차 응답표면 격자/등고선\n만족도 함수 (Desirability)\n최적 공정 레시피 확정',
      bg='#bbf7d0',
      stroke='#15803d',
      stroke_width=2,
  )
  b.add_box(
      'i_pilot',
      945,
      515,
      225,
      70,
      '개선안 선정 & 파일럿 계획',
      'Solution Selection Matrix\n파일럿 실행 및 효과성 검증',
      bg='#ffffff',
      stroke='#16a34a',
  )

  # Column 5: Control
  b.add_box(
      'c_fmea_cp',
      1240,
      160,
      225,
      95,
      'FMEA 관리계획서 (Control Plan)',
      '공정 흐름 → 고장 모드 → AP 평가\n핵심 관리 특성 정의\n측정/검사/반응 방법 명시',
      bg='#f3e8ff',
      stroke='#7e22ce',
      stroke_width=2,
  )
  b.add_box(
      'c_spc_live',
      1240,
      285,
      225,
      85,
      'SPC 실시간 관리도 모니터링',
      'I-MR / Xbar-R / EWMA / CUSUM\n관리한계선(UCL/LCL) 감시\n이상 신호 감지(Nelson Rules)',
      bg='#ffffff',
      stroke='#9333ea',
  )
  b.add_box(
      'c_dashboard',
      1240,
      400,
      225,
      85,
      '품질 대시보드 (/quality)',
      '불변 ResultBundle 수치 경로 연결\n핵심 지표 스냅샷 모니터링\n경고/위험 임계치 & 담당자',
      bg='#ffffff',
      stroke='#9333ea',
  )
  b.add_box(
      'c_handoff',
      1240,
      515,
      225,
      70,
      '관리 인수인계 (Control Handoff)',
      '현장 책임자 인계 / 반응 계획\n정기 검토 주기 & 표준화 보존',
      bg='#ffffff',
      stroke='#9333ea',
  )

  # Major Stage Connectors (Big Flow)
  b.add_arrow(
      'd_sipoc',
      'm_plan',
      285,
      375,
      355,
      200,
      label='CTQ 및 공정경계 전달',
      stroke='#0284c7',
      stroke_width=3,
  )
  b.add_arrow(
      'm_baseline_spc',
      'a_pareto',
      580,
      435,
      650,
      200,
      label='산포 데이터 인계',
      stroke='#ca8a04',
      stroke_width=3,
  )
  b.add_arrow(
      'a_rca',
      'i_doe_design',
      875,
      435,
      945,
      200,
      label='검증된 인자(X) 최적화',
      stroke='#db2777',
      stroke_width=3,
  )
  b.add_arrow(
      'i_optimizer',
      'c_fmea_cp',
      1170,
      435,
      1240,
      210,
      label='최적 레시피 반영',
      stroke='#16a34a',
      stroke_width=3,
  )

  # Cross-Domain Evidence References (Feedback & Traceability Loops)
  b.add_arrow(
      'm_msa',
      'c_fmea_cp',
      465,
      265,
      1240,
      180,
      label='[Evidence Ref] 측정시스템 적합성 증적',
      stroke='#0284c7',
      dashed=True,
  )
  b.add_arrow(
      'c_fmea_cp',
      'c_spc_live',
      1350,
      255,
      1350,
      285,
      label='관리항목 모니터링',
      stroke='#9333ea',
  )
  b.add_arrow(
      'c_spc_live',
      'c_fmea_cp',
      1240,
      330,
      1170,
      330,
      label='[Evidence Ref] 관리이탈 발생 시 FMEA 권고조치 피드백',
      stroke='#dc2626',
      dashed=True,
  )
  b.add_arrow(
      'c_spc_live',
      'c_dashboard',
      1350,
      370,
      1350,
      400,
      label='지표 스냅샷',
      stroke='#9333ea',
  )
  b.add_arrow(
      'c_dashboard',
      'c_handoff',
      1350,
      485,
      1350,
      515,
      label='운영 안정화',
      stroke='#9333ea',
  )

  return b.to_json()


if __name__ == '__main__':
  overall_data = build_overall_workflow()
  p_overall = Path(r'D:\Workspace\StatPro\sav.loc\diagrams\statpro-overall-workflow.excalidraw')
  p_overall.write_text(json.dumps(overall_data, indent=2, ensure_ascii=False), encoding='utf-8')
  print(f'Written {p_overall.name} ({len(overall_data["elements"])} elements)')

  int_data = build_integrated_workflow()
  p_int = Path(r'D:\Workspace\StatPro\sav.loc\diagrams\statpro-integrated-workflow.excalidraw')
  p_int.write_text(json.dumps(int_data, indent=2, ensure_ascii=False), encoding='utf-8')
  print(f'Written {p_int.name} ({len(int_data["elements"])} elements)')

