# Worksheet 필터·정렬·파생 열 증분 근거 기록

## StatPro 독립 구현

- `WorksheetSnapshot`은 원 Dataset digest와 부모 Worksheet digest를 분리해 보존한다.
  셀 변경에 이어 행 필터·행 정렬·파생 숫자 열도 같은 immutable revision 경계를 통과한다.
- 필터는 `equals`, 숫자 비교, text/categorical `contains`, 결측 여부를 지원하고,
  타입과 맞지 않는 비교는 거부한다. 결과 revision에는 실제로 남은 행만 있으며 원본과
  부모 revision은 변경하지 않는다.
- 정렬은 모든 지원 열 타입에 대해 안정적으로 적용하고 결측값을 마지막에 둔다.
- 파생 열은 numeric 열의 복사·더하기·빼기·곱하기·나누기만 허용한다. 임의 식이나
  코드를 평가하지 않고, 결측은 전파하며 0 나누기와 중복 열 이름은 거부한다.

## 검증과 경계

- 도메인 테스트는 필터·정렬·파생 열이 원본을 변경하지 않고 parent digest가 연결된
  새 revision을 만든다는 사실과 0 나누기·중복 열 이름의 거부를 고정한다.
- API 테스트는 CSV 가져오기부터 필터·정렬·파생 열의 연속 저장까지 storage version,
  revision, parent digest, 행/열 결과와 OpenAPI 경로를 검증한다.
- 현재 범위는 저장된 작업표의 로컬 변환이다. 데이터 내보내기, 조인, 임의 수식,
  서버 측 대규모 변환과 외부 데이터베이스 연결은 구현하지 않는다.
