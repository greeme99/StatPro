# I-MR 결과 출력 증분 근거 기록

## 범위

- 구현: 개별값(I)·이동범위(MR) 이중 관리도 결과의 인쇄용 HTML, SpreadsheetML Excel, 결합 PNG, 접근 가능한 결합 SVG
- 보존 식별값: Analysis Run ID, 엔진 버전, 입력 SHA-256 digest, I/MR 관리 한계, 관측별 신호와 규칙
- UI 경로: 결과 화면의 `결과 출력(Export)` 메뉴

## 산출물 계약

- SVG는 I와 MR 두 차트를 하나의 문서에 결정적으로 투영한다. 각 패널에는 CL/UCL/LCL, 관측 점, 신호와 관측 순서가 포함된다.
- PNG는 동일 SVG를 브라우저 Canvas에서 1200×900으로 변환한 파생 파일이다. SVG가 원본 시각 산출물이다.
- Excel은 요약과 관측 결과 시트를 제공한다. 각 행은 개별값, 이동범위, 결합 신호 상태와 규칙 ID를 보존한다.
- PDF는 별도 PDF 엔진이 아니라 인쇄 전용 HTML을 새 브라우저 창에서 열고 사용자의 브라우저 인쇄 대화상자로 저장하거나 인쇄한다.

## 검증

- `web/src/imrExport.test.ts`: I/MR 이중 SVG 제목·Run ID, Excel 시트, 인쇄 HTML의 입력 digest와 provenance를 검증했다.
- `npm run test -- --run src/imrExport.test.ts src/components/ResultExportMenu.test.ts`: 2개 파일, 3개 테스트 통과.
- `npm run build`: TypeScript 검사 및 Vite 프로덕션 빌드 통과. 번들 크기 경고는 기존 공통 차트 청크의 경고이며 이번 출력 모듈이 새 동적 차트를 추가하지는 않는다.

## 근거와 제한

- 이 증분은 StatPro ResultBundle의 저장된 I-MR 수치와 공개 통계 근거를 출력 형식으로 투영한다. Minitab 14의 그래픽 엔진, 화면 배치, 파일 포맷 또는 PDF 출력물과의 동등성을 주장하지 않는다.
- I-MR 계산·규칙 근거는 `docs/07.StatPro_Test_Report.md`와 기존 ResultBundle provenance에 분리 보존한다.
- I-MR·Xbar-R·Xbar-S 외 SPC 관리도의 PDF·Excel·PNG·SVG 출력은 아직 지원하지 않는다.
