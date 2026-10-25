# p·np·c·u 관리도 증분 근거 기록

## Minitab 14 정적 관찰

- 대상 실행 파일: `C:\Program Files (x86)\MINITAB 14\mtb14.exe`
- SHA-256: `BDB292434B7A95164FD47BC9B1BDEAD9FE479A077E1B54CAFAC365E3CFA019DB`
- Ghidra 12.1.4 정적 Evidence: `ev_5e02d8b4b8a90989ba7d44912f6254c916e1545643643717a473bf717d6a3a27`
- Ghidra 정의 문자열/심볼 검색에서 다음 `Mtb14GraphicsCmnd.dll` 관리도 생성 후보가 관찰되었다.
  - `CmBuiltInControlChart::mGetModelCt` — `0xb21f8a`
  - `CmBuiltInControlChart::mGetModelVars` — `0xb21fb8`
  - `CmBuiltInControlChart::mNewDataRepList` — `0xb2202e`
  - `CmBuiltInControlChart::mNewFigure` — `0xb22070`
  - `CmBuiltInControlChart::mCreateBuiltIn` — `0xb220d8`
- 별도 정적 메모의 `Mtb14GraphicsCmnd.dll` SHA-256은 `f0974fd9a3d0514753587401f9488f8e2d6e67e74f8f9ed1fd386057e9b8320e`이다.

이 관찰은 설치된 Minitab 14에 내장 관리도 모델과 그래프 생성 경로가 존재한다는 기능 후보를 뒷받침한다. p/np 관리도의 계산식, 데이터 계약, 기본 옵션, 대화상자, 세션 명령 또는 출력 형식을 증명하지 않는다.

## 제한된 음성 결과

- 기존 분석 산출물의 `pchart`, `npchart`, `p chart`, `np chart`, `attribute chart`, `defective` 제한 검색에서는 p/np 전용 심볼을 식별하지 못했다.
- Ghidra 문자열 인벤토리는 정의된 문자열만 포함하며 PDB는 로드되지 않았다. 따라서 이 음성 결과는 기능 부재를 뜻하지 않는다.
- 이번 증분에서 Minitab GUI를 새로 조작하거나 런타임 값을 비교하지 않았다.

## 독립 구현 근거

- NIST/SEMATECH 6.3.3은 p 관리도를 부적합품 비율, np 관리도를 부적합품 개수에 대한 이항 속성 관리도로 구분한다.
  - <https://www.itl.nist.gov/div898/handbook/pmc/section3/pmc33.htm>
- StatPro는 전체 검사 수로 가중한 통합 부적합률을 Phase I 중심 추정치로 사용한다.
- p 관리도는 각 부분군의 표본 크기로 표준오차와 3σ 한계를 각각 계산하므로 가변 표본 크기를 허용한다.
- np 관리도는 일정한 표본 크기만 허용하고 부적합품 개수 척도에서 중심선과 3σ 한계를 계산한다.
- 확률·개수의 유효 범위를 벗어나는 이론 한계는 각각 `[0, 1]`, `[0, n]`으로 제한하며 제한 전 값을 diagnostics에 보존한다.
- 기대 적합품 또는 부적합품 수가 5 미만인 부분군에는 정규근사 정확도 경고를 남긴다.

이는 공개 수학의 clean-room 구현이며 Minitab 내부 코드의 번역, 화면 복제 또는 수치 동등성 주장이 아니다.

## 결과 계약과 확장 경계

- `chart_points`는 `index`, `nonconforming`, `sample_size`, `statistic`, `center`, `lcl`, `ucl`, `signal`을 공통 보유한다.
- `p_chart`와 `np_chart`는 단일 이항 속성 관리도 경계에서 입력 정규화·신호·진단·provenance를 공유한다.
- 향후 c/u 관리도는 같은 포인트/ResultBundle 계약에 포아송 중심·분산 계산기를 추가할 수 있으며, 현재 이항 계산을 재해석하지 않는다.

## 남은 미확인 범위

- Minitab 14 p/np 대화상자와 표본 크기 입력 방식
- 과거 중심선, stage, 결측·불균등 간격, 희귀사건 대체 한계 처리
- p/np 보조 규칙의 기본 활성화 상태와 Minitab 14 수치 비교
- 세션 명령어, 결과 열 이름, MTW/MPJ 직렬화
- Laney P′/U′ 및 희귀사건 관리도

## c/u 후속 증분

- NIST/SEMATECH 6.3.3.1의 공개 포아송 정의를 기준으로 c/u를 독립 구현했다.
- c는 동일 검사 기회의 결점 수, u는 가변 검사 단위당 결점 수를 계산한다.
- 네 관리도는 분포 중립 `event_count`, `opportunity`, `statistic`, `center`, `lcl`, `ucl`, `signal` 포인트 계약을 공유한다.
- Minitab 14의 c/u 전용 명령·기본값·수치 동등성은 확인하지 않았다.
