# 경험적 비정규 공정능력 근거 기록

## 공개 통계 근거

- NIST/SEMATECH 6.1.6은 일반 Cp/Cpk/Cpm이 정규분포 가정을 전제로 함을 명시하고, 비정규 자료의 대안으로 변환 또는 비모수 `Cnp/Cnpk/Cnpm`을 제시한다.
  - https://www.itl.nist.gov/div898/handbook/pmc/section1/pmc16.htm
- StatPro는 NIST의 `p(0.00135)`, median, `p(0.99865)` 정의를 선형 보간 경험적 order statistic으로 계산한다. 동일 문헌에 약 100개 이상의 독립 관측값이 일반적으로 필요하다는 주의가 있으므로, 더 작은 표본에는 경고를 남긴다.

## Minitab 14 근거 상태

- 이번 증분에서 새 Minitab 14 정적 또는 동적 관찰은 얻지 못했다. REA `binary_session`은 활성 대상이 없고 Ghidra provider는 설치 레이아웃을 검증하지 못해 새 native 분석을 실행하지 않았다.
- 따라서 Minitab 14의 비정규 capability 메뉴, 분포 적합, 변환, 백분위수 보간법, 기본값, 출력 형식, 세션 명령, UI 또는 런타임 동등성은 모두 미확인이다.

## StatPro 독립 구현

- `capability.nonnormal_empirical`은 named distribution fit을 하지 않는다. 입력 정렬 후 선형 보간 경험적 quantile로 Cnp/Cnpl/Cnpu/Cnpk와 선택적 Cnpm을 산출한다.
- Run은 입력 digest, 정량화 규칙, quantile 확률, 관찰 불량, 가정·경고·provenance를 ResultBundle에 보존한다.
- CLI `capability-nonnormal` 및 loopback API `POST /v1/analysis-runs/capability-nonnormal`은 같은 코어를 호출한다.

## 검증과 제한

- 비대칭 표본의 양측 Cnp/Cnpl/Cnpu/Cnpk/Cnpm, 단측 규격, 0 tail spread tagged error, REST catalog adapter, CLI sample을 unittest로 검증했다.
- 10,000개 관측값의 representative in-process 측정은 cold 34.324 ms, warm 50회 평균 37.550 ms, Python `tracemalloc` peak 4,584,996 bytes였다. 프로세스 패밀리 peak memory와 agent token 비용은 측정하지 않았다.
- 분포의 안정성·정규성·단일 모집단 여부를 자동으로 입증하지 않는다. 이 방법은 parametric Weibull/lognormal/Johnson 적합, Box-Cox 변환, bootstrap confidence interval, subgroup capability 또는 Minitab 동등성 주장을 포함하지 않는다.
