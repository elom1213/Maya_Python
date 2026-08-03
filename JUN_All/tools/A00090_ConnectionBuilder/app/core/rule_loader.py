# Python Script by Ji Hun Park
# last Update date : 2026-08-03
#
# v01.05 : rules/<version>/*.json 구조 지원 (v001, v002 ... 버전 폴더 선택).

import os
import json

from .connection_rule import ConnectionRule


class RuleLoader:
    """`app/rules/<version>/*.json` 규칙 파일 로더.

    규칙 json 은 버전 폴더(`v001`, `v002` ...) 아래에 둔다.
    현재 버전은 클래스 상태(`_version`)로 들고 있으며 UI 의 Version 콤보가 `set_version()`
    으로 바꾼다. 개별 메서드에 `version` 인자를 주면 그 호출만 해당 버전을 쓴다.
    """

    # 버전 폴더들을 담는 루트 : app/rules
    RULES_ROOT = os.path.normpath(
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "rules"
        )
    )

    # 버전 폴더가 하나도 없을 때/설정 전 기본값.
    DEFAULT_VERSION = "v001"

    # 현재 선택된 버전 (None 이면 사용 가능한 첫 버전을 쓴다).
    _version = None

    # -------------------------------------------------
    # Version
    # -------------------------------------------------

    @classmethod
    def find_versions(cls):
        """RULES_ROOT 아래의 버전 폴더 이름 목록(정렬)."""

        if not os.path.isdir(cls.RULES_ROOT):
            return []

        return sorted(
            name
            for name in os.listdir(cls.RULES_ROOT)
            if os.path.isdir(os.path.join(cls.RULES_ROOT, name))
            and not name.startswith((".", "_", "__"))
        )

    @classmethod
    def get_version(cls):
        """현재 버전. 설정값이 없거나 사라졌으면 사용 가능한 첫 버전으로 되돌린다."""

        versions = cls.find_versions()

        if cls._version and cls._version in versions:
            return cls._version

        if versions:
            return versions[0]

        return cls.DEFAULT_VERSION

    @classmethod
    def set_version(cls, version):
        """현재 버전 지정. 존재하지 않는 폴더면 ValueError."""

        if version not in cls.find_versions():
            raise ValueError(
                f"Rule version not found : {version} "
                f"(available : {', '.join(cls.find_versions()) or 'none'})"
            )

        cls._version = version

        return cls._version

    @classmethod
    def rule_dir(cls, version=None):
        """해당 버전의 규칙 폴더 경로."""

        return os.path.join(
            cls.RULES_ROOT,
            version or cls.get_version()
        )

    # -------------------------------------------------
    # Load
    # -------------------------------------------------

    @classmethod
    def _read_json(cls, rule_name, version=None):
        """버전 폴더에서 규칙 json 을 읽어 dict 로 반환."""

        json_path = os.path.join(
            cls.rule_dir(version),
            f"{rule_name}.json"
        )

        if not os.path.exists(json_path):

            raise FileNotFoundError(
                f"Rule not found : {json_path}"
            )

        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)

    @classmethod
    def load(
        cls,
        rule_name,
        solver_node="",
        driver_node="",
        blendshape_node="",
        version=None
    ):

        data = cls._read_json(rule_name, version)

        return ConnectionRule(

            solver_node=solver_node,

            driver_node=driver_node,

            blendshape_node=blendshape_node,

            mapping=data["mapping"]
        )

    @classmethod
    def load_solver_rule(cls, rule_name, version=None):
        """기존 load 와 달리 json 의 solver_node 를 그대로 사용하는 ConnectionRule 반환.

        Intermediate 연결(각 solver 의 outputs 를 공통 null 노드로 모으기)은
        UI 입력이 아니라 json 에 적힌 solver_node 자체가 필요하므로 별도 경로로 둔다.
        """

        data = cls._read_json(rule_name, version)

        return ConnectionRule(
            solver_node=data["solver_node"],
            driver_node="",
            blendshape_node="",
            mapping=data["mapping"]
        )

    @classmethod
    def find_all_json(cls, version=None):
        # get .json file names in the version dir removing extension (디렉토리 동적 스캔)

        directory = cls.rule_dir(version)

        if not os.path.isdir(directory):
            return []

        return sorted(
            os.path.splitext(f)[0]
            for f in os.listdir(directory)
            if os.path.isfile(os.path.join(directory, f)) and f.lower().endswith(".json")
        )

    @classmethod
    def load_all(cls, version=None):

        rules = []

        for rule_name in cls.find_all_json(version):

            rule = cls.load(rule_name, version=version)

            if rule:
                rules.append(rule)

        return rules
