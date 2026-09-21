---
name: wip-a00050-uvtool-v02
description: A00050_uvTool_V02 — V01(maya.cmds)의 PySide 이식. UV 세트 규칙 위반을 사유와 함께 로그로 찍고 선택, rename 은 before->after 와 실패 사유를 적는다. 원하는 세트 이름은 화면에서 입력(v02.01)
metadata:
  node_type: memory
  type: project
---

`A00050_uvTool_V02` (v02.00, 2026-09-21, 사용자 요청). V01(`A00050_uvTool`, maya.cmds UI)을
**PySide(아키텍처 B)로 이식**하면서 **로그를 말하게** 만들었다. V01 은 그대로 둔다.

**규칙**: 메시는 **`map1` UV 세트 하나**. 위반 세 가지 — `multiple`(2개 이상) ·
`wrong_name`(하나인데 이름이 다름) · `no_uv`(없음). V01 은 **2개 이상만** 찾았다.

- `Catch Objects` : 메시마다 **사유 문구**를 로그에 적고, 리스트에 담고, **씬에서 선택**한다.
  씬 전체(기본) / 리스트 한정 선택 가능. 씬은 안 바꾼다.
- `Rename UV Set` : **첫** UV 세트를 `map1` 으로. 메시마다 `uvSet9 -> map1` 로 적는다.

**★ V01 이 조용히 삼키던 것** — `['map1','uvSet1']` 메시에 rename 을 걸면 마야가
`RuntimeError: Cannot rename uv set to an existing uv set name.` 로 거절하는데 V01 은
`try/except: pass` 라 **아무 일도 안 났는데 성공처럼** 보였다. V02 는 **미리 판정**해서
`blocked` 로 사유를 적고, 첫 세트가 이미 `map1` 인데 다른 세트가 남은 경우는 `extra` 로
"이 툴은 UV 세트를 지우지 않는다" 고 말한다(**기본 UV 세트는 마야가 못 지우게 한다** —
`The default uv set cannot be deleted.`).

**mayapy 2024 실측**
- `polyUVSet` 은 **오브젝트를 인자로 받는다**(트랜스폼·셰이프 둘 다) → V01 의 `cmds.select`
  왕복이 필요 없다. **씬 선택을 건드리지 않는 것**이 실익.
- `map1` -> `map1` 도 같은 "existing name" 에러 → 이미 맞는 메시는 **시도하지 않는다**.
- `ls(type="mesh")` 는 **Orig(중간) 셰이프까지** 준다 → 디포머 붙은 메시가 두 번 걸린다.
  `noIntermediate=True` 로 거른다(V01 은 안 걸렀다).
- UV 세트 rename 은 **undo 된다** → 전체를 `undo_chunk()` 로.
- 첫 세트 = `polyUVSet(q=allUVSets)` 순서, `currentUVSet` 과 다를 수 있다(V01 기준 유지).

**v02.01 (사용자 요청): 바꿀 이름을 화면에서 입력.** `UV set name` 칸(기본 `map1`) +
기본값 버튼. ★ **칸 하나가 두 버튼을 함께 정한다** — Rename 의 목표 이름이자 Catch 의 규칙
이름이다. 따로 두면 "잡아서 고쳤는데 여전히 위반" 이 된다. 코어는 `find_offenders(wanted=)` ·
`rename_first_uv_set(new_name=)` 로 받고 기본값은 `map1` 그대로.
★ 실측 — **마야가 거절하는 이름은 빈 것뿐**(`Invalid new uv set name specified`)이고
공백(`UV Map`) · `-` · `.` · `:` · `|` · 숫자 시작은 **그대로 받는다.** 그래서 막지 않고
**앞뒤 공백만** 떼어(오타 대비) 칸에도 되돌려 준다.

실행 대상 우선순위도 뒤집었다 — **리스트가 먼저**, 비면 씬 선택(그 사실을 로그에).
V01 은 선택이 먼저라 리스트를 채워 두고 눌렀을 때 무엇이 대상인지 알 수 없었다.

검증: mayapy 2024 헤드리스 **57항목**(코어 + 오프스크린 Qt, 이름 칸 15항목 포함).
창 최소 533x772.
마야 GUI 에서는 아직 안 눌러 봄.
관련: [[mayapy-headless-verify]], [[undo-chunk-by-default]], [[prefer-pyside-for-new-tools]],
[[new-tool-needs-icon]](아이콘은 V01 그림을 그대로 씀)
