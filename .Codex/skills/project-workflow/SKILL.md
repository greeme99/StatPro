---
name: project-workflow
description: 검증과 승인 게이트를 포함한 프로젝트 기본 작업 절차
---
# Project Workflow

## When to Use

두 단계 이상이거나 파일 변경이 필요한 비단순 작업에 사용한다.

## Procedure

1. 세 memory와 남아 있는 pending 초안을 읽는다.
2. 목표, 범위, 제약, 검증 가능한 완료 조건을 짧게 정한다.
3. 필요한 역할에 탐색·계획·구현·검토를 위임한다.
4. 최소 변경으로 구현하고 관련 테스트를 실행한다.
5. 정정, 실패 해결, 반복 가능한 절차를 회고한다.
6. 저장 가치가 있으면 `grow` 형식의 pending 초안만 만든다.
7. 사용자 승인 후 승격하고 skill usage를 기록한다.

## Pitfalls

- 같은 사실을 user, memory, skill에 중복 저장하지 않는다.
- 테스트되지 않은 추측이나 일회성 오류를 일반 규칙으로 만들지 않는다.
- 승인 게이트를 건너뛰어 canonical 파일을 직접 학습시키지 않는다.

## Verification

`.Codex/scripts/Test-LearningLoop.ps1`가 통과하고 변경 범위에 맞는 테스트가 성공해야 한다.
