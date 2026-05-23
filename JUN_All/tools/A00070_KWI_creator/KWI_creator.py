# -*- coding: utf-8 -*-

# last Update date : 26.05.23
# Python Script by Ji Hun Park

# KWI creator V01.00
# V01.00 : Create


import glob, os, re, math, ast
from utility import *


path_read = "0010_Src"
path_write = "0020_out"

fileName_KWI_node = "A001_Src_KWI_node.py"
fileName_tgtBones = "A002_tgtBones.py"

fileName_out_KWI_nodes = "A001_KWI_nodes_out.py"

current_dir = os.path.dirname(os.path.abspath(__file__))
target_path_read_root = os.path.join(current_dir, path_read, "*")
target_path_read_KWI_node = os.path.join(current_dir, path_read, fileName_KWI_node)
target_path_read_tgtBones = os.path.join(current_dir, path_read, fileName_tgtBones)

target_path_write = os.path.join(current_dir, path_write, fileName_out_KWI_nodes)


file_list = glob.glob(target_path_read_root)

KWI_use_kawaii_generator = True

KWI_create_multiple_nodes = True
KWI_create_single_node = False

KWI_keyward_src_node = "A001_Src_KWI_node"

KWI_tgt_node_num = -1
KWI_node_num = 1
KWI_idx_jump = 1

KWI_class_name = "AnimGraphNode_KawaiiPhysics_"

KWI_token_nodePos_X = "NodePosX="
KWI_token_nodePos_Y = "NodePosY="
KWI_nodePos_start_X = 200
KWI_nodePos_start_Y = 30
KWI_nodePos_offset_X = 280
KWI_nodePos_offset_Y = 200
KWI_nodePos_lineChange = 4

def join_list_with_newline(items, end_newline=False):
    text = "\n".join(items)
    if end_newline:
        text += "\n"
    return text

def KWI_get_replace_bone_name(text, new_name):
    """
    BoneName="..." 형식에서 따옴표 안의 문자열을 new_name으로 바꿉니다.
    """
    pattern = r'BoneName="[^"]*"'  # BoneName="..." 형태 찾기
    replaced_text = re.sub(pattern, f'BoneName="{new_name}"', text)
    return replaced_text

def KWI_get_changed_num(text, new_number, str_token):
    """
    파일 내의 'AnimGraphNode_KawaiiPhysics_숫자' 형태를 찾아
    숫자를 new_number로 교체합니다.
    """
    # 정규식 패턴: _숫자 로 끝나는 문자열 찾기
    pattern = rf"({str_token})-?\d+"

    # 교체 문자열 생성
    replaced_text = re.sub(pattern, r"\g<1>" + str(new_number), text)

    return replaced_text


  
def KWI_add_bones_in_single_node(text, bones_list):
    # pattern = r'\s*,\s*ShowPinForProperties(0)'
    pattern = r'ShowPinForProperties\(0\)'
    
    return re.sub(
        pattern,
        f"{bones_list} \n   ShowPinForProperties(0)",
        text
    )
   
def KWI_create_text_rootBones(bone_list):
    if not bone_list:
        return ""

    # 첫 번째는 RootBone
    root_bone = bone_list[0]

    # 나머지는 AdditionalRootBones
    additional = bone_list[1:]

    # AdditionalRootBones 문자열 생성
    if additional:
        additional_str = ",".join(
            f'(RootBone=(BoneName="{bone}"))' for bone in additional
        )
        additional_part = f',AdditionalRootBones=({additional_str})'
    else:
        additional_part = ""

    # 최종 문자열
    result = (
        f'Node=(RootBone=(BoneName="{root_bone}")'
        f'{additional_part})'
    )

    return result

file_list = sorted(file_list)
text_new_lst = []
KWI_text_single_node = []

# main ==============================================================================

read_text_node = None
KWI_tgtBones_name = None
    
if not KWI_use_kawaii_generator:
    exit()

if KWI_create_multiple_nodes and KWI_create_single_node:
    print("check single mode")
    exit()

with open(target_path_read_KWI_node, 'r', encoding="utf-8") as f:
    read_text_node = f.read()

KWI_tgtBones_name = get_tgt_bones(target_path_read_tgtBones)


if KWI_create_multiple_nodes:
    KWI_tgt_node_num = len(KWI_tgtBones_name)
    for idx_nodeNum in range(0, KWI_tgt_node_num):
        KWI_text_single_node = KWI_get_changed_num(read_text_node, KWI_node_num, KWI_class_name)
        KWI_text_single_node = KWI_get_replace_bone_name(KWI_text_single_node, KWI_tgtBones_name[idx_nodeNum])

        posX = KWI_nodePos_start_X + KWI_nodePos_offset_X * (idx_nodeNum % KWI_nodePos_lineChange)
        posY = KWI_nodePos_start_Y + (math.floor(idx_nodeNum/KWI_nodePos_lineChange) * KWI_nodePos_offset_Y)

        KWI_text_single_node = KWI_get_changed_num(KWI_text_single_node, posX, KWI_token_nodePos_X)
        KWI_text_single_node = KWI_get_changed_num(KWI_text_single_node, posY, KWI_token_nodePos_Y)

        KWI_text_single_node = add_linkedto_to_lines(KWI_text_single_node, idx_nodeNum)
        text_new_lst.append(KWI_text_single_node)
        KWI_node_num += KWI_idx_jump

if KWI_create_single_node:
    KWI_text_root_bones = KWI_create_text_rootBones(KWI_tgtBones_name)
    KWI_text_mult_bones_in_single_node = KWI_add_bones_in_single_node(read_text_node, KWI_text_root_bones)
    text_new_lst.append(KWI_text_mult_bones_in_single_node)

text_new_string = join_list_with_newline(text_new_lst, True)


with open(target_path_write, 'w', encoding="utf-8") as f:
    f.write(text_new_string)


