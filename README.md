# StatPro

전자 제조 현장의 제조·품질·연구개발 업무를 위한 로컬 우선 통계 분석 플랫폼입니다. 데이터, 분석 실행, 시각화, 결과 보고서, FMEA 조치와 승인 근거를 하나의 재현 가능한 작업 흐름으로 연결합니다.

## 현재 제품 기준선

- **실험계획법(DOE)**: 완전·일부 요인, 자동 생성식, 블록·foldover, Box–Behnken·중심합성·Plackett–Burman, 반응 분석, 제약 다중응답 최적화
- **통계적 공정관리(SPC)**: I-MR, Xbar-R, Xbar-S, EWMA, CUSUM, p/np/c/u, Laney P′/U′, 희귀사건 G/T, 정규·경험적 비정규 공정능력
- **측정시스템분석(MSA)**: 균형 교차·중첩 Gage R&R(비풀링 ANOVA F·p 판정, 반복성 분산의 정확 95% 신뢰구간), Attribute Agreement, Gage 편의·선형성
- **고장 형태 및 영향 분석(FMEA)**: 불변 개정, AIAG/VDA 7단계, 조치·재평가·검토·승인, 외부 Action Priority 정책, PFMEA–Control Plan 추적, SPC/MSA Run 연결
- **데이터·실행 관리**: UTF-8 CSV와 값 전용 XLSX 첫 워크시트 Dataset snapshot, 필터·정렬·선택형 사칙연산 파생 열·현재 revision CSV 내보내기를 갖춘 Worksheet, Analysis Run, ETag/낙관적 동시성, cursor paging, ResultBundle
- **결과 출력**: 모든 Analysis Run의 읽기 전용 인쇄 보고서·JSON·CSV·Excel 호환 표, SPC 관리도의 PNG·SVG 차트 출력
- **품질 도구와 DMAIC 연결**: 체크 시트, 일반 파레토, 특성요인도, 홈 기반 DMAIC 작업 흐름과 학습 리소스
- **품질 대시보드**: 저장된 ResultBundle의 수치 경로를 불변 지표 스냅샷으로 연결하고 상태·담당·검토 주기·원본 Run 증거를 함께 표시
- **결함 분석**: 체크 시트 개정 근거 또는 수동 입력에서 범주별 결함·검사 기회·단위 손실·심각도를 기록하고 DPMO·손실·위험 우선순위를 불변 개정으로 보존
- **AI Copilot**: 오른쪽 보이기·감추기 대화 패널에서 현재 작업공간과 저장된 분석 실행·DMAIC 프로젝트 근거를 읽고, 검토된 Rulebase로 추천 도구·메뉴 경로·체크리스트·업무절차를 우선 안내. 대화에서 선택한 Workflow는 현재 단계 완료와 작업공간 이동으로 이어지며, 설정·결과·프로젝트 문서는 사용자가 해당 작업공간에서 별도로 저장함
- **분석 선택 도우미**: 판단 목적, 데이터 유형, 표본·기회 구조를 단계적으로 선택해 현재 실행 가능한 SPC·DOE·FMEA·DMAIC 작업공간과 필수 입력·사전 점검 항목을 제안

제품 웹 UI의 표준 흐름은 `홈(Home) → 작업공간(Workspace) → 작업 흐름(Workflow) → 데이터 입력(Input) → 분석 실행(Run) → 결과 검토(Review) → 결과 출력(Export)`입니다. 메뉴와 화면 표기는 한국어를 우선하고 필요한 경우 영어를 괄호로 병기합니다. 홈의 DOE·SPC·FMEA 카드에서 저장한 즐겨찾기는 상단 우측의 **즐겨찾기** 메뉴와 홈 바로가기 영역에 현재 브라우저별로 보존되어 즉시 작업공간을 열 수 있습니다.

## 빠른 시작

### 통계 코어와 CLI

```powershell
py -3.12 -m unittest discover -s tests -v
$env:PYTHONPATH = "src"
py -3.12 -m statpro.cli xbar-r --input samples\xbar-r.json
py -3.12 -m statpro.cli xbar-s --input samples\xbar-s.json
py -3.12 -m statpro.cli imr --input samples\imr-nist.json
py -3.12 -m statpro.cli ewma --input samples\ewma.json
py -3.12 -m statpro.cli cusum --input samples\cusum.json
py -3.12 -m statpro.cli p-chart --input samples\p-chart.json
py -3.12 -m statpro.cli doe-full-factorial --input samples\doe-full-factorial.json
py -3.12 -m statpro.cli doe-optimize-responses --input samples\doe-response-optimizer.json
py -3.12 -m statpro.cli gage-rr-crossed --input samples\gage-rr-crossed.json
```

### 로컬 API 및 웹 UI

```powershell
py -3.12 -m pip install -e ".[api]"
statpro-api --storage "D:\StatProData" --host 127.0.0.1 --port 8765

cd web
npm ci
npm run dev -- --host 127.0.0.1
```

### AI Copilot의 선택적 생성형 AI 연결

기본 상태는 외부 호출이 비활성화되어 Rulebase만 사용합니다. 저장소 루트의 `.env.example`을 `.env`로 복사한 뒤, 키를 **채팅이나 Git에 올리지 말고 로컬 `.env`에만** 입력합니다.

```powershell
Copy-Item .env.example .env
```

```dotenv
STATPRO_COPILOT_LLM_ENABLED=true
GEMINI_API_KEY=여기에_발급받은_키를_입력
STATPRO_COPILOT_GEMINI_SIMPLE_MODEL=gemini-3.5-flash-lite
STATPRO_COPILOT_GEMINI_COMPLEX_MODEL=gemini-3.8-flash
```

API는 `statpro-api` 실행 시 저장소 루트의 `.env`를 읽습니다. 다른 파일을 쓰려면 `statpro-api --env-file "D:\secure\statpro.env" ...`처럼 지정합니다. `.env`는 `.gitignore`로 제외되며, 이미 설정된 프로세스 환경 변수는 파일 값으로 덮어쓰지 않습니다. Rulebase 미일치 요청은 난이도 분류 후 단순 요청은 Gemini 3.5 Flash-Lite, 복잡·다단계·코드 요청은 Gemini 3.8 Flash로 전달합니다. Gemini에는 미일치 질문과 현재 작업공간 문맥만 전달되므로 조직 정책과 개인정보 기준을 확인한 뒤 활성화하십시오.

Gemini 호출이 실패했거나 비활성화된 경우에는 아래 Ollama OpenAI 호환 `chat/completions` endpoint로 폴백합니다. 일반 Workflow에는 `qwen3:4b-q4_K_M`, 코드 생성 요청에는 `qwen2.5-coder:7b-instruct-q4_K_M`을 사용합니다. `http://127.0.0.1`, `http://localhost`, `http://[::1]` 같은 loopback HTTP 주소만 허용하며, Rulebase가 일치한 질의는 모델로 전송하지 않습니다. 모든 모델이 실패하면 Copilot은 재시도와 분석 목적·데이터 구조·제약의 수동 입력을 안내합니다.

```dotenv
STATPRO_COPILOT_OLLAMA_ENABLED=true
STATPRO_COPILOT_OLLAMA_URL=http://127.0.0.1:11434/v1/chat/completions
STATPRO_COPILOT_OLLAMA_WORKFLOW_MODEL=qwen3:4b-q4_K_M
STATPRO_COPILOT_OLLAMA_CODE_MODEL=qwen2.5-coder:7b-instruct-q4_K_M
```

API 문서: <http://127.0.0.1:8765/docs> · 웹 UI: <http://127.0.0.1:5173>

주요 화면 경로는 `/home`, `/data`, `/doe`, `/spc`, `/fmea`, `/quality`, `/defects`, `/home/dmaic`, `/home/learning`입니다. `/api` 요청은 loopback API로 프록시됩니다.

## 결과와 내보내기

모든 분석은 입력 digest, 엔진 버전, 옵션, 경고, 공개 근거를 포함하는 `ResultBundle` 경계를 통과합니다. DOE는 결정론적 JSON·HTML·수식 없는 XLSX·UTF-8 CSV 표와 SVG 그래프가 포함된 ZIP 내보내기를 제공합니다. 모든 결과는 경로·값 단일 시트 SpreadsheetML Excel 호환 표를 제공하며 원래 계층 구조는 JSON으로 확인합니다. I-MR, Xbar-R, Xbar-S는 추가로 브라우저 인쇄용 HTML(PDF 저장 가능), 전용 SpreadsheetML Excel, 결합 PNG·접근 가능한 SVG를 제공합니다. EWMA·CUSUM·p/np/c/u·Laney P′/U′·희귀사건 G/T는 저장된 `ResultBundle` 차트 데이터로 단일 PNG·접근 가능한 SVG를 생성합니다. 모든 출력은 Run ID·입력 digest·엔진 버전을 함께 보존하며, 차트 화면은 핵심 수치, 관리한계, 이상 신호, 접근 가능한 대체 표, 다음 조치를 같은 결과 맥락에 표시합니다.

브라우저 인쇄 기반 PDF의 파일 생성·보관은 사용자의 브라우저 인쇄 대화상자가 담당합니다. I-MR, Xbar-R, Xbar-S 외 SPC 관리도의 전용 PDF·Excel 보고서와 공정능력 전용 PNG·SVG, 조직별 규제/고객 템플릿은 기능별 지원 계약을 확인해야 하는 후속 범위입니다.

## 개발 및 검증

```powershell
py -3.12 -m unittest discover -s tests -q
cd web
npm run check
cd ..
python tools\oss_gate.py --check
```

현재 기준 검증 결과는 Python 267개와 웹 99개 테스트 통과, 웹 빌드 통과, OSS 게이트 통과입니다. 전체 Ruff 실행에는 기존 코드의 비관련 lint 항목이 남아 있으므로 새 변경은 대상 파일에 대해 별도 검사하고 기존 부채는 후속 정리 항목으로 추적합니다.

차트 엔진은 제품 런타임에서 Recharts를 사용합니다. ECharts 6.1.0은 `web/benchmarks/chart-engines/`의 격리된 성능 비교에만 존재하며 제품 코드로 가져오지 않습니다. 근거는 [브라우저 벤치마크](docs/evidence/chart-engine-browser-benchmark.json), [번들 벤치마크](docs/evidence/chart-engine-bundle-benchmark.json)에 보존합니다.

## 설계 원칙

- 공개 통계 기준과 재현 가능한 fixture를 계산 근거로 사용합니다.
- 상용 제품의 바이너리 내부·전용 UI 자산·결정 테이블을 제품 코드에 복사하지 않습니다.
- 결측값은 명시적으로 보존하며 0으로 조용히 대체하지 않습니다.
- 관리한계와 규격한계를 별도 도메인 개념으로 유지합니다.
- 원본 입력, 변환, 옵션, 엔진 버전, 결과와 근거를 추적합니다.
- 외부 정책·IdP·승인 정보가 검증되지 않으면 확정 상태로 표시하지 않습니다.

## 문서 지도

- [요구사항 명세서(SRS)](docs/01.StatPro_SRS.md)
- [제품 기능·상세 명세서(PRD/FS)](docs/02.StatPro_PRD_FS.md)
- [정보구조도(IA)](docs/03.StatPro_IA.md)
- [와이어프레임](docs/04.StatPro_Wireframes.md)
- [UI 디자인 기준](docs/05.StatPro_UI_Design.md)
- [개발 스택·아키텍처](docs/06.StatPro_Development_Stack.md)
- [테스트 결과 보고서](docs/07.StatPro_Test_Report.md)
- [메뉴·화면 제안 및 상태](docs/08.StatPro_Menu_UI_Proposal.md)
- [오픈소스 거버넌스](docs/09.StatPro_OSS_Governance.md)
- [컨텍스트 맵](CONTEXT-MAP.md)
