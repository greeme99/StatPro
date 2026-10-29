# DMAIC 메뉴·화면 구조 제안 근거 기록

## 제공 화면에서 확인한 구조

- Define, Measure, Analyze, Improve, Control의 고정 순서와 단계별 목표 문구가
  상단·측면 탐색·본문 카드에 반복된다.
- 각 단계는 도구를 카드로 나열하고, 단계 목적과 다음 행동을 함께 보인다.
- Measure에는 MSA/Gage R&R, 기준 성능, SPC가, Improve에는 DOE가, Control에는
  관리계획서·공정능력·SPC가 배치되어 있다.

## StatPro 적용 결정

- 제안 화면 `개선 프로젝트(DMAIC)`는 DOE·SPC·FMEA의 계산 엔진을 복제하지 않고
  현재 작업공간·Analysis Run·FMEA Study로 이동하는 조정 허브로 설계한다.
- 구현 도구는 `구현됨`, 미구현 도구는 `개발 예정`, 조직 제공 요건이 필요한 기능은
  `외부 정책 필요`로 표시한다. 잠금, 크레딧, 구독 유도 상태는 사용하지 않는다.
- 현재 구현 연결은 Measure의 MSA/Gage R&R·공정능력·SPC, Improve의 DOE, Control의
  FMEA 관리계획서와 SPC다. Define/Analyze의 업무 산출물과 Improve의 파일럿·비용편익,
  Control의 품질 대시보드는 개발 예정으로 남긴다.

## 제한

- 제공 화면은 정보구조·상호작용 참고 자료이며 상용 제품의 화면 배치, 브랜드, 용어,
  아이콘, 잠금 정책을 복제하는 근거가 아니다.
- `DmaicProject`와 단계별 evidence reference 데이터 모델은 아직 구현하지 않았다.
  제안된 화면을 구현할 때에도 기존 Analysis Run과 FMEA Study의 소유·digest 경계를
  유지해야 한다.
