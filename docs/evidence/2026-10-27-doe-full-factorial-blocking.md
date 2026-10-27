# DOE 완전요인 자동 블록 설계 근거 기록

## Minitab 14 정적 관찰

- 대상: `C:\Program Files (x86)\MINITAB 14\Mtb14Book.dll`
- SHA-256: `cc2b89d6472330030bc6c03111344625522848d39f43bc912bb3d33cbf6f5599`
- 기존 제한 문자열 관찰에서 `CmDOE` 계열 객체, `CmDOEFactor::mGetGenerator`, `mGetBlockColumn`, `mUseBlocks` 등 생성식·블록 관련 이름을 확인했다.
- 이 관찰은 Minitab 14에 DOE 생성식과 블록을 취급하는 기능이 존재할 가능성만 뒷받침한다. 자동 생성식 선택 정책, 동률 처리, 블록 번호, 중심점 배치, 세션 명령, 수치 출력 또는 화면 동작은 확인하지 않았다.
- 이번 증분은 새 Ghidra 런타임 관찰이나 Minitab 실행 결과를 근거로 사용하지 않았다.

## 공개 통계 근거

- NIST/SEMATECH 5.3.3.3.3은 고차 처리 교호작용 열을 블록 효과와 교락시키고 블록 안에서 실행 순서를 무작위화하며 각 블록에 중심점을 배치하는 2수준 요인설계 블록화를 설명한다.
  - https://www.itl.nist.gov/div898/handbook/pri/section3/pri3333.htm
- 현재 Minitab 공개 도움말은 `p`개 블록 생성식이 `2^p`개 블록을 만들고, 완전 2수준 설계의 대표 생성식과 블록별 중심점 추가를 설명한다. 이는 독립 교차검토 자료이며 Minitab 14 내부 동작의 증거가 아니다.
  - https://support.minitab.com/en-us/minitab/help-and-how-to/statistical-modeling/doe/how-to/factorial/create-factorial-design/create-2-level-factorial-specify-generators/create-the-design/specify-the-generators/
  - https://support.minitab.com/en-us/minitab/help-and-how-to/statistical-modeling/doe/supporting-topics/factorial-and-screening-designs/design-generators-for-2-level-designs/
  - https://support.minitab.com/en-us/minitab/help-and-how-to/statistical-modeling/doe/supporting-topics/factorial-and-screening-designs/how-minitab-adds-center-points/

## StatPro 독립 구현

- 블록 수는 `1, 2, 4, 8, 16`으로 제한하며 블록마다 반복당 최소 두 처리 조합을 요구한다.
- 요청 블록 수의 balanced-simplex 열 배정에서 가능한 remainder subset을 모두 검사한다. 주효과와 블록이 교락되는 후보를 제외하고, 블록 대비별 처리 단어 길이 패턴을 사전식으로 최소화하며 요인 순서로 동률을 결정한다.
- 검사한 후보 수, 단어 길이 패턴, 선택 모드와 탐색 범위를 ResultBundle 진단에 보존한다. 이 선택은 보고된 balanced-simplex 후보군 안에서만 완전하며 모든 가능한 블록 설계의 전역 최적성을 의미하지 않는다.
- 중심점 수는 블록당 수로 해석하고 각 블록에 동일하게 배치한다. 모서리점과 중심점은 전체를 섞지 않고 블록 안에서만 seed 기반으로 무작위화한다.
- 응답 분석은 모든 `2^p-1` 블록 대비를 nuisance term으로 적합한다. 블록 생성식 별칭과 동일한 처리항은 별도 `confounded_terms`로 보존하고 처리 모형에서는 제외한다.
- 코어가 생성식·별칭·블록 배치와 분석 결과를 소유하며 CLI, REST API와 React 화면은 같은 ResultBundle을 투영한다.

## 검증과 제한

- 3요인·2블록 설계에서 자동 생성식 `ABC`, 블록별 4개 모서리점과 1개 중심점, 주효과 직교성을 검증했다.
- 4요인·4블록 설계에서 후보 3개를 재현 가능하게 검사하고 단어 길이 패턴 `{2: 1, 3: 2}`를 보존함을 검증했다.
- 합성 응답에서 처리 A 계수 2와 블록 계수 5를 회수하고, 블록과 교락된 ABC 항을 처리 모형에서 제외하며 잔차가 0임을 검증했다.
- 잘못된 비제곱수 블록과 블록당 처리 조합이 두 개 미만인 설계는 tagged 입력 오류로 거부한다.
- 사용자 지정 완전요인 블록 생성식, blocked/부분 foldover, split-plot, 공변량, 제약 최적화와 사용자 선택 교호작용 모형은 아직 구현하지 않았다.
- Minitab 14의 자동 생성식·기본값·세션 명령·파일 저장·수치 출력·UI와의 런타임 동등성은 미확인이다.
