# DOE 정규 부분요인 블록 설계 근거 기록

## Minitab 14 정적 관찰

- 대상: `C:\Program Files (x86)\MINITAB 14\Mtb14Book.dll`
- SHA-256: `cc2b89d6472330030bc6c03111344625522848d39f43bc912bb3d33cbf6f5599`
- 원본 파일 바이트의 제한 문자열 검색에서 다음 이름을 관찰했다.
  - `?mIsBlockingColumnPresent@CmMixturesModel@@UBE_NXZ`
  - `?mIsBlockingColumnPresent@CmResponseSurfaceModel@@UBE_NXZ`
  - `?mGetBlockColumn@@YAHPAVCmDOE@@@Z`
  - `?mGetBlockFlag@CmResponseModels@@QAE_NI@Z`
  - `?mSetBlockFlag@CmResponseModels@@QAEXIH@Z`
  - `?mUseBlocks@CmResponseModels@@QAE_NI@Z`

이번 증분에서는 현재 Ghidra 공급자 설치 경로가 유효하지 않아 새 Ghidra 세션이나 Evidence ID를 만들지 못했다. 위 항목은 원본 DLL의 제한 문자열 관찰이며, Minitab 14에 블록을 인식하는 DOE/반응표면 모델 기능이 존재할 가능성만 뒷받침한다. 정규 부분요인 블록 생성 알고리즘, 기본 생성식, 블록 번호, 무작위화 순서, 세션 명령, 수치 결과 또는 화면 동작을 증명하지 않는다.

## 공개 통계 근거

- NIST/SEMATECH 5.3.3.3.3은 고차 처리 교호작용 열을 블록 효과와 교락시키고 블록 안에서 실행 순서를 무작위화하는 2수준 요인설계 블록화를 설명한다.
  - https://www.itl.nist.gov/div898/handbook/pri/section3/pri3333.htm
- 현재 Minitab 공개 도움말의 블록 예제와 생성자 설명은 독립 교차검토 자료로만 사용했다. 이는 Minitab 14 내부 동작의 증거가 아니다.
  - https://support.minitab.com/en-us/minitab/help-and-how-to/statistical-modeling/doe/how-to/factorial/create-factorial-design/create-2-level-factorial-default-generators/before-you-start/example-of-a-2-level-design-with-blocks/
  - https://support.minitab.com/en-us/minitab/help-and-how-to/statistical-modeling/doe/supporting-topics/factorial-and-screening-designs/design-generators-for-2-level-designs/

## StatPro 독립 구현

- 사용자는 최대 네 개의 블록 생성식을 요인 이름 배열로 명시한다. `p`개 생성식은 `2^p`개 블록을 만든다.
- 각 생성식과 생성식 조합의 대칭차를 treatment word로 만들고, 기존 부분요인 정의관계와 결합해 블록 대비별 전체 처리효과 별칭 집합을 계산한다.
- 상수 열이 되는 종속 생성식과 주효과를 블록에 교락시키는 생성식은 fail-closed 입력 오류로 거부한다.
- 각 블록에 반복당 최소 두 처리 조합을 요구하고, 전체 실행을 섞지 않고 블록 안에서만 seed 기반 무작위화한다.
- 블록 해상도는 블록 대비와 교락된 가장 짧은 처리효과 차수에 블록 차수 1을 더해 보고한다.
- 응답 분석은 모든 `2^p-1` 블록 대비를 nuisance term으로 함께 적합하고 계수·효과·제곱합·처리효과 별칭을 별도 표로 반환한다. 처리 주효과와 블록 효과를 합쳐 fitted value, 모형 제곱합과 잔차 자유도를 계산한다.
- 동일한 소유 경계가 코어, CLI, REST API와 React 화면의 생성식 입력·설계표·결과표에 사용된다.

## 검증과 제한

- 5요인 16회 절반부분요인 `E=ABCD`와 블록 생성식 `AB`, `AC`에서 네 블록이 각각 네 실행을 가지며 주효과와 직교함을 검증했다.
- 블록 대비 `Blk1`, `Blk2`, `Blk1*Blk2`의 처리효과 별칭 집합과 블록 해상도를 검증했다.
- 합성 응답에서 `A` 계수 2와 `Blk1` 계수 5를 동시에 회수하고 잔차가 0임을 검증했다.
- 종속 생성식, 주효과 교락, 지나치게 작은 블록, 블록과 full mirror-image foldover 조합은 지원되는 것처럼 추정하지 않고 오류로 실패한다.
- 완전요인 자동 블록 생성식 선택과 center point의 블록 배치는 후속 독립 증분으로 구현했으며 `2026-10-27-doe-full-factorial-blocking.md`에 근거와 제한을 분리해 기록했다. 부분 foldover, split-plot, 공변량, 사용자 선택 교호작용 모형은 아직 구현하지 않았다.
- Minitab 14의 기본 생성식·블록 번호·세션 명령·파일 저장·수치 출력·UI와의 런타임 동등성은 미확인이다.
