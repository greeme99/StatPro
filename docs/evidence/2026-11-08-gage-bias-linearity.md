# Gage 편의·선형성 증분 근거 기록

## 공개 통계 근거

- Minitab의 Gage Bias 수식 문서는 기준값 대비 측정 평균의 편의를 정의한다.
  https://support.minitab.com/en-us/minitab/help-and-how-to/quality-and-process-improvement/measurement-system-analysis/how-to/gage-study/gage-linearity-and-bias-study/methods-and-formulas/gage-bias/
- Minitab의 Gage Linearity 수식 문서는 기준값에 따른 편의 변화의 회귀 관계를 설명한다.
  https://support.minitab.com/en-us/minitab/help-and-how-to/quality-and-process-improvement/measurement-system-analysis/how-to/gage-study/gage-linearity-and-bias-study/methods-and-formulas/gage-linearity/

## StatPro 독립 구현

- `msa.gage_bias_linearity`는 `measurement - reference`를 편의로 정의한다. 양수 편의는
  측정값이 기준값보다 높게 읽혔음을 뜻한다.
- 각 기준값에 최소 2회 반복 측정을 요구하고, 기준값별 평균 편의에 대한 단순 선형 회귀의
  절편·기울기·R²·잔차 표준오차를 ResultBundle에 보존한다.
- 이 초기 구현은 설명적 회귀 결과를 제공한다. 교정 승인이나 적합성 결정을 위한 신뢰구간,
  유의성 검정 및 허용한계 비교는 제공하지 않으며 화면과 경고에 그 경계를 명시한다.

## 검증과 경계

- 코어 분석, API 입력 계약, UI 설정 화면·결과 연결을 로컬 회귀 테스트로 검증한다.
- 이번 증분에서는 Minitab 14 바이너리의 정적·동적 관찰을 새로 얻지 못했다. Minitab과의
  메뉴·기본값·출력·결과 동등성은 주장하지 않는다.
