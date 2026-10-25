# EWMA 관리도 증분 근거 기록

## Minitab 14 정적 관찰

- 대상 파일: `C:\Program Files (x86)\MINITAB 14\Mtb14GraphicsCmnd.dll`
- 원본 바이트의 제한 문자열 검색에서 다음 C++ 이름 후보를 관찰했다.
  - `CmQCEWMACmnd`, `CmQCEWMACompute`, `CmQCEWMAState`
  - `CmQCEWMACompute::mFindCenterLine`, `CmQCEWMACompute::mFindPlotPoints`
  - `CmQCEWMAState::mGetWeight`, `CmQCEWMAState::mSetWeight`
  - `CmQCEWMACompute::mCalcSLimits`, `mDoEWMA`

이 관찰은 설치된 Minitab 14 그래픽 명령 DLL에 EWMA로 해석 가능한 명령·계산·상태·가중치·한계 후보 이름이 존재한다는 사실만 뒷받침한다. 수식, 기본 가중치, 한계 폭, 시작 시점 처리, 대화상자, 세션 명령 또는 런타임 수치의 동등성을 증명하지 않는다. 같은 DLL의 MEWMA 후보는 다변량 기능일 수 있으므로 이번 단변량 EWMA 근거에 혼합하지 않았다.

이번 증분에서 구성된 Ghidra 경로는 `Ghidra/application.properties`, headless launcher와 native decompiler 검사를 통과하지 못해 semantic Evidence ID를 만들지 못했다. 따라서 위 이름은 원본 바이트의 제한 정적 관찰이며 함수 의미로 승격하지 않는다.

## 공개 통계 근거

- NIST/SEMATECH EWMA Control Charts:
  - <https://www.itl.nist.gov/div898/handbook/pmc/section3/pmc324.htm>
- NIST/SEMATECH EWMA finite-time covariance factor:
  - <https://www.itl.nist.gov/div898/handbook/pmc/section3/pmc343.htm>
- NIST/SEMATECH individual chart의 이동범위 sigma 추정:
  - <https://www.itl.nist.gov/div898/handbook/pmc/section3/pmc322.htm>
- 현재 Minitab의 time-weighted chart, EWMA 결과·옵션 문서는 독립 교차검증 자료로만 사용했다.
  - <https://support.minitab.com/en-us/minitab/help-and-how-to/quality-and-process-improvement/control-charts/supporting-topics/understanding-time-weighted-control-charts/time-weighted-control-charts-in-minitab/>
  - <https://support.minitab.com/en-us/minitab/help-and-how-to/quality-and-process-improvement/control-charts/how-to/time-weighted-charts/ewma-chart/interpret-the-results/key-results/>
  - <https://support.minitab.com/en-us/minitab/help-and-how-to/quality-and-process-improvement/control-charts/how-to/time-weighted-charts/ewma-chart/perform-the-analysis/ewma-options/enter-historical-parameters/>
  - <https://support.minitab.com/en-us/minitab/help-and-how-to/quality-and-process-improvement/control-charts/how-to/time-weighted-charts/ewma-chart/perform-the-analysis/ewma-options/modify-the-control-limits/>

현재 Minitab 문서는 Minitab 14 내부 구현의 증거가 아니며 제품 버전 간 기본값·계산 경로의 동일성을 가정하지 않는다.

## StatPro 독립 구현

- 개별 관측값에 대해 `Z_t = lambda*Y_t + (1-lambda)*Z_(t-1)`를 계산하고 `Z_0`는 기준 평균으로 둔다.
- 입력 경계는 관측값 2개 이상, `0 < lambda <= 1`, `0 < L <= 10`이다.
- 시점 `t`의 표준오차는 `sigma*sqrt(lambda/(2-lambda))*sqrt(1-(1-lambda)^(2t))`이다.
- 시작 시점 보정 한계는 `target ± L*SE_t`이며 각 점에 당시 LCL/CL/UCL을 보존한다.
- 과거 평균·sigma를 주면 그대로 사용한다. 생략하면 현재 관측 평균과 `MRbar/1.128`을 사용하되 prospective monitoring의 기준 오염 위험을 명시적으로 경고한다.
- 신호는 EWMA가 당시 한계 밖인 점이며 특별원인 확정이 아닌 조사 후보다.
- 결과는 공통 `ResultBundle`에 점별 관측값·EWMA·가변 한계·신호, lambda/L, 기준 모수 출처와 provenance를 보존한다.

이는 공개 수학의 clean-room 구현이며 Minitab 내부 코드·리소스·화면의 번역 또는 복제가 아니다.

## 검증 결과

- NIST 공개 점화식과 finite-time 분산식의 수계산 fixture 통과
- 과거 모수와 MRbar 기반 추정 모수의 출처·경고 계약 통과
- 작은 평균 이동 누적 신호와 잘못된 lambda/L/sigma 경계 통과
- API·CLI·React 입력/결과·접근 가능한 표 계약 통과
- 전체 Python 153/153, Vitest 47/47, Ruff, compileall, TypeScript/Vite production build 통과
- 대표 10,000개 관측 측정: cold wall 323.994ms/CPU 328.125ms, warm 20회 평균 wall 336.702ms/CPU 335.938ms, Python 추적 할당 peak 8,840,271 bytes, ResultBundle JSON 1,701,247 bytes

## 남은 미확인·후속 범위

- Minitab 14 EWMA 대화상자, 실제 기본값, 세션 명령과 수치 비교
- 부분군 EWMA, stage별 기준 모수, 결측·가변 표본 크기 처리
- ARL 기반 lambda/L 설계와 one-sided 한계
- Box-Cox 및 비정규 기준선
- MTW/MPJ 입력·결과 직렬화
- CUSUM, Laney P′/U′ 및 희귀사건 관리도
