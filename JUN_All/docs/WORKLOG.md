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
