# -*- coding: utf-8 -*-

# last Update date : 26.05.24
# Python Script by Ji Hun Park

# KWI creator V01.01
# V01.00 : Create
# V01.01 : create linking setting nodes, LD nodes


import glob, os, re, math, ast
from .tool_path import KWIPaths
from .utility import *
from .template_engine import *
from Framework.core.path_manager import PathManager

# ==============================================================================
# create base nodes

class KWI_creator:
    def __init__(self):

        self.set_path()

        self._interval_setting_node = 5

        self.node_name = "AnimGraphNode_KawaiiPhysics"

        self.nodePos_start_X = 200
        self.nodePos_start_Y = 30
        self.nodePos_offset_X = 280
        self.nodePos_offset_Y = 200

        self.setting_nodePos_offset_Y = 48

        self.nodePos_lineChange = 4

        self.tgtBones = get_file_to_list(self.paths.read_tgtBones)
        self.tgt_node_num = len(self.tgtBones)

        self._create_mode = "multiple"

        self.id_PhysicsSettings      = "F56CA1A44D9143498D4F0E924F403F39"
        self.id_pose                 = "4D524E0342A22F9A278E3EB31AF3C195"
        self.id_LD                   = "6222BDF34477D9F24F863390648BE4CA"

        self.replacements = {
                                "NODE_NAME"             : "cv_spline_necklace_02_01",
                                "ROOT_BONE"             : 'AdditionalRootBones=((RootBone=(BoneName="Spine1")),(RootBone=(BoneName="Spine")))',
                                "ROOT_BONE_ADDITIONAL"  : "",
                                "LINKED_TO"             : "(AnimGraphNode_KawaiiPhysics_0 4D524E0342A22F9A278E3EB31AF3C195)",
                                "NODE_POS_X"            : "",
                                "NODE_POS_Y"            : "",
                            }
        
        self.replacements_setting = {
                                        "NODE_NAME"     : "K2Node_VariableGet_1",
                                        "MEMBER_NAME"   : 'PS_base_01',
                                        "LINKED_TO"     : "(AnimGraphNode_KawaiiPhysics_0 4D524E0342A22F9A278E3EB31AF3C195)",
                                        "NODE_POS_X"    : "",
                                        "NODE_POS_Y"    : "",
                                    }
        
        self.replacements_LD = {
                                    "NODE_NAME"      : "K2Node_VariableGet_1",
                                    "MEMBER_NAME"    : 'LD_base_01',
                                    "LINKED_TO"      : "(AnimGraphNode_KawaiiPhysics_0 4D524E0342A22F9A278E3EB31AF3C195)",
                                    "NODE_POS_X"     : "",
                                    "NODE_POS_Y"     : "",
                                }

    def set_path(self):
        self.pm = PathManager(  __file__, 
                                read_dir  = "0010_src",
                                write_dir = "0020_out" )
        
        self.extension = "py"
        self.paths = KWIPaths(
                                read_base_node          =   self.pm.path(
                                    "read",
                                    f"A0001_Src_KWI_node_v03.{self.extension}"
                                ),
                            
                                read_setting_node        =   self.pm.path(
                                    "read",
                                    f"A0002_Src_KWI_setting_node_v02.{self.extension}"
                                ),
                            
                                read_LD_node             =   self.pm.path(
                                    "read",
                                    f"A0003_Src_KWI_LD_v02.{self.extension}"
                                ),

                                read_tgtBones           =   self.pm.path(
                                    "read",
                                    f"A0101_tgtBones.{self.extension}"
                                ),

                                write_base_node         =   self.pm.path(
                                    "write",
                                    f"A001_KWI_nodes_out.{self.extension}"
                                ),

                                write_setting_node      =   self.pm.path(
                                    "write",
                                    f"A002_KWI_setting_nodes_out.{self.extension}"
                                ),

                                write_LD_node           =   self.pm.path(
                                    "write",
                                    f"A003_KWI_LD_nodes_out.{self.extension}"
                                ),

                                write_combined_node     =   self.pm.path(
                                    "write",
                                    f"A000_KWI_combined_out.{self.extension}"
                                ),
                            )
        
    @property
    def create_multiple_nodes(self):
        return self._create_multiple_nodes
    
    @property
    def create_single_node(self):
        return self._create_single_node
    
    @property
    def interval_setting_node(self):
        return self._interval_setting_node
    
    @property
    def create_mode(self):
        return self._create_mode

    
    @create_multiple_nodes.setter
    def create_multiple_nodes(self, value):
        if not isinstance(value, bool):
            raise ValueError("Name must be a bool")
        self._create_multiple_nodes = value

    @create_single_node.setter
    def create_single_node(self, value):
        if not isinstance(value, bool):
            raise ValueError("Name must be a bool")
        self._create_single_node = value

    @interval_setting_node.setter
    def interval_setting_node(self, value):
        if not isinstance(value, int):
            raise ValueError("Name must be a int")
        self._interval_setting_node = value

    @create_mode.setter
    def create_mode(self, value):
        if not isinstance(value, str):
            raise ValueError("Name must be a string")
        self._create_mode = value

    def set_mode(self, mode):
        self._create_mode = mode
        print(mode)

    def create_base_nodes(self):

        mode_map = {
            "multiple"      :   self._create_multiple_nodes_impl,
            "single"        :   self._create_single_node_impl
        }

        func = mode_map.get(self._create_mode)

        if func:
            func()
    
    def set_mode(self, mode):
        self._create_mode = mode

    def set_tgt_bones(self, bones):
        # UI(TSL)에서 입력받은 타겟 본 목록을 적용한다.
        # V02 는 A0101_tgtBones.py 파일에서만 읽었지만, V03 는 UI 리스트로 주입한다.
        if not isinstance(bones, (list, tuple)):
            raise ValueError("bones must be a list")
        self.tgtBones = list(bones)
        self.tgt_node_num = len(self.tgtBones)

    def get_default_tgt_bones(self):
        # 기본 예시 본 목록(A0101_tgtBones.py)을 반환한다. UI 초기값/예시 로드용.
        return get_file_to_list(self.paths.read_tgtBones)

    def clear_replacements(self, repl):
        for key, val in repl.items():
            repl[key] = ""

    def _write(self, path, text):
        # ensure_dir + utf-8 쓰기를 묶은 작은 헬퍼 (중복 제거)
        self.pm.ensure_dir(path)
        with open(path, 'w', encoding="utf-8") as f:
            f.write(text)

    # ------------------------------------------------------------------
    # build 헬퍼 : 텍스트만 반환 (파일 쓰기 없음). 합본/개별 생성이 공유한다.

    def _build_base_text(self):
        # 현재 모드(multiple/single)에 따라 base 노드 텍스트를 생성해 반환
        if self._create_mode == "single":
            return self._build_base_text_single()
        return self._build_base_text_multiple()

    def _build_base_text_multiple(self):
        text_new_lst = []
        text_lst = []
        read_base_node = []

        self.clear_replacements(self.replacements)

        with open(self.paths.read_base_node, 'r', encoding="utf-8") as f:
            read_base_node = f.read()


        for idx_nodeNum in range(0, self.tgt_node_num):
            linked_to =  f"LinkedTo=({self.node_name}_{idx_nodeNum-1} {self.id_pose})"
            if idx_nodeNum-1 < 0:
                linked_to = ""

            posX = self.nodePos_start_X + self.nodePos_offset_X * (idx_nodeNum % self.nodePos_lineChange)
            posY = self.nodePos_start_Y + (math.floor(idx_nodeNum/self.nodePos_lineChange) * self.nodePos_offset_Y)

            self.replacements["NODE_NAME"] = self.node_name + "_" + str(idx_nodeNum)
            self.replacements["ROOT_BONE"] = self.tgtBones[idx_nodeNum]
            self.replacements["LINKED_TO"] = linked_to
            self.replacements["NODE_POS_X"] = posX
            self.replacements["NODE_POS_Y"] = posY

            text_lst = TemplateEngine.apply(read_base_node, self.replacements)
            self.clear_replacements(self.replacements)

            text_new_lst.append(text_lst)

        return join_list_with_newline(text_new_lst, True)

    def _build_base_text_single(self):
        read_base_node = []
        self.clear_replacements(self.replacements)
        with open(self.paths.read_base_node, 'r', encoding="utf-8") as f:
            read_base_node = f.read()

        additional = self.tgtBones[1:]

        if additional:
            additional_str = ",".join(
                f'(RootBone=(BoneName="{bone}"))' for bone in additional
            )

        self.replacements["NODE_NAME"] = self.node_name + "_0"
        self.replacements["ROOT_BONE"] = self.tgtBones[0]
        self.replacements["ROOT_BONE_ADDITIONAL"] = additional_str

        return TemplateEngine.apply(read_base_node, self.replacements)

    def _build_setting_text(self):
        setting_node = None
        text_new_lst = []
        self.clear_replacements(self.replacements_setting)

        with open(self.paths.read_setting_node, 'r', encoding="utf-8") as f:
            setting_node = f.read()
        lst_setting_node = get_keyword_linked_to(self._interval_setting_node,
                                                 self.tgt_node_num,
                                                 self.id_PhysicsSettings,
                                                 self.node_name)

        for idx_nodeNum in range(0, self._interval_setting_node):
            self.replacements_setting["NODE_NAME"] = "K2Node_VariableGet_" + str(idx_nodeNum)
            self.replacements_setting["MEMBER_NAME"] = "PS_base_" + str(idx_nodeNum)
            self.replacements_setting["LINKED_TO"] = lst_setting_node[idx_nodeNum]
            self.replacements_setting["NODE_POS_X"] = self.nodePos_start_X - 300
            self.replacements_setting["NODE_POS_Y"] = self.nodePos_start_Y + self.setting_nodePos_offset_Y*idx_nodeNum

            text_lst = TemplateEngine.apply(setting_node, self.replacements_setting)
            self.clear_replacements(self.replacements_setting)

            text_new_lst.append(text_lst)

        return join_list_with_newline(text_new_lst, True)

    def _build_LD_text(self):
        LD_node_base = None
        self.clear_replacements(self.replacements_LD)

        with open(self.paths.read_LD_node, 'r', encoding="utf-8") as f:
            LD_node_base = f.read()

        LD_linked_to = get_keyword_linked_to(1,
                                             self.tgt_node_num,
                                             self.id_LD,
                                             self.node_name)

        self.replacements_setting["NODE_NAME"] = "K2Node_VariableGet_1"
        self.replacements_setting["MEMBER_NAME"] = "LD_base_1"
        self.replacements_setting["LINKED_TO"] = LD_linked_to[0]
        self.replacements_setting["NODE_POS_X"] = self.nodePos_start_X - 600
        self.replacements_setting["NODE_POS_Y"] = self.nodePos_start_Y

        text_lst = TemplateEngine.apply(LD_node_base, self.replacements_setting)
        self.clear_replacements(self.replacements_LD)

        return text_lst

    # ------------------------------------------------------------------
    # 개별 생성 : build 헬퍼로 텍스트를 만들어 각 출력 파일에 쓴다.

    def _create_multiple_nodes_impl(self):
        self._write(self.paths.write_base_node, self._build_base_text_multiple())

    def _create_single_node_impl(self):
        self._write(self.paths.write_base_node, self._build_base_text_single())

    def create_setting_nodes(self):
        self._write(self.paths.write_setting_node, self._build_setting_text())

    def create_LD_nodes(self):
        self._write(self.paths.write_LD_node, self._build_LD_text())

    # ------------------------------------------------------------------
    # 합본 생성 : base -> setting -> LD 순서로 이어붙인 하나의 파일을 쓴다.

    def create_combined_file(self, write_individual=True):
        base_text    = self._build_base_text()
        setting_text = self._build_setting_text()
        ld_text      = self._build_LD_text()

        if write_individual:
            self._write(self.paths.write_base_node,    base_text)
            self._write(self.paths.write_setting_node, setting_text)
            self._write(self.paths.write_LD_node,      ld_text)

        combined = join_list_with_newline([base_text, setting_text, ld_text], True)
        self._write(self.paths.write_combined_node, combined)

        # 합본 텍스트와 출력 경로를 함께 반환 (UI 가 클립보드 복사에 사용)
        return self.paths.write_combined_node, combined
