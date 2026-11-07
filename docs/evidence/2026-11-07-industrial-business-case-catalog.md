# 산업계 비즈니스 케이스 카탈로그 근거

## 근거 범위

이 문서는 사용자가 제공한 `산업계-비즈니스케이스1.md` 및 `산업계-비즈니스케이스2.md`를 StatPro AI Copilot Rulebase의 입력 근거로 정리한 것이다. 외부 링크의 최신성이나 제품별 구현 가능성은 이 증분에서 독립 검증하지 않았으며, 실제 연동·규제 판단은 별도 검토가 필요하다.

## 카탈로그 보완 범위

| 현장 상황 | 기본 진입 | 승격 조건 | 주요 연결 도구 |
|---|---|---|---|
| 신규 제품·회로 설계 | DFSS/DMADV 안내 | 양산·고객 영향과 CTQ가 확정됨 | CTQ, DFMEA, Robust DOE, 검증계획 |
| PCB 표면처리·도금 편차 | DOE/SPC 안내 | 수율·스크랩 영향이 기준을 초과함 | DOE, 공정능력, SPC, PFMEA |
| 솔더페이스트 인쇄 편차 | SPC/DOE 안내 | FPY·재작업 비용 영향이 명확함 | SPI MSA, DOE, 관리도 |
| 부품 배치 편차 | MSA/DOE 안내 | 미스픽·배치 정확도 손실이 반복됨 | AOI MSA, DOE, SPC |
| ICT/FCT 오검출 | MSA 안내 | 출하·고객 불량 또는 검사비용 영향이 명확함 | Attribute MSA, DOE, FMEA |
| 조립·체결 불량 | FMEA/SPC 안내 | 안전·고객·재작업 영향이 명확함 | Torque SPC, PFMEA, Control Plan |
| 반도체 공정 drift/excursion | SPC 안내 | lot 격리·수율 손실 등 사업영향이 명확함 | SPC, FDC/APC/R2R 연계, FMEA |
| 출하·현장 클레임 | DMAIC 안내 | 반복·보증·재무 영향이 명확함 | 8D/CAPA, Pareto, FMEA, SPC |

## Rulebase 운영 원칙

1. 사용자의 현상과 데이터 형태를 먼저 확인하고, 가장 작은 작업공간으로 시작한다.
2. 측정시스템과 기준선이 불명확하면 MSA·데이터 준비를 먼저 안내한다.
3. 사업영향(수율, PPM, 보증비, 안전, 고객 영향)이 명확하면 단일 분석을 DMAIC 프로젝트로 승격한다.
4. DMAIC 승격은 자동 변경이 아니라 Copilot의 설명·체크리스트·사용자 확인을 거친다.
5. FDC/APC/R2R, Attribute MSA, 8D/CAPA, DFSS/DMADV의 완전한 실행은 현재 Rulebase의 안내·외부 연계 필요 항목으로 기록한다.

