# Xbar-S 관리도 증분 근거 기록

## Minitab 14 정적 관찰

- 대상 파일: `C:\Program Files (x86)\MINITAB 14\Mtb14GraphicsCmnd.dll`
- REA `open_binary`가 확인한 SHA-256: `f0974fd9a3d0514753587401f9488f8e2d6e67e74f8f9ed1fd386057e9b8320e`
- 원본 바이트의 제한 문자열 검색에서 다음 C++ 이름 후보를 관찰했다.
  - `CmQCSChartCmnd`, `CmQCSChartCompute`, `CmQCSChartState`
  - `CmQCXBarCmnd`, `CmQCXBarCompute`, `CmQCXBarState`
  - `mGetPooledStDev`
  - `CmQCSChartCompute::mGetCenterCorrectionFactor`
  - `CmQCSChartCompute::mGetLimitCorrectionFactor`

이 관찰은 설치된 Minitab 14 그래픽 명령 DLL에 Xbar/S 계열로 해석 가능한 명령·계산·상태 및 보정계수 후보 이름이 존재한다는 사실만 뒷받침한다. 수식, 상수표, 부분군 크기 기본값, 대화상자, 세션 명령, 결과 열 또는 런타임 수치의 동등성을 증명하지 않는다.

이번 증분에서 Ghidra provider는 구성 경로의 `Ghidra/application.properties`와 headless 실행 파일을 유효한 설치로 확인하지 못해 semantic Evidence ID를 새로 만들지 못했다. 따라서 위 이름은 원본 바이트의 제한 정적 관찰이며, 함수 의미로 승격하지 않는다.

## 공개 통계 근거

- NIST/SEMATECH Xbar and S Control Charts:
  - <https://www.itl.nist.gov/div898/handbook/pmc/section3/pmc321.htm>
- NIST/SEMATECH control-chart constants and c4 background:
  - <https://www.itl.nist.gov/div898/handbook/pmc/section3/pmc32.htm>
- 현재 Minitab Xbar-S 개요와 수식은 독립 교차검증 자료로만 사용했다.
  - <https://support.minitab.com/en-us/minitab/help-and-how-to/quality-and-process-improvement/control-charts/how-to/variables-charts-for-subgroups/xbar-s-chart/before-you-start/overview/>
  - <https://support.minitab.com/en-us/minitab/help-and-how-to/quality-and-process-improvement/control-charts/how-to/variables-charts-for-subgroups/xbar-s-chart/methods-and-formulas/xbar-chart/>
  - <https://support.minitab.com/en-us/minitab/help-and-how-to/quality-and-process-improvement/control-charts/how-to/variables-charts-for-subgroups/xbar-s-chart/methods-and-formulas/estimating-sigma/>

현재 Minitab 문서는 Minitab 14 내부 구현의 증거가 아니며 제품 버전 간 기본값·계산 경로의 동일성을 가정하지 않는다.

## StatPro 독립 구현

- 각 부분군은 Bessel 보정을 사용한 표본 표준편차 `s_i`를 계산한다.
- `Sbar`는 부분군 표준편차의 산술평균이다.
- `c4 = sqrt(2/(n-1)) * Gamma(n/2) / Gamma((n-1)/2)`이다.
- 공정 표준편차 추정치는 `sigma_hat = Sbar / c4`이다.
- Xbar 한계는 `Xbarbar ± 3 * sigma_hat / sqrt(n)`이며 `A3 = 3/(c4*sqrt(n))`로도 표현한다.
- S 한계는 `B3*Sbar`, `B4*Sbar`이고 `B3 = max(0, 1 - 3*sqrt(1-c4^2)/c4)`, `B4 = 1 + 3*sqrt(1-c4^2)/c4`이다.
- Xbar에는 Nelson Test 1–8, S에는 Test 1–4만 적용한다. `basic`은 Test 1만 평가한다.
- 일정한 2–100 크기의 부분군만 허용한다. 크기 9 미만은 계산을 허용하되 Xbar-R을 먼저 검토하도록 경고한다.
- 결과는 공통 `ResultBundle`에서 부분군 평균·표준편차, 두 관리한계, 신호, c4/A3/B3/B4, 추정 sigma, provenance를 보존한다.

이는 공개 수학의 clean-room 구현이며 Minitab 내부 코드·리소스·화면의 번역 또는 복제가 아니다.

## 검증 결과

- 공개 c4/A3/B3/B4 수계산 fixture 통과
- 불균등 부분군·지원 범위·유한 숫자 경계 통과
- Xbar Test 1–8/S Test 1–4 적용 범위 통과
- API·CLI·React 입력/결과 계약 통과
- 전체 Python 148/148, Vitest 45/45, Ruff, TypeScript/Vite production build 통과
- 대표 100개 부분군×10개 측정: cold wall 31.511ms/CPU 31.250ms, warm 100회 평균 wall 49.729ms/CPU 47.031ms, Python 추적 할당 peak 2,903,714 bytes, ResultBundle JSON 14,037 bytes

## 남은 미확인·후속 범위

- Minitab 14 Xbar-S 대화상자, 기본 규칙, 세션 명령과 수치 비교
- 과거 중심선·sigma, stage, 결측, 불균등 부분군, 가중 한계
- 부분군 pooled 표준편차 등 대체 sigma 추정법과 사용자 상수
- MTW/MPJ 입력·결과 직렬화
- EWMA, CUSUM, Laney P′/U′ 및 희귀사건 관리도
