---
title: 작업 일지 (WORKLOG)
aliases: [WORKLOG, 작업일지, devlog]
tags: [worklog, maya-python]
updated: 2026-09-04
---

# 작업 일지 (WORKLOG)

git 커밋 기록을 근거로 하루 작업을 요약한다. 최신 날짜가 위.

**이 파일은 현재 월을 담는다.** 지난 달은 [`worklog/`](worklog/) 로 내려간다 —
파일 자체는 늘 이 경로에 있으므로 이 문서를 가리키는 링크는 깨지지 않는다.
트리거와 절차는 [`worklog/README.md`](worklog/README.md).

> [!info] 보기
> Obsidian 에서 `JUN_All/docs` 를 vault(또는 폴더)로 열면 속성/태그/링크가 동작한다.
> 굵게/링크가 별표째 보이면 소스 모드이므로 `Ctrl+E` 로 읽기/라이브 프리뷰 전환.

---

## 지난 달 보관

| 월 | 파일 | 작업일 |
|----|------|--------|
| 2026-08 | [`worklog/2026-08.md`](worklog/2026-08.md) | 18일 |
| 2026-07 | [`worklog/2026-07.md`](worklog/2026-07.md) | 18일 |
| 2026-06 | [`worklog/2026-06.md`](worklog/2026-06.md) | 12일 |

---

## 2026-09-04 (오늘)

> [!summary] `A00090_ConnectionBuilder` **Pose Wrangler export 를 규칙으로 그대로** + 모든 버튼 undo 1스텝 (v01.06 -> 01.07)
- **요청 1**: `app/rules/v003/rules_v003.json` 은 마야 **Pose Wrangler 에서 솔버 세팅을 그대로
  export 한 파일**이다. 지금은 포즈를 고칠 때마다 `WRK_calf_l.json`, `WRK_calf_r.json` … 을
  **솔버 수만큼 손으로 다시 써야** 한다. 이 export 파일을 규칙으로 바로 읽어 v002 와 똑같이
  동작하게 할 것. 그리고 앞으로 v004, v005 에도 파일을 하나씩 둘 계획이니 **파일 이름 규칙을
  정해 달라**.
- **파일 이름은 `rules_<폴더이름>.json` 으로 정했다**(`v004/rules_v004.json`). 파일만 떼어 놔도
  어느 버전에서 나온 것인지 읽힌다. **다만 코드는 이 이름에 기대지 않는다** — 최상위에 `solvers`
  키가 있으면 번들로 읽으므로 Pose Wrangler 가 지어 준 이름 그대로 떨어뜨려도 되고, 한 폴더에
  두 방식(솔버당 파일 / 번들)을 **섞어 둬도 된다.** 이름 규칙은 나중에 폴더를 열어 본 사람을 위한
  것이지 동작 조건이 아니다.
- **★ 그대로 쓸 수 없는 이름이 딱 하나 있었다.** Pose Wrangler 는 중립 포즈를 **언제나 그냥
  `default`** 로 부른다. 그대로 mapping 에 넣으면 솔버 8개가 전부 `WRK_intermediate.default`
  라는 **같은 어트리뷰트 하나로 몰려 서로를 덮어쓴다.** 손글씨 규칙은 이 자리를
  `calf_l_default` 로 적고 있었고, 번들의 `drivers[0]` 이 정확히 `calf_l` 이라
  **`<driver>_default`** 로 되살렸다. 나머지 포즈는 사용자가 이미 드라이버 이름을 붙여 짓기
  때문에 손대지 않는다.
- **동치를 눈으로 확인하고 나서 붙였다** — v003 번들의 솔버 8개를 v002 손글씨 mapping 과 한 줄씩
  대조해 **mapping · solver_node 전부 일치**. 포즈 순서(=`outputs[i]` 순서)도 json 이 순서를
  보존하므로 그대로 맞는다.
- **규칙 이름은 솔버 이름에서 `_UERBFSolver` 를 뗀 것**으로 했다(`WRK_calf_l`). v002 의 파일
  이름과 같아서 **버전을 바꿔도 `Rule` 콤보 목록이 그대로다.**
- **파일을 고치면 `Refresh` 없이 반영된다** — 색인이 폴더 안 json 의 (이름 · 수정 시각 · 크기)를
  기억해 두고 달라지면 다시 읽는다. Pose Wrangler 에서 다시 export 해 덮어써도 그만이다.
- **요청 2**: `Connect Intermediate` 로 노드를 만든 뒤 `Ctrl+Z` 를 누르면 노드가 생기기 전으로
  돌아가지 않고 **어트리뷰트가 하나씩 끊어지다가 마지막에야 노드가 사라진다.** `undo_chunk()` 로
  안 묶인 곳을 묶을 것.
- **씬을 바꾸는 버튼 6개를 묶었다** — `Connect` / `Connect All` / `Disconnect` / `Set Attr` /
  `Del Attr` / `Connect Intermediate`. `Create` 계열은 v01.04 때 이미 묶여 있었고, `Validate` 는
  읽기만 해서 뺐다.
- **검증**(mayapy 2024 headless, Qt 창 실제 빌드): 49항목 통과 — 로더 30(두 포맷 동치 · 규칙 이름 ·
  `default` 이름 충돌 · 섞인 폴더 · 깨진 json 무시 · mtime 재읽기) + UI 19(`Connect Intermediate`
  뒤 **undo 한 번**으로 `WRK_All`/`WRK_intermediate` 까지 사라지는 것, Set/Del Attr · Connect/
  Disconnect 각각 한 번, 46개 attr 이름이 겹치지 않는 것).
- 파일: `app/core/rule_loader.py`, `app/ui/main_window.py`, `app/config/version.py`,
  [`docs/A00090_ConnectionBuilder.md`](A00090_ConnectionBuilder.md)(§1-2 · §4-2)
    #A00090 #ConnectionBuilder #poseWrangler #undo

---

## 2026-09-03

> [!summary] `A00145_RigConnect` **Connect > Pair — 오브젝트를 이름으로 짝짓기** (v01.36 -> 01.37)
- **요청**: Connect > Connect 하위 탭의 어트리뷰트 이름 매칭을 **오브젝트에도** 달라. Driver /
  Driven TSL 이 주어졌을 때 이름이 비슷하거나 같은 것끼리 짝짓고, 안 되면 `(Null)`.
  덧붙여 — 그 탭을 통째로 `A00310_SearchTool` 로 옮기는 게 낫지 않겠나(옮긴다면 constraint 는
  빼도 된다), 더 나은 방법이 있으면 제안하고 구현할 것.
- **옮기지 않기로 하고 A00145 에 두었다**(사용자 확인). 근거는 **정렬된 짝은 순서가 곧 의미**인데,
  툴 사이로 짝을 넘길 수단이 씬 선택뿐이라 **넘기는 순간 그 순서가 사라진다**는 것이다.
  `(Null)` 로 자리를 지켜 놓아도 다른 툴에서는 되살릴 방법이 없다. 짝을 세우는 자리는 그 짝을
  **소비하는 자리**(= 연결) 옆이어야 한다.
- **점수 계산을 새로 만들지 않았다** — `attr_match` 의 토큰 역색인 + IDF 엔진을 그대로 쓴다.
  이 모듈은 애초에 **이름 리스트만 받는 순수 파이썬**이라 어트리뷰트든 오브젝트든 상관이 없었다.
  새로 필요한 것은 **오브젝트 이름을 비교 가능하게 만드는 일**뿐이었다(`object_match.py`).
- **★ 경로/네임스페이스가 진짜 문제였다.** `|grp|rig:jnt_L_arm` 을 통째로 토큰화하면 `grp` ·
  `rig` 가 토큰으로 섞여, **한쪽 리스트에만 경로가 붙어 있으면 같은 오브젝트인데 문턱을 못 넘는다.**
  그래서 비교는 **말단 이름**으로 하고 네임스페이스는 옵션(`Ignore Namespace`, 기본 ON)으로 두되,
  **돌려주는 것은 언제나 원래(전체) 이름**이다 — 말단 이름을 돌려주면 동명 노드가 있는 씬에서
  엉뚱한 노드를 잡는다. 비교용 이름과 실제 이름을 갈라 두고 인덱스로 되짚는다.
- **★ 짝을 세워 놔도 Connect 가 거리로 다시 계산하고 있었다.** 기존 `connect_closest` 는 리스트
  순서를 아예 보지 않는다(Get Closest 로 채워 넣어도 연결 때 다시 최근접 매칭). 그대로 두면
  이름으로 세운 짝이 **연결 순간 조용히 뒤집힌다.** 그래서 짝짓는 방법을 `Pairing` 라디오
  (`Closest distance` / `List order`)로 꺼내고, Match by Name 이 자동으로 `List order` 로 돌린다.
  - `List order` 는 **거르기 전에 짝을 만든다** — 씬에 없는 항목을 먼저 빼면 그 자리가 사라져
    뒤의 짝이 한 칸씩 밀린다.
- 하위 탭 이름을 **`Connect Closest` -> `Pair`** 로 바꿨다(이제 거리만이 아니라 이름으로도 짝을
  세운다). Get Closest 와 Match by Name 이 **후보 풀 규칙을 공유**하도록 정리했다.
- **검증**(mayapy 2024 headless, Qt 창 실제 빌드): 25항목 전부 통과 —
  driver 순서 유지 · `(Null)` · 전체 경로 반환 · **동명 말단 이름 두 개가 서로 다른 경로로** ·
  exact / unique / namespace 옵션 · 빈 리스트 · 컴포넌트 이름 보존 · `(Null)` 과 없는 노드가 낀
  자리 건너뛰기 · **같은 리스트를 두 Pairing 으로 연결하면 서로 다른 짝**(거리는 엇갈리고
  자리는 그대로) · UI 에서 Match by Name -> Connect 까지.
- 파일: `app/core/object_match.py`(신규), `app/core/closest_connector.py`(짝짓기 모드),
  `app/ui/main_window.py`, `app/config/version.py`,
  [`docs/A00145_RigConnect.md`](A00145_RigConnect.md)(§Pair)
    #A00145 #RigConnect #nameMatching

> [!summary] `A00145_RigConnect` **Constrain > Update — AE 의 Update 버튼을 리스트 전체에** (v01.35 -> 01.36)
- **요청**: Attribute Editor 에서 parentConstraint 를 열면 **Update** 버튼이 있다. constraint 가
  걸린 오브젝트를 옮긴 뒤 그 버튼을 누르면 offset 이 다시 계산되어 옮긴 자리 그대로
  물린다(`parentConstraint -e -maintainOffset curve2  curve1_parentConstraint1;`).
  그걸 **TSL 에 담은 constraint 여러 개에 한번에** 돌리고 싶다. parent 뿐 아니라
  point · scale 도 같이.
- **계산을 다시 구현하지 않고 Maya 명령을 그대로 불렀다** —
  `cmds.<type>Constraint(*targets, cn, e=True, mo=True)`. AE 버튼과 결과가 어긋날 이유가
  없어야 하기 때문이다. 대신 **명령에 넘길 타깃 목록**이 까다로워서 mayapy(2024) 로
  세 가지를 먼저 확인했다.
  - **타깃을 전부 넘겨야 한다.** 2개 중 하나만 넘기면 **넘긴 슬롯의 offset 만** 다시
    구워지고 나머지는 옛 값 그대로 남는다 → weight 가 섞이는 순간 driven 이 튀다.
  - **타깃이 아닌 오브젝트를 넘기면 `-e` 인데도 타깃으로 추가된다.** 그래서 이름을 새로
    만들지 않고 **지금 연결된 target 슬롯에서 그대로 읽어** 넘긴다.
  - `-q -targetList` 는 **짧은 이름**이라 동명 노드에서 어긋난다 → Target Edit 과 같은
    `_target_entries()`(입력 연결 역추적, 롱네임)를 쓴다.
- **타입별로 되는 것과 안 되는 것이 갈린다** — parent / point / orient / scale / aim /
  pointOnPoly 는 `-e -mo` 를 받고, `geometry` / `normal` / `tangent` / `poleVector` 는 애초에
  플래그가 없어 **`Invalid flag 'mo'`** 로 거절한다 → 건너뛰고 경고.
- **로그가 `updated` 와 `no change` 를 가른다.** 아무도 안 움직인 constraint 에 돌리면
  offset 값이 그대로인 무해한 no-op 이므로, "일단 다 담고 돌리기" 가 안전하다.
- 리스트에는 **constraint 노드도, constraint 가 걸린 오브젝트도** 담을 수 있다(오브젝트는
  그 아래 constraint 로 확장). 고른 항목만 대상으로 하는 규칙도 Target Edit 과 같다.
- **검증**(mayapy 2024 headless): parent(타깃 2개 + weight 0.3 혼합) · point · orient ·
  scale · aim(aim/up 설정 보존 확인) · pointOnPoly 전부 **driven 월드 행렬 오차 1e-16** ·
  네임스페이스 · **동명 타깃(긴 이름)** · 조인트 driven · 지원 안 하는 타입 경고 ·
  같은 constraint 를 두 번 담았을 때 1회만 처리 · 빈 리스트 방어. **Qt 창을 실제로 빌드해**
  하위 탭 6개와 로그 출력까지 확인했다.
- 파일: `app/core/constraint_update_manager.py`(신규), `app/ui/main_window.py`(Constrain 하위 탭
  `Update` + 핸들러), `app/config/version.py`, [`docs/A00145_RigConnect.md`](A00145_RigConnect.md)(§Update)
    #A00145 #RigConnect #constraint

> [!summary] `docs` **WORKLOG 8월 롤링** — 루트는 9월부터
- 월이 바뀌었으므로 8월 항목 **18일치 3,108줄**을 [`worklog/2026-08.md`](worklog/2026-08.md) 로
  내렸다. **본문은 순수 이동**이고, 한 단계 깊어졌으므로 **상대 링크 24건에 `../` 를
  붙였다**(이미 `../tools/...` 였던 것은 `../../tools/...`). 규칙과 절차는
  [`worklog/README.md`](worklog/README.md).
    #docs #worklog

---
