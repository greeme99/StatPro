# 중첩 Gage R&R 증분 근거 기록

## 공개 통계 근거

- Minitab의 Nested Gage R&R variance components 수식 문서는 작업자마다 다른 부품을
  반복 측정하는 중첩 설계의 분산성분 표를 설명한다.
  https://support.minitab.com/en-us/minitab/help-and-how-to/quality-and-process-improvement/measurement-system-analysis/how-to/gage-study/nested-gage-r-r-study/methods-and-formulas/gage-r-r-table/
- NIST/SEMATECH Variance Components 자료는 ANOVA 기반 분산성분 추정의 일반 원칙을
  제공한다.
  https://www.itl.nist.gov/div898/handbook/prc/section4/prc44.htm
- Minitab의 Nested Gage R&R 신뢰구간 수식 문서는 분산성분 신뢰구간에 대한
  MLS 근사와 반복성 성분의 카이제곱 기반 계산을 구분한다.
  https://support.minitab.com/en-us/minitab/help-and-how-to/quality-and-process-improvement/measurement-system-analysis/how-to/gage-study/nested-gage-r-r-study/methods-and-formulas/variance-components-in-confidence-intervals/

## StatPro 독립 구현

- `msa.gage_rr_nested`는 `작업자 → 작업자 내 부품 → 반복 측정`의 균형 중첩 설계를
  검증하고, 작업자·부품(작업자 내)·반복성의 method-of-moments 분산성분을 계산한다.
- 같은 부품이 두 작업자에게 배정되는 교차 설계는 거부한다. 모든 작업자에 같은 수의
  부품, 각 부품에 같은 반복 횟수가 필요하다.
- 음의 원 추정 분산성분은 결과의 물리적 해석을 위해 0으로 절단하지만 원 추정값과
  경고를 ResultBundle에 남긴다. 입력 digest, ANOVA, 분산성분, %Contribution,
  %Study Variation, NDC 및 provenance도 함께 보존한다.
- 반복성 분산성분에는 잔차 자유도와 카이제곱 분위수를 사용한 정확 95% 신뢰구간을
  추가한다. 이 값은 반복성 성분에 한정하며 다른 성분의 신뢰구간이나 전체 Gage R&R
  신뢰구간으로 표시하지 않는다.

## 검증과 경계

- 균형 중첩 fixture의 ANOVA·분산성분 계산, 잘못된 작업자-부품 배정과 불균형 설계의
  거부, REST 입력 계약, UI 설정 화면 경로를 로컬 회귀 테스트로 검증한다.
- 이 구현은 균형 중첩 설계만 지원한다. 작업자 효과는 작업자 내 부품 평균제곱을,
  작업자 내 부품 효과는 반복성 평균제곱을 분모로 하는 비풀링 F 검정과 상측 p 값을
  ResultBundle에 보존한다. 이는 variance component의 음수 절단 정책과 독립된
  ANOVA 검정값이다.
- 반복성 이외 분산성분의 근사 신뢰구간, REML, 상호작용 풀링, 비균형 설계와
  교차·중첩 혼합 설계는 포함하지 않는다.
- 이번 증분에서는 Minitab 14 바이너리의 정적·동적 관찰을 새로 얻지 못했다. Minitab과의
  메뉴·기본값·출력·결과 동등성은 주장하지 않는다.
