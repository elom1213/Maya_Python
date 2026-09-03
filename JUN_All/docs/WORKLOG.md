---
title: 작업 일지 (WORKLOG)
aliases: [WORKLOG, 작업일지, devlog]
tags: [worklog, maya-python]
updated: 2026-09-03
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

## 2026-09-03 (오늘)

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
