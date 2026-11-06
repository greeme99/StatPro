# 분석 선택 도우미 구현 근거

## 범위

- 라우트: `/analyses`
- 진입점: 전역 사이드 메뉴 `분석 선택 (Analysis Selection)` 및 AI Copilot 일반 선택 안내
- 목적: 사용자가 현장 판단 목적과 데이터 구조를 먼저 구분한 뒤 현재 실제 실행 가능한 분석 작업공간으로 이동하도록 지원

## 결정 규칙

- 연속형: 개별값→I-MR, 작은 부분군→Xbar-R, 큰 부분군→Xbar-S, 작은 지속 이동→EWMA
- 부적합품: 검사 수 변동→p, 검사 수 고정→np
- 결점 수: 기회·단위 수 변동→u, 고정→c
- 희귀사건: 사건 사이 기회 수→G, 경과 시간→T
- 다수 인자 선별→Plackett–Burman, 곡률·최적화→Box–Behnken
- 공정 위험→PFMEA, 개선 프로젝트 운영→DMAIC

추천은 자동 분석 실행이나 설정 변경이 아니다. 화면은 선택 이유, 필수 입력, 사전 확인사항과 실행 링크를 표시하며 최종 판단은 사용자가 수행한다.

## 검증

- `cd web; npm run check`
- Vitest: 7개 파일, 96개 테스트 통과
- TypeScript 프로젝트 빌드 및 Vite 프로덕션 빌드 통과
- 선택 화면은 별도 lazy chunk(`AnalysisSelectionPage`)로 생성되어 초기 라우트 번들에 포함되지 않는다.
