# -*- coding: utf-8 -*-
"""
ClosestConnector - 핵심 로직 (Connect Closest 탭).

각 driver 에 대해 가장 가까운 driven 을 1:1 로 매칭하고, 선택된 constraint 종류로
연결한다. UI 비의존 — MayaScene 어댑터만 사용하고, 결과는 dict 리스트로 반환해서
UI 가 로그로 출력하도록 한다.

A00140_ConnectClosest 의 closest_connector 를 그대로 옮겨온 것이다.
"""

from .maya_scene import MayaScene


# constraint key -> (label, MayaScene 메서드명).
# UI 의 체크박스 순서/라벨과 1:1 로 대응한다.
CONSTRAINT_TYPES = [
    ("parent", "Parent", "parent_constraint"),
    ("point", "Point", "point_constraint"),
    ("orient", "Orient", "orient_constraint"),
    ("scale", "Scale", "scale_constraint"),
]


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


def connect_closest(drivers, drivens, constraint_keys, maintain_offset=True):
    """driver 들을 가장 가까운 driven 과 1:1 매칭 후 constraint 로 연결.

    Args:
        drivers: driver 오브젝트 이름 리스트.
        drivens: driven 오브젝트 이름 리스트 (1:1 매칭 — 한 번 쓰이면 풀에서 제외).
        constraint_keys: 적용할 constraint key 리스트 (예: ["parent", "scale"]).
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

    # 매칭 + 연결 -----------------------------------------------------
    for driver in valid_drivers:

        if not driven_pool:
            errors.append("No driven left for driver: {0}".format(driver))
            continue

        driven, dist = find_closest(driver, driven_pool)
        # 1:1 매칭: 선택된 driven 은 풀에서 제거해 재사용 방지.
        driven_pool.remove(driven)

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
