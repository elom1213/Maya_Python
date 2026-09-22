# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-09-22
# A00400_CurveTool - Display > Replace 탭 (컨트롤 커브의 셰이프를 다른 커브 모양으로 교체)
#
# v01.15 에서는 `Create > Controls` 탭 안의 한 섹션이었고 대상/교체본을 **텍스트 칸**에
# 담았다(원본 bs_controls 의 모양). v01.16 에서 **하위 탭으로 떼어 내고 두 칸을 공용 TSL**
# 로 바꿨다 - 리스트에 담아 두고 순서를 손보며 여러 번 돌리는 것이 실제 작업 방식이다.
#
# 짝 짓기: 두 리스트 개수가 같으면 **순서대로 1:1**, 다르면 **적은 개수만큼**만 한다
# (교체본이 하나면 모든 대상에 같은 모양). 규칙은 core `control_manager.replace_shapes`.
#
# v01.22 - 대상이 **레퍼런스**면 셰이프 노드를 지울 수 없으므로 셰이프를 바꾸는 대신
# **CV 만 대응 CV 에 맞춘다**(Mirror 를 켜면 월드 X 를 뒤집은 자리로). 대상마다 자동으로
# 갈리고 화면에서 켤 것은 없다 - 어느 쪽으로 처리했는지는 로그에 적힌다.

import maya.cmds as cmds

from Framework.qt.qt import *
from Framework.qt import JUN_mod_tsl_qt

from tools.A00400_CurveTool.app.core import control_manager as ctl_mgr


class ReplaceTab(QWidget):
    """셰이프 교체 탭. 로그는 툴 창의 것을 그대로 쓴다(log_callback)."""

    def __init__(self, log_callback=None, parent=None):
        super(ReplaceTab, self).__init__(parent)

        self._log = log_callback or (lambda text: None)
        self.build_ui()

    # ==================================================================
    # UI
    # ==================================================================

    def build_ui(self):
        root = QVBoxLayout(self)

        note = QLabel(
            "Swap a control's curve shape for another curve's shape.\n"
            "The target keeps its name, transform and connections - only the\n"
            "shape node is replaced.\n"
            "Referenced targets keep their shape node too - their CVs are moved\n"
            "onto the replacement's CVs one by one (same CV count needed).")
        note.setAlignment(Qt.AlignCenter)
        root.addWidget(note)

        self.tsl_targets = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Shapes to replace", select_label="List Selected",
            show_sort=False, list_min_height=150, log_callback=self._log)
        self.tsl_replacements = JUN_mod_tsl_qt.JUN_mod_tsl_qt_v01(
            title="Replacement", select_label="List Selected",
            show_sort=False, list_min_height=150, log_callback=self._log)

        lists = QHBoxLayout()
        lists.addWidget(self.tsl_targets)
        lists.addWidget(self.tsl_replacements)
        root.addLayout(lists, 1)

        pair_note = QLabel(
            "Same count -> paired in list order. Different counts -> only the first\n"
            "matching pairs run. One replacement -> it goes on every target.")
        pair_note.setAlignment(Qt.AlignCenter)
        root.addWidget(pair_note)

        self.btn_resolve = QPushButton("Resolve Pair from Selection")
        self.btn_resolve.setMinimumHeight(28)
        self.btn_resolve.setToolTip(
            "Fill 'Shapes to replace' with the mirrored counterpart of each\n"
            "replacement - the other side of the rig, found by the shared\n"
            "left/right token rules (Framework/rules/mirror_tokens.json).\n"
            "\n"
            "Uses the current scene selection as the replacements; with nothing\n"
            "selected it uses the 'Replacement' list as it stands.\n"
            "\n"
            "Only counterparts that exist in the scene as a curve are kept, and\n"
            "both lists are rewritten together so the pairs stay lined up.\n"
            "Replacements with no counterpart are dropped and named in the log.")
        self.btn_resolve.clicked.connect(self.on_resolve_pair)
        root.addWidget(self.btn_resolve)

        self.chk_mirror = QCheckBox("Mirror Shapes")
        self.chk_mirror.setToolTip(
            "Flip the replacement across X before it is applied - for the other\n"
            "side of the rig. The target's own position is then not matched.\n"
            "On a referenced target each CV is moved to the mirrored world\n"
            "position of the matching CV on the replacement.")
        root.addWidget(self.chk_mirror)

        self.btn_replace = QPushButton("Replace Shapes")
        self.btn_replace.setMinimumHeight(32)
        self.btn_replace.setToolTip(
            "Give every listed target the shape of its replacement.\n"
            "The target's transform, name and connections stay as they are.\n"
            "Referenced targets have their CVs matched instead - the shape node\n"
            "cannot be deleted there.\n"
            "One undo step.")
        self.btn_replace.clicked.connect(self.on_replace)
        root.addWidget(self.btn_replace)

        return self

    # ==================================================================
    # 동작
    # ==================================================================

    def _nodes(self, tsl):
        """TSL 에 담긴 노드들. UUID 로 지금 이름을 되찾는다(리네임·리페어런트 안전)."""
        return tsl.get_all_nodes() or tsl.get_all_items()

    @staticmethod
    def _listed_name(node):
        """리스트에 보여 줄 이름. 마야가 주는 **고유한 최소 이름**을 쓴다.

        전체 경로(`|grp|ctrl_l`)를 그대로 넣으면 목록이 읽기 어렵고, 짧은 이름만 쓰면
        동명 노드에서 엉뚱한 것이 잡힌다. `cmds.ls` 는 필요할 때만 경로를 붙인 이름을
        돌려주므로 둘 다 피할 수 있다 - 'List Selected' 로 담을 때와 같은 모양이다.
        """
        found = cmds.ls(node) or []
        return found[0] if found else node.split("|")[-1]

    def on_resolve_pair(self):
        """교체본의 반대쪽 커브를 찾아 좌측 'Shapes to replace' 를 채운다.

        대상은 **씬 선택**이 있으면 그것, 없으면 이미 담겨 있는 'Replacement' 리스트다
        (A00110_animTool_V02 의 `Resolve Pairs from Selection` 과 같은 규칙).

        ★ 두 리스트를 **짝지어진 것만으로 함께** 다시 채운다. 좌측만 채우면 짝을 못 찾은
          교체본 때문에 순서가 밀려 **엉뚱한 셰이프가 적용**된다(짝은 리스트 순서로 맺어진다).
        """
        selection = cmds.ls(selection=True, long=True) or []

        if selection:
            sources = selection
        else:
            sources = self._nodes(self.tsl_replacements)
            if not sources:
                self._log("[WARN] Select the replacement curve(s) in the scene, or list "
                          "them under 'Replacement' first.")
                return

        pairs, messages = ctl_mgr.resolve_mirror_pairs(sources)

        for message in (messages or []):
            self._log(message)

        if not pairs:
            return

        self.tsl_targets.set_items([self._listed_name(t) for t, _ in pairs])
        self.tsl_replacements.set_items([self._listed_name(r) for _, r in pairs])

        dropped = len(sources) - len(pairs)
        if dropped:
            self._log("{0} replacement(s) had no counterpart and were left out of both "
                      "lists.".format(dropped))

    def on_replace(self):
        targets = self._nodes(self.tsl_targets)
        replacements = self._nodes(self.tsl_replacements)

        if not targets:
            self._log("[WARN] 'Shapes to replace' is empty - select control(s) in the "
                      "scene and click 'List Selected'.")
            return
        if not replacements:
            self._log("[WARN] 'Replacement' is empty - select the curve(s) to copy the "
                      "shape from and click 'List Selected'.")
            return

        _replaced, messages = ctl_mgr.replace_shapes(
            targets, replacements, mirror=self.chk_mirror.isChecked())
        for message in (messages or []):
            self._log(message)
