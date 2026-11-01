# SPC 특성요인도 작업공간 증거 기록

## 관찰(Observation)

- 사용자 제공 `SPC_오픈소스.md`는 D3를 특성요인도와 같은 사용자 정의 SVG 시각화 후보로 제시했다.
- StatPro의 기존 일반 파레토는 불변 Analysis Run이며, 특성요인도처럼 반복 편집되는 원인 문서와
  동일한 수명주기나 소유권을 갖지 않는다.

## 도출(Derivation)

- `FishboneSnapshot`을 원인 문서의 단일 소유자로 두고 생성·원인 추가마다 revision,
  parent digest, digest를 새로 계산한다.
- 원인 후보는 6M 범주, 증거 참조, 검증 대상 여부를 보존한다. 동일 cause ID는 문서 전체에서
  거부하며 API 갱신은 예상 저장 버전을 요구한다.
- D3 `d3-shape`는 SVG의 spine·bone·cause 경로 투영에만 사용한다. 통계 의미, 원인 판정,
  revision 계산 또는 증거 해석에는 관여하지 않는다.

## 검증(Verification)

- 도메인: 생성, revision/digest 사슬, 중복 원인 ID와 잘못된 digest 거부.
- API: 생성·조회·원인 추가 계약과 저장 버전, ETag, 증거 참조 보존.
- UI: 작업공간 생성, D3 SVG 접근성 이름, 원인 추가, 검증 대상 표시와 접근 가능한 대체 표.

## 미확인·제한(Unknowns and limitations)

- 특성요인도에 기록된 항목은 원인 가설이며 인과관계가 검증된 근본원인이 아니다.
- 증거 참조 문자열의 대상 존재 여부와 신뢰성은 이 증분에서 검증하지 않는다.
- 외부 제품과의 픽셀·기능 동등성, 자동 원인 추천, 협업 동시 편집은 주장하지 않는다.
