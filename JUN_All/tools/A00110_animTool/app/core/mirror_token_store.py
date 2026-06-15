# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-06-15
# A00110_animTool - Mirror Key 좌/우 토큰 쌍 JSON 입출력 (maya.cmds 비의존)
# app/config/mirror_tokens.json 을 읽고/쓰며, 파일이 없거나 깨졌으면 코드 내장 기본값으로 폴백한다.

import os
import json


class MirrorTokenStore:
    """
    좌↔우 컨트롤러 페어링에 쓰는 토큰 쌍을 JSON 파일로 관리한다.

    파일 경로: app/config/mirror_tokens.json
    스키마:
        {
          "version": 1,
          "token_pairs": [ {"left": "_l", "right": "_r", "enabled": true}, ... ]
        }

    load() 는 enabled=true 인 (left, right) 쌍만 반환하고,
    파일 없음 / 파싱 실패 / 빈 목록이면 DEFAULT_TOKEN_PAIRS 로 폴백한다(항상 동작 보장).
    save() 는 UI 편집 결과를 같은 JSON 으로 기록한다(encoding=utf-8).
    JSON 의 위→아래 순서가 매칭 우선순위이므로 구체적인 토큰을 위에 둔다.
    """

    # 코드 내장 폴백. JSON 을 못 읽어도 최소한 이 쌍들로 동작한다.
    DEFAULT_TOKEN_PAIRS = [
        ("_l", "_r"),
        ("_L", "_R"),
        ("_lf", "_rt"),
        ("Left", "Right"),
    ]

    # app/core/ 기준 -> app/config/mirror_tokens.json
    _JSON_PATH = os.path.normpath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "..", "config", "mirror_tokens.json")
    )

    @staticmethod
    def json_path():
        return MirrorTokenStore._JSON_PATH

    @staticmethod
    def load():
        """
        JSON 에서 enabled 토큰 쌍을 읽어 반환.
        반환: (pairs, msg)  -  pairs = [(left, right), ...]
        실패/빈 목록이면 DEFAULT_TOKEN_PAIRS 로 폴백.
        """
        path = MirrorTokenStore._JSON_PATH
        default = list(MirrorTokenStore.DEFAULT_TOKEN_PAIRS)

        if not os.path.exists(path):
            return (default, "[Info] mirror_tokens.json not found. Using built-in defaults.")

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            return (default, "[Warning] Failed to read mirror_tokens.json ({0}). Using defaults.".format(e))

        pairs = []
        for row in (data.get("token_pairs") or []):
            if not row.get("enabled", True):
                continue
            left = (row.get("left") or "").strip()
            right = (row.get("right") or "").strip()
            if left and right:
                pairs.append((left, right))

        if not pairs:
            return (default, "[Warning] No enabled token pairs in JSON. Using defaults.")

        return (pairs, "{0} token pair(s) loaded.".format(len(pairs)))

    @staticmethod
    def save(pairs):
        """
        (left, right) 쌍 리스트를 JSON 으로 기록(모두 enabled=true).
        반환: (count, msg)
        """
        clean = []
        for left, right in pairs:
            left = (left or "").strip()
            right = (right or "").strip()
            if left and right:
                clean.append({"left": left, "right": right, "enabled": True})

        data = {"version": 1, "token_pairs": clean}

        try:
            with open(MirrorTokenStore._JSON_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            return (0, "[Warning] Failed to save mirror_tokens.json ({0}).".format(e))

        return (len(clean), "{0} token pair(s) saved.".format(len(clean)))
