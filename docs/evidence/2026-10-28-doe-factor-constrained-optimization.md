# DOE 요인 제약 응답 최적화 근거 기록

## Minitab 14 정적 관찰

- 대상: `C:\Program Files (x86)\MINITAB 14\Mtb14Book.dll`
- SHA-256: `cc2b89d6472330030bc6c03111344625522848d39f43bc912bb3d33cbf6f5599`
- 기존 제한 문자열 관찰에서 `CmMROptStorage`, `mGetMROptimize`와 응답 수·시작점·스케일 관련 이름을 확인했다.
- 이 정적 후보는 Minitab 14에 다중응답 최적화 기능이 존재할 가능성만 뒷받침한다. 요인 제약 형식, 탐색 알고리즘, 기본값, 세션 명령, 수치 결과와 UI 동작은 확인하지 않았다.

## 공개 통계·행동 교차검토 근거

- NIST/SEMATECH 5.5.3.1.6은 적합한 실험영역을 벗어나지 않는 제약 최적화의 필요성을 설명한다.
  - https://www.itl.nist.gov/div898/handbook/pri/section5/pri5316.htm
- NIST/SEMATECH 5.5.3.2.2는 다중응답 desirability와 복합 desirability를 설명한다.
  - https://www.itl.nist.gov/div898/handbook/pri/section5/pri5322.htm
- 현재 Minitab 공개 도움말은 연속 변수의 범위 제한과 특정 값 고정을 설명한다. 이는 행동 교차검토 자료이며 Minitab 14 내부 동작의 증거가 아니다.
  - https://support.minitab.com/en-us/minitab/help-and-how-to/statistical-modeling/using-fitted-models/how-to/response-optimizer/perform-the-analysis/specify-the-analysis-options/

## StatPro 독립 구현

- 선택적 `factor_constraints`는 요인별 실제 공학 단위 `lower`·`upper`를 받는다. 같은 값은 고정 설정으로 취급한다.
- 요인 이름, 유한값, `design low <= lower <= upper <= design high`를 소유 경계에서 검증한다.
- 제약을 coded 범위로 한 번 변환하고 기존 결정론적 다중시작 pattern search의 시작점·모든 이동에 같은 범위를 적용한다.
- 결과는 적용 제약, 제약 요인 수, 제약 영역 모서리 수, 권장 실제·coded 설정과 후보 평가 수를 공통 `ResultBundle`에 보존한다.
- CLI·REST API·웹 입력 및 결과 화면이 같은 코어 계약을 사용한다.

## 검증과 제한

- 2요인 선형 fixture에서 A를 0.2–0.6으로 제한하고 B를 0.4에 고정했을 때 권장 설정 A=0.6, B=0.4와 composite desirability 0.6을 회수했다.
- 미등록 요인과 설계영역 밖 제약은 tagged 입력 오류로 거부한다.
- API·CLI는 A 상한 0.6을 보존하고 두 응답의 복합 desirability `sqrt(0.6)`을 반환한다. UI는 범위·고정 제약을 전송하고 결과에서 감사 표로 표시한다.
- 대표 2요인·1응답·범위 1개·고정값 1개 측정은 cold wall 6.049ms/CPU 15.625ms, warm 100회 평균 wall 7.065ms/CPU 7.031ms, Python 추적 할당 peak 63,219 bytes, ResultBundle JSON 4,577 bytes였다. 프로세스 패밀리 peak memory와 agent token 비용은 측정하지 않았다.
- 이 증분은 축 정렬 범위·고정 제약만 지원한다. 일반 선형/비선형 결합 제약, 정수·범주형 요인, 비용함수, 신뢰구간 기반 robust optimization과 전역 최적 증명은 지원하지 않는다.
- Minitab 14의 제약 문법·기본값·탐색·수치 출력·UI와의 런타임 동등성은 미확인이다.
