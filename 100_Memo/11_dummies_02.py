import unreal

# 선택된 AnimSequence들
anims = [
    a for a in unreal.EditorUtilityLibrary.get_selected_assets()
    if isinstance(a, unreal.AnimSequence)
]

if not anims:
    raise RuntimeError("AnimSequence를 선택하세요")

# Control Rig
control_rig = unreal.load_object(
    None,
    "/Game/Characters/Mannequins/Rigs/CR_Manny_footIKFollow_JUN.CR_Manny_footIKFollow_JUN"
)

# Level Sequence 생성
seq = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
    "Temp_Bake_Sequence",
    "/Game/_Temp",
    unreal.LevelSequence,
    unreal.LevelSequenceFactoryNew()
)

# Sequencer 열기
unreal.LevelSequenceEditorBlueprintLibrary.open_level_sequence(seq)

for anim in anims:
    print("Baking:", anim.get_name())

    # Skeletal Mesh Actor 추가
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.SkeletalMeshActor,
        unreal.Vector(0, 0, 0)
    )

    sk_comp = actor.skeletal_mesh_component
    sk_comp.set_animation_mode(
        unreal.AnimationMode.ANIMATION_SINGLE_NODE
    )
    sk_comp.set_animation(anim)

    binding = seq.add_possessable(actor)

    # Control Rig 트랙 추가
    track = binding.add_track(unreal.MovieSceneControlRigParameterTrack)
    # track.set_control_rig(control_rig)

    # 🔥 핵심: Bake
    unreal.SequencerTools.bake_to_anim_sequence(
        level_sequence=seq,
        bindings=[binding],
        bake_settings=unreal.SequencerBakeSettings()
    )

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


import unreal

rig_asset = unreal.load_object(
    None,
    "/Game/Characters/Mannequins/Rigs/CR_Manny_footIKFollow_JUN"
)

selected_assets = unreal.EditorUtilityLibrary.get_selected_assets()

for asset in selected_assets:
    if not isinstance(asset, unreal.AnimSequence):
        continue

    print(f"Baking: {asset.get_name()}")

    unreal.ControlRigSequencerLibrary.bake_anim_sequence_to_control_rig(
        anim_sequence=asset,
        control_rig=rig_asset,
        bake_settings=unreal.ControlRigBakeSettings()
    )

    ##=============================================================


src_ = "Jog_CH_n_MainRoot_xx_ctl"
dst_ = "CH:Cage:CH_n_MainRoot_xx_ctl"
time_range_ = (0, 4)

def fast_copy_paste(src, dst, time_range):
    # --- 상태 저장 ---
    ogs_paused = bool(mel.eval('ogs -query -pause;'))
    auto_key = cmds.autoKeyframe(q=True, state=True)
    refresh = cmds.refresh(suspend=True)

    try:
        # --- 완전 정지 ---
        if not ogs_paused:
            mel.eval('ogs -pause;')

        cmds.autoKeyframe(state=False)
        cmds.refresh(suspend=True)

        # --- 핵심 작업 ---
        cmds.copyKey(src, time=time_range)
        cmds.pasteKey(dst, option="insert")

    finally:
        # --- 복원 ---
        cmds.refresh(suspend=False)
        cmds.autoKeyframe(state=auto_key)

        if not ogs_paused:
            mel.eval('ogs -resume;')
            
fast_copy_paste(src_, dst_, time_range_)


#==========================================================================


class JUN_ToolUI_QuickTool:
    def __init__(self):

        mod_tsl_from = JUN_module_tsl_v01()
        mod_tsl_to__ = JUN_module_tsl_v01()


    def build(self, btn_specs):
        
        self.mod_tsl_from.build()
        

scaleKey -scaleSpecifiedKeys 1 -autoSnap 0 -time ":" -float ":" -timeScale 1.3 -timePivot 0 -floatScale 1.3 -floatPivot 0 -valueScale 1 -valuePivot 0 -hierarchy none -controlPoints 0 -shape 1 {"skk:Cage:CH_n_MainRoot_xx_ctl.visibility", "skk:Cage:CH_n_MainRoot_xx_ctl.translateX", "skk:Cage:CH_n_MainRoot_xx_ctl.translateY", "skk:Cage:CH_n_MainRoot_xx_ctl.translateZ", "skk:Cage:CH_n_MainRoot_xx_ctl.rotateX", "skk:Cage:CH_n_MainRoot_xx_ctl.rotateY", "skk:Cage:CH_n_MainRoot_xx_ctl.rotateZ", "skk:Cage:CH_n_MainRoot_xx_ctl.scaleX", "skk:Cage:CH_n_MainRoot_xx_ctl.scaleY", "skk:Cage:CH_n_MainRoot_xx_ctl.scaleZ"};


['CH_Lttle_intermediate_L_xx_ctl',
 'CH_Thumb_intermediate_L_xx_ctl',
 'CH_Index_intermediate_L_xx_ctl',
 'CH_Lttle_distal_L_xx_ctl',
 'CH_Index_distal_L_xx_ctl',
 'CH_Index_proxinal_L_xx_ctl',
 'CH_Ring_metacarpal_L_xx_ctl',
 'CH_Index_metacarpal_L_xx_ctl',
 'CH_Lttle_proximal_L_xx_ctl',
 'CH_Lttle_metacarpal_L_xx_ctl',
 'CH_Ring_proximal_L_xx_ctl',
 'CH_Middle_proximal_L_xx_ctl',
 'CH_Ring_distal_L_xx_ctl',
 'CH_Middle_intermideate_L_xx_ctl',
 'CH_Middle_distal_L_xx_ctl',
 'CH_Thumb_distal_L_xx_ctl',
 'CH_Ring_intermediate_L_xx_ctl',
  'CH_Thumb_proxinal_L_xx_ctl',
  'CH_Middle_metacarpal_L_xx_ctl']


['CH_Middle_metacarpal_R_xx_ctl',
 'CH_Lttle_intermediate_R_xx_ctl',
 'CH_Middle_distal_R_xx_ctl',
 'CH_Thumb_intermediate_R_xx_ctl',
 'CH_Lttle_metacarpal_R_xx_ctl',
 'CH_Index_proxinal_R_xx_ctl',
 'CH_Lttle_proximal_R_xx_ctl',
 'CH_Index_distal_R_xx_ctl',
 'CH_Thumb_proxinal_R_xx_ctl',
 'CH_Index_intermediate_R_xx_ctl',
 'CH_Ring_intermediate_R_xx_ctl',
 'CH_Ring_proximal_R_xx_ctl',
 'CH_Ring_distal_R_xx_ctl',
  'CH_Middle_proximal_R_xx_ctl',
  'CH_Middle_intermideate_R_xx_ctl',
  'CH_Lttle_distal_R_xx_ctl',
  'CH_Ring_metacarpal_R_xx_ctl',
  'CH_Thumb_distal_R_xx_ctl',
  'CH_Index_metacarpal_R_xx_ctl']
