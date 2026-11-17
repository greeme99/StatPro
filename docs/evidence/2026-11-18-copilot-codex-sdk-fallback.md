# AI Copilot Codex SDK 폴백 근거

기준일: 2026-11-18

## 확인한 사실

- 공식 [Codex SDK 문서](https://learn.chatgpt.com/docs/codex-sdk)는 Python SDK가 로컬 Codex app-server를 JSON-RPC로 제어하며, `pip install openai-codex`, `Codex`, `Sandbox`, `thread_start()`, `thread.run()`을 제공한다고 설명한다.
- 공식 [Python SDK README](https://github.com/openai/codex/blob/main/sdk/python/README.md)는 기존 Codex 인증을 재사용하고 `thread.run()` 결과가 최종 응답·items·usage를 포함한다고 설명한다.
- 공식 문서는 `Sandbox.read_only`가 읽기만 허용하고, `Sandbox.workspace_write`와 `Sandbox.full_access`는 더 넓은 권한이라고 명시한다. StatPro Copilot은 가이드 전용이므로 `read_only`만 사용한다.
- 이 개발 환경에서는 `openai-codex 0.169.0`의 import와 `Sandbox.read_only` enum 값을 확인했다. 계정 인증·실제 모델 호출·전송 정책은 이 변경에서 실행하거나 검증하지 않았다.

## 구현 결정

1. 고정 순서는 `Rulebase → EXAONE API → Codex SDK → 수동 입력`이다.
2. Codex SDK는 `STATPRO_COPILOT_CODEX_ENABLED=true`일 때만 인스턴스화한다. 패키지가 없거나 응답 JSON 계약이 틀리면 다음 수동 입력 단계로 실패 폐쇄한다.
3. SDK 프롬프트는 파일 변경·도구 실행·설정 변경을 금지하고, 답변·권장 도구·메뉴 경로·체크리스트·업무절차 JSON만 요청한다.
4. 상태 API는 설정과 SDK 설치 여부만 반환하며, 상태 조회로 인증·모델 요청을 만들지 않는다.

## 미확인 범위

- 실제 Codex 계정의 모델 가용성, 비용, 응답 지연, 조직 데이터 전송·보관 정책
- 해당 환경에서의 실제 Codex app-server 인증 및 사용자 대화 전송 승인
- 스트리밍 UI·스레드 재개·장기 대화 이력 보관

이 미확인 범위는 실제 사용자 질의를 SDK에 전송하기 전에 조직 정책과 계정 권한으로 별도 검증해야 한다.
