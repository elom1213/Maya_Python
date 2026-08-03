# last Update date 26 05 27
# Python Script by Ji Hun Park

# Quickk Tool V01.13
# V01.04 : Create Create tool
# V01.05 : Create Anim Tool
# V01.06 : Create UV Tool
# V01.07 : Update Anim Tool
# V01.08 : Update Anim Tool. Add ty
# V01.09 : Create separate curve tool
# V01.10 : remove separate curve tool
# V01.11 : remove rename uv button
# V01.12 : Create tool - add "Cluster Each" button (one cluster per selected object)
# V01.13 : add Pin (always on top) toggle / remove Anim Tool UI
# V01.14 : add "Copy Scene Folder" button (copy current scene folder path to clipboard)
# V01.15 : add "Local Axis ON / OFF" buttons (batch show/hide local rotation axes)

import maya.cmds as cmds;
import maya.mel as mel
import os
from functools import partial

import config
from Framework.core.maya_undo import undo_chunk
from Framework.qt.maya_window import maya_ui_widget
from Framework.qt.qt import Qt

#====================================================================
# call back functions (Start)

def JUN_cmd_update_window_for_anim(*is_selected_only, **kw_args):
    if is_selected_only[0]:
        cmds.playbackOptions(view ="active") 
    else:
        cmds.playbackOptions(view ="all") 

def JUN_cmd_print_selected(*args, **kwargs):
    print(cmds.ls(sl = True))

def JUN_cmd_importFBX_nrm(*args, **kwargs):
    mel.eval('FBXProperty "Import|IncludeGrp|Geometry|OverrideNormalsLock" -v 1')

def JUN_cmd_create_tex_file(*args, **kwargs):
    file__ =  mel.eval("shadingNode -asTexture -isColorManaged file")
    place2Tex__ =  mel.eval("shadingNode -asUtility place2dTexture;")

    lst_attr = ["coverage",
                "translateFrame",
                "rotateFrame",
                "mirrorU",
                "mirrorV",
                "stagger",
                "wrapU",
                "wrapV",
                "repeatUV",
                "offset",
                "rotateUV",
                "noiseUV",
                "vertexUvOne",
                "vertexUvTwo",
                "vertexUvThree",
                "vertexCameraOne"]

    for i in range(len(lst_attr)):
        cmds.connectAttr( place2Tex__ + "." + lst_attr[i], file__ + "." + lst_attr[i])

    cmds.connectAttr( place2Tex__ + ".outUV", file__ + ".uv")
    cmds.connectAttr( place2Tex__ + ".outUvFilterSize", file__ + ".uvFilterSize")

def JUN_cmd_create_cluster_each(*args, **kwargs):
    """선택한 오브젝트마다 클러스터를 하나씩 만든다 (한 번에 하나씩 select 후 cluster).

    cmds.cluster 는 선택 전체에 클러스터 '하나'를 만들기 때문에, 개별로 걸려면
    오브젝트마다 따로 선택해서 호출해야 한다. relative=True 로 만든다.
    """
    objs = cmds.ls(sl=True, long=True)

    if not objs:
        cmds.warning("Select object(s) first.")
        return

    handles = []

    # 오브젝트가 여러 개여도 undo 한 번으로 되돌아가게 묶는다.
    with undo_chunk():
        for obj in objs:
            cmds.select(obj, replace=True)
            # cluster() 반환: [clusterNode, clusterHandle]
            handles.append(cmds.cluster(relative=True)[1])

    if handles:
        cmds.select(handles, replace=True)

    print("Created {0} cluster(s): {1}".format(len(handles), handles))


def JUN_fun_resolve_local_axis_node(node):
    """`displayLocalAxis` 를 가진 노드(transform)를 돌려준다. 없으면 None.

    - 컴포넌트를 선택하면 `ls(objectsOnly=True)` 가 shape 를 주는데, shape 에는
      `displayLocalAxis` 가 없다(있는 척도 안 하고 toggle 도 조용히 무시된다).
      그래서 shape 면 부모 transform 으로 올라간다.
    """
    if cmds.attributeQuery("displayLocalAxis", node=node, exists=True):
        return node

    parents = cmds.listRelatives(node, parent=True, fullPath=True) or []

    for parent in parents:
        if cmds.attributeQuery("displayLocalAxis", node=parent, exists=True):
            return parent

    return None


def JUN_cmd_set_local_axis(state, *args, **kwargs):
    """선택한 오브젝트의 로컬 축 표시를 한 번에 켜거나 끈다.

    현재 상태(`displayLocalAxis`)를 먼저 진단해서, 목표 상태와 다른 오브젝트만
    바꾼다. 이미 목표 상태인 것은 건드리지 않으므로 선택이 섞여 있어도(일부만
    켜져 있어도) 전부 같은 상태로 맞춰진다.

    `toggle -localAxis` 대신 `setAttr` 을 쓴다: MEL toggle 은 undo 큐에 아무것도
    남기지 않아서(빈 청크) 실행 후 Ctrl+Z 를 누르면 로컬 축이 아니라 그 **이전**
    작업이 취소된다. setAttr 은 정상적으로 undo 된다.

    잠기거나 연결된 어트리뷰트는 setAttr 이 실패하므로 따로 모아서 보고한다.
    """
    state = bool(state)

    # 컴포넌트 선택도 받아주되(objectsOnly), 노드는 중복 없이 한 번씩만 처리한다.
    nodes = cmds.ls(sl=True, long=True, objectsOnly=True) or []

    if not nodes:
        cmds.warning("Select object(s) first.")
        return

    targets = []

    for node in nodes:
        resolved = JUN_fun_resolve_local_axis_node(node)

        if resolved and resolved not in targets:
            targets.append(resolved)

    if not targets:
        cmds.warning("No selected object has a local axis display attribute.")
        return

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

    print("Local axis {0}: changed {1} of {2} object(s).".format(
        "ON" if state else "OFF", len(changed), len(targets)))

    if failed:
        cmds.warning("Local axis could not be changed on {0} object(s) "
                     "(locked or connected): {1}".format(len(failed), failed))


def JUN_cmd_copy_scene_path(*args, **kwargs):
    """현재 씬 파일이 저장된 '폴더' 경로를 클립보드에 복사한다 (이후 Ctrl+V 로 붙여넣기).

    - 파일 이름은 빼고 폴더까지만 복사한다(os.path.dirname).
    - 경로는 cmds.file(q, sceneName) 로 얻는다(미저장 씬이면 "" -> 경고만 낸다).
    - Maya 는 슬래시(/) 경로를 주므로 os.path.normpath 로 OS 네이티브(Windows 는 \\)
      형태로 바꿔 탐색기/파일 다이얼로그에 그대로 붙여넣을 수 있게 한다.
    - 클립보드는 Qt(QApplication.clipboard)로 설정해 Maya 밖 다른 앱에서도 붙여넣기가 된다.
    """
    scene_path = cmds.file(q=True, sceneName=True)

    if not scene_path:
        cmds.warning("Current scene has not been saved yet (no file path to copy).")
        return

    # 파일 이름을 떼고 저장 폴더만 남긴다.
    folder_path = os.path.normpath(os.path.dirname(scene_path))

    from Framework.qt.qt import QApplication
    clipboard = QApplication.clipboard()
    if clipboard is None:
        cmds.warning("Could not access the system clipboard.")
        return
    clipboard.setText(folder_path)

    print("Copied scene folder to clipboard: {0}".format(folder_path))


# call back functions (End)
#====================================================================


class JUN_ToolUI_QuickTool:
    def __init__(self):
        # self.str_winTitle = "Quick Tool V01.06"
        self.str_headTitle = "Quick Tool V01.15"
        self.str_winName = "Junny_win_Quick_tool_V01_15"
        self.win_width = 300;
        # File / Display 섹션을 추가한 만큼 창 세로를 늘려, 마지막 버튼 아래
        # Copyright 문구까지 잘리지 않고 보이게 한다. 버튼 높이는 기존 값(450/40)을 유지.
        self.win_height = 420;
        self.btn_hight = 11.25

        self.color_mainDark = [0.10, 0.12, 0.18]
        self.color_main     = [0.14, 0.17, 0.25]
        self.color_sub      = [0.18, 0.22, 0.32]
        self.color_btn      = [0.30, 0.35, 0.45]
        self.color_back     = [0.12, 0.14, 0.20]

        self.idx_updateWin = 0
        self.idx_printTool = 1
        self.idx_importFBX_nrm = 2
        self.idx_create_tex_file = 3
        self.idx_file = 4
        self.idx_display = 5

        self.menu_cmd = "cmds.confirmDialog( title=\'About\', icon =\"information\", bgc ={}, button = \"OK\", messageAlign = \"center\", message=\' Written by Ji Hun Park. \\n Update date: 23-MAY-2026\')".format(self.color_main)

    def cb_toggle_pin(self, enabled, *args, **kwargs):
        """Pin(Always on Top) 토글.

        maya.cmds 창에는 최상단 고정 플래그가 없어서, 창을 QWidget 으로 감싼 뒤
        Qt.WindowStaysOnTopHint 를 켜고/끈다(Qt 툴들의 Pin 과 같은 방식).
        플래그를 바꾸면 창이 숨으므로 반드시 다시 show() 한다.
        """
        widget = maya_ui_widget(self.str_winName)

        if widget is None:
            cmds.warning("Pin: could not access this window as a Qt widget.")
            return

        enabled = bool(enabled)

        if hasattr(widget, "setWindowFlag"):
            widget.setWindowFlag(Qt.WindowStaysOnTopHint, enabled)
        else:
            # Qt 5.9 미만 폴백
            flags = widget.windowFlags()
            widget.setWindowFlags(flags | Qt.WindowStaysOnTopHint if enabled
                                  else flags & ~Qt.WindowStaysOnTopHint)

        widget.show()

    def fun_dummy(self, *args , **kwargs):
        print("fun_dummy called")
        print("args :", args)
        print("kwargs :", kwargs)

    def build(self, btn_specs):

        if cmds.window( self.str_winName , exists=True ): 
            cmds.deleteUI( self.str_winName , window=True )
        
        cmds.window( self.str_winName, bgc=self.color_mainDark, title= self.str_headTitle)

        cmds.menuBarLayout (bgc=self.color_mainDark); 
    
        cmds.menu( label='Help' );
        cmds.menuItem( label='About', command = self.menu_cmd);

        cmds.columnLayout(adjustableColumn=True,
                          columnAttach=('both', 5),
                          rowSpacing=6,
                          bgc =self.color_mainDark);

        # Pin (always on top)
        self.chk_pin = cmds.checkBox( label="Pin (always on top)",
                                      value=False,
                                      annotation="Keep this window above other windows",
                                      changeCommand=self.cb_toggle_pin,
                                      bgc=self.color_sub );

        # Update window (open)

        cmds.columnLayout( adjustableColumn=True, columnAttach=('both', 5), rowSpacing=5,  bgc =self.color_sub );
    
        cmds.text( align="left", label='Update window' );

        cmds.setParent( '..' )

        cmds.paneLayout( configuration= "vertical2", paneSize = ([1,50,100],[2,50,100]))

        self.create_buttons(btn_specs[self.idx_updateWin])

        cmds.setParent( '..' )

        # Update window (close)


        # Print tool (open)

        cmds.columnLayout( adjustableColumn=True, columnAttach=('both', 5), rowSpacing=5,  bgc =self.color_sub );

        cmds.text( align="left", label='print' );

        cmds.setParent( '..' )

        cmds.paneLayout( configuration= "vertical2", paneSize = ([1,50,100],[2,50,100]))

        self.create_buttons(btn_specs[self.idx_printTool])

        cmds.setParent( '..' )

        # Print tool (close)

        # Import tool (open)
        cmds.columnLayout( adjustableColumn=True, columnAttach=('both', 5), rowSpacing=5,  bgc =self.color_sub );

        cmds.text( align="left", label='Import option' );

        cmds.setParent( '..' )

        cmds.paneLayout( configuration= "vertical2", paneSize = ([1,50,100],[2,50,100]))

        self.create_buttons(btn_specs[self.idx_importFBX_nrm])

        cmds.setParent( '..' )
        # Import tool (close)

        # Create tool (open)
        cmds.columnLayout( adjustableColumn=True, columnAttach=('both', 5), rowSpacing=5,  bgc =self.color_sub );

        cmds.text( align="left", label='Create tool' );

        cmds.setParent( '..' )

        cmds.paneLayout( configuration= "vertical2", paneSize = ([1,50,100],[2,50,100]))

        self.create_buttons(btn_specs[self.idx_create_tex_file])

        cmds.setParent( '..' )
        # Create tool (close)

        # File tool (open)
        cmds.columnLayout( adjustableColumn=True, columnAttach=('both', 5), rowSpacing=5,  bgc =self.color_sub );

        cmds.text( align="left", label='File' );

        cmds.setParent( '..' )

        cmds.paneLayout( configuration= "vertical2", paneSize = ([1,50,100],[2,50,100]))

        self.create_buttons(btn_specs[self.idx_file])

        cmds.setParent( '..' )
        # File tool (close)

        # Display tool (open)
        cmds.columnLayout( adjustableColumn=True, columnAttach=('both', 5), rowSpacing=5,  bgc =self.color_sub );

        cmds.text( align="left", label='Display' );

        cmds.setParent( '..' )

        cmds.paneLayout( configuration= "vertical2", paneSize = ([1,50,100],[2,50,100]))

        self.create_buttons(btn_specs[self.idx_display])

        cmds.setParent( '..' )
        # Display tool (close)

        cmds.text( align="center", label='Copyright (c) Park Ji Hun. All rights reserved.' );

        cmds.showWindow(self.str_winName);
        cmds.window(self.str_winName, e = True, widthHeight = [self.win_width, self.win_height]);


    def create_buttons(self, button_specs):
        for spec in button_specs:
            self.create_btn(spec.get("label", "default"),
                            spec.get("callback", self.fun_dummy),
                            *spec.get("args", []),
                            **spec.get("kwargs", {}))
            
    def create_btn(self, flag_lable = "default", flag_command = None, *cb_args, **cb_kwargs):
        if flag_command is None:
            flag_command = self.fun_dummy
        cmds.button( h = self.btn_hight,
                     label= flag_lable, 
                     bgc=self.color_btn, 
                     command=partial(flag_command, *cb_args, **cb_kwargs));

           
def JUN_PY_Quick_tool_v01_08():
    JUN_Win_QuickTool = JUN_ToolUI_QuickTool()

    btn_specs =  [
                    # idx_updateWin : 0
                    [
                        {
                            "label": "Selected",
                            "callback": JUN_cmd_update_window_for_anim,
                            "args": [1]
                        },
                        {
                            "label": "All Windows",
                            "callback": JUN_cmd_update_window_for_anim,
                            "args": [0]
                        }
                    ],
                    # idx_printTool : 1
                    [
                        {
                            "label": "Print Selected",
                            "callback": JUN_cmd_print_selected,
                        }
                    ],
                    # idx_importFBX_nrm : 2
                    [
                        {
                            "label": "Import FBX normal",
                            "callback": JUN_cmd_importFBX_nrm
                        }
                    ],
                    # idx_create_tex_file : 3
                    [
                        {
                            "label": "Create texture file",
                            "callback": JUN_cmd_create_tex_file
                        },
                        {
                            "label": "Cluster Each",
                            "callback": JUN_cmd_create_cluster_each
                        }

                    ],
                    # idx_file : 4
                    [
                        {
                            "label": "Copy Scene Folder",
                            "callback": JUN_cmd_copy_scene_path
                        }
                    ],
                    # idx_display : 5
                    [
                        {
                            "label": "Local Axis ON",
                            "callback": JUN_cmd_set_local_axis,
                            "args": [True]
                        },
                        {
                            "label": "Local Axis OFF",
                            "callback": JUN_cmd_set_local_axis,
                            "args": [False]
                        }
                    ]
                ]
    
    JUN_Win_QuickTool.build(btn_specs)

def build__():
    JUN_PY_Quick_tool_v01_08()
