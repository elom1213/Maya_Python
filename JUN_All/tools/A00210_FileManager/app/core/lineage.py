# Python Script by Ji Hun Park
# last Update date : 2026-06-18
# A00210_FileManager - lineage graph (UI/DCC 비의존)
#
# 마야 파일들 사이의 브랜치/병합 관계(DAG)를 사용자가 직접 기록하고, git-graph 스타일의
# 색상 레인 트리로 다시 볼 수 있게 한다. 관계 데이터는 store_dir 안에 JSON 으로 저장하므로
# (키 방식과 동일) git_sync 의 push/pull 로 자동 동기화된다. path_structure.py 와 같은 패턴.
#
#   <store_dir>/lineage/<name>.json
#
# - 노드 1개 = 마야 파일 1개(또는 "제작 예정" placeholder). parents 로 부모 노드를 가리킨다.
# - 병합 = 부모 여럿, 브랜치 = 한 부모에 자식 여럿.
# - 레인(세로 컬럼)/색상은 DAG 토폴로지에서 계산한다(사용자는 관계만 기록). 노드 위치(x/y)는
#   캔버스에서 사용자가 드래그한 값을 그대로 저장한다.

import os
import json
import uuid

from dataclasses import dataclass, field, asdict

from .store import MetaStore, OutsideProjectRootError


LINEAGE_DIR = "lineage"

# Windows 파일명에 못 쓰는 문자.
_ILLEGAL = '\\/:*?"<>|'

# 레인별 색상 팔레트(구분되는 12색). lane % len 으로 순환한다.
LANE_PALETTE = [
    "#4F8DFD",  # blue
    "#39B58A",  # green
    "#E0A93B",  # amber
    "#D2603A",  # orange-red
    "#9B6DD6",  # purple
    "#3FB6C9",  # cyan
    "#C75B9A",  # magenta
    "#7FB23A",  # lime
    "#E06C9F",  # pink
    "#5C6BC0",  # indigo
    "#B0883B",  # bronze
    "#48A36B",  # teal-green
]


def lane_color(lane):
    """레인 인덱스 -> 색상 hex 문자열."""
    return LANE_PALETTE[lane % len(LANE_PALETTE)]


# ------------------------------------------------------------------- dataclass

@dataclass
class LineageNode:
    """관계 그래프의 노드 1개 = 마야 파일 1개(또는 제작 예정 placeholder)."""

    id: str = ""               # 내부 안정 식별자(uuid hex). key 와 분리.
    file_name: str = ""        # 표시 라벨 (예: "JP__LUN_rig_0140.mb")
    key: str = ""              # project_root 기준 POSIX 키 ("" 면 planned/루트밖)
    planned: bool = False      # 아직 안 만든 파일("제작 예정")
    label: str = ""            # 자유 주석
    relation: str = ""         # primary parent 에 대한 관계: ""(auto)|"version"|"branch"
    parents: list = field(default_factory=list)   # 부모 노드 id 목록
    x: float = 0.0             # 저장된 캔버스 위치(사용자 드래그)
    y: float = 0.0
    seq: int = 0               # 생성 순서. 토폴로지 정렬 tie-break(결정적 레이아웃).

    def to_dict(self):
        return asdict(self)

    @staticmethod
    def from_dict(data):
        return LineageNode(
            id=data.get("id", ""),
            file_name=data.get("file_name", ""),
            key=data.get("key", ""),
            planned=bool(data.get("planned", False)),
            label=data.get("label", ""),
            relation=data.get("relation", ""),
            parents=list(data.get("parents", [])),
            x=float(data.get("x", 0.0)),
            y=float(data.get("y", 0.0)),
            seq=int(data.get("seq", 0)),
        )


@dataclass
class LineageGraph:
    """이름 붙인 관계 그래프 1개(에셋 단위)."""

    name: str = ""
    nodes: list = field(default_factory=list)   # list[LineageNode]
    created_by: str = ""
    created_at: str = ""

    def to_dict(self):
        return {
            "name": self.name,
            "nodes": [n.to_dict() for n in self.nodes],
            "created_by": self.created_by,
            "created_at": self.created_at,
        }

    @staticmethod
    def from_dict(data):
        graph = LineageGraph(
            name=data.get("name", ""),
            created_by=data.get("created_by", ""),
            created_at=data.get("created_at", ""),
        )
        graph.nodes = [
            LineageNode.from_dict(item)
            for item in data.get("nodes", [])
        ]
        return graph

    def node_by_id(self, node_id):
        for n in self.nodes:
            if n.id == node_id:
                return n
        return None


# --------------------------------------------------------------- name / path

def _sanitize_name(name):
    """표시 이름을 파일명으로 안전하게 변환. (JSON 안의 name 은 원문 유지)"""
    cleaned = "".join("_" if c in _ILLEGAL else c for c in (name or "").strip())
    cleaned = "_".join(cleaned.split())          # 공백 런 → 단일 _
    cleaned = cleaned.strip("_.")
    return cleaned or "lineage"


def lineage_dir(store_dir):
    return os.path.join(store_dir, LINEAGE_DIR)


def graph_path(store_dir, name):
    return os.path.join(lineage_dir(store_dir), _sanitize_name(name)) + ".json"


# --------------------------------------------------------------- save / load

def save(store_dir, graph):
    """LineageGraph 를 JSON 으로 저장하고 경로 반환."""
    path = graph_path(store_dir, graph.name)
    MetaStore._ensure_parent(path)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(graph.to_dict(), f, ensure_ascii=False, indent=2)

    return path


def list_names(store_dir):
    """저장된 그래프의 표시 이름 목록(대소문자 무시 정렬). 없으면 []."""
    dir_path = lineage_dir(store_dir)
    if not store_dir or not os.path.isdir(dir_path):
        return []

    names = []
    for fname in os.listdir(dir_path):
        if not fname.endswith(".json"):
            continue
        try:
            with open(os.path.join(dir_path, fname), "r", encoding="utf-8") as f:
                data = json.load(f)
            names.append(data.get("name") or fname[:-5])
        except (OSError, ValueError):
            names.append(fname[:-5])

    return sorted(names, key=str.lower)


def load(store_dir, name):
    """이름으로 LineageGraph 로드. 없으면 None."""
    path = graph_path(store_dir, name)
    if not os.path.isfile(path):
        return None

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return LineageGraph.from_dict(data)


def exists(store_dir, name):
    return os.path.isfile(graph_path(store_dir, name))


def delete(store_dir, name):
    path = graph_path(store_dir, name)
    if os.path.isfile(path):
        os.remove(path)
        return True
    return False


# ------------------------------------------------------------- node helpers

def new_node_id():
    return uuid.uuid4().hex


def node_from_entry(entry, seq):
    """scanner.scan() entry dict -> LineageNode (포맷 무관).

    루트 밖 파일은 entry["key"] 가 None 이므로 key="" 로 둔다(썸네일/기록 링크 없음).
    """
    return LineageNode(
        id=new_node_id(),
        file_name=entry.get("file_name", ""),
        key=entry.get("key") or "",
        planned=False,
        seq=seq,
    )


def node_from_path(abs_path, store, seq):
    """임의 경로의 파일 1개 -> LineageNode (포맷 무관).

    store(project_root 보유)로 키를 산출한다. 루트 밖/루트 미설정이면 key="" (기록 링크 없음).
    """
    key = ""
    if store is not None and getattr(store, "project_root", ""):
        try:
            key = store.make_key(abs_path)
        except OutsideProjectRootError:
            key = ""
    return LineageNode(
        id=new_node_id(),
        file_name=os.path.basename(abs_path),
        key=key,
        planned=False,
        seq=seq,
    )


def next_seq(graph):
    """그래프에서 다음 생성 순번."""
    if not graph.nodes:
        return 0
    return max(n.seq for n in graph.nodes) + 1


def remove_node(graph, node_id):
    """노드를 삭제하고 다른 모든 노드의 parents 에서 해당 id 를 제거(고아 정리)."""
    graph.nodes = [n for n in graph.nodes if n.id != node_id]
    for n in graph.nodes:
        if node_id in n.parents:
            n.parents = [p for p in n.parents if p != node_id]


# --------------------------------------------------------------- cycle guard

def _parents_map(graph):
    """node_id -> 유효한(그래프에 존재하는) 부모 id 목록."""
    ids = {n.id for n in graph.nodes}
    return {
        n.id: [p for p in n.parents if p in ids]
        for n in graph.nodes
    }


def has_cycle(graph):
    """그래프에 순환이 있으면 True (DFS color-marking)."""
    pmap = _parents_map(graph)
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {nid: WHITE for nid in pmap}

    def dfs(u):
        color[u] = GRAY
        for p in pmap.get(u, []):
            if color.get(p) == GRAY:
                return True
            if color.get(p) == WHITE and dfs(p):
                return True
        color[u] = BLACK
        return False

    for nid in pmap:
        if color[nid] == WHITE and dfs(nid):
            return True
    return False


def would_create_cycle(graph, parent_id, child_id):
    """parent->child 엣지(child.parents 에 parent 추가)가 순환을 만들면 True.

    child 가 이미 parent 의 조상이면(= parent 의 parents 를 거슬러 올라가 child 에 도달) 순환.
    """
    if parent_id == child_id:
        return True

    pmap = _parents_map(graph)
    stack = list(pmap.get(parent_id, []))
    seen = set()
    while stack:
        cur = stack.pop()
        if cur == child_id:
            return True
        if cur in seen:
            continue
        seen.add(cur)
        stack.extend(pmap.get(cur, []))
    return False


# ------------------------------------------------------- lanes / auto layout

def _topo_order(graph):
    """seq tie-break Kahn 위상정렬. 루트(부모 없음)부터. (id 목록 반환)

    순환이 있어 일부가 정렬되지 않으면 남은 노드를 seq 순으로 뒤에 붙인다(무한루프 방지).
    """
    import heapq

    pmap = _parents_map(graph)
    seq_of = {n.id: n.seq for n in graph.nodes}

    children = {nid: [] for nid in pmap}
    indeg = {nid: 0 for nid in pmap}
    for nid, parents in pmap.items():
        indeg[nid] = len(parents)
        for p in parents:
            children[p].append(nid)

    heap = [(seq_of[nid], nid) for nid, d in indeg.items() if d == 0]
    heapq.heapify(heap)

    order = []
    visited = set()
    while heap:
        _, nid = heapq.heappop(heap)
        order.append(nid)
        visited.add(nid)
        for c in children[nid]:
            indeg[c] -= 1
            if indeg[c] == 0:
                heapq.heappush(heap, (seq_of[c], c))

    if len(order) < len(pmap):
        # 순환 등으로 남은 노드 → seq 순으로 폴백.
        rest = sorted(
            (nid for nid in pmap if nid not in visited),
            key=lambda nid: seq_of[nid],
        )
        order.extend(rest)

    return order


def _leftmost_free(active):
    """active 에서 첫 None 인덱스. 없으면 새 컬럼을 추가하고 그 인덱스 반환."""
    for i, v in enumerate(active):
        if v is None:
            return i
    active.append(None)
    return len(active) - 1


def compute_lanes(graph):
    """DAG -> (lane_of: dict[id->lane], topo_order: list[id]). git-graph 컬럼 배정.

    위→아래(토폴로지) 순서로 처리:
      - 자기 id 로 예약된 레인이 있으면 그 중 가장 왼쪽을 차지하고 나머지는 해제(병합 수렴).
      - 없으면 가장 왼쪽 빈 레인(없으면 새 컬럼).
      - 자식들(seq 순) 중 '이 노드가 첫 부모인' 자식 하나가 트렁크(같은 레인)를 잇고,
        나머지 자식은 새 레인(브랜치/병합선)을 받는다. 트렁크 자식 선택은 relation 으로
        제어한다: relation=="version" 자식이 최우선, "branch" 는 트렁크 제외, 미지정은
        기존 기본(첫 자식). → "version-up"=부모와 같은 색, "branch"=다른 색.
    """
    order = _topo_order(graph)
    pmap = _parents_map(graph)
    seq_of = {n.id: n.seq for n in graph.nodes}
    relation_of = {n.id: getattr(n, "relation", "") for n in graph.nodes}

    children = {nid: [] for nid in pmap}
    for nid, parents in pmap.items():
        for p in parents:
            children[p].append(nid)

    # 자식별 '첫 부모'(seq 최소) = primary parent. 이 부모만 트렁크를 잇는다.
    primary_parent = {}
    for nid, parents in pmap.items():
        if parents:
            primary_parent[nid] = min(parents, key=lambda p: seq_of.get(p, 0))

    active = []           # active[i] = 그 레인이 향하는(예약된) 노드 id, 또는 None
    lane_of = {}

    for nid in order:
        # 1) 내 레인 결정.
        mine = [i for i, v in enumerate(active) if v == nid]
        if mine:
            lane = mine[0]
            for j in mine[1:]:      # 병합: 나머지 예약 레인 해제
                active[j] = None
        else:
            lane = _leftmost_free(active)
        lane_of[nid] = lane

        # 2) 자식 레인 예약.
        kids = sorted(children.get(nid, []), key=lambda c: seq_of.get(c, 0))

        # 트렁크(부모 레인 상속)를 이어받을 자식 1개 선택. 이 노드가 primary parent 인
        # 자식만 후보. relation=="version" 최우선, 그다음 "branch" 가 아닌 첫 자식.
        own = [c for c in kids if primary_parent.get(c) == nid]
        trunk_child = next((c for c in own if relation_of.get(c) == "version"), None)
        if trunk_child is None:
            trunk_child = next((c for c in own if relation_of.get(c) != "branch"), None)

        # 트렁크 레인을 먼저 예약(없으면 종료)해 나머지 자식이 그 레인을 뺏지 않게 한다.
        active[lane] = trunk_child     # None 이면 이 노드에서 레인 종료(리프/전부 branch)
        for c in kids:
            if c is trunk_child:
                continue
            j = _leftmost_free(active)
            active[j] = c              # 브랜치 / 병합 보조선

    return lane_of, order


def auto_layout(graph, x_step=160, y_step=90):
    """레인/토폴로지로 노드의 x/y 를 in-place 설정(저장 시 위치 영속).

    x = lane * x_step, y = (토폴로지 행 인덱스) * y_step.
    반환: (lane_of, order) — 호출자가 재렌더에 재사용.
    """
    lane_of, order = compute_lanes(graph)
    row_of = {nid: i for i, nid in enumerate(order)}

    for n in graph.nodes:
        n.x = float(lane_of.get(n.id, 0) * x_step)
        n.y = float(row_of.get(n.id, 0) * y_step)

    return lane_of, order
