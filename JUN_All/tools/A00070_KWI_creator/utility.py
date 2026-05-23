import glob, os, re, math, ast

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
        target_text="07E3FD484D9ABE61B95D8EB9E224A86E",
        node_name="AnimGraphNode_KawaiiPhysics",
        link_id="4D524E0342A22F9A278E3EB31AF3C195"
    ):

    if found_index == 0:
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
