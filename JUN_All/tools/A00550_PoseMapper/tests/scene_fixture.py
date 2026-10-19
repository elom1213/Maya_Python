# -*- coding: utf-8 -*-
# A00550_PoseMapper 시험 공용 - 테스트 씬을 "툴을 쓰기 전" 배선으로 되돌린다 (메모리 안에서만, 파일은 저장하지 않는다).
#
# 테스트 씬(JP__CHN_Basic_1070_JALI_test.mb)은 사용자가 툴로 작업하며 다시 저장한다. 2026-10-19 16:20 저장본에는
# 이 툴의 노드망이 두 개(pm_NET: JALI1:JALI_IN -> BS, pm_NET1: JALI1:CNT_PHONEMES -> BS, Replace) 들어 있어
# BS 를 무엇이 구동하는지가 저장할 때마다 달라진다. 시험은 늘 같은 출발점에서 돌아야 하므로:
#   1) 이 툴이 만든 노드망을 전부 지우고  2) JALI1:ARKIT_OUT.<타겟> -> BS.<타겟> 원래 연결을 되살린다.

import maya.cmds as cmds

BS = "CHN_n_Face_xx_bs"
ARKIT_OUT = "JALI1:ARKIT_OUT"


def reset_to_original_wiring():
    from tools.A00550_PoseMapper.app.core import attrs, network
    removed = network.find_networks()
    for net in removed:
        network.remove(net)
    relinked = 0
    for t in attrs.blendshape_targets(BS):
        src = "{0}.{1}".format(ARKIT_OUT, t)
        if cmds.objExists(src) and not cmds.isConnected(src, "{0}.{1}".format(BS, t)):
            cmds.connectAttr(src, "{0}.{1}".format(BS, t), force=True)
            relinked += 1
    print("  [fixture] removed tool networks {0}, relinked {1} ARKIT_OUT -> BS".format(removed, relinked))
