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