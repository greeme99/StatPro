# SPC CUSUM FIR·신호 후 재설정 근거

## 범위

StatPro의 표준화 양측 tabular CUSUM에 선택형 FIR(Fast Initial Response) 시작값과 신호 후 재설정 정책을 추가한다. 기본값은 FIR `0`, 재설정 `false`이며, 기존 누적 계산을 유지한다.

## 공개 통계 근거

- NIST Dataplot CUSUM 문서는 FIR이 상·하 누적합의 초기값을 설정하고, 재시작 뒤에도 이상 상태가 계속되면 더 빠른 검출에 쓰일 수 있음을 설명한다. 일반적인 시작값 제안은 `h/2`이나 이는 사용자가 바꿀 수 있는 제안일 뿐 StatPro의 강제 기본값이 아니다. <https://www.itl.nist.gov/div898/software/dataplot/refman1/auxillar/cusum.htm>
- NIST Engineering Statistics Handbook은 표준 양측 tabular CUSUM 점화식과 0에서 시작하는 기본 누적합을 제시한다. <https://www.itl.nist.gov/div898/handbook/pmc/section3/pmc323.htm>

## 구현 계약

- `0 <= fir_head_start < decision_interval`만 허용한다.
- FIR은 상·하 누적합 모두에 같은 시작값을 적용한다.
- 재설정을 선택하면 신호가 난 관측값과 신호는 결과에 그대로 보존하고, 다음 관측값 직전에 양 누적합을 FIR 시작값으로 되돌린다.
- `fir_head_start=0`, `reset_after_signal=false`에서는 기존 수치 점화식과 입력 digest를 유지한다.

## 증거 분류와 미확인 범위

- 위 수식·FIR 사용 목적은 공개 통계 근거에서 독립 구현했다.
- Minitab 14 정적 문자열에는 FIR/reset 후보가 있으나, 동적 화면·기본값·재설정 시점·런타임 동등성은 관찰하지 않았다.
- V-mask와 ARL 기반 설계·튜닝은 이 증분 범위 밖이며 미구현이다.

## 검증

- 엔진 단위 시험은 FIR로 시작한 상측 누적합, 신호 지점의 보존, 다음 관측값부터의 재설정, 허용 범위 검증을 다룬다.
- API·CLI 계약 시험은 새 선택 입력의 전달과 결과 파라미터를 확인한다.
- 웹 시험은 기본 0 시작·재설정 없음 요청과 재설정된 접근 가능한 결과 행을 확인한다.
