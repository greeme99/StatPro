# StatPro UI/UX 4차 개선 감사

## 목표와 범위

- 참조: `D:\Workspace\StatPro\Ref.doc\4차-UI.UX_개선.md`
- 흐름: 구조 마련 → 변경 전 캡처 → 개선 제안 → 개선 반영 → 변경 후 검증
- 대상: 분석 선택 목록, 실제 데이터 작업표, 핵심 화면 시각 회귀
- 기준: 프로젝트 `DESIGN.md`, WCAG 2.1 A/AA, 한국어 제조 UX 규칙
- 데이터: 로컬 문서 저장소와 분리된 고정 SMT 순간정지 작업표 fixture

## 산출물 구조

```text
round-4/
  README.md
  captures/
    before-{home,data,worksheet,analyses,reports}.png
    before-{home,data,worksheet,analyses,reports}-accessibility.txt
    before-summary.json
    after-{home,data,worksheet,analyses,reports}.png
    after-{home,data,worksheet,analyses,reports}-accessibility.txt
    after-summary.json
```

`npm run capture:ux -- before 4`와 `npm run capture:ux -- after 4`로 같은 조건의 PNG, ARIA 스냅샷, 브라우저 오류 요약을 생성한다.

## 진행 상태

- [x] 4차 감사 구조와 대표 작업표 fixture 마련
- [x] 변경 전 캡처
- [x] 개선 제안 확정
- [x] P1 개선 반영
- [x] 변경 후 캡처와 회귀 검증

## 발견 사항과 반영 결과

| 우선순위 | 화면 | 문제 | 사용자 영향 | 반영 | 검증 |
|---|---|---|---|---|---|
| P1 | 분석 선택 | 29개 기본 분석이 단일 목록에 고정되어 있음 | 분석 목적에 맞는 항목 탐색 비용이 큼 | 4개 업무 그룹, 검색, 결과 수, 초기화, 결과 없음 상태 추가 | `user-event` 검색·초기화 테스트 |
| P1 | 작업표 | 실제 데이터에서 변환 도구가 좁은 좌측 카드에 배치됨 | 라벨·설명·입력 폭이 줄어듦 | 균형 2열 도구 그리드로 변경 | 전후 PNG 비교 |
| P1 | 작업표 | 결측 필터에도 값 입력이 활성화됨 | 불필요한 값 입력 가능성 | 결측 조건에서 입력 비활성화와 설명 추가 | `user-event` 필터 테스트 |
| P1 | 실제 데이터 작업표 | 빈 상태 테스트로는 보이지 않던 대비 미달 3건 | WCAG AA 회귀 위험 | 기존 텍스트·성공 토큰 조합으로 보정 | axe serious/critical 0건 |

## 확정 백로그

| 우선순위 | 항목 | 범위와 완료 기준 | 제외 사유 |
|---|---|---|---|
| 완료 | 반응형 작업표 과업 | 1024px 2열·768px 1열 전환과 열 선택 키보드 조작을 고정 fixture로 회귀 검사 | 대용량 성능 측정은 P3로 분리 |
| 완료 | 작업표 필터 결과 피드백 | revision 저장 뒤 결과 행 수와 목록 확인 경로를 화면에 제공 | 과거 revision 직접 열람은 서버 이력 API가 필요 |
| 완료 | 분석 선택의 URL 상태 | 검색어와 열려 있는 그룹을 URL에 반영해 새로고침·공유 후 탐색 맥락 유지 | 현재 URL 파라미터만으로 충분 |
| P3 | 시각 회귀 확장 | 다크 테마와 1024px 기준선, 변동 데이터 마스킹 규칙을 추가 | 현재 1440px 라이트 테마 기준선과 1024px/768px 동작 검사가 적용됨 |
| P3 | 대용량 데이터 성능 | 200행 이상·다수 열 fixture에서 초기 렌더, 스크롤, 셀 편집 성능 측정 | 기능·접근성 회귀가 아닌 성능 측정 과업 |

## 최종 검증

- `npm run test`: Vitest 158건 통과
- `npm run build`: TypeScript 및 Vite 프로덕션 빌드 통과
- `npm run test:a11y`: axe 5화면과 시각 회귀 4화면, 총 9건 통과
- 변경 전·후 브라우저 캡처: 각 5화면, page error 0건, console error 0건
- 디자인 토큰: 신규 토큰·원시 색상 추가 없음

## P2 후속 검증 상태

- 추가: 1024px 2열·768px 1열 작업표 도구 배치와 키보드 열 선택 Playwright 검사
- 추가: 분석 검색어·그룹 열림 상태 URL 복원, 변환 결과 행 수 안내 구현
- 대기: 실행 환경의 셸 보조 프로세스 초기화 오류로 위 P2 후속 변경 뒤의 전체 자동 검증·캡처 갱신은 미실행

## 제한 사항

- 시각 기준선은 Windows/Edge 렌더링 환경의 라이트 테마 1440px `main` 영역을 대상으로 한다.
- 고정 fixture는 로컬 문서 저장소 장애와 대용량 작업표 성능을 재현하지 않는다.
