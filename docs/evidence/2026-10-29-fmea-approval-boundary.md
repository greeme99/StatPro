# FMEA 승인 정책 경계 — 2026-10-29

## 구현한 독립 기능

- 로컬 승인 identity는 `active: true|false` 상태를 가진다. 비활성 identity는
  올바른 비밀번호를 제시해도 FMEA 승인을 수행할 수 없다.
- identity 파일의 선택형 정책
  `approval_policy.require_independent_approver: true`는 승인자 ID와 현재
  Study의 이전 감사 actor 값을 비교한다. 일치하면 승인을 거부한다.
- 승인 성공 시 선택 정책, 이전 actor 일치 수, 그리고 actor 비교의 한계를
  승인 감사 이벤트 및 읽기 전용 FMEA 보고서에 보존한다.

## 설정 예시

```json
{
  "format": "statpro.approval-identities.v1",
  "approval_policy": { "require_independent_approver": true },
  "identities": [
    { "user_id": "quality.approver", "active": true, "roles": ["fmea_approver"] }
  ]
}
```

실제 identity에는 `create_approval_identity`가 생성한 scrypt verifier가 추가된다.
비밀번호나 verifier 예제는 이 문서에 기록하지 않는다.

## 미확인·외부 정책 경계

이는 StatPro 로컬 identity와 self-reported FMEA actor의 문자열 일치만
판정한다. SAML/OIDC, MFA, SCIM 프로비저닝·비활성화, 조직 역할 매핑, 계정
잠금·만료, 법적 전자서명 또는 규제 준수는 구현·검증하지 않았다. 해당 범위는
조직이 제공하는 IdP와 승인 정책을 선택한 별도 adapter에서만 확장할 수 있다.

## 검증

- `python -m unittest discover -s tests -q`: 200 passed
- `web`: `npm test -- --run`: 57 passed
- `web`: 임시 output directory를 사용한 `vite build`: 성공

