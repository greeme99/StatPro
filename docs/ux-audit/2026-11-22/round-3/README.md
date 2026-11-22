# StatPro UI/UX 3차 개선 감사

## 목표와 범위

- 참조: `D:\Workspace\StatPro\Ref.doc\3차-UI.UX_개선.md`
- 흐름: 구조 마련 → 변경 전 캡처 → 개선 제안 → 개선 반영 → 변경 후 검증
- 대상: `/home`, `/data`, `/analyses`, `/catalog/reports`
- 조건: Edge headless, 1440×1000, 라이트 테마, 한국어, 모션 감소
- 기준: 프로젝트 `DESIGN.md`, WCAG 2.1 A/AA, 한국어 제조 UX 규칙
- 데이터: 로컬 문서 저장소와 분리된 고정 API 응답

## 산출물 구조

```text
round-3/
  README.md
  captures/
    before-{home,data,analyses,reports}.png
    before-{home,data,analyses,reports}-accessibility.txt
    before-summary.json
    after-{home,data,analyses,reports}.png
    after-{home,data,analyses,reports}-accessibility.txt
    after-summary.json
```

`npm run capture:ux -- before|after`로 동일 조건의 PNG, ARIA 스냅샷, 브라우저 오류 요약을 다시 생성할 수 있다.

## 발견 사항과 개선 제안

| 우선순위 | 영역 | 발견 사항 | 개선안 | 상태 |
|---|---|---|---|---|
| P0 | 공통 셸 | 사이드바 너비 조절 버튼에 허용되지 않는 값 ARIA 속성이 있고 키보드 조절이 불가능함 | 수평 slider 역할과 현재 값·텍스트를 제공하고 화살표·Home·End 키 지원 | 반영 |
| P1 | 공통 헤더 | 즐겨찾기 버튼의 표시 텍스트와 접근 가능한 이름이 불일치함 | 중복 `aria-label`을 제거해 표시 텍스트를 이름으로 사용 | 반영 |
| P1 | 홈·공통 내비게이션 | 활성 메뉴, 작업공간 보조 라벨, DMAIC 보조 텍스트·링크의 대비가 AA 미달 | 기존 `action-hover`, `text-secondary` 의미 토큰 사용 | 반영 |
| P1 | 결과 및 보고서 | `구현됨` 배지 대비가 4.5:1에 근소하게 미달 | 기본 텍스트 토큰과 성공 테두리를 함께 사용 | 반영 |
| P0 | 음이항 회귀 | 화면 제목은 음이항 회귀지만 실행 버튼은 선형회귀로 표시됨 | 분석 유형 분기에서 `음이항 회귀 실행` 라벨 제공 | 반영 |
| P1 | 회귀 인프라 | Vitest가 Playwright 전용 파일까지 수집해 표준 검사 명령이 실패함 | Vitest 수집 범위에서 접근성 E2E 폴더 제외 | 반영 |
| P2 | 분석 선택 | 기본 분석 항목이 긴 단일 카드 목록으로 이어져 탐색 비용이 큼 | 목적별 그룹·검색 또는 접기 도입을 별도 증분으로 검증 | 보류 |
| P2 | 작업표 | 자동 감사가 빈 상태만 다뤄 정렬·결측·가로 스크롤의 실제 데이터 검증이 부족함 | 대표 작업표 fixture를 추가한 표 과업 감사를 별도 수행 | 보류 |

## 자동 접근성 결과

| 화면 | 변경 전 serious/critical 대상 | 변경 후 |
|---|---:|---:|
| 홈 | 13 | 0 |
| 작업표 및 데이터 | 3 | 0 |
| 분석 선택 | 3 | 0 |
| 결과 및 보고서 | 8 | 0 |

변경 전 규칙은 `aria-allowed-attr`, `label-content-name-mismatch`, `color-contrast`였다. 개선 후 기준선 예외를 제거했고, 네 화면 모두 위반 0을 회귀 조건으로 사용한다.

## 반영 내용

- 사이드바 너비 조절을 접근 가능한 slider로 바꾸고 키보드 조작을 추가
- 즐겨찾기 버튼의 실제 표시 텍스트를 접근 가능한 이름으로 사용
- 활성 메뉴·홈 보조 정보·DMAIC 링크에 더 진한 기존 의미 토큰 적용
- 구현 상태 배지에 텍스트 대비와 성공 상태 테두리 적용
- 음이항 회귀 실행 버튼을 화면의 분석 유형과 일치시킴
- Vitest와 Playwright 테스트 수집 범위를 분리
- axe 테스트의 기존 위반 기준선을 제거하고 0건을 통과 조건으로 강화
- 반복 가능한 전후 캡처 명령 추가

## 최종 검증

- `npm run check`: 통과
  - Vitest: 157건 통과
  - TypeScript + Vite 프로덕션 빌드: 통과
  - Playwright + axe: 핵심 4화면 통과, serious/critical 위반 0건
- 변경 전·후 브라우저 캡처: 각 4화면, page error 0건, console error 0건
- 개선 후 PNG 육안 검토: 레이아웃·텍스트 잘림·상태 표현 회귀 없음
- `git diff --check`: 통과
- 디자인 토큰: 신규 토큰과 원시 색상 추가 없음

## 남은 리스크

- axe 자동 검사는 인지 부하, 정보 구조, 업무 적합성을 보장하지 않는다.
- 분석 선택의 긴 목록과 실제 데이터가 있는 작업표의 표·필터 과업은 후속 사용성 검증이 필요하다.
- 캡처는 고정 API 응답을 사용하므로 로컬 저장소 장애와 대용량 데이터 성능은 이번 범위 밖이다.
