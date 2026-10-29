# DOE 보고서 양식·SVG 그래프 내보내기 근거 기록

## Minitab 14 정적 관찰

- 대상: `C:\Program Files (x86)\MINITAB 14\mtb14.exe`, SHA-256 `bdb292434b7a95164fd47bc9b1bdead9fe479a077e1b54cafac365e3cfa019db`.
- 기존 Ghidra Evidence `ev_5e02d8b4b8a90989ba7d44912f6254c916e1545643643717a473bf717d6a3a27`에서 `CmGraphPrintMgr::mPrintGraph`, `CmGraphDoc::mCopyGraphToPrinter`, `CmGraphDoc::mCopyGraphToClipboard`, `CmWorksheet::mGetHTMLOptions` 이름을 관찰했다.
- 이 이름은 그래프 인쇄·복사와 Worksheet HTML 옵션 기능 후보만 나타낸다. DOE 보고서 구성, 세션 출력 저장 형식, 표 선택, CSV 직렬화, 메뉴 기본값과 실제 런타임 동작은 확인하지 않았다.

## 공개 행동 교차검토

- 현재 Minitab 공개 도움말은 선택 출력의 RTF/HTML 저장, 개별 표·그래프 또는 분석 전체를 보고서로 보내는 흐름을 설명한다.
  - https://support.minitab.com/en-us/minitab/help-and-how-to/data-input-and-output/save-and-export-data-and-output/save-and-export-output-graphs-reports-and-history/
  - https://support.minitab.com/en-us/minitab/help-and-how-to/minitab-environment/interface/interface-components/reports/
- 위 자료는 현재 제품의 공개 행동 교차검토이며 Minitab 14의 내부 구현이나 정확한 형식 증거가 아니다.

## StatPro 독립 구현

- 저장된 DOE `ResultBundle`을 `statpro.doe.analysis_report.v2`로 한 번 투영하며 Run ID·storage version·ETag, analysis/input/result/report digest를 함께 보존한다.
- 표는 행·열·row count와 원래 값을 유지한다. 중첩 셀은 CSV에서 정렬된 JSON 문자열로 표현한다.
- 의미 기반 HTML은 외부 스크립트·스타일·네트워크 요청 없이 같은 보고서 계약에서 생성한다. 지원되는 effect/Pareto형 막대 plot과 잔차 계열 plot은 저장된 수치에서 결정적으로 SVG를 만들고 HTML에는 data URI로 포함한다.
- `standard`, `customer_review`, `regulatory_review` 양식은 같은 원 Run을 서로 다른 검토 문서로 투영한다. 고객·규제 양식은 조직 입력 필드를 안내할 뿐 고객 승인이나 규제 준수 여부를 판정하지 않는다.
- ZIP은 고정 entry 시각·순서·권한을 사용하고 HTML, JSON, 지원 SVG, 데이터가 있는 각 표의 UTF-8 BOM CSV를 담아 같은 입력에서 같은 bytes를 반환한다.
- REST API와 React 결과 화면은 같은 application report owner를 사용한다. 보고서 조회와 다운로드는 원 Run을 변경하지 않는다.

## 검증과 제한

- 2요인 완전요인 Run에서 보고서 식별값·4개 설계 행을 회수하고 동일 보고서와 ZIP의 결정성을 검증했다.
- JSON·HTML·ZIP 응답은 같은 report digest ETag를 반환하며 비 DOE Run은 `unsupported_report_type`으로 거부한다.
- UI는 DOE 결과에서 보고서 양식 선택과 HTML·그래프·CSV·JSON ZIP 링크를 키보드 접근 가능한 native link로 제공한다.
- 이전 v1 측정값은 SVG 렌더링과 검토용 양식이 없는 구현의 수치이므로 v2 성능 주장에 사용하지 않는다. v2의 대표 cold/warm wall·CPU·프로세스 패밀리 peak memory·agent token 비용은 아직 측정하지 않았다.
- 지원되지 않는 plot 구조는 `plots` 데이터만 보존하고 이미지로 추정·재계산하지 않는다. PDF/RTF/XLSX, 조직별 승인 전자서명·필수 항목 검증, 다중 Run 합성 보고서와 Minitab 파일/배치 동등성은 지원하지 않는다.
