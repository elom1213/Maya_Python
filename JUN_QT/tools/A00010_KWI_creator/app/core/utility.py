import glob, os, re, math, ast


def remove_specific_pattern(text, patterns_to_remove):
    for pattern in patterns_to_remove:
        text = text.replace(pattern, "")
    return text

def join_list_with_newline(items, end_newline=False):
    text = "\n".join(items)
    if end_newline:
        text += "\n"
    return text

def get_replaced_root_bone_name(text, new_name, pattern_given = "JUN_RootBone"):
    pattern = pattern_given
    replaced_text = re.sub(pattern, f'Node=(RootBone=(BoneName="{new_name}")', text)
    return replaced_text

def KWI_replace_by_pattern_before_num(text, new_pattern, pattern_given):
    pattern = rf"({pattern_given})-?\d+"
    replaced_text = re.sub(pattern, r"\g<1>" + str(new_pattern), text)
    return replaced_text

  
def KWI_add_addtitional_bones(text, bones_list, pattern_given = 'JUN_AdditionalRootBones'):
    pattern = pattern_given
    
    return re.sub(
        pattern,
        f"{bones_list}",
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


def get_tgt_bones(target_path_tgtBones):
  with open(target_path_tgtBones, 'r', encoding="utf-8") as f:
    read_text = f.read()
    try:
        result = ast.literal_eval(read_text)
        if isinstance(result, list):
            return result
        else:
            raise ValueError("The string does not represent a list.")
    except Exception as e:
        print("Error converting string to list:", e)
        return []

    return read_text
  
def add_linkedto_to_lines(
        text_block,
        found_index,
        node_name="AnimGraphNode_KawaiiPhysics",
        target_text="07E3FD484D9ABE61B95D8EB9E224A86E",
        link_id="4D524E0342A22F9A278E3EB31AF3C195"
    ):

    if found_index < 0:
        return text_block

    lines = text_block.splitlines()

    new_lines = []

    for line in lines:

        if target_text in line:

            add_text = (
                f"LinkedTo=({node_name}_{found_index} {link_id})"
            )

            close_paren_index = line.rfind(")")

            if close_paren_index != -1:

                line = (
                    line[:close_paren_index]
                    + add_text
                    + line[close_paren_index:]
                )

                found_index += 1

        new_lines.append(line)

    # 다시 하나의 문자열로 합치기
    return "\n".join(new_lines)

def build_setting_nodes_link(text, lst_setting_node, target_text = "EGPD_Output"):
    new_lines = []
    idx_setting_node = 0
    tkn_begin_obj = "Begin Object"

    for idx, line in enumerate(text):
        if idx_setting_node >= len(lst_setting_node) and tkn_begin_obj in line:
            break

        if target_text in line:
            close_paren_index = line.rfind(")")
            if close_paren_index != -1:

                line = (
                    line[:close_paren_index]
                    + lst_setting_node[idx_setting_node]
                    + line[close_paren_index:]
                )
                idx_setting_node += 1

        new_lines.append(line)

    return "".join(new_lines)

def create_keyword_linked_to(
        num_setting_node,
        KWI_tgt_node_num,
        node_name="AnimGraphNode_KawaiiPhysics",
        pin_id="F56CA1A44D9143498D4F0E924F403F39"
    ):

    setting_nodes = []

    for start in range(1, num_setting_node + 1):

        links = []

        for i in range(start, KWI_tgt_node_num + 1, num_setting_node):

            links.append(
                f"{node_name}_{i} {pin_id}"
            )

        linked_text = "LinkedTo=(" + ",".join(links) + ")"

        setting_nodes.append(linked_text)

    return setting_nodes

def link_LD_node(text, str_linked_to, target_text = "EGPD_Output"):
    new_lines = []
    for idx, line in enumerate(text):
        if target_text in line:
            close_paren_index = line.rfind(")")
            if close_paren_index != -1:

                line = (
                    line[:close_paren_index]
                    + str_linked_to
                    + line[close_paren_index:]
                )

        new_lines.append(line)

    return "".join(new_lines)