# Python Script by Ji Hun Park
# last Update date : 2026-06-22
# A00211_RefLineage - Maya 씬의 reference 관계를 읽어 A00210 Lineage 그래프로 변환.
#
# 현재 열린 Maya 씬과 그 씬이 (중첩 포함) 불러오는 모든 reference 파일을 노드로 만들고,
# "참조 대상(불러와지는 파일) -> 참조하는 파일" 방향의 reference 엣지로 연결한 뒤
# A00210_FileManager 의 lineage JSON(<store_dir>/lineage/<name>.json) 과 완전히 동일한
# 포맷으로 저장한다. 포맷·설정의 단일 소스를 위해 A00210 의 lineage/store/prefs 모듈을
# 그대로 재사용한다(같은 인터프리터에서 tools.A00210_FileManager.* 로 import).
#
#   - 노드 1개 = 파일 1개(절대경로로 dedup). 씬 자신도 노드(루트, depth 0).
#   - reference 엣지: owner(참조하는 파일).references 에 source(참조 대상) id 를 넣는다
#     (A00210 의 reference 방향 규약과 동일: 화살표 source -> owner).
#   - key 는 project_root 기준 상대경로(루트 밖/미설정이면 ""), 위치는 depth 로 자동 배치.
#
# maya.cmds 는 함수 안에서 lazy import 한다(Maya 밖에서도 모듈 import 가 깨지지 않게).

import os
import time

# A00210 의 순수 파이썬(UI/DCC 비의존) 모듈 재사용 — 포맷/설정 단일 소스.
from tools.A00210_FileManager.app.core import lineage as lin
from tools.A00210_FileManager.app.core import prefs as fm_prefs
from tools.A00210_FileManager.app.core.store import MetaStore, OutsideProjectRootError


# 노드 자동 배치 간격(A00210 캔버스의 NODE_W=150 / NODE_H=48 기준 여유 포함).
_COL_SPACING = 210.0
_ROW_SPACING = 150.0

# 씬이 저장 전(untitled)일 때 루트 노드를 식별할 내부 키.
_UNTITLED = "__UNTITLED_SCENE__"


# ------------------------------------------------------------------ prefs/store

def load_store():
    """A00210 의 prefs.json 에서 store_dir/project_root 를 읽어 (MetaStore, prefs) 반환."""
    prefs = fm_prefs.load()
    store = MetaStore(prefs.get("store_dir", ""), prefs.get("project_root", ""))
    return store, prefs


# ------------------------------------------------------------------ maya scan

def _norm(path):
    """대소문자/슬래시 차이를 무시한 dedup 키."""
    return os.path.normcase(os.path.normpath(path)) if path else _UNTITLED


def current_scene_path():
    """현재 씬 파일 절대경로. 저장 전(untitled)이면 ""."""
    import maya.cmds as cmds
    return cmds.file(q=True, sceneName=True) or ""


def _ref_nodes_with_files(cmds):
    """파일이 해석되는 reference 노드만 {refNode: (file_path, is_loaded)} 로 반환.

    sharedReferenceNode 등 파일이 없는 노드는 referenceQuery 가 예외를 내므로 건너뛴다.
    """
    out = {}
    for node in (cmds.ls(references=True) or []):
        try:
            fpath = cmds.referenceQuery(node, filename=True, withoutCopyNumber=True)
        except (RuntimeError, ValueError):
            continue
        if not fpath:
            continue
        try:
            loaded = bool(cmds.referenceQuery(node, isLoaded=True))
        except (RuntimeError, ValueError):
            loaded = True
        out[node] = (fpath, loaded)
    return out


def _parent_ref_node(cmds, ref_node):
    """ref_node 를 담고 있는 부모 reference 노드. 최상위(씬 직속)면 None."""
    try:
        return cmds.referenceQuery(ref_node, referenceNode=True, parent=True)
    except (RuntimeError, ValueError):
        return None


def collect_scene_references():
    """현재 씬의 reference 관계를 중간 표현(dict)으로 수집.

    반환:
      {
        "scene":      <씬 절대경로 또는 "">,
        "scene_norm": <루트 식별 키>,
        "paths":      {norm: abs_path},          # 씬 포함 모든 파일(빈 abs 는 untitled 씬)
        "loaded":     {norm: bool},              # 파일이 로드된 reference 인지(씬=True)
        "edges":      [(owner_norm, source_norm)],  # owner 가 source 를 참조
        "depth":      {norm: int},               # 씬=0, 직속 ref=1, 중첩=2 ...
      }
    """
    import maya.cmds as cmds

    scene = current_scene_path()
    scene_norm = _norm(scene)

    paths = {scene_norm: scene}
    loaded = {scene_norm: True}

    ref_files = _ref_nodes_with_files(cmds)
    node_norm = {}                       # refNode -> 파일 norm
    for node, (fpath, is_loaded) in ref_files.items():
        n = _norm(fpath)
        node_norm[node] = n
        paths.setdefault(n, fpath)
        # 같은 파일을 여러 번 참조하면 하나라도 로드면 로드로 본다.
        loaded[n] = loaded.get(n, False) or is_loaded

    edges = []
    seen_edge = set()
    for node, source_norm in node_norm.items():
        parent_node = _parent_ref_node(cmds, node)
        owner_norm = node_norm.get(parent_node, scene_norm) if parent_node else scene_norm
        if owner_norm == source_norm:
            continue                     # 자기참조 방어
        key = (owner_norm, source_norm)
        if key in seen_edge:
            continue
        seen_edge.add(key)
        edges.append(key)

    depth = _compute_depth(scene_norm, edges, paths.keys())

    return {
        "scene": scene,
        "scene_norm": scene_norm,
        "paths": paths,
        "loaded": loaded,
        "edges": edges,
        "depth": depth,
    }


def _compute_depth(scene_norm, edges, all_norms):
    """씬(루트)으로부터 owner->source 방향 BFS 로 각 파일의 깊이를 구한다."""
    children = {}
    for owner, source in edges:
        children.setdefault(owner, []).append(source)

    depth = {scene_norm: 0}
    queue = [scene_norm]
    while queue:
        cur = queue.pop(0)
        for nxt in children.get(cur, []):
            if nxt not in depth:
                depth[nxt] = depth[cur] + 1
                queue.append(nxt)

    # 씬에 닿지 않은(이론상 없음) 파일은 1로.
    for n in all_norms:
        depth.setdefault(n, 1)
    return depth


# ------------------------------------------------------------------ graph build

def _make_node(abs_path, store, seq, is_scene, is_loaded):
    """파일 1개 -> LineageNode. key 는 project_root 상대경로(밖/미설정이면 "")."""
    key = ""
    if abs_path and getattr(store, "project_root", ""):
        try:
            key = store.make_key(abs_path)
        # ValueError: Windows 에서 project_root 와 다른 드라이브의 파일(relpath 가 던짐).
        except (OutsideProjectRootError, ValueError):
            key = ""

    file_name = os.path.basename(abs_path) if abs_path else "(untitled scene)"
    node = lin.LineageNode(id=lin.new_node_id(), file_name=file_name, key=key, seq=seq)

    labels = []
    if is_scene:
        labels.append("current scene")
    if not is_loaded and not is_scene:
        labels.append("unloaded")
    node.label = " / ".join(labels)
    return node


def _layout(nodes_by_norm, depth):
    """depth 별로 가로로 균등(중앙 정렬) 배치. references 는 Auto Layout 에 안 잡히므로
    내보낼 때 보기 좋은 초기 위치를 직접 준다."""
    by_depth = {}
    for norm, node in nodes_by_norm.items():
        by_depth.setdefault(depth.get(norm, 1), []).append(norm)

    for d, norms in by_depth.items():
        norms.sort(key=lambda n: nodes_by_norm[n].seq)   # 결정적 순서
        count = len(norms)
        for col, norm in enumerate(norms):
            node = nodes_by_norm[norm]
            node.x = (col - (count - 1) / 2.0) * _COL_SPACING
            node.y = d * _ROW_SPACING


def build_graph(collected, store, name, author=""):
    """collect_scene_references() 결과 -> LineageGraph (저장 직전 상태)."""
    graph = lin.LineageGraph(
        name=name,
        created_by=author or "",
        created_at=time.strftime("%Y-%m-%d %H:%M:%S"),
    )

    scene_norm = collected["scene_norm"]
    paths = collected["paths"]
    loaded = collected["loaded"]

    # 노드 생성 — 씬을 seq 0 으로 먼저, 나머지는 경로 정렬로 결정적.
    ordered = [scene_norm] + sorted(n for n in paths if n != scene_norm)
    nodes_by_norm = {}
    for seq, norm in enumerate(ordered):
        node = _make_node(
            paths.get(norm, ""), store, seq,
            is_scene=(norm == scene_norm),
            is_loaded=loaded.get(norm, True),
        )
        graph.nodes.append(node)
        nodes_by_norm[norm] = node

    _layout(nodes_by_norm, collected["depth"])

    # reference 엣지: owner.references += source.id (화살표 source -> owner).
    for owner_norm, source_norm in collected["edges"]:
        owner = nodes_by_norm.get(owner_norm)
        source = nodes_by_norm.get(source_norm)
        if owner is None or source is None or owner is source:
            continue
        if source.id not in owner.references:
            owner.references.append(source.id)

    return graph


def export_scene_references(name="", author=""):
    """원샷 헬퍼: 현재 씬 스캔 -> 그래프 빌드 -> lineage JSON 저장. (저장 경로, 그래프) 반환.

    UI 없이 '특별한 명령'으로 바로 내보낼 때 쓴다. name 이 없으면 씬 파일명을 쓴다.
    store_dir 미설정이면 ValueError.
    """
    store, prefs = load_store()
    if not store.store_dir:
        raise ValueError("Store Repo is not set. Configure it in A00210_FileManager first.")

    collected = collect_scene_references()
    if not name:
        scene = collected["scene"]
        name = os.path.splitext(os.path.basename(scene))[0] if scene else "scene_references"

    graph = build_graph(collected, store, name, author or prefs.get("author", ""))
    path = lin.save(store.store_dir, graph)
    return path, graph
