# DOE blocked·단일요인 foldover 근거 기록

## Minitab 14 정적 관찰

- 대상: `C:\Program Files (x86)\MINITAB 14\Mtb14Book.dll`
- SHA-256: `cc2b89d6472330030bc6c03111344625522848d39f43bc912bb3d33cbf6f5599`
- 기존 REA/Ghidra 및 제한 문자열 관찰에서 `CmDOEFactor::mGetGenerator`, `mGetBlockColumn`, `mUseBlocks` 등 DOE 생성식·블록 관련 이름을 확인했다.
- 이 증분에서는 Minitab 14의 foldover 메뉴·세션 명령·계산 결과를 동적으로 관찰하지 않았다. 따라서 위 정적 후보는 Minitab 14에 DOE 생성식·블록 기능이 존재할 가능성만 뒷받침하며, 단일요인 fold 정책·블록 유지 방식·기본값·수치 출력·UI 동등성을 증명하지 않는다.

## 공개 통계·행동 교차검토 근거

- NIST/SEMATECH 5.3.3.8.1은 모든 요인 부호를 반전한 mirror-image foldover가 해상도 III 설계의 주효과를 2요인 교호작용에서 분리하는 원리를 설명한다.
  - https://www.itl.nist.gov/div898/handbook/pri/section3/pri3381.htm
- NIST/SEMATECH 5.3.3.8.2는 한 요인만 반전하는 대안 foldover가 선택 요인과 그 요인이 포함된 2요인 교호작용의 별칭을 끊으며, 결합 설계의 전체 해상도는 III으로 남을 수 있음을 설명한다.
  - https://www.itl.nist.gov/div898/handbook/pri/section3/pri3382.htm
- NIST/SEMATECH 5.3.3.3.3은 고차 처리 교호작용 열을 블록 열로 사용하고 블록 안에서 무작위화하는 원리를 설명한다.
  - https://www.itl.nist.gov/div898/handbook/pri/section3/pri3333.htm
- 현재 Minitab 공개 도움말의 `Fold Design`과 생성 옵션은 독립 행동 교차검토 자료로만 사용했다. 이는 Minitab 14 내부 동작의 증거가 아니다.
  - https://support.minitab.com/en-us/minitab/help-and-how-to/statistical-modeling/doe/how-to/factorial/display-and-modify-design/perform-the-analysis/fold-design/
  - https://support.minitab.com/en-us/minitab/help-and-how-to/statistical-modeling/doe/how-to/factorial/create-factorial-design/create-2-level-factorial-specify-generators/create-the-design/specify-the-options/

## StatPro 독립 구현

- `foldover=true`는 기존 해상도 III 전체 mirror-image fold를 유지한다. `foldover_factor`는 이름이 일치하는 한 요인의 부호만 반전하며 두 옵션을 동시에 지정하면 tagged 입력 오류로 거부한다.
- 원 설계의 정의관계에서 전체 fold는 홀수 길이 단어를, 단일요인 fold는 선택 요인이 들어간 단어를 제거해 결합 설계의 유효 정의관계를 계산한다.
- 주효과별 별칭 집합과 2요인 교호작용 분리 여부를 유효 정의관계에서 다시 계산한다. 단일요인 fold에서 전체 설계 해상도가 III으로 남더라도 어떤 주효과가 분리됐는지 개별적으로 보존한다.
- 블록 생성식이 있으면 원 실행과 fold 실행에 같은 블록 열 정의를 적용하고, 유효 정의관계로 블록 대비별 처리효과 별칭을 다시 계산한 뒤 블록 안에서만 무작위화한다.
- API·CLI·웹 입력과 `ResultBundle`은 fold 방식, 선택 요인, 실제 반전 요인, 분리된 주효과, 원/유효 정의관계를 함께 보존한다.

## 검증과 제한

- 5요인 8회 해상도 III 설계 `D=AB`, `E=AC`에서 D만 반전한 16회 결합 설계와 유효 정의관계 `I=ACE`를 검증했다.
- 단일요인 fold에서 D는 2요인 교호작용과 분리되지만 A는 계속 별칭됨을 효과별로 검증했다.
- 블록 생성식 `BC`를 함께 사용하면 2개 블록이 각각 8회이며, 블록 별칭 `BC=ABE`를 유효 정의관계에서 계산함을 검증했다.
- 같은 `BC` 블록 생성식과 전체 mirror fold를 결합해 두 블록이 각각 8회이고 블록 별칭이 `BC=DE`로 다시 계산됨을 검증했다.
- 합성 응답에서 D 효과 4와 `Blk1` 계수 5를 동시에 회수했다. 상충 옵션, 미등록 요인, 별칭 감소 없이 실행만 복제하는 fold는 fail-closed 오류로 검증했다.
- 임의의 다중요인 부분 fold, semifolding, 3/4 fraction, 음의 fraction, split-plot, 공변량은 지원하지 않는다.
- Minitab 14의 단일요인 fold 기본값·블록 번호·세션 명령·파일 저장·수치 출력·UI와의 런타임 동등성은 미확인이다.
