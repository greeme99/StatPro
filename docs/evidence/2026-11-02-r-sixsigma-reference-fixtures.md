# R SixSigma 공개 소스 기반 SPC 기준값 fixture

## 목적

StatPro의 Xbar-R 및 Xbar-S 보정계수를 동일 구현의 자기검증이 아닌 외부 공개 소스와 대조한다. 이 증거는 오픈소스 코드를 제품 런타임에 포함하거나 복제하기 위한 것이 아니라, 공개 수식과 기준값을 버전 고정 fixture로 보존하기 위한 것이다.

## 관찰(Observation)

- CRAN `SixSigma` 0.11.1의 `ss.cc.R`에는 `ss.cc.getd2`, `ss.cc.getd3`, `ss.cc.getc4`가 공개되어 있다.
- `ss.cc.getc4`는 감마 함수식으로 c4를 계산한다.
- `ss.cc.getd2`와 `ss.cc.getd3`는 정규분포 범위의 적분을 이용해 계수를 계산한다.
- `ss.cc`의 공개 구현은 이동범위(`mr`) 관리도를 지원한다. 따라서 SixSigma가 StatPro Xbar-R 결과 전체를 직접 생성한다고 해석하지 않는다.
- 검증 환경에는 R/Rscript가 설치되어 있지 않았다.

## 도출(Derivation)

`tests/fixtures/sixsigma_0_11_1_shewhart_constants.json`은 다음을 버전 고정한다.

- 공개 c4 감마 함수식과 n=2..10 기준값
- 공개 범위분포 함수에 대응하는 3자리 d2/d3 기준값
- d2/d3에서 독립적으로 도출한 A2, D3, D4 식

테스트는 내부 상수에 직접 접근하지 않는다. `xbar_r`와 `xbar_s`의 공개 ResultBundle 파라미터를 읽어 fixture에서 도출한 값과 비교한다. d2/d3 기준값은 3자리로 반올림되어 있으므로 Xbar-R 계수에는 fixture가 선언한 절대 허용오차 0.002를 적용한다. c4는 1e-10 절대 허용오차로 비교한다.

## 검증 범위

- n=2..10 Xbar-R A2/D3/D4 공개 결과
- n=2..10 Xbar-S c4 공개 결과
- fixture의 패키지명·버전·실행 한계 메타데이터

## 한계와 미확인(Unknown)

- R 런타임을 설치하거나 실행하지 않았으므로 이 fixture는 **source-derived reference**이며 R 실행 결과 캡처가 아니다.
- SixSigma·Minitab·StatPro의 제품 동등성을 주장하지 않는다.
- 오픈소스 패키지는 테스트 기준의 출처일 뿐 StatPro 배포 의존성에 포함되지 않는다.
- 향후 R이 승인된 검증 환경에 제공되면 동일 버전의 실제 함수 출력을 별도 runtime fixture로 캡처하고 현재 source-derived fixture와 구분해야 한다.

## 출처

- CRAN SixSigma: <https://cran.r-project.org/package=SixSigma>
- SixSigma `ss.cc` 문서: <https://rdrr.io/cran/SixSigma/man/ss.cc.html>
- SixSigma `ss.cc.R` 공개 소스: <https://rdrr.io/cran/SixSigma/src/R/ss.cc.R>
