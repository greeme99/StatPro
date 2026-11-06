# DMAIC 관리 인계 불변 근거 계약

## 범위

- `DmaicControlHandoff`가 관리 단계의 모니터링 계획, 검토 주기, 효과 기준과 반응 계획을
  프로젝트별 불변 revision으로 소유한다.
- 관리 인계는 선택한 PFMEA 관리계획 항목의 Study ID·저장 ETag·Study digest·Control ID를
  스냅샷으로 보존한다. FMEA 관리계획 원문은 복제하지 않는다.
- 관리 효과 근거는 저장된 SPC 또는 공정능력 Analysis Run의 Run ID·분석 유형·Run ETag·
  입력 digest로 고정한다.
- 프로젝트에 연결된 Define·Measure·Analyze·Improve 문서의 ID·revision·digest를 서버가
  자동 스냅샷해 현장 관리 기준의 의사결정 계보를 유지한다.

## 검증 경계

- API는 요청된 FMEA 관리계획 항목이 저장된 Study에 실제 존재하는지 확인한다.
- API와 도메인 워크플로 모두 관리 근거를 `spc.*` 또는 `capability.*` Analysis Run으로
  제한한다. DOE 등 다른 실행 유형은 관리 효과 근거로 수락하지 않는다.
- 관리 인계에는 하나 이상의 효과 기준, 반응 계획, FMEA 관리 항목과 Analysis Run이
  반드시 필요하다.
- `DmaicControlHandoff.from_dict`는 저장 digest를 재계산해 변조된 문서를 거부한다.

## 검증 결과

- `python -m ruff check --no-cache src/statpro/dmaic src/statpro/api/app.py tests/test_dmaic.py tests/test_api.py` 통과.
- `.venv\\Scripts\\python.exe -m unittest tests.test_dmaic tests.test_api` 47개 통과.
- `npm test -- App.test.tsx` 77개 통과. 관리 가이드의 작업공간 링크와 빈 상태 화면을 검증했다.
- `npm run build` 통과. TypeScript 계약과 Vite 프로덕션 번들을 검증했다.
- `git diff --check` 통과.

## 남은 범위

- 관리 인계 개정·승인 UI와 서명 권한 정책.
- 일반 결함 분석 revision을 반응 계획의 명시적 Evidence Reference로 연결.
- 관리 기준 충족 여부를 후속 Run으로 재평가하는 효과 확인 기록과 조직 알림 정책.
