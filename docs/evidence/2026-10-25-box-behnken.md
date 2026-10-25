# Box–Behnken 증분 근거 기록

## Minitab 14 정적 관찰

- 대상: `C:\Program Files (x86)\MINITAB 14\mtb14.exe`
- SHA-256: `BDB292434B7A95164FD47BC9B1BDEAD9FE479A077E1B54CAFAC365E3CFA019DB`
- 원본 파일 바이트의 제한 문자열 검색에서 파일 오프셋 `7,646,980`에 `CmProjManBoxBehnken`이 관찰되었다.
- `Mtb14Book.dll`에서는 `CmDOERsPlot` 등 일반 DOE/response-surface 클래스명 후보가 관찰됐지만, ASCII·UTF-16 제한 검색에서 `Behnken` 직접 문자열은 관찰되지 않았다.
- REA/Ghidra로 `Mtb14Book.dll`을 새로 열려던 호출은 450초 tool timeout으로 완료되지 않았으며 Evidence ID를 생성하지 못했다. 같은 호출은 반복하지 않았다.

이 관찰은 Minitab 14에 Box–Behnken 프로젝트 관리 기능이 존재할 가능성을 뒷받침한다. 함수 동작, 설계표 구성, 기본 중심점 수, 무작위화, 명령 문법 또는 화면 동작을 증명하지 않는다.

## 독립 구현 근거

- NIST/SEMATECH 5.3.3.6.2: Box–Behnken 설계는 3수준 독립 quadratic 설계이며 처리 조합은 실험영역 edge midpoint와 center에 위치한다.
  - https://www.itl.nist.gov/div898/handbook/pri/section3/pri3362.htm
- NIST/SEMATECH 5.3.3.6.3: 공개 3요인 표준순서와 3·4·5요인의 15·27·46회 실행 수를 검증 기준으로 사용했다.
  - https://www.itl.nist.gov/div898/handbook/pri/section3/pri3363.htm

StatPro 구현은 모든 요인쌍에 대해 다른 요인을 0에 고정하고 해당 두 요인의 `(-1,-1)`, `(+1,-1)`, `(-1,+1)`, `(+1,+1)` 조합을 생성한다. 3–5요인만 지원하며 공개 실행 수와 맞추기 위해 자동 중심점은 각각 3, 3, 6개다. 이는 공개 수학의 독립 구현이고 Minitab 내부 코드의 번역이나 동등 구현 주장이 아니다.

## 남은 미확인 범위

- Minitab 14의 Box–Behnken 기본 중심점·블록·무작위화 동작
- Minitab 세션 명령어와 출력 열 이름
- 6요인 이상에서 사용하는 특수 불완전 블록 구성
- Box–Behnken 응답 분석과 Minitab 출력의 대응 관계

## 2026-10-25 응답 분석 구현 증분

- StatPro는 생성된 Box–Behnken 실행순서와 일대일인 응답에 complete coded second-order model(상수, 선형, 모든 2요인 교호작용, 제곱항)을 적합한다.
- 계수·ANOVA·순수오차/적합결여 분해·적합값·잔차·R²는 중앙합성설계와 동일한 단일 quadratic-fit 소유 경계에서 계산한다.
- 공개 통계 근거는 NIST/SEMATECH response-surface model과 residual diagnostics이며, Minitab 14 구현을 복제한 계산식이라는 주장은 하지 않는다.
- `CmProjManBoxBehnken` 정적 문자열은 Minitab 기능 후보 증거일 뿐이다. 본 증분에서도 Minitab 14의 계수 표기, ANOVA 자유도, p값, 적합결여 또는 화면 동작과의 동등성은 확인하지 않았다.

## 2026-10-25 정상점·표면 탐색 증분

- Box–Behnken 완전 2차 모형은 중앙합성설계와 같은 단일 quadratic-surface 소유 경계에서 `y=b0+b'x+x'Bx`를 구성한다.
- 정상점은 비특이 `B`에서 `x*=-0.5 B^-1b`로 계산하고, 대칭 `B`의 canonical 고유값 부호로 최대·최소·안장·능선/평탄을 분류한다.
- 선택한 두 요인은 coded `[-1,1]`의 홀수 5–51 격자에서 평가한다. 나머지 요인은 명시한 hold 값에 고정하며 기본값은 0이다.
- 동일 격자에서 bounded 최소·최대, marching-squares iso-response 선분과 접근 가능한 표, 결정론적 3D 와이어프레임 데이터를 반환한다.
- 3요인 합성 응답의 내부 최대점 `(0.25, -0.5, 0.1)`과 최대 51×51 격자·12개 등고선 수준을 검증했다.
- 이 수학과 시각화는 공개 반응표면 이론에 따른 StatPro 독립 구현이다. `CmProjManBoxBehnken`·`CmDOERsPlot` 이름은 Minitab 14의 정상점 계산, canonical 허용오차, hold 기본값, contour 보간, 카메라 또는 UI 동등성을 증명하지 않는다.
