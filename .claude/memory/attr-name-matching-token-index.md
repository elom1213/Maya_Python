---
name: attr-name-matching-token-index
description: 이름 유사도 대량 검색은 편집 거리 말고 토큰 역색인 + IDF. difflib 비율은 coverage 와 척도가 다르다
metadata: 
  node_type: memory
  type: reference
  originSessionId: ee81a66a-5136-4bb8-b44a-7fa187164cdb
  modified: 2026-08-10T02:10:24.612Z
---

이름 n 개 ↔ 이름 m 개를 유사도로 짝지을 때(어트리뷰트/본/노드 이름 매칭) 쓰는 방식.

**편집 거리·difflib 전수 비교는 쓰지 말 것** — `O(n·m·L²)`. n=m=1000, L≈25 면 6억 회 문자 연산
(파이썬 분 단위). 정확도도 낮다: `brow_up` vs `lod0_mesh_body_brow_up` 은 길이 차 때문에 편집 거리상
"많이 다른" 문자열이지만 사람이 보기엔 같은 것을 가리킨다.

**대신 토큰 역색인 + IDF:**
1. 구분자(`_`,`-`,`.`)와 **camelCase 경계**에서 토큰화 → `browUp` 과 `brow_up` 이 같아진다.
2. 후보를 한 번만 훑어 `토큰 → 후보 인덱스` 역색인 + `idf = log(1 + m/df)`.
   → `lod0` `mesh` `body` 같은 **공통 접두어는 IDF 가 0 에 가까워 자동으로 무시된다**(사람이
   접두어를 지정할 필요 없음).
3. 점수 = **coverage** = (후보가 설명하는 질의 토큰 IDF) / (질의 토큰 IDF 합), 0~1.
   precision·토큰 연속·접미 일치·부분 문자열·길이 근접은 **coverage 보다 작은 가산점**으로만.
4. **정확한 가지치기**: 포스팅을 드문 토큰부터 읽다가 *남은* 토큰들의 IDF 합이
   `min_score × 질의 IDF 합` 에 못 미치면 중단. 그 뒤 토큰만 공유하는 후보는 문턱을 넘을 수
   없으므로 **정답을 놓치지 않는다**(휴리스틱 아님). 보일러플레이트 토큰의 거대한 포스팅을 안 읽는다.

복잡도 `O(m·L + n·(g·t + g·log k))` (g = 토큰을 공유해 실제 점수를 낸 후보 수), 최악 `O(n·m·t)`.
실측 1000×1000 **0.15s**, difflib 전수 대비 **≈145배**.

**함정: difflib 비율과 coverage 는 척도가 다르다.** 토큰이 안 겹칠 때 폴백으로 `difflib` 을 쓰면,
무관한 이름도 0.45 가 예사다(`identification` vs `wibble_frobnicate`). 같은 문턱으로 비교하면 엉뚱한
매칭이 통과하므로 **0.5→0, 1.0→1 로 재스케일**해 문턱의 의미를 맞춰야 한다.

구현: `A00145_RigConnect/app/core/attr_match.py` ([[wip-a00145-attr-name-matching]]).
UI 는 결과를 소스 순서대로 목록 앞에 정렬 — `connect_attrs` 가 순서로 짝짓기 때문.
