# DOE 자동 정규 부분요인 생성자 선택 근거 기록

## Minitab 14 정적 관찰

- 대상: `C:\Program Files (x86)\MINITAB 14\Mtb14Book.dll`
- SHA-256: `cc2b89d6472330030bc6c03111344625522848d39f43bc912bb3d33cbf6f5599`
- REA/Ghidra 정적 분석에서 `CmDOEFactor::mGetGenerator`와 DOE 생성자 관련 이름이 관찰되었다.
- 원본 Evidence ID:
  - `ev_a81110e91594134718d8935a6583812c6966726977ae420d38a0fe4c585e1132`
  - `ev_5ad0956c7fdcc14afd3f0570b242a82ad794bce1efb2518fca4c00bbef243972`
  - `ev_4765b19b9011e7d98b23cddb72ede9bb952cdade97f7e856b69a78b03ad4e922`
  - `ev_88beffb79dc8bec97b675f9d81a31ae565cc0ffbd1d7efd914b17701a25265e4`
- 상세 원본: `D:\Workspace\REA\artifacts\mtb14-doe-fractional-evidence.md`

이 관찰은 Minitab 14에 부분요인 생성자를 조회·취급하는 기능이 존재한다는 후보 근거다. 생성식 문법, 기본 실행 수, 해상도 선택 정책, 최소 이상률 알고리즘, 동률 처리, 숫자 결과 또는 화면 동작을 증명하지 않는다. digest와 Evidence ID는 이 저장소의 독립 구현 근거가 아니라 REA 원본 기록을 찾아가기 위한 참조다.

## 공개 통계 근거

- NIST/SEMATECH 5.3.3.4.4는 정규 부분요인의 정의관계, 해상도, minimum aberration을 설명한다.
  - https://www.itl.nist.gov/div898/handbook/pri/section3/pri3344.htm
- NIST/SEMATECH 5.3.3.4.7은 요인 수·실행 수별 유용한 정규 부분요인 설계를 요약한다.
  - https://www.itl.nist.gov/div898/handbook/pri/section3/pri3347.htm
- 현재 Minitab 공개 도움말의 생성자 표는 독립 교차검토 자료로만 사용한다. 이는 Minitab 14 내부 동작의 증거가 아니다.
  - https://support.minitab.com/en-us/minitab/help-and-how-to/statistical-modeling/doe/supporting-topics/factorial-and-screening-designs/design-generators-for-2-level-designs/
  - https://support.minitab.com/en-us/minitab/help-and-how-to/statistical-modeling/doe/supporting-topics/factorial-and-screening-designs/what-is-a-design-generator/

## StatPro 독립 구현

- 자동 경로는 3–10개 요인으로 제한한다. 더 큰 설계는 기존의 명시적 생성식 경로를 사용한다.
- 선택한 기본 요인의 두 개 이상 열을 곱한 모든 후보 열에서 서로 다른 생성자 집합을 완전 탐색한다.
- 각 후보의 완전한 정의관계를 구성하고 단어 길이 패턴 `A3, A4, ...`를 사전식으로 최소화한다. 이는 먼저 해상도를 최대화하고 같은 해상도에서는 최단 정의 단어 수부터 최소화한다.
- 실행 수를 생략하면 요청한 최소 해상도를 만족하는 가장 작은 2의 거듭제곱 실행 수를 선택한 뒤 minimum aberration을 적용한다. 실행 수를 지정하면 그 실행 수 안에서만 선택한다.
- 동등한 요인 재명명 설계가 여러 개일 수 있으므로 결정론적 후보 순서의 첫 설계를 반환하고 경고한다.
- 결과에는 선택 모드, 요청/선택 실행 수, 최소/선택 해상도, 단어 길이 패턴, 검사한 후보 수, 탐색 완료 여부를 감사 메타데이터로 보존한다.
- 자동 설계와 주효과 분석은 기존 수동 생성식 엔진의 정의관계·별칭·분석 경계를 재사용한다.

## 검증과 제한

- 5요인 8회 설계에서 결정론적으로 `D=AB`, `E=AC`, 해상도 III, 단어 길이 패턴 `A3=2, A4=1`을 선택한다.
- 6요인에서 실행 수를 생략하고 최소 해상도 IV를 요청하면 16회를 선택한다.
- 6요인 8회에서 해상도 IV를 요청하면 가능한 것처럼 추정하지 않고 `automatic_generator_unavailable`로 실패한다.
- 자동 블록 생성식 선택, center point, 음의 fraction, 부분 foldover, 선택 모형 및 Minitab 14 기본값·동률 처리와의 런타임 동등성은 아직 확인하지 않았다. 명시적 정규 블록 생성식 경로는 별도 근거 문서에서 다룬다.
