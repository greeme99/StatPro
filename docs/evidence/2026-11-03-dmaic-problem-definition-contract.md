# DMAIC 문제 정의 계약 증거

## 범위

`문제 정의 (Problem Definition)`는 DMAIC 정의 단계에서 관찰된 현상과 목표 상태를
분리해 기록하는 독립 연결 문서다. 이 문서는 원인·대책을 확정하거나 외부 승인 권한을
판단하지 않는다.

## 구현 판단

- 프로젝트는 최신 문제 정의의 문서 ID·개정·digest만 참조한다.
- 문서 본문은 immutable revision으로 저장하며, 다음 저장본은 이전 digest를
  `parent_digest`로 보존한다.
- API 저장은 프로젝트 `storage_version`을 받아 낙관적 동시성을 검사한다.
- 웹 작업공간은 `설정 → 현상 → 격차 → 우선순위 → 보고서` 순서로 입력을 안내한다.

## 검증

- `tests/test_dmaic.py`는 불변 개정, 부모 digest, 프로젝트 참조 축약 및 직렬화 왕복을 검증한다.
- `tests/test_api.py`는 저장·조회와 오래된 저장 버전의 충돌을 검증한다.
- 웹 프로덕션 빌드는 TypeScript 계약과 라우팅을 검증한다.
