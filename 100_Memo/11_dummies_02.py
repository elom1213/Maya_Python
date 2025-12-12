import maya.cmds as cmds

class FKIKSourceUI:
    def __init__(self, parent_tab, is_visible=True):
        """Source 탭 UI를 생성하는 클래스"""
        self.parent_tab = parent_tab
        self.is_visible = is_visible

        self.tab_layout = None

        self.build_ui()

        # 생성 후 표시 여부 적용
        #self.set_visible(self.is_visible)

    def build_ui(self):

        """Source 탭 내부 UI 생성"""
        self.tab_layout = cmds.columnLayout(adj=True)

        # ▼ Tool: Setup Source
        cmds.frameLayout(
            label="Tool : Setup Source",
            collapsable=True,
            bgc=[0.2, 0.2, 0.28],
            marginHeight=5
        )

        # 여기에 네가 기존에 만들던 Source 탭 UI 요소들을 넣으면 됨
        cmds.columnLayout(adj=True)
        cmds.text(label="Set source : FK", h=20)
        cmds.separator(h=5)

        cmds.text(label="[ ... 여기에 기존 FK UI 요소들 ... ]")
        cmds.setParent("..")

        cmds.columnLayout(adj=True)
        cmds.text(label="Set source : IK", h=20)
        cmds.separator(h=5)

        cmds.text(label="[ ... 여기에 기존 IK UI 요소들 ... ]")
        cmds.setParent("..")

        cmds.setParent("..")  # frameLayout 닫기

        # 탭에 추가
        cmds.setParent(self.parent_tab)
        cmds.tabLayout(self.parent_tab, e=True, tabLabel=(self.tab_layout, "Source"))
        
        state = self.is_visible
        print("is vis: : " + str(self.is_visible) )
        cmds.layout(self.tab_layout, e=True, manage=state)

    def set_visible(self, state):
        """UI 표시/숨김 설정"""
        self.is_visible = state
        print("is vis: : " + str(self.is_visible) )
        cmds.layout(self.tab_layout, e=True, manage=state)
        
class FKIKToolMainUI:
    def __init__(self, dev_mode=False):
        self.dev_mode = dev_mode  # 개발자 모드 여부

        if cmds.window("FKIKToolWin", exists=True):
            cmds.deleteUI("FKIKToolWin")

        self.win = cmds.window("FKIKToolWin", title="FKIK Tool", width=600, height=400)
        self.main_tab = cmds.tabLayout()

        # Source 탭 (개발 모드에만 표시)
        self.source_tab = FKIKSourceUI(self.main_tab, is_visible=self.dev_mode)

        # TODO: Match FK 탭
        cmds.columnLayout()
        cmds.text(label="Match FK UI here")
        cmds.setParent("..")

        # TODO: Match IK 탭
        cmds.columnLayout()
        cmds.text(label="Match IK UI here")
        cmds.setParent("..")

        cmds.showWindow(self.win)
        
ui = FKIKToolMainUI(dev_mode=False)