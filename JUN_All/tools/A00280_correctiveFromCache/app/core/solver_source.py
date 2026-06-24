# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-06-24
# A00280_correctiveFromCache - 솔버 소스 (씬 / sample_04 스타일 JSON) 파싱 (UI 비의존)
#
# 처리 대상 RBF 솔버 이름 목록을 두 소스에서 얻는다.
#   - 씬: PoseWrangler 가 인식하는 솔버.
#   - JSON: sample_04.json 의 "solvers" 키. 이름을 씬 솔버로 해석해 사용.

import json


class SolverSource:

    @staticmethod
    def from_scene(bridge):
        """씬의 솔버 이름 목록."""
        return bridge.list_solver_names()

    @staticmethod
    def from_json(json_path):
        """sample_04 스타일 json 에서 솔버 이름 목록.
        구조: {"solvers": {"<name>": {...}, ...}, "metadata": {...}}"""
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        solvers = data.get("solvers", {})
        return list(solvers.keys())

    @staticmethod
    def pose_names_from_json(json_path, solver_name):
        """json 에서 특정 솔버의 포즈 이름 목록 (참고용; 실제 처리는 씬 솔버 기준)."""
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        solver = data.get("solvers", {}).get(solver_name, {})
        return list(solver.get("poses", {}).keys())
