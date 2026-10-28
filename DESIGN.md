# StatPro Design System

StatPro inherits **Work App Design System v1.0** from `C:\Users\0208m\.codex\DESIGN.md` without token overrides.

## Product application

- Product name: StatPro
- Product type: desktop-first manufacturing analytics web application
- Themes: light and dark
- Densities: comfortable for dashboards/forms, compact for worksheets and analysis tables
- Minimum supported viewport: 768px
- Accessibility: WCAG 2.1 AA
- Font assumption: Pretendard Variable with the global fallback stack
- Chart assumption: Recharts for the first release; evaluate ECharts before large time-series delivery

## Mandatory rules

- UI values reference the inherited CSS tokens; components must not introduce raw colors, spacing, radii, shadows, or z-index values.
- `brand-500`, `success-500`, and `danger-500` are fill/chart colors, not text colors.
- Every data view provides loading, empty, error, and keyboard-accessible states.
- Charts provide an accessible summary and a data table alternative.
- Missing observations are never plotted as zero.
- Status is communicated with text or icons in addition to color.
- Each screen has at most one primary action.
- Analysis drill-down uses the standard DetailDrawer and mirrors state in the URL.

The inherited global document remains the complete token and component specification.

## Korean product language and delivery status

All user-visible navigation, controls, guidance, empty states, validation
messages, reports, and accessibility labels are written in Korean. International
manufacturing abbreviations may be retained only when the Korean name appears
with them on first use.

| Canonical label | Use in the product |
|---|---|
| 실험계획법(DOE) | DOE workspace, design, analysis, optimization |
| 통계적 공정관리(SPC) | control charts and process capability |
| 고장 형태 및 영향 분석(FMEA) | study, PFMEA, control plan, approval |
| 작업표 | worksheet |
| 분석 실행 | immutable Analysis Run |
| 결과 및 보고서 | run history and report/export surfaces |
| 단계별 설정 | guided workflow |
| 빠른 설정 | expert/direct setup |

Do not use commercial upsell language such as `Pro`, `잠금 해제`, daily credit,
or artificial feature locks. The navigation catalog communicates delivery
truthfully with a status badge:

- `구현됨`: an end-to-end local workflow is available now.
- `개발 예정`: a named capability is planned but cannot be started.
- `외부 정책 필요`: the feature needs organization-supplied policy or identity
  integration; do not imply that it is enabled.

Badges never replace a written empty state. A planned destination explains its
scope, dependency, and the closest usable current workflow.

## Manufacturing workspace patterns

- Use cards to choose a workspace or start an action; use tables, charts, and
  traceability links for actual DOE, SPC, and FMEA work.
- Keep one shared process shell: `설정 → 데이터 → 분석 → 결과 → 보고서`.
  A module may hide inapplicable steps but must not reorder them.
- A setup screen shows completion conditions next to a disabled primary action.
  Never leave users to infer why `실행표 생성` or `분석 실행` is unavailable.
- DOE uses a guided setup rail for `목적 · 인자와 반응 · 설계와 블록 · 실행표 · 분석과 최적화`.
- SPC puts chart, signal summary, baseline parameters, and capability evidence
  in one run-oriented view.
- FMEA prioritizes the compact traceability table and revision/approval state;
  its risk records are not represented as decorative cards.
