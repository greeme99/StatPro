# DMAIC 고객의 소리(VOC) 불변 계약

## 범위

이 증분은 DMAIC 정의 단계의 고객의 소리(VOC)를 독립 불변 문서로 저장한다.
문서는 수집 계획, 데이터 지점, 고객 요구사항, 불편, 기회, 조치, 권고 및 다음
단계를 보관한다. 프로젝트는 최신 VOC 본문을 복제하지 않고 문서 ID·개정·digest만
참조한다.

## 근거 구분

- **사용자 제공 화면 참조:** VOC 화면의 접힌 정보 섹션과 프로젝트 연결 필요성.
- **구현 판단:** 각 저장본이 재현 가능해야 하므로 이전 digest를 가리키는 immutable
  revision 체인과 API 낙관적 저장 버전 검사를 사용한다.
- **미포함:** VOC 화면, Word 내보내기, SIPOC, 문제 정의, 이해관계자 분석, 외부
  고객 시스템 연동. 이들은 구현되었다고 주장하지 않는다.

## 검증 계약

- `POST /v1/dmaic-projects/{project_id}/voice-of-customer-studies`는 현재 프로젝트
  저장 버전과 일치할 때에만 새 immutable VOC 문서와 프로젝트 참조를 생성한다.
- `GET /v1/dmaic-projects/{project_id}/voice-of-customer-studies/{document_id}`는
  프로젝트 소유 문서만 반환한다.
- 이전 문서는 변경하지 않으며, 이전 저장 버전 요청은 HTTP 409 충돌을 반환한다.
