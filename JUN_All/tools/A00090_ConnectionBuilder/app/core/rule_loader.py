import os
import json

from .connection_rule import ConnectionRule


class RuleLoader:

    RULE_DIR = os.path.join(
        os.path.dirname(__file__),
        "..",
        "rules_v01"
    )

    @classmethod
    def load(
        cls,
        rule_name,
        solver_node="",
        driver_node="",
        blendshape_node=""
    ):

        json_path = os.path.join(
            cls.RULE_DIR,
            f"{rule_name}.json"
        )

        if not os.path.exists(json_path):

            raise FileNotFoundError(
                f"Rule not found : {json_path}"
            )

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return ConnectionRule(

            solver_node=solver_node,

            driver_node=driver_node,

            blendshape_node=blendshape_node,

            mapping=data["mapping"]
        )
    
    @classmethod
    def load_solver_rule(cls, rule_name):
        """기존 load 와 달리 json 의 solver_node 를 그대로 사용하는 ConnectionRule 반환.

        Intermediate 연결(각 solver 의 outputs 를 공통 null 노드로 모으기)은
        UI 입력이 아니라 json 에 적힌 solver_node 자체가 필요하므로 별도 경로로 둔다.
        """
        json_path = os.path.join(
            cls.RULE_DIR,
            f"{rule_name}.json"
        )

        if not os.path.exists(json_path):

            raise FileNotFoundError(
                f"Rule not found : {json_path}"
            )

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return ConnectionRule(
            solver_node=data["solver_node"],
            driver_node="",
            blendshape_node="",
            mapping=data["mapping"]
        )

    @classmethod
    def find_all_json(cls):
        # get .json file names in RULE_DIR removing extension (디렉토리 동적 스캔)
        return [
            os.path.splitext(f)[0]
            for f in os.listdir(cls.RULE_DIR)
            if os.path.isfile(os.path.join(cls.RULE_DIR, f)) and f.lower().endswith(".json")
        ]

    @classmethod
    def load_all(cls):

        rules = []

        for json_path in cls.find_all_json():

            rule = cls.load(json_path)

            if rule:
                rules.append(rule)
                
        print(cls.find_all_json())
        return rules