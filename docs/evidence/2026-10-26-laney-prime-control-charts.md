# Laney P′/U′ 관리도 증분 근거 기록

## Minitab 14 정적 관찰

- 대상: `mtb14.exe`, `Mtb14Book.dll`, `Mtb14GraphicsCmnd.dll`
- 원본 바이트를 `Laney`, `PPrime`, `UPrime`, `PPRIME`, `UPRIME`로 제한 검색했으나 명시적인 후보 문자열을 확인하지 못했다.

검색 결과가 없다는 사실은 기능 부재의 증거가 아니다. 이름 제거, 다른 명명, 리소스·명령 코드 기반 구현 가능성이 있으므로 Minitab 14의 Laney 지원 여부는 **미확인**으로 유지한다. 이번 증분에는 Ghidra semantic Evidence ID나 동적 화면 증거가 없다.

## 공개 통계 근거

- 공개 접근 가능한 Laney P′ Phase I 수식과 Sigma Z 설명:
  - <https://www.mdpi.com/2227-7390/11/15/3411>
- Minitab 공개 Assistant Attribute Control Charts 부록의 P′/U′ 수식:
  - <https://support.minitab.com/minitab/media/pdfs/translate/Assistant_Attribute_Control_Charts.pdf>
- 현재 Minitab Laney U′ 수식은 독립 교차검증 자료로만 사용했다.
  - <https://support.minitab.com/en-us/minitab/help-and-how-to/quality-and-process-improvement/control-charts/how-to/attributes-charts/laney-u-chart/methods-and-formulas/methods-and-formulas/>

현재 Minitab 자료는 설치된 Minitab 14 내부 구현의 증거가 아니며 제품 버전 간 기능·기본값·계산 경로의 동일성을 가정하지 않는다.

## StatPro 독립 구현

- P′ 중심선은 `pbar = sum(x_i)/sum(n_i)`, 이론 표준오차는 `sqrt(pbar*(1-pbar)/n_i)`이다.
- U′ 중심선은 `ubar = sum(c_i)/sum(n_i)`, 이론 표준오차는 `sqrt(ubar/n_i)`이다.
- 각 부분군 통계량을 이론 표준오차로 표준화해 `z_i`를 계산한다.
- `Sigma Z = MRbar(z)/1.128`로 연속 부분군 간 추가 변동을 추정한다.
- 관리한계는 `center ± 3*theoretical_sigma_i*Sigma Z`이며 P′는 `[0,1]`, U′는 0 이상으로 절단한다.
- Sigma Z가 1보다 크면 과산포, 작으면 과소산포 경고를 보존한다.
- 이론 분산이 0이면 Sigma Z를 계산한 것으로 가장하지 않고 tagged error로 실패한다.
- p/np/c/u와 같은 속성 관리도 포인트·차트·표 계약을 재사용한다.

이는 공개 수학의 clean-room 구현이며 Minitab 내부 코드·리소스·화면의 번역 또는 복제가 아니다.

## 검증 결과

- P′ Sigma Z와 부분군별 한계의 독립 수계산 fixture 통과
- U′ 가변 검사 단위, 과산포·과소산포 방향, 입력 경계 통과
- API·CLI·React 선택/결과·접근 가능한 표 계약 통과
- 전체 Python 163/163, Vitest 50/50, Ruff, TypeScript/Vite production build 통과

## 남은 미확인·후속 범위

- Minitab 14 Laney 기능 존재, 대화상자, 세션 명령과 수치 비교
- 과거 중심선·Sigma Z, stage, 제외 부분군과 결측 처리
- 신뢰구간·희귀사건 관리도와 대체 분산 추정
- MTW/MPJ 입력·결과 직렬화
