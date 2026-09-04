# Python Script by Ji Hun Park
# last Update date : 2026-09-04
#
# v01.05 : rules/<version>/*.json 구조 지원 (v001, v002 ... 버전 폴더 선택).
# v01.07 : Pose Wrangler 가 내보낸 **번들 json 하나**도 규칙으로 읽는다(솔버당 파일 불필요).

import os
import json

from .connection_rule import ConnectionRule


# ---------------------------------------------------------------- 번들 포맷

# Pose Wrangler export 를 알아보는 표식. 최상위에 solver 이름 -> 설정 dict 가 들어 있다.
# (파일 **이름**이 아니라 **내용**으로 판정한다 — 아래 '파일 이름 규칙' 참고.)
BUNDLE_KEY = "solvers"

# 솔버 노드 이름의 접미사. 규칙 이름을 만들 때 떼어 낸다
# ("WRK_calf_l_UERBFSolver" -> "WRK_calf_l" = v001/v002 의 파일 이름과 같아진다).
SOLVER_SUFFIX = "_UERBFSolver"

# Pose Wrangler 가 자동으로 만드는 중립 포즈의 이름.
DEFAULT_POSE = "default"


def pose_attr_name(pose_name, drivers):
    """포즈 이름 -> 어트리뷰트 이름.

    Pose Wrangler 는 중립 포즈를 **언제나 그냥 `default`** 로 부른다. 그대로 쓰면 솔버
    8개가 전부 `WRK_intermediate.default` 라는 **같은 어트리뷰트 하나**로 몰려 서로를
    덮어쓴다. 손으로 쓰던 v001/v002 는 이 자리를 `<driver>_default` 로 적었으므로
    (`calf_l_default`) 같은 규칙을 여기서 되살린다.

    나머지 포즈는 사용자가 이미 드라이버 이름을 붙여 짓기 때문에 손대지 않는다.
    v003 번들의 8개 솔버를 v002 의 손글씨 mapping 과 대조해 **전부 일치**하는 것을 확인했다.
    """
    if pose_name == DEFAULT_POSE and drivers:
        return "{0}_{1}".format(drivers[0], DEFAULT_POSE)
    return pose_name


class RuleLoader:
    """`app/rules/<version>/*.json` 규칙 파일 로더.

    규칙 json 은 버전 폴더(`v001`, `v002` ...) 아래에 둔다.
    현재 버전은 클래스 상태(`_version`)로 들고 있으며 UI 의 Version 콤보가 `set_version()`
    으로 바꾼다. 개별 메서드에 `version` 인자를 주면 그 호출만 해당 버전을 쓴다.

    ## 두 가지 파일 형태

    한 버전 폴더 안에서 **둘을 섞어 두어도 된다.** 파일 이름이 아니라 **내용**으로 가른다.

    1. **솔버당 한 파일** (v001 · v002) — `WRK_calf_l.json` 처럼 솔버 하나를 적는다.

           {"solver_node": "...", "driver_node": "...", "blendshape_node": "",
            "mapping": ["calf_l_default", "calf_l_back_30", ...]}

    2. **Pose Wrangler 번들** (v003 ~) — 마야 Pose Wrangler 에서 **export 한 파일 그대로**.
       최상위 `solvers` 아래에 솔버가 전부 들어 있어 **파일 하나로 끝난다.**
       포즈를 고칠 때마다 솔버 수만큼 규칙 파일을 다시 쓰던 반복이 없어진다.

           {"solvers": {"WRK_calf_l_UERBFSolver": {"drivers": ["calf_l"],
                                                   "poses": {"default": {...}, ...}}, ...},
            "metadata": {...}}

       - **규칙 이름**은 솔버 이름에서 `_UERBFSolver` 를 뗀 것(`WRK_calf_l`)이다. v002 의
         파일 이름과 같아서 Rule 콤보에 보이는 목록이 버전을 바꿔도 그대로다.
       - **mapping** 은 `poses` 의 **키 순서**다. json 은 순서를 보존하고(Python 3.7+ dict),
         그 순서가 솔버의 `outputs[i]` 순서다 — v002 의 손글씨 mapping 과 8개 솔버 전부
         일치하는 것으로 확인했다. 중립 포즈 이름만 `pose_attr_name()` 이 고친다.

    ## 파일 이름 규칙 (번들)

    **`rules_<폴더이름>.json`** 으로 둔다 — `v003/rules_v003.json`, `v004/rules_v004.json`.
    파일만 따로 떼어 놓아도 어느 버전에서 나온 것인지 읽힌다.

    다만 **코드는 이 이름에 기대지 않는다.** 최상위에 `solvers` 가 있으면 번들로 읽으므로,
    Pose Wrangler 가 지어 준 이름 그대로 떨어뜨려도 동작한다. 이름 규칙은 사람이 폴더를
    열어 봤을 때를 위한 것이다.
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

    # 버전별 규칙 색인 캐시 : version -> (signature, {rule_name: spec})
    # signature 는 폴더 안 json 들의 (이름, mtime, 크기) 목록이라, 파일을 고치면 다음
    # 호출에서 저절로 다시 읽는다(Refresh 를 누르지 않아도 최신 내용이 나온다).
    _cache = {}

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
    # Index  (파일 -> 규칙 이름별 spec)
    # -------------------------------------------------

    @classmethod
    def _signature(cls, directory):
        """폴더 안 json 들의 (이름, mtime, 크기). 하나라도 달라지면 다시 읽는다."""

        if not os.path.isdir(directory):
            return ()

        rows = []

        for name in sorted(os.listdir(directory)):

            path = os.path.join(directory, name)

            if not os.path.isfile(path) or not name.lower().endswith(".json"):
                continue

            try:
                stat = os.stat(path)
            except OSError:
                continue

            rows.append((name, stat.st_mtime, stat.st_size))

        return tuple(rows)

    @classmethod
    def _spec_from_bundle(cls, solver_name, solver):
        """Pose Wrangler 번들의 솔버 하나 -> 규칙 spec."""

        drivers = solver.get("drivers") or []
        driven = solver.get("driven_transforms") or []

        mapping = [
            pose_attr_name(pose_name, drivers)
            for pose_name in (solver.get("poses") or {})
        ]

        # driver_node 는 두 로드 경로 모두 쓰지 않는다(UI 입력 또는 빈 문자열로 덮인다).
        # 그래도 v002 와 같은 값을 넣어 두어, 파일만 보고도 짝이 읽히게 한다.
        driver_node = "{0}__null__".format(driven[0]) if driven else ""

        return {
            "solver_node": solver.get("solver_name") or solver_name,
            "driver_node": driver_node,
            "blendshape_node": "",
            "mapping": mapping,
        }

    @classmethod
    def _index(cls, version=None):
        """{규칙 이름: spec} — 폴더 안 json 을 전부 훑어 만든 색인(캐시).

        솔버당 한 파일이면 **파일 이름**이 규칙 이름이고, 번들이면 그 안의 솔버마다
        **`_UERBFSolver` 를 뗀 이름**이 규칙 이름이 된다.
        """

        version = version or cls.get_version()
        directory = cls.rule_dir(version)

        signature = cls._signature(directory)

        cached = cls._cache.get(version)
        if cached and cached[0] == signature:
            return cached[1]

        index = {}

        for name, _mtime, _size in signature:

            path = os.path.join(directory, name)

            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except (ValueError, OSError) as e:
                print(f"[Rule] Could not read {path} : {e}")
                continue

            if not isinstance(data, dict):
                print(f"[Rule] Not a rule json (expected an object) : {path}")
                continue

            solvers = data.get(BUNDLE_KEY)

            # --- (2) Pose Wrangler 번들 : 솔버마다 규칙 하나 ---
            if isinstance(solvers, dict):

                for solver_name, solver in solvers.items():

                    if not isinstance(solver, dict):
                        continue

                    rule_name = solver_name
                    if rule_name.endswith(SOLVER_SUFFIX):
                        rule_name = rule_name[:-len(SOLVER_SUFFIX)]

                    if rule_name in index:
                        print(f"[Rule] Duplicate rule '{rule_name}' in {name} "
                              f"- keeping the first one.")
                        continue

                    index[rule_name] = cls._spec_from_bundle(solver_name, solver)

                continue

            # --- (1) 솔버당 한 파일 (v001 / v002) ---
            if "mapping" not in data:
                print(f"[Rule] No 'mapping' and no '{BUNDLE_KEY}' : {path}")
                continue

            rule_name = os.path.splitext(name)[0]

            if rule_name in index:
                print(f"[Rule] Duplicate rule '{rule_name}' - keeping the first one.")
                continue

            index[rule_name] = {
                "solver_node": data.get("solver_node", ""),
                "driver_node": data.get("driver_node", ""),
                "blendshape_node": data.get("blendshape_node", ""),
                "mapping": data["mapping"],
            }

        cls._cache[version] = (signature, index)

        return index

    # -------------------------------------------------
    # Load
    # -------------------------------------------------

    @classmethod
    def _spec(cls, rule_name, version=None):
        """규칙 이름 -> spec. 없으면 FileNotFoundError."""

        index = cls._index(version)

        if rule_name not in index:
            raise FileNotFoundError(
                f"Rule not found : {rule_name} "
                f"(in {cls.rule_dir(version)})"
            )

        return index[rule_name]

    @classmethod
    def load(
        cls,
        rule_name,
        solver_node="",
        driver_node="",
        blendshape_node="",
        version=None
    ):
        """UI 가 지정한 노드로 규칙을 만든다(mapping 만 파일에서 가져온다)."""

        spec = cls._spec(rule_name, version)

        return ConnectionRule(

            solver_node=solver_node,

            driver_node=driver_node,

            blendshape_node=blendshape_node,

            mapping=spec["mapping"]
        )

    @classmethod
    def load_solver_rule(cls, rule_name, version=None):
        """기존 load 와 달리 json 의 solver_node 를 그대로 사용하는 ConnectionRule 반환.

        Intermediate 연결(각 solver 의 outputs 를 공통 null 노드로 모으기)은
        UI 입력이 아니라 json 에 적힌 solver_node 자체가 필요하므로 별도 경로로 둔다.
        """

        spec = cls._spec(rule_name, version)

        return ConnectionRule(
            solver_node=spec["solver_node"],
            driver_node="",
            blendshape_node="",
            mapping=spec["mapping"]
        )

    @classmethod
    def find_all_json(cls, version=None):
        """그 버전이 제공하는 **규칙 이름** 목록(정렬).

        이름은 파일 하나가 곧 규칙이던 시절의 습관이라 그대로 두지만, 번들 파일에서는
        파일 이름이 아니라 **솔버 이름**에서 나온다.
        """

        return sorted(cls._index(version))

    @classmethod
    def load_all(cls, version=None):

        rules = []

        for rule_name in cls.find_all_json(version):

            rule = cls.load(rule_name, version=version)

            if rule:
                rules.append(rule)

        return rules
