# 산업계 비즈니스 케이스 4·5·6 근거 및 Copilot 반영

## 범위

다음 사용자 제공 문서를 근거로 Rulebase 카탈로그를 보완했다.

- `D:\Workspace\StatPro\Ref.doc\산업계-비즈니스케이스4.md`
- `D:\Workspace\StatPro\Ref.doc\산업계-비즈니스케이스5.md`
- `D:\Workspace\StatPro\Ref.doc\산업계-비즈니스케이스6.md`
- `D:\Workspace\StatPro\Ref.doc\산업계-비즈니스케이스7.md`

이 문서는 문서에 적힌 사례·체크리스트·권장 흐름과 StatPro가 현재 안내할 수 있는 작업공간 경계를 구분한다. 문서의 외부 표준·고객 기준은 제품에 내장된 사실로 승격하지 않고 출처와 적용판 확인을 요구한다.

## 카탈로그 반영

| Rule ID | 문서 근거 | Copilot 진입점 | 핵심 안내 |
|---|---|---|---|
| `fmea-prevention-detection-action` | 4: 예방·탐지 조치 마스터, AP 재평가 | FMEA 조치·검토·승인 | 예방과 탐지를 분리하고 조치 후 O·D·AP를 재평가 |
| `dmaic-yield-optimization` | 4·5: FPY/RTY/Scrap/Rework/DPMO/Cpk 및 DMAIC 체크리스트 | DMAIC 프로젝트 개요 | MSA·기준선부터 시작하고 사업영향이 명확할 때 DMAIC 승격을 승인 |
| `doe-monte-carlo-robustness` | 4·5: 분포·공차·상관관계·Pilot 검증 | DOE 반응표면 및 최적화 | 시뮬레이션은 강건성 검토로 사용하고 실측·Pilot으로 확인 |
| `doe-reflow-profile-void` | 5·6: Ramp/Soak/TAL/Peak/Cooling, BGA Void | DOE 실험 설정 | Void·툼스톤 등 반응과 프로파일 요인을 함께 설계 |
| `spc-rule-response-plan` | 7: Western Electric/Nelson 규칙, 반응계획·CAPA | SPC 관리도 결과·반응계획 | 신호 규칙을 지정하고 담당·기한·재검증을 연결 |
| `fmea-high-ap-evidence` | 7: High AP 예방·탐지 조치 및 검증 | FMEA 조치·검토·승인 | High AP 조치 또는 현행관리 타당성 근거를 감사 가능하게 기록 |

## 운영 원칙

1. FMEA의 예방조치와 탐지조치는 별도 필드와 증거로 기록한다. 검사 강화만으로 예방조치를 대체하지 않는다.
2. 수율 개선은 평균 수율 하나가 아니라 FPY·RTY·Scrap·Rework·DPMO·Cpk의 정의와 기간을 먼저 고정한다.
3. Monte Carlo·DOE 결과는 추정치다. 분포 선택, 상관관계, 규격, 반복 횟수와 Pilot 검증 여부를 함께 표시한다.
4. 리플로우 기준값은 제품·페이스트·장비·고객 규격과 표준 개정판을 확인한 뒤 사용한다. Copilot은 이미지나 문서만으로 공정 설정값을 확정하지 않는다.
5. FDC/APC/R2R, PPAP, 8D/CAPA, Attribute MSA와 같은 외부 시스템·정책 연동은 현재 구현 여부를 확인하고 미연동 상태로 명시한다.
6. IPC-7095·IPC-A-610·J-STD-001 및 고객도면의 Void 합격 기준은 제품별 적용판과 고객 요구를 확인해야 하며, Rulebase가 임의의 합격·불합격을 결정하지 않는다.

## 관찰과 제안의 구분

- **문서에서 관찰한 내용**: SMT·리플로우·FMEA·DMAIC·Monte Carlo·SPC의 사례와 KPI, 외부 표준 링크.
- **비즈니스 케이스 7 추가 관찰**: High AP 조치, BGA Void 판정의 우선순위, Western Electric/Nelson 규칙과 CAPA 연결, 리플로우 ANOVA 예시.
- **StatPro가 제안하는 흐름**: 데이터·MSA → 원인/위험 구조화 → DOE 또는 SPC 실행 → 검증 → Control Plan/FMEA 연결.
- **미확인**: 특정 고객의 합격 기준, 현장 장비의 실시간 연결, 조직별 AP 정책, 외부 IdP·CAPA·MES 연동 상태.

