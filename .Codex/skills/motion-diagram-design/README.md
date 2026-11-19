# 🎬 Motion Diagram Design Skill (범용 모션 다이어그램 디자인 스킬)

> **"복잡한 업무 흐름, 시스템 구성도, 파이프라인을 살아 숨쉬며 스스로 설명하는 인터랙티브 모션 그래픽 HTML 아티팩트로 자동 생성하는 범용 스킬"**

---

## 🌟 주요 특징 (Key Features)

1. **10대 인포그래픽 & 다이어그램 비주얼 테마 지원**:
   - 🏢 **3단 스윔레인 플로우 (`swimlane`)**: 역할별 레인 + 에어갭 보안 경계 + 양방향 피드백 분기
   - 📍 **수평 교차 핀 타임라인 (`timeline`)**: 수평 레일 위아래로 교차하는 인포그래픽 핀
   - ⏩ **셰브론 파이프라인 (`chevron`)**: 맞물리는 화살촉 셰브론 블록 + 세그먼트 카드
   - 🛣️ **커브드 아스팔트 로드맵 (`roadmap`)**: S자 고속도로 + 마일스톤 핀 + 질주하는 자동차
   - 💎 **다이아몬드 코어 허브 (`hub`)**: 45도 회전 코어 심장박동 + 방사형 빔
   - 🧩 **인터로킹 퍼즐 체인 (`interlock`)**: 직소 퍼즐 결합형 단계별 프로세스
   - 📝 **손글씨 줄노트 스케치 (`sketch`)**: 아날로그 볼펜 잉크 + 고대비 칠판 다크모드
   - 💻 **모던 UI 대시보드 (`modern`)**: 글래스모피즘 + 캔버스 데이터 파티클 + 신디사이저 사운드
   - 📖 **기술 문서 파이프라인 (`docs`)**: 아키텍처 다이어그램 + 수식/코드 인스펙터
   - ✦ **올인원 테마 스튜디오 (`studio`)**: 상단 탭으로 10개 모든 테마 실시간 전환

2. **완벽한 공통 제어기 기본 탑재**:
   - **상단 고정 헤더 (`sticky`)**: 스크롤을 내려도 항상 최상단에 고정
   - **4단계 속도 조절 (`⚡ 0.5x / 1.0x / 1.5x / 2.0x`)**: 실시간 타이머 가속
   - **라이트 / 다크 모드 (`🌙 / ☀️`)**: 전면 딥 슬레이트 & 고대비 보색(Complementary Color) 적용
   - **단축키 지원**: `Space` (재생/일시정지), `←` / `→` (스텝 이동), `R` (초기화)
   - **오프라인 100% 자립 동작**: CDN 없이 로컬 브라우저에서 단일 파일로 실행

---

## 🚀 빠른 시작 (Quick Start)

### 1) AI 에이전트에게 요청하기
Antigravity, Codex, Claude Code, Cursor 등 코딩 에이전트에게 다음과 같이 요청하면 자동으로 생성됩니다:

```text
"우리 서비스의 사용자 주문 및 배포 프로세스를 /motion-diagram-design 스킬을 사용해서 
스스로 설명하는 인터랙티브 모션 그래픽 HTML 다이어그램으로 만들어줘."
```

### 2) 파이썬 CLI로 생성하기

```bash
# 기본 교차 핀 타임라인 생성
py scripts/generate_motion_diagram.py --theme timeline --input examples/sample_workflow.json --output my_timeline.html

# 셰브론 화살표 파이프라인 생성
py scripts/generate_motion_diagram.py --theme chevron --input examples/demo_e_commerce.json --output my_ecommerce.html
```

### 3) 원클릭 데모 실행 (Windows)
`examples/run_demo.bat`을 더블 클릭하면 브라우저에서 사전 렌더링된 데모가 즉시 실행됩니다.

---

## 📂 패키지 구조

```
motion-diagram-design/
├── SKILL.md                          # 에이전트용 메인 스킬 지침 (V3.0 Universal)
├── README.md                         # 사용자 안내서 (현재 문서)
├── manifest.json                     # 스킬 메타데이터
├── scripts/
│   └── generate_motion_diagram.py    # 범용 Python CLI 생성기
├── examples/
│   ├── sample_workflow.json          # 범용 워크플로우 예제 데이터
│   ├── demo_e_commerce.json          # 이커머스 주문 흐름 데이터
│   ├── demo_ai_pipeline.json         # AI MLOps 파이프라인 데이터
│   ├── demo_swimlane.html            # 3단 스윔레인 데모
│   ├── demo_timeline.html            # 교차 핀 타임라인 데모
│   ├── demo_chevron.html             # 셰브론 파이프라인 데모
│   ├── demo_roadmap.html             # 아스팔트 로드맵 데모
│   ├── demo_sketch.html              # 손글씨 칠판 스케치 데모
│   ├── demo_studio.html              # 10대 테마 통합 스튜디오 데모
│   └── run_demo.bat                  # 원클릭 브라우저 런처
```
