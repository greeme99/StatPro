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
