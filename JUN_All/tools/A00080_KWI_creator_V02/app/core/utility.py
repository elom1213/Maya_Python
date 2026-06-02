import glob, os, re, math, ast

def join_list_with_newline(items, end_newline=False):
    text = "\n".join(items)
    if end_newline:
        text += "\n"
    return text

def get_file_to_list(path):
  with open(path, 'r', encoding="utf-8") as f:
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

def get_keyword_linked_to(
        interval,
        KWI_tgt_node_num,
        pin_id,
        node_name
    ):

    setting_nodes = []

    for start in range(0, interval):

        links = []

        for i in range(start, KWI_tgt_node_num, interval):

            links.append(
                f"{node_name}_{i} {pin_id}"
            )

        linked_text = ",".join(links)

        setting_nodes.append(linked_text)

    return setting_nodes