import json
import re
import sys, os

ROOT = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "..",
            ".."
        )
    )

if ROOT not in sys.path:
    sys.path.append(ROOT)


from Framework.core.path_manager import PathManager

def natural_sort_key(s):
    """
    정렬 규칙:
    1. 'default'는 항상 가장 앞에 위치합니다.
    2. 나머지는 숫자 크기순(예: 5, 10, 50, 90, 100), 그 외는 사전순으로 정렬합니다.
    """
    if s == 'default':
        return (0, "")
    
    # 숫자와 문자를 분리하여 숫자 부분은 정수(int)로 변환해 비교합니다.
    parts = [int(text) if text.isdigit() else text.lower() for text in re.split('([0-9]+)', s)]
    return (1, parts)

def process_and_sort(d):
    """
    재귀적으로 딕셔너리를 탐색하며 모든 키를 정렬하는 함수입니다.
    """
    if isinstance(d, dict):
        # 1. 현재 딕셔너리의 모든 키를 가져와 natural_sort_key 규칙으로 정렬
        sorted_keys = sorted(d.keys(), key=natural_sort_key)
        
        new_dict = {}
        for k in sorted_keys:
            # 2. 값에 대해서도 재귀적으로 정렬 수행
            new_dict[k] = process_and_sort(d[k])
        return new_dict
    
    elif isinstance(d, list):
        # 리스트 내부에 딕셔너리가 있을 경우를 대비해 순회
        return [process_and_sort(i) for i in d]
    
    else:
        return d

def main():

    pm = PathManager(  __file__, 
                                read_dir  = "0010_src",
                                write_dir = "0020_out" )
    
                            
    input_file = 'sample_01.json'
    output_file = 'sorted_sample_01.json'
    

    try:
        # JSON 파일 읽기
        with open(pm.path("read", input_file), 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 정렬 수행
        sorted_data = process_and_sort(data)

        # 정렬된 JSON 파일 저장
        with open(pm.path("write", output_file), 'w', encoding='utf-8') as f:
            json.dump(sorted_data, f, indent=4, ensure_ascii=False)
        
        print(f"성공! '{output_file}' 파일이 생성되었습니다.")
        
    except Exception as e:
        print(f"오류가 발생했습니다: {e}")

if __name__ == "__main__":
    main()