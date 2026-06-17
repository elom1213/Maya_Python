s = cmds.ls(sl=True, fl=True)
print(names)

def rename_with_number_at(names, start=1, width=2, position=3, separator="_"):
    """
    Maya 오브젝트 이름에 번호를 문자열 특정 위치에 삽입해서 rename.

    Args:
        names (list of str): 바꿀 오브젝트 이름 리스트
        start (int): 시작 번호 (기본 1)
        width (int): 번호 자리수 (예: 2 -> 01, 02, 03)
        position (int): 문자열 내 삽입 위치 (0=맨 앞, len(name)=맨 뒤)
        separator (str): 구분자 (기본 "_")

    Returns:
        list of str: 새 이름 리스트
    """
    new_names = []
    for i, old_name in enumerate(names, start=start):
        number_str = "A"+ f"{i:0{width}d}{separator}"
        
        # position 값이 문자열 길이보다 크면 맨 뒤에 붙이기
        pos = min(position, len(old_name))
        
        new_name = old_name[:pos] + number_str + old_name[pos:]
        
        if cmds.objExists(old_name):  # 씬에 오브젝트 존재할 때만 rename
            new_name = cmds.rename(old_name, new_name)
        new_names.append(new_name)
    
    return new_names

rename_with_number_at(names)