# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-06-10
# A00120_FKIK - 토큰 검색 (레거시 JUN_cmd_Search_By_Token 복원, 순수 함수)


def search_by_token(items, token, invert=False):
    """
    items 중 이름에 token 을 포함하는 항목 리스트 반환 (순서 유지).
    invert=True 면 포함하지 않는 항목 반환.
    선택/하이라이트 처리는 UI 가 담당.
    """
    matched = [obj for obj in items if token in obj]

    if invert:
        matched_set = set(matched)
        matched = [obj for obj in items if obj not in matched_set]

    return matched
