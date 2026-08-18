# -*- coding: utf-8 -*-
"""snapshot_manager - Match 탭의 "추상 캐시(Snapshot)" 자료구조.

오브젝트를 잠깐 옮겼다가 되돌리려고 **로케이터를 1000개 만들던 흐름**을 대신한다.
씬에 노드를 만들지 않고 **월드 T/R/S 를 값으로만** 들고 있다가 그대로 되돌려 준다.

    Targets 에 오브젝트 리스트업 -> [Cache Targets] -> Followers 에 스냅샷 항목
    -> [Swap] -> (오브젝트를 마음대로 옮긴 뒤) -> [Match] -> 원래 자리로 복구

리스트에는 오브젝트처럼 한 줄씩 보이지만 씬에는 없는 항목이다. 그래서 표시 텍스트를
**노드 이름이 될 수 없는 형태**로 만든다:

    @cache pCube1
    @cache body_geo.vtx[128]

`@` 는 마야 노드 이름에 쓸 수 없다(`rename` 이 `_` 로 바꿔 버린다). 즉 이 텍스트가 실제 노드와
겹칠 일이 없고, 리스트 위젯도 이 항목을 씬에서 찾으려 하지 않는다(Framework TSL 이 "노드 이름
모양이 아닌 텍스트"는 마야에 묻지 않는다).

이 모듈은 **마야에 의존하지 않는다** — 캡처(월드 행렬 샘플링)는 `match_manager.capture()` 가 하고
여기서는 담아 두기만 한다. 덕분에 키 규칙과 캐시 동작은 마야 없이 테스트할 수 있다.

수명
----
캐시는 **툴 창이 들고 있는 세션 데이터**다(`MainWindow.snapshots`). 창을 닫거나 툴을 reload 하면
사라지고 씬 파일에도 저장되지 않는다 — 애초에 "잠깐 옮겼다 되돌리는" 용도라 그게 맞다.
대신 **원본 오브젝트가 지워져도 캐시는 살아 있다**(값만 들고 있으므로).
"""

# 스냅샷 항목의 표시 텍스트 접두사. 뒤에 캡처 당시의 이름이 붙는다.
SNAPSHOT_PREFIX = "@cache "


def is_snapshot(name):
    """이 텍스트가 스냅샷 항목인가."""
    return bool(name) and name.startswith(SNAPSHOT_PREFIX)


def key_for(source):
    """원본 이름 -> 스냅샷 키(= 리스트에 보이는 텍스트)."""
    return SNAPSHOT_PREFIX + source


def source_of(name):
    """스냅샷 키 -> 캡처 당시의 원본 이름. 스냅샷이 아니면 그대로 돌려준다."""
    return name[len(SNAPSHOT_PREFIX):] if is_snapshot(name) else name


class Snapshot(object):
    """캡처된 한 항목: 원본 이름 + 종류 + 월드 행렬(16개)."""

    __slots__ = ("source", "kind", "matrix")

    def __init__(self, source, kind, matrix):
        self.source = source
        self.kind = kind                  # transform / vertex / mesh / cluster / component
        self.matrix = list(matrix)        # 월드 행렬 (row-major 16)

    @property
    def key(self):
        return key_for(self.source)

    def position(self):
        return (self.matrix[12], self.matrix[13], self.matrix[14])

    def __repr__(self):
        return "Snapshot({0!r}, {1})".format(self.source, self.kind)


class SnapshotCache(object):
    """스냅샷 보관소. 키는 표시 텍스트 그대로다.

    같은 오브젝트를 다시 캡처하면 **덮어쓴다** — 키가 이름에서 나오므로 리스트에 이미 올라간
    항목의 텍스트가 그대로 유효하고, 오래된 사본이 쌓이지도 않는다.
    """

    def __init__(self):
        self._items = {}

    # ---- 담기 / 꺼내기
    def add(self, source, kind, matrix):
        """캡처 결과를 담고 스냅샷 키를 돌려준다."""
        snap = Snapshot(source, kind, matrix)
        self._items[snap.key] = snap
        return snap.key

    def get(self, key):
        """키로 스냅샷을 찾는다. 없으면 None."""
        return self._items.get(key)

    def keys(self):
        """담긴 스냅샷 키 목록(담은 순서)."""
        return list(self._items.keys())

    # ---- 관리
    def remove(self, keys):
        """주어진 키들을 버린다. 실제로 지운 개수를 돌려준다."""
        removed = 0
        for key in keys or []:
            if self._items.pop(key, None) is not None:
                removed += 1
        return removed

    def clear(self):
        """전부 버린다. 버린 개수를 돌려준다."""
        count = len(self._items)
        self._items.clear()
        return count

    def missing(self, keys):
        """주어진 키 중 캐시에 없는 것들(순서 유지, 중복 제거)."""
        seen, gone = set(), []
        for key in keys or []:
            if is_snapshot(key) and key not in self._items and key not in seen:
                seen.add(key)
                gone.append(key)
        return gone

    def __len__(self):
        return len(self._items)

    def __contains__(self, key):
        return key in self._items
