# CUSUM 관리도 증분 근거 기록

## Minitab 14 정적 관찰

- 대상 파일: `C:\Program Files (x86)\MINITAB 14\Mtb14GraphicsCmnd.dll`
- 원본 바이트의 제한 문자열 검색에서 다음 C++ 이름 후보를 관찰했다.
  - `CmQCCUSUMCmnd`, `CmQCCUSUMCompute`, `CmQCCUSUMState`
  - `CmQCCUSUMCompute::mFindCenterLine`, `CmQCCUSUMCompute::mFindPlotPoints`, `mCalcSLimits`
  - `CmQCCUSUMState::mGetH`, `mSetH`, `mGetK`, `mSetK`, `mGetTarget`, `mSetTarget`
  - `CmQCCUSUMState::mGetFIR`, `mSetFIR`, `mIsFIR`, `mIsReset`
  - `CmQChartState::mStoreCUSUMPlotPoints`

이 관찰은 설치된 Minitab 14 그래픽 명령 DLL에 CUSUM으로 해석 가능한 명령·계산·상태·H/K/target/FIR/reset 후보 이름이 존재한다는 사실만 뒷받침한다. 수식, 기본값, 단위, 초기화·reset 동작, 대화상자, 세션 명령 또는 런타임 수치의 동등성을 증명하지 않는다. 이번 증분에는 semantic Evidence ID가 없으므로 함수 의미로 승격하지 않는다.

## 공개 통계 근거

- NIST/SEMATECH CUSUM Control Charts와 tabular recurrence:
  - <https://www.itl.nist.gov/div898/handbook/pmc/section3/pmc323.htm>
- NIST/SEMATECH CUSUM Average Run Length와 표준화:
  - <https://www.itl.nist.gov/div898/handbook/pmc/section3/pmc3231.htm>
- NIST Dataplot의 양측 표준화 누적합 정의:
  - <https://www.itl.nist.gov/div898/software/dataplot/refman1/auxillar/cusum.htm>
- 현재 Minitab CUSUM 수식 문서는 H/K/FIR 개념의 독립 교차검증 자료로만 사용했다.
  - <https://support.minitab.com/en-us/minitab/help-and-how-to/quality-and-process-improvement/control-charts/how-to/time-weighted-charts/cusum-chart/methods-and-formulas/methods-and-formulas/>

현재 Minitab 문서는 Minitab 14 내부 구현의 증거가 아니며 제품 버전 간 기본값·계산 경로의 동일성을 가정하지 않는다.

## StatPro 독립 구현

- 개별 관측값을 `z_i = (x_i-target)/sigma`로 표준화한다.
- 상측 누적합은 `C+_i = max(0, C+_(i-1) + z_i - k)`이다.
- 하측 크기는 `C-_magnitude,i = max(0, C-_magnitude,(i-1) - z_i - k)`이며 차트에는 음수로 표시한다.
- 상측이 `h`보다 크거나 하측이 `-h`보다 작을 때 방향별 신호를 낸다. 두 누적합의 초기값은 0이다.
- 입력 경계는 관측값 2개 이상, `k >= 0`, `0 < h <= 100`, `sigma > 0`이다.
- 과거 평균·sigma를 주면 그대로 사용한다. 생략하면 현재 평균과 `MRbar/1.128`을 사용하되 prospective monitoring의 기준 오염 위험을 경고한다.
- 결과는 공통 `ResultBundle`에 관측값·표준화 값·상하 누적합·판정구간·방향별 신호, k/h, 기준 모수 출처와 provenance를 보존한다.

이는 공개 수학의 clean-room 구현이며 Minitab 내부 코드·리소스·화면의 번역 또는 복제가 아니다.

## 검증 결과

- 공개 표준화 양측 tabular recurrence의 수계산 fixture 통과
- 상측·하측 작은 이동 누적과 판정구간 초과 시점 통과
- 과거/추정 모수 출처와 k/h/sigma/zero-variation 경계 통과
- API·CLI·React 입력/결과·접근 가능한 표 계약 통과
- 전체 Python 158/158, Vitest 49/49, Ruff, TypeScript/Vite production build 통과
- 대표 10,000개 관측 측정: cold wall 272.474ms/CPU 281.250ms, warm 20회 평균 wall 304.751ms/CPU 304.688ms, Python 추적 할당 peak 8,815,449 bytes, ResultBundle JSON 2,267,987 bytes

## 남은 미확인·후속 범위

- Minitab 14 CUSUM 대화상자, 실제 기본값, 세션 명령과 수치 비교
- 부분군 CUSUM, stage별 기준 모수, 결측·가변 부분군 처리
- FIR/headstart, signal 후 reset, one-sided CUSUM, V-mask
- ARL/alpha-beta 기반 k/h 설계와 run-length 시뮬레이션
- MTW/MPJ 입력·결과 직렬화
- Laney P′/U′ 및 희귀사건 관리도
