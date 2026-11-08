# SPC 공통 차트 이미지 출력

## 관찰

- 기존 I-MR, Xbar-R, Xbar-S는 각 분석별 전용 SVG와 Canvas PNG 변환을 제공했다.
- EWMA, CUSUM, 계수형(p/np/c/u·Laney P′/U′), 희귀사건(G/T)의 ResultBundle에는 `tables.chart_points`에 관측값·중심선·상하 관리한계·신호가 저장된다.

## 구현

- `web/src/spcChartExport.ts`는 위 ResultBundle 계약을 검증해 화면 DOM이 아닌 저장된 차트 데이터로 SVG를 만든다.
- SVG에는 Run ID, 관측 수, 신호 수, 중심선·상하 관리한계, 각 계열의 접근 가능한 제목과 설명을 포함한다.
- PNG는 그 결정론적 SVG를 브라우저 Canvas에서 변환한 파생 파일이다.
- CUSUM은 상측·하측 누적합을 별도 계열로 보존한다. 속성·희귀사건은 부분군별 관리한계를 그대로 사용한다.

## 검증과 한계

- `web/src/components/ResultExportMenu.test.ts`는 저장된 p 관리도 ResultBundle에서 독립 SVG가 생성되고 Run ID가 보존되는지 검증한다.
- `npm run build`는 TypeScript 계약과 실제 번들을 검증한다.
- 이 증분은 전용 PDF·Excel 보고서나 공정능력·MSA 차트 이미지를 제공하지 않는다.
