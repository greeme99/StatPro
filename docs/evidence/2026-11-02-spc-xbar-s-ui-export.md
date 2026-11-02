# Xbar-S 결과 출력 증분 근거 기록

## 범위

- 구현: Xbar/S 이중 관리도 결과의 인쇄용 HTML, SpreadsheetML Excel, 결합 PNG, 접근 가능한 결합 SVG
- 보존 식별값: Analysis Run ID, 엔진 버전, 입력 SHA-256 digest, 부분군 크기, 추정 sigma, 관리 한계와 신호
- UI 경로: 결과 화면의 `결과 출력(Export)` 메뉴

## 산출물 계약

- SVG는 부분군 평균(Xbar)과 부분군 표준편차(S)를 한 문서에 결정적으로 투영한다. 각 차트에는 CL/UCL/LCL, 점, 신호와 부분군 번호가 포함된다.
- PNG는 동일 SVG를 브라우저 Canvas에서 1200×900으로 변환한 파생 파일이다. SVG가 원본 시각 산출물이다.
- Excel은 요약과 부분군 결과 시트를 제공한다. 각 행은 평균, 표준편차, 신호 기반 상태를 보존한다.
- PDF는 별도 PDF 엔진이 아니라 인쇄 전용 HTML을 새 브라우저 창에서 열고 사용자의 브라우저 인쇄 대화상자로 저장하거나 인쇄한다.

## 검증

- `web/src/xbarSExport.test.ts`: Xbar/S 이중 SVG 제목·추정 sigma·Run ID, Excel 시트, 인쇄 HTML의 입력 digest와 provenance를 검증했다.
- `npm run test -- --run src/xbarSExport.test.ts src/components/ResultExportMenu.test.ts`: 2개 파일, 3개 테스트 통과.
- `npm run build`: TypeScript 검사 및 Vite 프로덕션 빌드 통과. 번들 크기 경고는 기존 공통 차트 청크의 경고이며 이번 출력 모듈이 새 동적 차트를 추가하지는 않는다.

## 근거와 제한

- 이 증분은 StatPro ResultBundle의 저장된 Xbar-S 수치와 공개 통계 근거를 출력 형식으로 투영한다. Minitab 14의 그래픽 엔진, 화면 배치, 파일 포맷 또는 PDF 출력물과의 동등성을 주장하지 않는다.
- Minitab 14 정적 관찰과 Xbar-S 계산 근거는 [2026-10-25-xbar-s-control-chart.md](2026-10-25-xbar-s-control-chart.md)에 별도로 보존한다.
- 다른 SPC 관리도의 PDF·Excel·PNG·SVG 출력은 아직 지원하지 않는다.
