# DMAIC 메뉴·화면 구조 제안 근거 기록

## 제공 화면에서 확인한 구조

- Define, Measure, Analyze, Improve, Control의 고정 순서와 단계별 목표 문구가
  상단·측면 탐색·본문 카드에 반복된다.
- 각 단계는 도구를 카드로 나열하고, 단계 목적과 다음 행동을 함께 보인다.
- Measure에는 MSA/Gage R&R, 기준 성능, SPC가, Improve에는 DOE가, Control에는
  관리계획서·공정능력·SPC가 배치되어 있다.
- Define 입력 화면은 프로젝트 헌장(정보·사업 타당성·범위·성공 지표·팀·예산·이정표·
  이해관계자·위험·가정), VOC, SIPOC, 문제 정의, 이해관계자 분석의 개별 폼을 보인다.
- 프로젝트 헌장은 첫 패널만 펼치고 나머지는 접힌 섹션으로 표시한다. VOC는 수집과
  요구사항·불편·기회·조치·권고를, SIPOC는 공정 경계와 다섯 요소의 목록을 입력한다.
- Measure 입력 화면은 데이터 수집 계획의 프로젝트 정보·핵심 지표·기준/목표값·문제/
  목표 정의, 수집 전략, 표본추출 계획, 측정 시스템, 수집 양식, 수집자, 품질보증,
  분석 방법, 비용·자원을 보인다. MSA와 Gage R&R은 별도 다단계 화면으로 보인다.
- Analyze 입력 화면은 근본원인 분석·특성요인도·5 Why·파레토의 설정, 문제 정의,
  잠재 원인, 근본원인, 시정조치, 결론을 개별 단계 또는 문서로 보인다. 별도의 방법
  탐색 화면은 상관/회귀와 추론 통계를 질문과 결과척도에 따라 카드로 나열한다.
- Improve 입력 화면은 개선안 선정 매트릭스, 파일럿 계획, 비용편익 분석, 실행계획의
  기본 정보와 단계별 탭을 보인다. DOE는 개선 단계의 도구로 배치된다.

## StatPro 적용 결정

- 제안 화면 `개선 프로젝트(DMAIC)`는 DOE·SPC·FMEA의 계산 엔진을 복제하지 않고
  현재 작업공간·Analysis Run·FMEA Study로 이동하는 조정 허브로 설계한다.
- 구현 도구는 `구현됨`, 미구현 도구는 `개발 예정`, 조직 제공 요건이 필요한 기능은
  `외부 정책 필요`로 표시한다. 잠금, 크레딧, 구독 유도 상태는 사용하지 않는다.
- 현재 구현 연결은 Measure의 MSA/Gage R&R·공정능력·SPC, Improve의 DOE, Control의
  FMEA 관리계획서와 SPC다. Define/Analyze의 업무 산출물과 Improve의 파일럿·비용편익,
  Control의 품질 대시보드는 개발 예정으로 남긴다.
- Define은 `DmaicProject`와 immutable 연결 문서의 첫 수직 증분으로 계획한다. 프로젝트
  헌장과 VOC/SIPOC/문제 정의/이해관계자 분석은 독립 revision과 digest를 갖고, 프로젝트는
  그 ID·digest만 참조한다. 따라서 다른 단계의 Analysis Run 또는 FMEA Study를 복제하거나
  변경하지 않는다.
- Measure의 다음 증분은 `DataCollectionPlan` 연결 문서다. 교정/MSA 체크 항목과
  계획된 표본 수는 판정이 아니라 계획 입력으로 남기고, 완료된 MSA·공정능력·SPC
  Analysis Run의 ID·ETag·input digest만 연결한다.
- Analyze는 `RootCauseAnalysis`를 중심으로 CauseAndEffectMap, FiveWhyChain,
  ParetoStudy를 별도 revision 문서로 둔다. DOE 효과 파레토는 현재 DOE 결과에만
  존재하므로 일반 원인 파레토 기능으로 과장하지 않는다. 상관·회귀·추론 통계는
  현재 구현 증거가 없어 메뉴에서 `개발 예정`으로 남긴다.
- Improve는 SolutionSelectionMatrix, PilotPlan, CostBenefitAnalysis,
  ImplementationPlan을 독립 revision 문서로 둔다. DOE는 기존 Analysis Run을 참조하고
  가중 점수·파일럿 성공 지표·재무 값은 입력 가정에 따른 의사결정 보조로 기록한다.

## 제한

- 제공 화면은 정보구조·상호작용 참고 자료이며 상용 제품의 화면 배치, 브랜드, 용어,
  아이콘, 잠금 정책을 복제하는 근거가 아니다.
- `DmaicProject`와 단계별 evidence reference 데이터 모델은 아직 구현하지 않았다.
  제안된 화면을 구현할 때에도 기존 Analysis Run과 FMEA Study의 소유·digest 경계를
  유지해야 한다.
