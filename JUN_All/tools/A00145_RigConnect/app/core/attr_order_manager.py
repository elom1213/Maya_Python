# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-09-17
# A00145_RigConnect - Attribute > Edit : 어트리뷰트 순서 바꾸기 (maya.cmds, UI 비의존)
"""
attr_order_manager - 사용자 정의 어트리뷰트의 **나열 순서**를 위/아래로 옮긴다.

★ 마야에는 어트리뷰트를 재정렬하는 명령이 없다
-----------------------------------------------
`addAttr` 에도 `attributeQuery` 에도 순서 플래그가 없다. 유일하게 되는 방법은

    deleteAttr  ->  undo

다. 지웠다 되돌리면 그 어트리뷰트가 **목록 맨 뒤로** 간다. 그러므로 원하는 순서대로
전부 한 바퀴 돌리면 결과가 정확히 그 순서가 된다. (mayapy 실측: 4개짜리를 뒤집어
`['atD','atC','atB','atA']` 를 얻었고, 200개 전체 재정렬이 **0.004초**다.)

**값 · 커넥션 · 키가 그대로 살아남는다.** undo 가 원래 상태를 되돌리는 것이므로
직접 다시 이어 줄 필요가 없다(실측: `driver.translateX` 연결과 키프레임 유지).

★ 그래서 조심해야 하는 것 세 가지 — 전부 실측으로 확인했다
---------------------------------------------------------
1. **`deleteAttr` 가 실패했는데 `undo()` 를 부르면 남의 작업을 되돌린다.**
   잠긴 어트리뷰트가 그 경우다. 실측: 실패 뒤 undo 를 불렀더니 **사용자가 만든 노드가
   사라졌다.** 그래서 **성공했을 때만** undo 를 부른다.
2. **undo 가 꺼져 있으면 어트리뷰트가 그대로 없어진다.** 지우고 되돌릴 수가 없기 때문이다.
   시작 전에 `undoInfo -q -state` 를 보고, 꺼져 있으면 **아무것도 하지 않는다.**
3. **이 작업은 Ctrl+Z 로 되돌아가지 않는다.** delete 와 undo 가 짝이라 큐에 아무것도
   남지 않는다. 오히려 그 뒤에 Ctrl+Z 를 누르면 **그 전에 하던 작업**이 취소된다
   (실측 확인). 호출부가 이 사실을 로그로 알려야 한다.

기본(빌트인) 어트리뷰트는 `deleteAttr` 대상이 아니므로 **순서를 바꿀 수 없다.**
목록에서 걸러 내고 이유를 돌려준다.

Maintain connections (v01.46)
-----------------------------
옮기기 **전에** 그 오브젝트에 걸린 연결을 **플러그 이름으로** 적어 두고, 옮긴 **뒤에** 다시 읽어
어긋난 것만 되돌린다 — `attr_01_a -> attr_02_a` 는 `attr_02_a` 가 몇 번째 자리로 가든 그대로다.

사용자 보고: `obj_02` 의 `attr_02_a` / `attr_02_b` 순서를 바꾸자 연결이 자리 기준으로 엇갈렸다
(`attr_01_a -> attr_02_b`). **mayapy 와 마야 GUI(2024, 병렬 평가)에서는 재현되지 않았다** —
이름 · API 연결 · 실제 값 흐름이 모두 유지됐다(17가지 변형). 원인과 상관없이 결과를 보장하도록
**비교 후 복구**로 만들었다. 어긋난 것이 없으면 씬을 전혀 건드리지 않는다.

- 연결은 `skipConversionNodes=True` 로 **실제 양 끝**을 적는다. `unitConversion` 노드는 undo 가
  다른 이름으로 되살릴 수 있어, 그 이름으로 비교하면 멀쩡한 연결을 "틀렸다" 고 끊게 된다.
- 되돌리기는 **받는 쪽(dst)** 기준이다 — `connectAttr -force` 로 맞는 소스를 다시 물리고, 그래도
  남은 낯선 연결은 dst 에 직접 붙은 플러그를 찾아 끊는다(사이에 변환 노드가 있어도 된다).
- 잠긴 dst 는 잠깐 풀었다가 다시 잠근다.
- 여러 오브젝트를 함께 옮기면 **전부 먼저 적고 → 전부 옮기고 → 전부 확인**한다. 둘이 서로
  연결돼 있을 때, 한쪽을 옮긴 뒤에 다른 쪽을 적으면 이미 어긋난 상태를 "원래" 로 삼게 된다.
"""

import maya.cmds as cmds


def user_attr_order(obj):
    """obj 의 사용자 정의 어트리뷰트를 **씬에 있는 순서 그대로**."""
    return list(cmds.listAttr(obj, userDefined=True) or [])


def plan_order(current, chosen, up=True):
    """`chosen` 을 한 칸 위(또는 아래)로 옮긴 새 순서를 만든다.

    여러 개를 한꺼번에 옮길 때는 **덩어리가 서로를 밀지 않도록** 한다 - 바로 앞(뒤)이
    이미 고른 것이면 그 자리는 건너뛴다. 맨 위(아래)에 닿은 것은 더 안 움직인다.
    (레이어 목록을 올리고 내리는 것과 같은 규칙)
    """
    result = list(current)
    picked = set(chosen)

    if up:
        for i in range(len(result)):
            if result[i] in picked and i > 0 and result[i - 1] not in picked:
                result[i - 1], result[i] = result[i], result[i - 1]
    else:
        for i in range(len(result) - 1, -1, -1):
            if result[i] in picked and i < len(result) - 1 \
                    and result[i + 1] not in picked:
                result[i + 1], result[i] = result[i], result[i + 1]

    return result


def _apply_order(obj, new_order):
    """`new_order` 대로 실제 어트리뷰트 순서를 갈아 끼운다.

    반환: (옮긴 개수, 실패 사유 목록). 실패하면 **그 오브젝트는 거기서 멈춘다** -
    중간까지만 돌린 순서는 어차피 의미가 없고, 계속 밀어붙이면 상황만 나빠진다.
    """
    moved = 0
    problems = []

    for name in new_order:
        plug = "{0}.{1}".format(obj, name)

        try:
            locked = bool(cmds.getAttr(plug, lock=True))
        except Exception:
            locked = False
        if locked:
            cmds.setAttr(plug, lock=False)

        try:
            cmds.deleteAttr(obj, attribute=name)
        except Exception as exc:
            # ★ 지우지 못했으면 undo 를 부르면 안 된다 - 남의 작업을 되돌린다.
            if locked:
                cmds.setAttr(plug, lock=True)
            problems.append((name, str(exc).strip().splitlines()[0]))
            break

        cmds.undo()

        # undo 가 정말 되돌렸는지 확인한다. 안 돌아왔다면 어트리뷰트를 잃은 것이므로
        # 더 진행하지 않고 크게 알린다(일어나선 안 되는 일이다).
        if not cmds.attributeQuery(name, node=obj, exists=True):
            problems.append((name, "LOST - deleteAttr succeeded but undo did not "
                                   "bring it back"))
            break

        if locked:
            cmds.setAttr(plug, lock=True)
        moved += 1

    return moved, problems


# ======================================================================
# Maintain connections
# ======================================================================

def connection_snapshot(obj):
    """obj 에 걸린 연결 전부를 `{(src_plug, dst_plug), ...}` 로. 변환 노드는 건너뛴 실제 양 끝."""
    pairs = set()

    incoming = cmds.listConnections(
        obj, source=True, destination=False, connections=True, plugs=True,
        skipConversionNodes=True) or []
    for i in range(0, len(incoming) - 1, 2):
        pairs.add((incoming[i + 1], incoming[i]))

    outgoing = cmds.listConnections(
        obj, source=False, destination=True, connections=True, plugs=True,
        skipConversionNodes=True) or []
    for i in range(0, len(outgoing) - 1, 2):
        pairs.add((outgoing[i], outgoing[i + 1]))

    return pairs


def _direct_source(dst):
    """dst 에 **직접** 붙은 소스 플러그(변환 노드면 그 노드의 출력). 없으면 None."""
    found = cmds.listConnections(dst, source=True, destination=False, plugs=True,
                                 skipConversionNodes=False) or []
    return found[0] if found else None


def _with_unlocked(plug, func):
    try:
        locked = bool(cmds.getAttr(plug, lock=True))
    except Exception:
        locked = False
    if locked:
        cmds.setAttr(plug, lock=False)
    try:
        func()
    finally:
        if locked:
            cmds.setAttr(plug, lock=True)


def restore_connections(obj, expected):
    """지금 연결을 `expected` 와 비교해 어긋난 것만 되돌린다.

    반환: (되돌린 연결 줄 목록, 실패 사유 목록). 어긋난 게 없으면 ([], []) 이고 씬은 그대로다.
    """
    fixed = []
    problems = []

    actual = connection_snapshot(obj)
    if actual == expected:
        return fixed, problems

    # 1) 빠진 연결을 다시 문다. force 라 dst 에 잘못 붙은 소스는 이 한 번으로 바뀐다.
    for src, dst in sorted(expected - actual):
        if not cmds.objExists(src) or not cmds.objExists(dst):
            problems.append("{0} -> {1} : plug no longer exists".format(src, dst))
            continue
        try:
            _with_unlocked(dst, lambda s=src, d=dst: cmds.connectAttr(s, d, force=True))
            fixed.append("reconnected {0} -> {1}".format(src, dst))
        except Exception as exc:
            problems.append("{0} -> {1} : {2}".format(
                src, dst, str(exc).strip().splitlines()[0]))

    # 2) 그래도 남은 낯선 연결은 끊는다(받는 쪽에 직접 붙은 플러그 기준).
    for src, dst in sorted(connection_snapshot(obj) - expected):
        direct = _direct_source(dst)
        if not direct:
            continue
        try:
            _with_unlocked(dst, lambda s=direct, d=dst: cmds.disconnectAttr(s, d))
            fixed.append("disconnected {0} -> {1}".format(src, dst))
        except Exception as exc:
            problems.append("{0} -> {1} : {2}".format(
                src, dst, str(exc).strip().splitlines()[0]))

    if connection_snapshot(obj) != expected and not problems:
        problems.append("connections still differ after restoring")
    return fixed, problems


def move_attributes(objects, attrs, up=True, maintain_connections=True):
    """`objects` 각각에서 `attrs` 를 한 칸 위/아래로 옮긴다.

    - 오브젝트마다 **독립으로** 처리한다. 그 오브젝트에 없는 어트리뷰트는 건너뛴다.
    - 사용자 정의가 아닌 어트리뷰트(`translateX` …)는 마야가 지울 수 없어 **옮길 수 없다.**
    - 이미 끝(맨 위/맨 아래)이라 바뀔 게 없으면 그 오브젝트는 건드리지 않는다.
    - `maintain_connections` 이면 옮기기 전 연결을 이름으로 적어 두고 옮긴 뒤 어긋난 것을 되돌린다.

    반환: (로그 줄 목록, 순서가 실제로 바뀐 오브젝트 수)
    """
    logs = []

    if not objects:
        return ["[WARN] Object list is empty."], 0
    if not attrs:
        return ["[WARN] Check the attributes to move first."], 0

    # ★ undo 가 꺼져 있으면 절대 시작하지 않는다 - 지우고 못 되돌리면 그대로 잃는다.
    if not cmds.undoInfo(query=True, state=True):
        return ["[ERR] Undo is disabled - reordering needs it "
                "(deleteAttr + undo). Turn undo on and try again."], 0

    changed = 0
    plans = []   # (obj, new_order)

    for obj in objects:
        if not cmds.objExists(obj):
            logs.append("[WARN] {0} : not found in scene".format(obj))
            continue

        current = user_attr_order(obj)
        if not current:
            continue

        # 사용자 정의가 아닌 것은 애초에 current 에 없다. 고른 것 중 빠진 것을 먼저 알린다.
        # (`here` 가 비었다고 그냥 넘어가면 "왜 아무 일도 안 일어나지" 가 된다)
        skipped = [a for a in attrs
                   if a not in current and cmds.attributeQuery(
                       a, node=obj, exists=True)]
        if skipped:
            logs.append("[WARN] {0} : {1} cannot be moved (not user defined)"
                        .format(obj, ", ".join(skipped[:6])))

        here = [a for a in attrs if a in current]
        if not here:
            continue

        new_order = plan_order(current, here, up)
        if new_order == current:
            continue
        plans.append((obj, new_order))

    # ★ 전부 먼저 적는다 - 서로 연결된 두 오브젝트를 함께 옮길 때, 한쪽을 옮긴 뒤에 다른 쪽을
    #   적으면 이미 어긋난 상태를 "원래" 로 삼게 된다.
    snapshots = {}
    if maintain_connections:
        for obj, _order in plans:
            snapshots[obj] = connection_snapshot(obj)

    for obj, new_order in plans:
        moved, problems = _apply_order(obj, new_order)
        for name, why in problems:
            logs.append("[WARN] {0}.{1} : {2}".format(obj, name, why))
        if moved and not problems:
            changed += 1

    if maintain_connections and plans:
        restored = 0
        for obj, _order in plans:
            fixed, problems = restore_connections(obj, snapshots[obj])
            for line in fixed:
                logs.append("       {0} : {1}".format(obj, line))
            for why in problems:
                logs.append("[WARN] {0} : connection not restored - {1}".format(obj, why))
            restored += len(fixed)
        checked = sum(len(s) for s in snapshots.values())
        if restored:
            logs.append("[OK] Maintain connections : fixed {0} connection(s) "
                        "({1} checked).".format(restored, checked))
        else:
            logs.append("       Maintain connections : all {0} connection(s) "
                        "kept.".format(checked))

    if changed:
        logs.append("       Order changed on {0} object(s).".format(changed))
    elif not logs:
        logs.append("       Nothing to move - already at the "
                    "{0}.".format("top" if up else "bottom"))

    # ★ 호출부가 아니라 여기서 말한다 - 이 동작의 성질이라 빠뜨리면 안 된다.
    if changed:
        logs.append("[INFO] Reorder cannot be undone with Ctrl+Z "
                    "(it uses deleteAttr + undo internally).")
    return logs, changed
