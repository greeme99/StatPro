# SPC Xbar-R 결과 조사·출력 증거

## 범위

- 대상: `spc.xbar_r` ResultBundle의 전용 결과 UI와 로컬 출력
- 구현: Xbar/R 이중 관리도, 부분군 표, 규칙별 관리이탈 조사표, PDF 인쇄 HTML,
  SpreadsheetML Excel, 결합 PNG/SVG
- 비범위: Minitab 14의 화면 배치·그래픽 엔진·파일 포맷 복제, 다른 SPC 관리도의 동일 출력

## 보존 계약

- 화면과 출력은 엔진이 소유한 `tables.limits`, `plots.*.values`, `plots.*.signals`,
  `plots.*.rule_signals`를 재해석 없이 사용한다.
- 규칙 사건의 0-based `involved_indices`는 표시 경계에서만 1-based 부분군 번호로 바꾼다.
- 보고서와 Excel에 Run ID, 엔진 버전, 입력 SHA-256, 부분군 크기, 규칙 세트,
  A2/D3/D4와 공개 근거를 포함한다.
- PNG는 동일한 결정론적 결합 SVG를 브라우저 Canvas로 변환한다. SVG가 원본 차트 산출물이다.
- PDF는 별도 PDF 생성 라이브러리 없이 의미 기반 HTML을 새 창에서 열고 브라우저의
  `PDF로 저장 또는 인쇄` 기능을 사용한다.

## 검증

- `web`: Vitest 3 files, 69 tests 통과
- `web`: `tsc -b && vite build` 통과
- 알려진 비차단 경고: 초기 앱 번들이 500 kB를 초과한다. Recharts 차트는 기존처럼 지연 로딩된다.

## 근거 구분

- 공개 통계 근거와 Xbar-R 계산은 기존 엔진·provenance 계약이 소유한다.
- 이번 증분의 HTML·Excel·SVG/PNG 레이아웃은 StatPro 고유 UI/보고서 설계다.
- Minitab 14 정적 증거는 기능 후보 존재만 뒷받침하며, 출력 형식이나 UI 동등성을 증명하지 않는다.
