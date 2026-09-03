# -*- coding: utf-8 -*-
"""
ClosestConnector - 핵심 로직 (Connect Closest 탭).

각 driver 에 대해 가장 가까운 driven 을 1:1 로 매칭하고, 선택된 constraint 종류로
연결한다. UI 비의존 — MayaScene 어댑터만 사용하고, 결과는 dict 리스트로 반환해서
UI 가 로그로 출력하도록 한다.

A00140_ConnectClosest 의 closest_connector 를 그대로 옮겨온 것이다.
"""

from .maya_scene import MayaScene
from .object_match import NULL_TARGET


# constraint key -> (label, MayaScene 메서드명).
# UI 의 체크박스 순서/라벨과 1:1 로 대응한다.
CONSTRAINT_TYPES = [
    ("parent", "Parent", "parent_constraint"),
    ("point", "Point", "point_constraint"),
    ("orient", "Orient", "orient_constraint"),
    ("scale", "Scale", "scale_constraint"),
]

# 짝짓는 방법.
#   closest : 거리로 다시 계산한다 (원래 동작 — 리스트 순서를 보지 않는다).
#   order   : 리스트에 보이는 자리 그대로 (Match by Name 결과, 손으로 Up/Down 한 순서).
PAIRING_CLOSEST = "closest"
PAIRING_ORDER = "order"


def find_closest(driver, driven_pool):
    """driven_pool 중 driver 와 거리가 가장 가까운 항목과 그 거리를 반환.

    빈 풀이면 (None, None).
    """
    closest = None
    closest_dist = None

    for driven in driven_pool:
        dist = MayaScene.distance(driver, driven)
        if closest_dist is None or dist < closest_dist:
            closest = driven
            closest_dist = dist

    return closest, closest_dist


def match_closest_pairs(drivers, pool):
    """driver 순서대로 greedy 1:1 최단 매칭. 쓰인 항목은 풀에서 제거(재사용 방지).

    connect_closest(연결) 와 find_closest_for_drivers(Get Closest 미리채우기) 가
    공유하는 매칭 로직 — 둘의 결과가 항상 일치하도록 단일 출처로 둔다.

    Args:
        drivers: driver 오브젝트 이름 리스트(순서 유지).
        pool: 후보 오브젝트 이름 리스트(존재/유효성은 호출측에서 미리 거른다).

    Returns:
        [(driver, driven, dist), ...] — 풀이 먼저 비면 남은 driver 는 빠진다.
    """
    remaining = list(pool)
    pairs = []
    for driver in drivers:
        if not remaining:
            break
        driven, dist = find_closest(driver, remaining)
        remaining.remove(driven)
        pairs.append((driver, driven, dist))
    return pairs


def find_closest_for_drivers(drivers, candidates):
    """각 driver 의 가장 가까운 후보를 greedy 1:1 로 찾는다(Get Closest 버튼용).

    "각 driver 에 가장 가까운 오브젝트가 무엇인지" 발견/미리채우기가 목적이다.
    drivers 자신은 후보 풀에서 자동 제외(자기 자신은 거리 0 이라 최단이 되어버림).

    Args:
        drivers: driver 오브젝트 이름 리스트.
        candidates: 후보 풀(예: Driven 리스트 또는 현재 씬 선택).

    Returns:
        (pairs, errors) 튜플.
          pairs:  [(driver, driven, dist), ...] (driver 순서, 1:1).
          errors: 영어 경고/에러 메시지 문자열 리스트.
    """
    errors = []

    if not drivers:
        errors.append("No driver objects. Add objects to the Driver list.")
        return [], errors

    # 존재하지 않는 driver 는 제외.
    valid_drivers = []
    for driver in drivers:
        if MayaScene.exists(driver):
            valid_drivers.append(driver)
        else:
            errors.append("Driver not found in scene, skipped: {0}".format(driver))

    # 후보 풀: 존재하는 것만, driver 자신은 제외.
    driver_set = set(valid_drivers)
    pool = []
    for cand in candidates:
        if not MayaScene.exists(cand):
            errors.append("Candidate not found in scene, skipped: {0}".format(cand))
        elif cand in driver_set:
            continue
        else:
            pool.append(cand)

    if not pool:
        errors.append(
            "No candidate objects. Fill the Driven list or "
            "select objects in the scene, then press Get Closest.")
        return [], errors

    pairs = match_closest_pairs(valid_drivers, pool)

    if len(pairs) < len(valid_drivers):
        errors.append(
            "More drivers ({0}) than candidates ({1}); "
            "{2} driver(s) left without a match.".format(
                len(valid_drivers), len(pool),
                len(valid_drivers) - len(pairs)))

    return pairs, errors


def pairs_by_order(drivers, drivens):
    """**리스트에 보이는 자리 그대로** 짝짓는다 (`PAIRING_ORDER`).

    거리로 다시 계산하지 않는다. Match by Name 으로 세운 짝이나 Up/Down 으로 손수
    맞춘 순서를 그대로 연결하려면 이 방법이어야 한다 — 거리로 다시 짝지으면 애써 세운
    순서가 조용히 뒤집힌다.

    `(Null)` 자리는 짝이 없다는 표식이므로 **자리째** 건너뛴다. 한쪽만 빼면 뒤의 짝이
    한 칸씩 밀려 엉뚱한 오브젝트끼리 연결된다.

    Returns:
        ([(driver, driven, dist), ...], errors) — dist 는 로그용(못 재면 0.0).
    """
    pairs = []
    errors = []

    paired = min(len(drivers), len(drivens))
    if len(drivers) != len(drivens):
        errors.append(
            "Driver/Driven counts differ ({0} vs {1}); pairing the first "
            "{2} row(s).".format(len(drivers), len(drivens), paired))

    for i in range(paired):
        driver, driven = drivers[i], drivens[i]

        if driver == NULL_TARGET or driven == NULL_TARGET:
            errors.append("Row {0}: no match ({1}), skipped.".format(
                i + 1, NULL_TARGET))
            continue
        if not MayaScene.exists(driver):
            errors.append("Driver not found in scene, skipped: {0}".format(driver))
            continue
        if not MayaScene.exists(driven):
            errors.append("Driven not found in scene, skipped: {0}".format(driven))
            continue

        try:
            dist = MayaScene.distance(driver, driven)
        except Exception:
            dist = 0.0
        pairs.append((driver, driven, dist))

    return pairs, errors


def connect_closest(drivers, drivens, constraint_keys, maintain_offset=True,
                    pairing=PAIRING_CLOSEST):
    """driver 들을 driven 과 1:1 매칭 후 constraint 로 연결.

    Args:
        drivers: driver 오브젝트 이름 리스트.
        drivens: driven 오브젝트 이름 리스트 (1:1 매칭 — 한 번 쓰이면 풀에서 제외).
        constraint_keys: 적용할 constraint key 리스트 (예: ["parent", "scale"]).
        pairing: `PAIRING_CLOSEST`(거리로 다시 계산) 또는 `PAIRING_ORDER`(리스트 자리).
        maintain_offset: constraint 의 maintain offset 옵션.

    Returns:
        (results, errors) 튜플.
          results: 성공 매핑 dict 리스트
                   {driver, driven, distance, constraints:[label,...]}.
          errors:  영어 에러/경고 메시지 문자열 리스트.
    """
    results = []
    errors = []

    # key -> (label, method) 매핑 (CONSTRAINT_TYPES 기준).
    type_map = {key: (label, method) for key, label, method in CONSTRAINT_TYPES}

    # 입력 검증 -------------------------------------------------------
    if not drivers:
        errors.append("No driver objects. Add objects to the Driver list.")
        return results, errors

    if not drivens:
        errors.append("No driven objects. Add objects to the Driven list.")
        return results, errors

    if not constraint_keys:
        errors.append("No constraint type selected. Check at least one type.")
        return results, errors

    # 리스트 자리로 짝짓는 모드는 **거르기 전에** 짝을 만든다 — 존재하지 않는 항목을
    # 먼저 빼 버리면 그 자리가 사라져 뒤의 짝이 한 칸씩 밀린다.
    if pairing == PAIRING_ORDER:
        pairs, order_errors = pairs_by_order(drivers, drivens)
        errors.extend(order_errors)
        return _apply_constraints(pairs, type_map, constraint_keys,
                                  maintain_offset, results, errors)

    # 씬에 존재하지 않는 오브젝트는 미리 걸러낸다.
    valid_drivers = []
    for driver in drivers:
        if MayaScene.exists(driver):
            valid_drivers.append(driver)
        else:
            errors.append("Driver not found in scene, skipped: {0}".format(driver))

    driven_pool = []
    for driven in drivens:
        if MayaScene.exists(driven):
            driven_pool.append(driven)
        else:
            errors.append("Driven not found in scene, skipped: {0}".format(driven))

    # 1:1 매칭이므로 driven 풀보다 driver 가 많으면 일부는 짝이 없다.
    if len(valid_drivers) > len(driven_pool):
        errors.append(
            "More drivers ({0}) than drivens ({1}); "
            "{2} driver(s) will be left unconnected.".format(
                len(valid_drivers), len(driven_pool),
                len(valid_drivers) - len(driven_pool),
            )
        )

    # 매칭 (driver 순서 greedy 1:1, Get Closest 와 동일 로직) -----------
    pairs = match_closest_pairs(valid_drivers, driven_pool)
    matched = {driver for driver, _, _ in pairs}
    for driver in valid_drivers:
        if driver not in matched:
            errors.append("No driven left for driver: {0}".format(driver))

    # 연결 -----------------------------------------------------------
    return _apply_constraints(pairs, type_map, constraint_keys, maintain_offset,
                              results, errors)


def _apply_constraints(pairs, type_map, constraint_keys, maintain_offset,
                       results, errors):
    """짝 목록에 고른 constraint 를 건다. 두 짝짓기 모드가 공유하는 마지막 단계."""
    for driver, driven, dist in pairs:

        applied = []
        for key in constraint_keys:
            label, method_name = type_map[key]
            try:
                getattr(MayaScene, method_name)(driver, driven, maintain_offset)
                applied.append(label)
            except Exception as exc:
                errors.append(
                    "{0} constraint failed ({1} -> {2}): {3}".format(
                        label, driver, driven, exc
                    )
                )

        if applied:
            results.append({
                "driver": driver,
                "driven": driven,
                "distance": dist,
                "constraints": applied,
            })

    return results, errors
