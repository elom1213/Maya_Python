# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-09-16
# A00030_quickTool_V02 - 핵심 로직 (maya.cmds / mel, UI 비의존)
"""
quick_ops - Quick Tool 의 버튼 하나하나가 실제로 하는 일.

레거시 `A00030_quickTool/MOD_QuickTool_v01.py` 의 콜백들을 그대로 옮겼다.
**동작은 바꾸지 않고**, UI 의존만 걷어냈다.

  - 레거시는 `print()` 와 `cmds.warning()` 으로 결과를 알렸다. 여기서는 전부
    **로그 문자열 리스트를 돌려준다** — 툴 창의 공용 로그에 쌓기 위해서다.
    (`[WARN] ...` 접두사는 다른 Qt 툴들과 같은 규칙이다.)
  - 클립보드는 Qt 의 것이라 여기서 만지지 않는다. `scene_folder()` 는 **경로만**
    돌려주고 복사는 UI 가 한다.
"""

import os

import maya.cmds as cmds
import maya.mel as mel

from Framework.core.maya_undo import undo_chunk
from Framework.core.file_opener import open_path


# ==========================================================================
# Update window
# ==========================================================================

def set_playback_view(selected_only):
    """재생 중 갱신할 뷰포트를 정한다 (Selected = 활성 뷰만).

    뷰포트를 하나만 갱신하면 무거운 씬에서 재생이 눈에 띄게 빨라진다.
    """
    view = "active" if selected_only else "all"
    cmds.playbackOptions(view=view)
    return ["Playback view : {0}".format(
        "active view only" if selected_only else "all views")]


# ==========================================================================
# Print
# ==========================================================================

def selected_names():
    """현재 선택을 짧은 이름 목록으로. 레거시 `print(cmds.ls(sl=True))` 와 같은 내용."""
    selection = cmds.ls(sl=True) or []
    if not selection:
        return [], ["[WARN] Nothing selected."]
    return selection, ["Selected ({0}) : {1}".format(len(selection), selection)]


# -- 계층 트리 -------------------------------------------------------------
# 트리 그림 문자. 스크립트 에디터도 로그창도 유니코드를 그대로 찍는다.
TREE_MID = u"├── "   # |--
TREE_END = u"└── "   # `--
TREE_BAR = u"│   "             # |
TREE_GAP = u"    "


def _short_name(path):
    """DAG 경로에서 leaf 이름만. 네임스페이스는 남긴다(레퍼런스에서 의미가 있다)."""
    return path.split("|")[-1]


def _child_transforms(path):
    """자식 트랜스폼(조인트 포함)을 풀 경로로. 셰이프는 뺀다.

    `listRelatives -type transform` 은 **조인트도 함께 준다**(joint 가 transform 을
    상속하므로 - 실측). 셰이프만 빠지므로 부모 관계를 보는 데 이게 맞다.
    """
    return cmds.listRelatives(path, children=True, fullPath=True,
                              type="transform") or []


def build_tree(root_path):
    """root_path 이하를 트리 그림 줄 목록으로. **재귀를 쓰지 않는다.**

    조인트 체인은 수백 단계로 깊어질 수 있는데(300단 체인도 흔한 형태), 재귀로 짜면
    파이썬 재귀 한계(기본 1000, 마야 콜백 스택 위라 여유가 더 적다)에 걸릴 수 있다.
    명시적 스택으로 훑는다.
    """
    lines = [_short_name(root_path)]

    def push_children(stack, parent, prefix):
        """자식을 **역순으로** 쌓는다. LIFO 라 그래야 첫 자식이 먼저 꺼내진다."""
        kids = _child_transforms(parent)
        for i in range(len(kids) - 1, -1, -1):
            stack.append((kids[i], prefix, i == len(kids) - 1))

    # (노드 경로, 이 줄에 붙을 접두사, 형제 중 마지막인가)
    stack = []
    push_children(stack, root_path, u"")

    while stack:
        node, prefix, is_last = stack.pop()

        # 꺼내는 즉시 줄을 만든다 = 깊이 우선 전위 순회.
        # (자식을 다 쌓아 두고 나중에 줄을 만들면 손자가 형제들 뒤로 밀린다)
        lines.append(prefix + (TREE_END if is_last else TREE_MID)
                     + _short_name(node))

        # 마지막 형제 아래로는 세로줄을 잇지 않는다
        push_children(stack, node, prefix + (TREE_GAP if is_last else TREE_BAR))

    return lines


def hierarchy_text(roots):
    """선택한 오브젝트마다 트리를 그려 하나의 문자열로. (텍스트, 노드 수) 반환."""
    paths = []
    for node in (roots or []):
        found = cmds.ls(node, long=True) or []
        if found:
            paths.append(found[0])

    # 이미 다른 선택의 자손인 것은 건너뛴다 - 계층을 통째로 고르면 같은 트리가
    # 몇 번이고 다시 찍히기 때문이다.
    roots_only = []
    skipped = 0
    for path in paths:
        if any(path != other and path.startswith(other + "|") for other in paths):
            skipped += 1
            continue
        roots_only.append(path)

    blocks = []
    total = 0
    for path in roots_only:
        lines = build_tree(path)
        total += len(lines)
        blocks.append(u"\n".join(lines))

    text = u"\n\n".join(blocks)
    if skipped:
        text += (u"\n\n[Info] {0} selected object(s) were skipped - they are already "
                 u"inside another printed tree.".format(skipped))
    return text, total


def print_hierarchy():
    """선택 오브젝트와 그 아래 자식들의 부모 관계를 트리로 만든다.

        joint_01
        └── joint_02_zro_01
            └── joint_02_zro_02

    씬은 건드리지 않는다. (텍스트, 로그) 반환.
    """
    selection = cmds.ls(sl=True, long=True) or []
    if not selection:
        return u"", ["[WARN] Select one or more objects first."]

    text, total = hierarchy_text(selection)
    return text, ["Print Hierarchy : {0} node(s).".format(total)]


# ==========================================================================
# Import option
# ==========================================================================

FBX_PLUGIN = "fbxmaya"


def import_fbx_normal():
    """FBX 임포트 때 **노멀을 파일 것 그대로** 쓰게 한다(잠금 무시).

    다음 임포트부터 적용되는 **전역 FBX 설정**이다 - 지금 씬을 바꾸지 않는다.

    ★ `FBXProperty` 는 MEL 명령이 아니라 **`fbxmaya` 플러그인이 등록하는 프로시저**다.
    플러그인이 안 올라와 있으면 `Cannot find procedure "FBXProperty"` 로 죽는다(레거시는
    이 경우 스크립트 에디터에 트레이스백만 남겼다). 먼저 플러그인을 올리고, 그래도 안 되면
    **로그로 이유를 말한다.**
    """
    try:
        loaded = cmds.pluginInfo(FBX_PLUGIN, query=True, loaded=True)
    except RuntimeError:
        loaded = False

    if not loaded:
        try:
            cmds.loadPlugin(FBX_PLUGIN, quiet=True)
        except RuntimeError:
            return ["[WARN] FBX plugin ('{0}') is not available - "
                    "cannot set the import option.".format(FBX_PLUGIN)]

    try:
        mel.eval('FBXProperty "Import|IncludeGrp|Geometry|OverrideNormalsLock" -v 1')
    except RuntimeError:
        return ["[WARN] FBX plugin ('{0}') did not provide FBXProperty - "
                "cannot set the import option.".format(FBX_PLUGIN)]

    return ["FBX import : OverrideNormalsLock ON (applies to the next import)."]


# ==========================================================================
# Create
# ==========================================================================

# file 노드가 place2dTexture 에서 받아야 하는 어트리뷰트. 마야가 UI 로 만들 때
# 이어 주는 것과 같은 목록이다(하나라도 빠지면 UV 조작이 따로 논다).
_PLACE2D_ATTRS = (
    "coverage", "translateFrame", "rotateFrame", "mirrorU", "mirrorV",
    "stagger", "wrapU", "wrapV", "repeatUV", "offset", "rotateUV", "noiseUV",
    "vertexUvOne", "vertexUvTwo", "vertexUvThree", "vertexCameraOne",
)


def create_texture_file():
    """`file` + `place2dTexture` 를 만들어 제대로 연결한다.

    하이퍼셰이드에서 file 노드만 만들면 place2dTexture 가 딸려 오지만, 스크립트로
    `shadingNode` 만 부르면 **연결이 안 된 채** 생긴다. 그래서 직접 이어 준다.
    """
    with undo_chunk():
        file_node = cmds.shadingNode("file", asTexture=True, isColorManaged=True)
        place = cmds.shadingNode("place2dTexture", asUtility=True)

        for attr in _PLACE2D_ATTRS:
            cmds.connectAttr("{0}.{1}".format(place, attr),
                             "{0}.{1}".format(file_node, attr))

        cmds.connectAttr(place + ".outUV", file_node + ".uv")
        cmds.connectAttr(place + ".outUvFilterSize", file_node + ".uvFilterSize")

    return file_node, place, ["Created texture : {0} <- {1}".format(file_node, place)]


def create_cluster_each():
    """선택한 오브젝트마다 클러스터를 **하나씩** 만든다.

    `cmds.cluster` 는 선택 전체에 클러스터 **하나**를 만든다. 개별로 걸려면
    오브젝트마다 따로 선택해서 호출해야 한다. relative=True 로 만든다.
    """
    objs = cmds.ls(sl=True, long=True) or []
    if not objs:
        return [], ["[WARN] Select object(s) first."]

    handles = []

    # 오브젝트가 여러 개여도 undo 한 번으로 되돌아가게 묶는다.
    with undo_chunk():
        for obj in objs:
            cmds.select(obj, replace=True)
            # cluster() 반환: [clusterNode, clusterHandle]
            handles.append(cmds.cluster(relative=True)[1])

    if handles:
        cmds.select(handles, replace=True)

    return handles, ["Created {0} cluster(s) : {1}".format(len(handles), handles)]


# ==========================================================================
# File
# ==========================================================================

def scene_folder():
    """현재 씬이 저장된 **폴더** 경로. 저장 전이면 ("", 경고).

    - 파일 이름은 빼고 폴더까지만(`os.path.dirname`).
    - 마야는 슬래시(/) 경로를 주므로 `os.path.normpath` 로 OS 네이티브(윈도우는 `\\`)
      형태로 바꿔 탐색기·파일 다이얼로그에 그대로 붙여넣을 수 있게 한다.
    - **클립보드 복사는 UI 가 한다**(Qt 의 일이라 코어에 두지 않는다).
    """
    scene_path = cmds.file(q=True, sceneName=True)
    if not scene_path:
        return "", ["[WARN] Current scene has not been saved yet (no path to copy)."]

    folder = os.path.normpath(os.path.dirname(scene_path))
    return folder, []


def open_scene_folder():
    """현재 씬이 저장된 폴더를 OS 탐색기로 연다. 로그 리스트를 돌려준다.

    - 씬 파일이 디스크에 있으면 폴더를 열고 **그 파일을 선택(하이라이트)** 한다
      (`Framework.core.file_opener.open_path` 가 파일 경로면 `explorer /select,` 로 연다).
    - 파일이 지워졌거나 이름이 바뀌어 없으면 **폴더만** 연다.
    - 폴더까지 없으면(드라이브 분리 등) 탐색기를 띄우지 않고 경고한다.
    """
    folder, _logs = scene_folder()
    if not folder:
        return ["[WARN] Current scene has not been saved yet (no folder to open)."]

    if not os.path.isdir(folder):
        return ["[WARN] Scene folder does not exist on disk : {0}".format(folder)]

    scene_path = os.path.normpath(cmds.file(q=True, sceneName=True))
    target = scene_path if os.path.isfile(scene_path) else folder

    try:
        open_path(target)
    except Exception as exc:
        return ["[WARN] Could not open the folder : {0} ({1})".format(folder, exc)]

    return ["Opened scene folder : {0}".format(folder)]


# ==========================================================================
# Display
# ==========================================================================

def _resolve_local_axis_node(node):
    """`displayLocalAxis` 를 가진 노드(transform)를 돌려준다. 없으면 None.

    컴포넌트를 선택하면 `ls(objectsOnly=True)` 가 shape 를 주는데, shape 에는
    `displayLocalAxis` 가 없다(있는 척도 안 하고 toggle 도 조용히 무시된다).
    그래서 shape 면 부모 transform 으로 올라간다.
    """
    if cmds.attributeQuery("displayLocalAxis", node=node, exists=True):
        return node

    for parent in cmds.listRelatives(node, parent=True, fullPath=True) or []:
        if cmds.attributeQuery("displayLocalAxis", node=parent, exists=True):
            return parent

    return None


def set_local_axis(state):
    """선택한 오브젝트의 로컬 축 표시를 한 번에 켜거나 끈다.

    현재 상태를 먼저 보고 **목표와 다른 것만** 바꾼다. 선택이 섞여 있어도(일부만
    켜져 있어도) 전부 같은 상태로 맞춰진다.

    ★ `toggle -localAxis` 대신 `setAttr` 을 쓴다: MEL toggle 은 undo 큐에 아무것도
    남기지 않아서(빈 청크) 실행 후 Ctrl+Z 를 누르면 로컬 축이 아니라 그 **이전**
    작업이 취소된다. `setAttr` 은 정상적으로 undo 된다.

    잠기거나 연결된 어트리뷰트는 `setAttr` 이 실패하므로 따로 모아 보고한다.
    """
    state = bool(state)

    # 컴포넌트 선택도 받아주되(objectsOnly), 노드는 중복 없이 한 번씩만 처리한다.
    nodes = cmds.ls(sl=True, long=True, objectsOnly=True) or []
    if not nodes:
        return ["[WARN] Select object(s) first."]

    targets = []
    for node in nodes:
        resolved = _resolve_local_axis_node(node)
        if resolved and resolved not in targets:
            targets.append(resolved)

    if not targets:
        return ["[WARN] No selected object has a local axis display attribute."]

    changed = []
    failed = []

    # 여러 오브젝트를 한 번의 undo 로 되돌린다.
    with undo_chunk():
        for target in targets:
            if bool(cmds.getAttr(target + ".displayLocalAxis")) == state:
                continue
            try:
                cmds.setAttr(target + ".displayLocalAxis", state)
            except RuntimeError:
                failed.append(target)
            else:
                changed.append(target)

    logs = ["Local axis {0} : changed {1} of {2} object(s).".format(
        "ON" if state else "OFF", len(changed), len(targets))]

    if failed:
        logs.append("[WARN] Could not change {0} object(s) (locked or connected) : "
                    "{1}".format(len(failed), failed))
    return logs


# ==========================================================================
# Shelf
# ==========================================================================

def _shelf_top_level():
    """셸프 탭 레이아웃 이름(`$gShelfTopLevel`). UI 가 없으면 빈 문자열."""
    try:
        return mel.eval('global string $gShelfTopLevel; '
                        '$JUN_quickTool_tmp = $gShelfTopLevel;') or ""
    except RuntimeError:
        return ""


def _shelf_file(folder, name):
    return os.path.join(folder, "shelf_{0}.mel".format(name))


def _mtime(path):
    try:
        return os.path.getmtime(path)
    except OSError:
        return None


def save_all_shelves():
    """지금 셸프 상태를 `prefs/shelves` 에 **즉시** 쓴다.

    ★ 왜 필요한가 — **마야는 셸프를 종료할 때 저장한다.** 그래서 셸프를 고쳐 놓고(드롭 설치로
    버튼이 생기는 것도 포함) 그 마야를 켠 채 **다른 마야를 새로 띄우면**, 새 마야는 디스크에
    남아 있는 **옛 파일**을 읽어 바뀐 것이 하나도 안 보인다. 고친 마야를 껐다 켜야 반영된다.
    이 함수가 그 저장을 **지금** 해 버리므로, 이후에 뜨는 마야는 바뀐 셸프를 그대로 읽는다.

    ★ 조심할 것 — `saveAllShelves("")` 는 **빈 인자에도 조용히 성공한다**(mayapy 실측).
    그대로 부르면 아무것도 안 쓰고 "됐다" 고 말하게 된다. 그래서
      1) UI 가 있는지(`$gShelfTopLevel` + 탭 레이아웃)를 먼저 보고,
      2) 저장 전후의 **파일 수정 시각을 비교해** 실제로 쓰였는지 확인한다.
    """
    top = _shelf_top_level()
    if not top or not cmds.shelfTabLayout(top, exists=True):
        return ["[WARN] Shelves are only available in the Maya UI "
                "(nothing to save here)."]

    folder = cmds.internalVar(userShelfDir=True)
    names = cmds.shelfTabLayout(top, query=True, childArray=True) or []
    if not names:
        return ["[WARN] No shelf found to save."]

    before = {name: _mtime(_shelf_file(folder, name)) for name in names}

    try:
        mel.eval('global string $gShelfTopLevel; saveAllShelves($gShelfTopLevel);')
    except RuntimeError as exc:
        return ["[WARN] Could not save the shelves : {0}".format(
            str(exc).strip().splitlines()[0] if str(exc).strip() else exc)]

    written = [name for name in names
               if _mtime(_shelf_file(folder, name)) != before[name]]

    if not written:
        return ["[WARN] saveAllShelves ran but no shelf file changed on disk - "
                "check that {0} is writable.".format(folder)]

    logs = ["Saved {0} of {1} shelf file(s) to {2}".format(
        len(written), len(names), folder)]
    logs.append("A Maya started from now on will see these shelves "
                "(no need to close this one first).")

    missed = [name for name in names if name not in written]
    if missed:
        logs.append("[WARN] Not written : {0}".format(missed))
    return logs
