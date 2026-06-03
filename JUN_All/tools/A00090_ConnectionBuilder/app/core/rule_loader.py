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
    def find_all_json(cls):
        # get file name in RULE_DIR removing extension
        return [os.path.splitext(f)[0] for f in os.listdir(cls.RULE_DIR) if os.path.isfile(os.path.join(cls.RULE_DIR, f))]

    @classmethod
    def load_all(cls):

        rules = []

        for json_path in cls.find_all_json():

            rule = cls.load(json_path)

            if rule:
                rules.append(rule)
                
        print(cls.find_all_json())
        return rules