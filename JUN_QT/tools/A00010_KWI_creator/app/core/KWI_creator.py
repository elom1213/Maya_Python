# -*- coding: utf-8 -*-

# last Update date : 26.05.24
# Python Script by Ji Hun Park

# KWI creator V01.01
# V01.00 : Create
# V01.01 : create linking setting nodes, LD nodes


import glob, os, re, math, ast
from .tool_path import KWIPaths
from .utility import *
from Framework.core.path_manager import PathManager

# ==============================================================================
# create base nodes

class KWI_creator:
    def __init__(self):

        self.KWI_text_single_node = []
        self.patten_to_remove = ["JUN_RootBone,", "JUN_AdditionalRootBones,"]

        self.set_path()

        self._num_setting_node = 5

        self.KWI_class_name = "AnimGraphNode_KawaiiPhysics_"

        self.KWI_token_nodePos_X = "NodePosX="
        self.KWI_token_nodePos_Y = "NodePosY="
        self.KWI_nodePos_start_X = 200
        self.KWI_nodePos_start_Y = 30
        self.KWI_nodePos_offset_X = 280
        self.KWI_nodePos_offset_Y = 200
        self.KWI_nodePos_lineChange = 4

        self.KWI_tgtBones_name = get_tgt_bones(self.paths.read_tgtBones)
        self.KWI_tgt_node_num = len(self.KWI_tgtBones_name)

        self._create_mode = "multiple"

    def set_path(self):
        self.pm = PathManager(  __file__, 
                                read_dir  = "0010_src",
                                write_dir = "0020_out" )
        
        self.extension = "py"
        self.paths = KWIPaths(
                                read_KWI_base_node      =   self.pm.path(
                                    "read",
                                    f"A0001_Src_KWI_node.{self.extension}"
                                ),
                            
                                read_KWI_setting_node   =   self.pm.path(
                                    "read",
                                    f"A0002_Src_KWI_setting_node.{self.extension}"
                                ),
                            
                                read_KWI_LD_node        =   self.pm.path(
                                    "read",
                                    f"A0003_Src_KWI_LD.{self.extension}"
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
                            )
        
    @property
    def create_multiple_nodes(self):
        return self._create_multiple_nodes
    
    @property
    def create_single_node(self):
        return self._create_single_node
    
    @property
    def num_setting_node(self):
        return self._num_setting_node
    
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

    @num_setting_node.setter
    def num_setting_node(self, value):
        if not isinstance(value, int):
            raise ValueError("Name must be a int")
        self._num_setting_node = value

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

    def _create_multiple_nodes_impl(self):

        text_new_lst = []
        read_base_node = []
        base_node_num_str = 0
        with open(self.paths.read_KWI_base_node, 'r', encoding="utf-8") as f:
            read_base_node = f.read()


        for idx_nodeNum in range(0, self.KWI_tgt_node_num):
            self.KWI_text_single_node = KWI_replace_by_pattern_before_num(read_base_node, base_node_num_str, self.KWI_class_name)
            self.KWI_text_single_node = get_replaced_root_bone_name(self.KWI_text_single_node, self.KWI_tgtBones_name[idx_nodeNum])

            posX = self.KWI_nodePos_start_X + self.KWI_nodePos_offset_X * (idx_nodeNum % self.KWI_nodePos_lineChange)
            posY = self.KWI_nodePos_start_Y + (math.floor(idx_nodeNum/self.KWI_nodePos_lineChange) * self.KWI_nodePos_offset_Y)

            self.KWI_text_single_node = KWI_replace_by_pattern_before_num(self.KWI_text_single_node, posX, self.KWI_token_nodePos_X)
            self.KWI_text_single_node = KWI_replace_by_pattern_before_num(self.KWI_text_single_node, posY, self.KWI_token_nodePos_Y)

            self.KWI_text_single_node = add_linkedto_to_lines(self.KWI_text_single_node, idx_nodeNum-1)
            text_new_lst.append(self.KWI_text_single_node)
            base_node_num_str += 1

        text_new_string = join_list_with_newline(text_new_lst, True)

        text_new_string = remove_specific_pattern(text_new_string, self.patten_to_remove)

        self.pm.ensure_dir(self.paths.write_base_node)
        with open(self.paths.write_base_node, 'w', encoding="utf-8") as f:
            f.write(text_new_string)


    def _create_single_node_impl(self):

        text_new_lst = []
        read_base_node = []
        with open(self.paths.read_KWI_base_node, 'r', encoding="utf-8") as f:
            read_base_node = f.read()
    
        KWI_text_root_bones = KWI_create_text_rootBones(self.KWI_tgtBones_name)
        KWI_text_mult_bones_in_single_node = KWI_add_addtitional_bones(read_base_node, KWI_text_root_bones)
        text_new_lst.append(KWI_text_mult_bones_in_single_node)

        text_new_string = join_list_with_newline(text_new_lst, True)

        text_new_string = remove_specific_pattern(text_new_string, self.patten_to_remove)

        self.pm.ensure_dir(self.paths.write_base_node)
        with open(self.paths.write_base_node, 'w', encoding="utf-8") as f:
            f.write(text_new_string)


    def create_setting_nodes(self):

        read_text_setting_node = None
        
        with open(self.paths.read_KWI_setting_node, 'r', encoding="utf-8") as f:
            read_text_setting_node = f.readlines()

        lst_setting_node =  create_keyword_linked_to(self._num_setting_node, self.KWI_tgt_node_num)
        setting_node_new =  build_setting_nodes_link(read_text_setting_node, lst_setting_node)

        self.pm.ensure_dir(self.paths.write_setting_node)
        with open(self.paths.write_setting_node, 'w', encoding="utf-8") as f:
            f.write(setting_node_new)


    def create_LD_nodes(self):
        read_text_limited_data_node = None

        with open(self.paths.read_KWI_LD_node, 'r', encoding="utf-8") as f:
            read_text_limited_data_node = f.readlines()

        LD_linked_to = create_keyword_linked_to(1, self.KWI_tgt_node_num, pin_id = "6222BDF34477D9F24F863390648BE4CA")
        read_text_limited_data_node = link_LD_node(read_text_limited_data_node, LD_linked_to[0])

        self.pm.ensure_dir(self.paths.write_LD_node)
        with open(self.paths.write_LD_node, 'w', encoding="utf-8") as f:
            f.write(read_text_limited_data_node)
