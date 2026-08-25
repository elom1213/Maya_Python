# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-08-25
# A00010_humanIKTool_V02 - HumanIK 슬롯 ID <-> 슬롯 이름 테이블과 좌/우 슬롯 짝짓기.
#
# HumanIK 캐릭터라이제이션의 슬롯은 정수 ID 로 지정한다(setCharacterObject 의 3번째 인자).
# 그런데 슬롯이 왼쪽인지 오른쪽인지, 그 반대쪽 슬롯이 몇 번인지는 ID 만 봐서는 알 수 없다.
# ID -> 이름("LeftArm" / "RightArm" ...) 을 얻으면 접두사로 좌/우를 판정하고 이름을 뒤집어
# 반대쪽 ID 를 역인덱스로 찾을 수 있다. Mirror 기능 전체가 이 테이블 위에서 돈다.
#
# 이름은 mayaHIK 플러그인의 MEL 전역 프로시저 GetHIKNodeName(id) 이 권위다(런타임 조회).
# Maya 2024 에서 hikGetNodeCount() = 212, ID 0~171 이 캐릭터 정의(definition) 슬롯이고
# 172~211 은 Leaf roll(커스텀 리그 전용)이다.
# 플러그인이 없거나 프로시저가 바뀐 상황을 대비해 Maya 2024 에서 실측한 값을 정적 폴백으로 둔다.
#
# 슬롯 ID 는 캐릭터 노드의 어트리뷰트 이름이기도 하다 - 조인트는
#   <character>.<슬롯이름>  (예: TestChar.LeftArm)
# 플러그에 message 로 연결되므로, listConnections 로 "지금 무엇이 할당돼 있는지" 를 읽는다.

import maya.cmds as cmds
import maya.mel as mel


# Maya 2024 실측값(mayapy + GetHIKNodeName). 런타임 조회가 실패할 때만 쓰는 폴백.
_FALLBACK_NAMES = {
    0: "Reference",
    1: "Hips",
    2: "LeftUpLeg",
    3: "LeftLeg",
    4: "LeftFoot",
    5: "RightUpLeg",
    6: "RightLeg",
    7: "RightFoot",
    8: "Spine",
    9: "LeftArm",
    10: "LeftForeArm",
    11: "LeftHand",
    12: "RightArm",
    13: "RightForeArm",
    14: "RightHand",
    15: "Head",
    16: "LeftToeBase",
    17: "RightToeBase",
    18: "LeftShoulder",
    19: "RightShoulder",
    20: "Neck",
    21: "LeftFingerBase",
    22: "RightFingerBase",
    23: "Spine1",
    24: "Spine2",
    25: "Spine3",
    26: "Spine4",
    27: "Spine5",
    28: "Spine6",
    29: "Spine7",
    30: "Spine8",
    31: "Spine9",
    32: "Neck1",
    33: "Neck2",
    34: "Neck3",
    35: "Neck4",
    36: "Neck5",
    37: "Neck6",
    38: "Neck7",
    39: "Neck8",
    40: "Neck9",
    41: "LeftUpLegRoll",
    42: "LeftLegRoll",
    43: "RightUpLegRoll",
    44: "RightLegRoll",
    45: "LeftArmRoll",
    46: "LeftForeArmRoll",
    47: "RightArmRoll",
    48: "RightForeArmRoll",
    49: "HipsTranslation",
    50: "LeftHandThumb1",
    51: "LeftHandThumb2",
    52: "LeftHandThumb3",
    53: "LeftHandThumb4",
    54: "LeftHandIndex1",
    55: "LeftHandIndex2",
    56: "LeftHandIndex3",
    57: "LeftHandIndex4",
    58: "LeftHandMiddle1",
    59: "LeftHandMiddle2",
    60: "LeftHandMiddle3",
    61: "LeftHandMiddle4",
    62: "LeftHandRing1",
    63: "LeftHandRing2",
    64: "LeftHandRing3",
    65: "LeftHandRing4",
    66: "LeftHandPinky1",
    67: "LeftHandPinky2",
    68: "LeftHandPinky3",
    69: "LeftHandPinky4",
    70: "LeftHandExtraFinger1",
    71: "LeftHandExtraFinger2",
    72: "LeftHandExtraFinger3",
    73: "LeftHandExtraFinger4",
    74: "RightHandThumb1",
    75: "RightHandThumb2",
    76: "RightHandThumb3",
    77: "RightHandThumb4",
    78: "RightHandIndex1",
    79: "RightHandIndex2",
    80: "RightHandIndex3",
    81: "RightHandIndex4",
    82: "RightHandMiddle1",
    83: "RightHandMiddle2",
    84: "RightHandMiddle3",
    85: "RightHandMiddle4",
    86: "RightHandRing1",
    87: "RightHandRing2",
    88: "RightHandRing3",
    89: "RightHandRing4",
    90: "RightHandPinky1",
    91: "RightHandPinky2",
    92: "RightHandPinky3",
    93: "RightHandPinky4",
    94: "RightHandExtraFinger1",
    95: "RightHandExtraFinger2",
    96: "RightHandExtraFinger3",
    97: "RightHandExtraFinger4",
    98: "LeftFootThumb1",
    99: "LeftFootThumb2",
    100: "LeftFootThumb3",
    101: "LeftFootThumb4",
    102: "LeftFootIndex1",
    103: "LeftFootIndex2",
    104: "LeftFootIndex3",
    105: "LeftFootIndex4",
    106: "LeftFootMiddle1",
    107: "LeftFootMiddle2",
    108: "LeftFootMiddle3",
    109: "LeftFootMiddle4",
    110: "LeftFootRing1",
    111: "LeftFootRing2",
    112: "LeftFootRing3",
    113: "LeftFootRing4",
    114: "LeftFootPinky1",
    115: "LeftFootPinky2",
    116: "LeftFootPinky3",
    117: "LeftFootPinky4",
    118: "LeftFootExtraFinger1",
    119: "LeftFootExtraFinger2",
    120: "LeftFootExtraFinger3",
    121: "LeftFootExtraFinger4",
    122: "RightFootThumb1",
    123: "RightFootThumb2",
    124: "RightFootThumb3",
    125: "RightFootThumb4",
    126: "RightFootIndex1",
    127: "RightFootIndex2",
    128: "RightFootIndex3",
    129: "RightFootIndex4",
    130: "RightFootMiddle1",
    131: "RightFootMiddle2",
    132: "RightFootMiddle3",
    133: "RightFootMiddle4",
    134: "RightFootRing1",
    135: "RightFootRing2",
    136: "RightFootRing3",
    137: "RightFootRing4",
    138: "RightFootPinky1",
    139: "RightFootPinky2",
    140: "RightFootPinky3",
    141: "RightFootPinky4",
    142: "RightFootExtraFinger1",
    143: "RightFootExtraFinger2",
    144: "RightFootExtraFinger3",
    145: "RightFootExtraFinger4",
    146: "LeftInHandThumb",
    147: "LeftInHandIndex",
    148: "LeftInHandMiddle",
    149: "LeftInHandRing",
    150: "LeftInHandPinky",
    151: "LeftInHandExtraFinger",
    152: "RightInHandThumb",
    153: "RightInHandIndex",
    154: "RightInHandMiddle",
    155: "RightInHandRing",
    156: "RightInHandPinky",
    157: "RightInHandExtraFinger",
    158: "LeftInFootThumb",
    159: "LeftInFootIndex",
    160: "LeftInFootMiddle",
    161: "LeftInFootRing",
    162: "LeftInFootPinky",
    163: "LeftInFootExtraFinger",
    164: "RightInFootThumb",
    165: "RightInFootIndex",
    166: "RightInFootMiddle",
    167: "RightInFootRing",
    168: "RightInFootPinky",
    169: "RightInFootExtraFinger",
    170: "LeftShoulderExtra",
    171: "RightShoulderExtra",
    172: "LeafLeftUpLegRoll1",
    173: "LeafLeftLegRoll1",
    174: "LeafRightUpLegRoll1",
    175: "LeafRightLegRoll1",
    176: "LeafLeftArmRoll1",
    177: "LeafLeftForeArmRoll1",
    178: "LeafRightArmRoll1",
    179: "LeafRightForeArmRoll1",
    180: "LeafLeftUpLegRoll2",
    181: "LeafLeftLegRoll2",
    182: "LeafRightUpLegRoll2",
    183: "LeafRightLegRoll2",
    184: "LeafLeftArmRoll2",
    185: "LeafLeftForeArmRoll2",
    186: "LeafRightArmRoll2",
    187: "LeafRightForeArmRoll2",
    188: "LeafLeftUpLegRoll3",
    189: "LeafLeftLegRoll3",
    190: "LeafRightUpLegRoll3",
    191: "LeafRightLegRoll3",
    192: "LeafLeftArmRoll3",
    193: "LeafLeftForeArmRoll3",
    194: "LeafRightArmRoll3",
    195: "LeafRightForeArmRoll3",
    196: "LeafLeftUpLegRoll4",
    197: "LeafLeftLegRoll4",
    198: "LeafRightUpLegRoll4",
    199: "LeafRightLegRoll4",
    200: "LeafLeftArmRoll4",
    201: "LeafLeftForeArmRoll4",
    202: "LeafRightArmRoll4",
    203: "LeafRightForeArmRoll4",
    204: "LeafLeftUpLegRoll5",
    205: "LeafLeftLegRoll5",
    206: "LeafRightUpLegRoll5",
    207: "LeafRightLegRoll5",
    208: "LeafLeftArmRoll5",
    209: "LeafLeftForeArmRoll5",
    210: "LeafRightArmRoll5",
    211: "LeafRightForeArmRoll5",
}


class HIKNodes:
    """HumanIK 슬롯 ID 테이블. 최초 접근 때 한 번만 만들고 모듈 수준에 캐시한다."""

    _names = None        # {id: name}
    _ids = None          # {name: id}
    _from_plugin = False # 런타임 조회 성공 여부(로그/문서용)

    # 좌/우 접두사. HumanIK 슬롯 이름은 예외 없이 이 둘 중 하나로 시작하거나 무측(無側)이다.
    LEFT = "Left"
    RIGHT = "Right"

    # Leaf roll 슬롯은 캐릭터 정의에 쓰이지 않는다(커스텀 리그 전용).
    DEFINITION_SLOT_MAX = 171

    # ----------------------------------------------------------
    # 테이블
    # ----------------------------------------------------------

    @staticmethod
    def _build():
        names = {}
        from_plugin = False

        # 1순위: 플러그인 프로시저. 마야 버전이 슬롯을 늘려도 그대로 따라간다.
        try:
            count = int(mel.eval("hikGetNodeCount()"))
            for i in range(count):
                nm = mel.eval("GetHIKNodeName({0})".format(i))
                if nm:
                    names[i] = nm
            from_plugin = bool(names)
        except Exception:
            names = {}

        # 2순위: 실측 폴백.
        if not names:
            names = dict(_FALLBACK_NAMES)

        HIKNodes._names = names
        HIKNodes._ids = {}
        # Leaf roll 은 "LeftArmRoll" 같은 정의 슬롯 이름과 겹치지 않지만, 혹시 같은 이름이
        # 두 번 나오면 낮은(= 정의) ID 를 남긴다.
        for i in sorted(names):
            HIKNodes._ids.setdefault(names[i], i)
        HIKNodes._from_plugin = from_plugin

    @staticmethod
    def _ensure():
        if HIKNodes._names is None:
            HIKNodes._build()

    @staticmethod
    def refresh():
        """플러그인을 나중에 로드했을 때 테이블을 다시 만든다."""
        HIKNodes._names = None
        HIKNodes._ensure()

    @staticmethod
    def is_from_plugin():
        HIKNodes._ensure()
        return HIKNodes._from_plugin

    @staticmethod
    def name(slot_id):
        """슬롯 ID -> 슬롯 이름. 모르는 ID 면 None."""
        HIKNodes._ensure()
        return HIKNodes._names.get(int(slot_id))

    @staticmethod
    def slot_id(name):
        """슬롯 이름 -> 슬롯 ID. 모르는 이름이면 None."""
        HIKNodes._ensure()
        return HIKNodes._ids.get(name)

    @staticmethod
    def all_slots():
        """{id: name} 전체 사본."""
        HIKNodes._ensure()
        return dict(HIKNodes._names)

    # ----------------------------------------------------------
    # 좌 / 우
    # ----------------------------------------------------------

    @staticmethod
    def side_of(slot_id):
        """슬롯의 방향을 'Left' / 'Right' / None(무측) 으로."""
        nm = HIKNodes.name(slot_id)
        if not nm:
            return None
        # Leaf roll 은 "LeafLeftArmRoll1" 처럼 Leaf 접두사가 먼저 온다.
        core = nm[4:] if nm.startswith("Leaf") else nm
        if core.startswith(HIKNodes.LEFT):
            return HIKNodes.LEFT
        if core.startswith(HIKNodes.RIGHT):
            return HIKNodes.RIGHT
        return None

    @staticmethod
    def mirror_name(name):
        """슬롯 이름의 좌/우를 뒤집는다. 무측 이름이면 None."""
        if not name:
            return None
        prefix = ""
        core = name
        if core.startswith("Leaf"):
            prefix, core = "Leaf", core[4:]
        if core.startswith(HIKNodes.LEFT):
            return prefix + HIKNodes.RIGHT + core[len(HIKNodes.LEFT):]
        if core.startswith(HIKNodes.RIGHT):
            return prefix + HIKNodes.LEFT + core[len(HIKNodes.RIGHT):]
        return None

    @staticmethod
    def mirror_slot(slot_id):
        """슬롯 ID -> 반대쪽 슬롯 ID. 무측이거나 짝이 없으면 None."""
        m = HIKNodes.mirror_name(HIKNodes.name(slot_id))
        return HIKNodes.slot_id(m) if m else None

    @staticmethod
    def slots_of_side(side, definition_only=True):
        """한쪽 방향의 슬롯 ID 전체(오름차순)."""
        HIKNodes._ensure()
        out = []
        for i in sorted(HIKNodes._names):
            if definition_only and i > HIKNodes.DEFINITION_SLOT_MAX:
                continue
            if HIKNodes.side_of(i) == side:
                out.append(i)
        return out

    # ----------------------------------------------------------
    # 캐릭터 노드 조회
    # ----------------------------------------------------------

    @staticmethod
    def assigned_node(character, slot_id):
        """캐릭터의 슬롯에 지금 할당된 마야 노드 이름. 없으면 None.

        슬롯 플러그(<character>.<슬롯이름>)는 할당 여부와 무관하게 항상 존재하고,
        할당되면 노드의 .Character 메시지가 그 플러그로 연결된다.
        """
        nm = HIKNodes.name(slot_id)
        if not nm or not character:
            return None
        plug = "{0}.{1}".format(character, nm)
        if not cmds.objExists(plug):
            return None
        conns = cmds.listConnections(plug) or []
        return conns[0] if conns else None

    @staticmethod
    def definition(character, definition_only=True):
        """캐릭터에 할당된 모든 슬롯을 {slot_id: 노드이름} 으로."""
        out = {}
        if not character or not cmds.objExists(character):
            return out
        HIKNodes._ensure()
        for i in sorted(HIKNodes._names):
            if definition_only and i > HIKNodes.DEFINITION_SLOT_MAX:
                continue
            node = HIKNodes.assigned_node(character, i)
            if node:
                out[i] = node
        return out
