# DOE 표준 보고서·내보내기 근거 기록

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

- 저장된 DOE `ResultBundle`을 `statpro.doe.analysis_report.v1`로 한 번 투영하며 Run ID·storage version·ETag, analysis/input/result/report digest를 함께 보존한다.
- 표는 행·열·row count와 원래 값을 유지한다. 중첩 셀은 CSV에서 정렬된 JSON 문자열로 표현한다.
- 의미 기반 HTML은 외부 스크립트·스타일·네트워크 요청 없이 같은 보고서 계약에서 생성한다.
- ZIP은 고정 entry 시각·순서·권한을 사용하고 HTML, JSON, 데이터가 있는 각 표의 UTF-8 BOM CSV를 담아 같은 입력에서 같은 bytes를 반환한다.
- REST API와 React 결과 화면은 같은 application report owner를 사용한다. 보고서 조회와 다운로드는 원 Run을 변경하지 않는다.

## 검증과 제한

- 2요인 완전요인 Run에서 보고서 식별값·4개 설계 행을 회수하고 동일 보고서와 ZIP의 결정성을 검증했다.
- JSON·HTML·ZIP 응답은 같은 report digest ETag를 반환하며 비 DOE Run은 `unsupported_report_type`으로 거부한다.
- UI는 DOE 결과에서 HTML과 CSV·JSON ZIP 링크를 키보드 접근 가능한 native link로 제공한다.
- 대표 2요인 완전요인 Run의 JSON 투영·HTML·ZIP 생성은 cold wall 5.176ms/CPU 0ms(타이머 해상도 미만), warm 100회 평균 wall 4.634ms/CPU 4.688ms, Python 추적 할당 peak 420,852 bytes, HTML 4,508 bytes, ZIP 3,280 bytes였다. 프로세스 패밀리 peak memory와 agent token 비용은 측정하지 않았다.
- 그래프 이미지를 렌더링하지 않고 `plots` 데이터를 JSON에 보존한다. PDF/RTF/XLSX, 고객별 템플릿·서명, 다중 Run 합성 보고서와 Minitab 파일/배치 동등성은 지원하지 않는다.
