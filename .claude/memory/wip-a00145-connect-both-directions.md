---
name: wip-a00145-connect-both-directions
description: "A00145 Connect 하위 탭 양방향 연결(인자 순서만 뒤집기) + 개수 달라도 부분 연결 (v01.24~01.25)"
metadata:
  node_type: memory
  type: project
---

A00145_RigConnect **Connect 하위 탭의 역방향 연결** (v01.23→**01.24**, 2026-08-11).

`Source  ->  Destination` / `Destination  ->  Source` 두 버튼을 나란히 둔다. 로그에 방향이 함께 찍힌다.

- **코어(`connect_manager.connect_attrs`)는 수정하지 않았다.** 인자 순서만 뒤집으면 3가지
  브로드캐스트 패턴(오브젝트 1개 → 다수 등)까지 **그대로 뒤집혀** 적용된다. UI 에
  `_connect_in_direction(from_role, to_role)` 하나를 두고 두 슬롯이 감싼다.
  역할 표시 이름은 `ROLE_LABELS = {"src": "Source", "dst": "Destination"}`.
- 슬롯을 둘로 나눈 이유는 [[qt-clicked-passes-checked-bool]] 참고.
- 코어의 실패 메시지만 `(src N, dst M)` → **`(driver N, driven M)`** 으로 바꿨다. 양방향으로 쓰이니
  "src" 가 역방향에서 Destination 을 가리켜 헷갈렸다.
- `Connect 52 Facial Target` 은 요청 범위 밖이라 **Source → Destination 한 방향 그대로**. 필요하면
  같은 방식으로 뒤집으면 된다(인자 순서만).

**v01.25 — 개수가 달라도 멈추지 않는다.** 예전엔 양쪽 어트리뷰트 수가 다르면 아무것도 연결하지
않고 `ValueError` 였다. 이제 `min(개수)` 만큼 앞에서부터 짝짓고 **남는 것은 방치**한다(오브젝트 수도
동일, 단 브로드캐스트 패턴은 모든 대상 obj 사용). 개별 `connectAttr` 실패(잠김/타입 불일치)도
치명적이지 않게 바꿔 나머지를 계속 연결한다. 남은 항목·실패는 **이름까지 로그**로 알린다 —
조용히 넘기면 "왜 일부만 연결됐지?" 가 되기 때문.
반환이 `(count, mode)` → **`(count, mode, report)`** 로 바뀌었다
(`unused_driver_attrs` / `unused_driven_attrs` / `unused_driver_objs` / `unused_driven_objs` / `failed`).
기존 패턴 2(양쪽 attr 1개)는 패턴 3의 특수 경우라 같은 루프로 합치고 라벨만 구분한다.
**개수가 맞는 입력의 동작은 그대로**(회귀 테스트 있음).

검증: 정방향/역방향 연결, **값이 실제로 반대로 흐르는지 `getAttr` 확인**, 브로드캐스트 반전,
로그 방향 표기, 개수 불일치 방어 + 기존 A00145 스위트 6종 통과.
