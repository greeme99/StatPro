# FMEA 기업 IdP·권한 정책 증거 기록 — 2026-11-01

## 구현 결과

- Microsoft Entra ID OIDC 토큰을 직접 해석하지 않고, 서명·issuer·audience·수명을 검증한 verifier가 반환한 `VerifiedOidcClaims`만 신뢰한다. 선택형 `identity` 설치에는 tenant별 JWKS와 RS256을 검증하는 `EntraJwtVerifier`가 포함된다.
- 프로젝트 제공 문서 `Ref.doc/IdP 연동 기술 정보 및 권한 마스터 데이터.md`의 역할 마스터와 사용자–역할 매핑을 권한 정책에 반영했다.
- `ROLE_SYS_ADMIN`과 `ROLE_RND_QA`만 FMEA 승인 권한을 얻는다. 판매·생산·일반 역할은 역할 문자열이 토큰에 들어 있어도 FMEA 승인 권한으로 해석하지 않는다.
- IdP 토큰 역할과 StatPro 계정 마스터 역할의 교집합만 유효 권한으로 사용한다.
- 비활성 계정, MFA 누락, tenant/client/issuer 불일치, 미등록 사용자, 직무분리 위반은 실패 폐쇄한다.
- 승인 감사 이벤트에 IdP 종류, tenant, subject, 정책 버전, 유효 역할, 직무분리 판정을 남긴다.
- 기업 승인 전용 API는 `POST /v1/fmea-studies/{study_id}/approve-enterprise`이며 검증된 Bearer 경계를 요구한다. 기업 verifier가 주입되지 않은 기본 로컬 서버에서는 503으로 닫혀 있다.

## 권위별 근거 구분

### 프로젝트 제공 정책

- 역할 ID, 권한 범주, M150xx 사용자–역할 매핑은 사용자가 제공한 권한 마스터를 따른다.
- 제공 문서의 tenant/client/secret/URL 값은 예시 운영값으로 분류한다. client secret은 소스, 테스트, 문서, 로그에 복사하지 않았다.
- 메일 주소도 저장소 정책 파일에 복사하지 않았다. 계정의 안정 식별자는 제공된 사번형 사용자 ID를 사용한다.

### Microsoft 공개 기술 근거

- Entra OIDC discovery 문서는 tenant authority 아래 `/.well-known/openid-configuration`에서 제공되며 서명 키와 endpoint를 발견하는 기준이다: <https://learn.microsoft.com/en-us/entra/identity-platform/v2-protocols-oidc>
- 앱 역할은 검증된 토큰의 `roles` claim으로 전달되며 API에서 해당 역할을 검사해야 한다: <https://learn.microsoft.com/en-us/entra/identity-platform/howto-add-app-roles-in-apps>
- Entra provisioning은 SCIM 계정의 `active=false`를 비활성화로 전달할 수 있다: <https://learn.microsoft.com/en-us/entra/identity/app-provisioning/how-provisioning-works>

### StatPro 독립 구현 결정

- 조직 마스터와 토큰 역할을 교차검증하는 방식, FMEA 권한 문자열, 독립 승인 기본값, 감사 문맥 구조는 StatPro의 독립 설계다.
- `EntraApprovalConfiguration.for_tenant`는 공식 tenant-specific v2 authority 규칙에서 discovery URL과 issuer를 구성한다.

## 미확인·외부 필요 사항

- 제공된 예시 tenant에 대한 실제 네트워크 discovery, JWKS 서명 검증, 로그인, 조건부 액세스, 토큰 갱신은 실행하지 않았다. 구현된 verifier의 실 tenant 검증은 별도 운영 검증이 필요하다.
- 실제 client secret 또는 인증서, redirect URI, 운영 tenant의 앱 역할 등록은 저장소 밖 비밀 저장소와 Entra 관리자 작업이 필요하다.
- SCIM endpoint와 계정 수명주기 동기화는 아직 구현하지 않았다. 현재 `active` 값은 주입된 계정 마스터가 소유한다.
- 실제 운영 연결을 완료로 표시하려면 tenant별 discovery/JWKS 검증기, 키 회전, 감사 로그 보존, SCIM 비활성화 통합의 실환경 검증이 추가로 필요하다.

## 검증

- `tests.test_approval`: 정상 QA 승인, 판매 역할 거부, 비활성 계정 거부, MFA 누락 거부, audience 불일치 거부, 독립 승인 위반 거부.
- `tests.test_api`: 기업 승인 endpoint가 OpenAPI 계약에 노출됨을 검증.
- 기존 로컬 scrypt 재인증 경로는 유지한다.
