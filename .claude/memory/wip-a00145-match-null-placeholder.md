---
name: wip-a00145-match-null-placeholder
description: A00145 Connect - 이름 정확 매칭 + 짝 없는 자리를 (Null) 로 채워 순서 짝짓기를 지키는 패턴
metadata: 
  node_type: memory
  type: project
  originSessionId: d6fff52a-5254-4375-a0a5-2ad590931f68
  modified: 2026-08-28T01:41:07.669Z
---

A00145_RigConnect v01.34 (2026-08-28): Connect > Connect 하위 탭에 **`Match Same Name`**
(이름이 완전히 같은 것만) 버튼과 **`Show Match Only`** 체크박스(기본 ON)를 넣었다.

**짝이 없는 자리를 비우지 않고 `(Null)` 로 채우는 것이 이 기능의 전부다.**
`connect_attrs` 는 `src[i] <-> dst[i]` 를 **순서로** 짝짓는다. 짝 없는 소스를 그냥 건너뛰고
destination 목록을 만들면 그 뒤의 짝이 한 칸씩 밀려 **엉뚱한 어트리뷰트끼리 조용히 이어진다** —
연결은 성공하므로 에러도 안 난다. 그래서 자리를 표식으로 잡아 두고, 연결 직전에
`strip_null_pairs()` 로 **양쪽에서 함께** 뺀다(한쪽만 빼면 밀림이 그대로 살아난다).

- `attr_match.py` 추가분: `NULL_TARGET = "(Null)"`(마야 이름에 괄호를 못 써서 충돌 없음) ·
  `match_exact_names()`(색인/점수 불필요, `이름 -> 인덱스` 사전으로 O(n+m)) ·
  `align_matches()` / `aligned_names()` · `strip_null_pairs()`.
- **매칭 결과에 `source_index` 를 넣었다.** 소스 이름이 중복될 수 있어 이름으로 되짚으면
  같은 이름 둘이 첫 자리에 몰려 조용히 어긋난다.
- 두 매칭의 **반환 형태를 똑같이** 맞춰 UI 가 `exact` 플래그 하나로 한 경로를 탄다
  (`_match_destination`). `Show Match Only` OFF 는 v01.33 까지의 동작 그대로다.

같은 이유로 짝을 맞추는 다른 기능들과 함께 본다 — [[wip-a00145-attr-name-matching]],
[[wip-a00145-match-one-to-many]], [[wip-a00145-connect-both-directions]],
[[attr-name-matching-token-index]].
