# -*- coding: utf-8 -*-
"""
Build Universal Motion Diagram Design Skill Package
Creates:
1. Universal CLI generator supporting all 10 themes
2. Sample JSON datasets (E-Commerce, AI Pipeline, Standard Workflow)
3. Universal SKILL.md (V3.0 Universal Edition)
4. README.md & run_demo.bat
5. Pre-rendered HTML examples
6. Zipped release archive for instant download
"""

import os
import sys
import json
import zipfile
import shutil

DIST_DIR = os.path.abspath('dist/motion-diagram-design')
GLOBAL_SKILL_DIR = os.path.abspath('C:/Users/0208m/.gemini/config/skills/motion-diagram-design')
CODEX_SKILL_DIR = os.path.abspath('.Codex/skills/motion-diagram-design')
ARTIFACT_DIR = os.path.abspath('C:/Users/0208m/.gemini/antigravity/brain/3b3a945f-274b-405e-9963-58792169202a')

# Create necessary folders
for base in [DIST_DIR, GLOBAL_SKILL_DIR, CODEX_SKILL_DIR]:
    os.makedirs(os.path.join(base, 'scripts'), exist_ok=True)
    os.makedirs(os.path.join(base, 'examples'), exist_ok=True)
    os.makedirs(os.path.join(base, 'templates'), exist_ok=True)

# -------------------------------------------------------------
# 1. SAMPLE JSON DATASETS
# -------------------------------------------------------------
SAMPLE_WORKFLOW_JSON = {
    "title": "엔드투엔드 디지털 업무 프로세스",
    "subtitle": "데이터 인입부터 자동 검증, 분기 처리 및 최종 승인까지의 표준 흐름",
    "author": "시스템 아키텍처 팀",
    "version": "1.0.0",
    "lanes": [
        {
            "id": "lane-user",
            "title": "요청자 / 고객",
            "desc": "서비스 신청 · 요구사항 입력"
        },
        {
            "id": "lane-platform",
            "title": "서비스 플랫폼 (웹/API)",
            "desc": "실시간 유효성 검증 · 라우팅"
        },
        {
            "id": "lane-core",
            "title": "엔터프라이즈 코어 / DB",
            "desc": "무결성 보장 · 트랜잭션 처리 (안전 격리 구역)"
        }
    ],
    "steps": [
        {
            "step": 0,
            "id": "step-1",
            "title": "서비스 신청 및 요청 데이터 인입",
            "banner": "Step 1: 사용자가 요구사항을 제출하고 세션이 안전하게 초기화됩니다.",
            "desc": "사용자가 웹 폼 또는 API를 통해 요청 데이터를 제출하면 플랫폼 게이트웨이가 즉시 수신하여 불변 원본 스냅샷을 생성합니다.",
            "laneNodes": {
                "lane-user": {"title": "신청서 작성 & 제출", "desc": "요청 데이터 전송"},
                "lane-platform": {"title": "API 게이트웨이 수신", "desc": "인증 토큰 & 스키마 확인"},
                "lane-core": {"title": "세션 레코드 초기화", "desc": "불변 트랜잭션 ID 발급"}
            },
            "checklist": ["요청자 인증(OAuth/JWT) 검증 완료", "페이로드 스키마 정합성 통과", "감사 로그 세션 커밋"],
            "security": "SSL/TLS 1.3 암호화 전송",
            "engine": "FastAPI Gateway & Auth Validator",
            "rule": "표준 설계 1단계 (Ingestion)"
        },
        {
            "step": 1,
            "id": "step-2",
            "title": "비즈니스 규칙 검증 및 데이터 무결성 스캔",
            "banner": "Step 2: 비즈니스 정책 한계선 및 결측/이상치를 자동으로 정밀 검증합니다.",
            "desc": "수신된 데이터가 업무 규칙과 제약 조건을 만족하는지 규칙 엔진이 실시간 검사합니다. 결측치나 위배 데이터는 사전 격리됩니다.",
            "laneNodes": {
                "lane-user": {"title": "실시간 진행 상태 확인", "desc": "진행률 바 피드백"},
                "lane-platform": {"title": "비즈니스 룰 스캔", "desc": "필드별 제약 조건 검사"},
                "lane-core": {"title": "결측/이상치 사전 격리", "desc": "데이터 정합성 보장"}
            },
            "checklist": ["필수 파라미터 누락 여부 검증", "데이터 타입 및 범위 유효성 체크", "이상치 탐지 알고리즘 실행"],
            "security": "Pydantic V2 Strict Validation",
            "engine": "Business Rules Engine (BRE)",
            "rule": "표준 설계 2단계 (Verification)"
        },
        {
            "step": 2,
            "id": "step-3",
            "title": "코어 트랜잭션 연산 및 처리",
            "banner": "Step 3: 안전한 코어 엔진에서 비즈니스 로직 연산을 고속 수행합니다.",
            "desc": "정합성이 검증된 데이터를 바탕으로 핵심 로직(정산, 통계 산출, AI 추론, 주문 확정 등)을 트랜잭션 무결성 하에 고속 연산합니다.",
            "laneNodes": {
                "lane-user": {"title": "입력 보완 요청 알람", "desc": "특이사항 발생 시 알림"},
                "lane-platform": {"title": "실시간 연산 모니터링", "desc": "처리 진행률 렌더링"},
                "lane-core": {"title": "코어 연산 엔진 가동", "desc": "트랜잭션 커밋 & 락 관리"}
            },
            "checklist": ["ACID 트랜잭션 무결성 보장", "연산 완료 결과 ResultBundle 생성", "처리 지연 0.5초 이내 유지"],
            "security": "DB Row-level Optimistic Locking",
            "engine": "High-Performance Core Engine",
            "rule": "표준 설계 3단계 (Processing)"
        },
        {
            "step": 3,
            "id": "step-4",
            "title": "품질 판정 및 분기 처리 (확정 vs 협의 대기)",
            "banner": "Step 4: 모든 기준을 만족하면 즉시 확정되며, 이상 감지 시 예외 처리 루프가 작동합니다.",
            "desc": "판정 기준을 100% 충족하면 '승인/확정'으로 직행하며, 정책 위배나 수치 이상 발견 시 '협의 대기(보류)'로 분기하여 담당자 조치 후 승인 루프를 탑니다.",
            "laneNodes": {
                "lane-user": {"title": "최종 결과 수신 대기", "desc": "확정 / 협의 분기"},
                "lane-platform": {"title": "분기 결과 라우터", "desc": "정상 승인 vs 보류 라우팅"},
                "lane-core": {"title": "확정 (정상 완료)", "desc": "기준 충족 · 승인 커밋", "branch": "ok"}
            },
            "checklist": ["정상 기준: 룰 위배 0건 확인 즉시 승인", "이상 감지: 사유 기록 및 담당자 피드백 요청", "조치 완료 후 확정 승격 자동화"],
            "security": "Fail-safe Locking Mechanism",
            "engine": "Decision Logic & Dispatcher",
            "rule": "표준 설계 4단계 (Decision & Branching)"
        },
        {
            "step": 4,
            "id": "step-5",
            "title": "영구 아카이빙 및 최종 완료 통보",
            "banner": "Step 5: 처리 결과가 영구 저장소에 보존되고 요청자에게 최종 보고서가 발행됩니다.",
            "desc": "최종 확정된 트랜잭션은 위변조 방지 해시와 함께 영구 아카이브에 커밋되며, 요청자와 대시보드에 즉시 결과가 통보됩니다.",
            "laneNodes": {
                "lane-user": {"title": "최종 완료 보고서 수령", "desc": "결과 확인 및 다운로드"},
                "lane-platform": {"title": "대시보드 실시간 반영", "desc": "상태 열 '완료' 업데이트"},
                "lane-core": {"title": "스토리지 영구 커밋", "desc": "SHA-256 무결성 해시 커밋"}
            },
            "checklist": ["영구 아카이브 저장 완료", "요청자 알림 발송 (이메일/웹훅)", "종료 감사 로그 동기화"],
            "security": "SHA-256 Digest Signature",
            "engine": "Archiving & Notification Service",
            "rule": "표준 설계 5단계 (Completion & Archival)"
        }
    ]
}

AI_PIPELINE_JSON = {
    "title": "AI 모델 학습 및 배포 파이프라인 (AI/MLOps Pipeline)",
    "subtitle": "데이터 라벨링부터 모델 학습, 평가 검증, 카나리 배포 및 모니터링",
    "author": "AI 플랫폼 엔지니어링",
    "version": "2.0.0",
    "steps": [
        {"step": 0, "title": "01. 원천 데이터 수집 & 라벨링", "banner": "Step 1: 대용량 피처 데이터셋 수집 및 불변 스냅샷 생성", "desc": "정형/비정형 원천 데이터를 파이프라인으로 스트리밍하고 데이터 레이크에 스냅샷을 생성합니다."},
        {"step": 1, "title": "02. 피처 전처리 & 드리프트 검증", "banner": "Step 2: 데이터 드리프트 스캔 및 피처 스케일링", "desc": "피처 스토어에서 결측치 및 이상치를 필터링하고 데이터 분포 드리프트를 검증합니다."},
        {"step": 2, "title": "03. 분산 모델 학습 & 튜닝", "banner": "Step 3: GPU 클러스터 분산 학습 및 하이퍼파라미터 탐색", "desc": "최적의 가중치와 하이퍼파라미터를 탐색하여 모델 체크포인트를 빌드합니다."},
        {"step": 3, "title": "04. 벤치마크 평가 & 게이트웨이 승인", "banner": "Step 4: 성능 지표(F1, AUC, Latency) 검증 및 승인 분기", "desc": "기준 지표를 초과 달성하면 프로덕션 릴리스 게이트웨이로 직행합니다."},
        {"step": 4, "title": "05. 무중단 카나리 배포 & 모니터링", "banner": "Step 5: 카나리 배포 및 실시간 성능 모니터링 가동", "desc": "실시간 트래픽 5% 카나리 서빙 후 문제 없을 시 100% 롤아웃합니다."}
    ]
}

E_COMMERCE_JSON = {
    "title": "이커머스 실시간 주문 및 정산 흐름 (Order-to-Cash Flow)",
    "subtitle": "장바구니 담기부터 실시간 결제, 재고 차감, 배송 요청 및 대금 정산",
    "author": "커머스 플랫폼 개발팀",
    "version": "1.2.0",
    "steps": [
        {"step": 0, "title": "01. 상품 선택 & 주문서 생성", "banner": "Step 1: 구매자가 상품을 선택하고 임시 주문 세션이 생성됩니다.", "desc": "장바구니 상품에 대한 유효 재고를 확인하고 고유 주문번호(Order UUID)를 발급합니다."},
        {"step": 1, "title": "02. PG 결제 승인 & 에스크로 예치", "banner": "Step 2: 신용카드/간편결제 인증 및 결제 승인 처리", "desc": "PG사 결제 토큰 검증 및 결제 완료 트랜잭션을 원장 DB에 즉시 기록합니다."},
        {"step": 2, "title": "03. 실시간 재고 차감 & 패킹 요청", "banner": "Step 3: 물류 WMS 연동 재고 차감 및 출고 패킹 지시", "desc": "락(Lock) 기반 실시간 재고 차감 후 물류 센터로 바코드 패킹 지시를 전송합니다."},
        {"step": 3, "title": "04. 출고 검수 및 송장 바인딩", "banner": "Step 4: 바코드 검수 완료 후 택배사 송장 실시간 발급", "desc": "오배송 방지 바코드 스캔 통과 후 택배사 배송 API와 동기화합니다."},
        {"step": 4, "title": "05. 배송 완료 & 판매 대금 정산", "banner": "Step 5: 고객 수령 확인 후 판매자 정산 계좌 자동 송금", "desc": "구매확정 이벤트 수신 시 정산 수수료를 공제하고 대금을 자동 정산 커밋합니다."}
    ]
}

print("Saving sample JSON datasets...")
for base in [DIST_DIR, GLOBAL_SKILL_DIR, CODEX_SKILL_DIR]:
    with open(os.path.join(base, 'examples', 'sample_workflow.json'), 'w', encoding='utf-8') as f:
        json.dump(SAMPLE_WORKFLOW_JSON, f, ensure_ascii=False, indent=2)
    with open(os.path.join(base, 'examples', 'demo_ai_pipeline.json'), 'w', encoding='utf-8') as f:
        json.dump(AI_PIPELINE_JSON, f, ensure_ascii=False, indent=2)
    with open(os.path.join(base, 'examples', 'demo_e_commerce.json'), 'w', encoding='utf-8') as f:
        json.dump(E_COMMERCE_JSON, f, ensure_ascii=False, indent=2)

print("JSON files saved successfully!")

