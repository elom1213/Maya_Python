# Python Script by Ji Hun Park
# last Update date : 2026-10-01
# A00490_KeyboardTool - key name <-> Windows virtual-key code (UI/DCC 비의존)
#
# 키 이름 문자열("Down", "A", "Ctrl+C", "F5") 을 (modifiers, vk) 로 바꾼다.
# 가상 키 코드는 Windows 10 / 11 공통(winuser.h) 값이다.

_NAMED = {
    "Backspace": 0x08, "Tab": 0x09, "Enter": 0x0D, "Pause": 0x13,
    "CapsLock": 0x14, "Esc": 0x1B, "Space": 0x20,
    "PageUp": 0x21, "PageDown": 0x22, "End": 0x23, "Home": 0x24,
    "Left": 0x25, "Up": 0x26, "Right": 0x27, "Down": 0x28,
    "PrintScreen": 0x2C, "Insert": 0x2D, "Delete": 0x2E,
    "Num0": 0x60, "Num1": 0x61, "Num2": 0x62, "Num3": 0x63, "Num4": 0x64,
    "Num5": 0x65, "Num6": 0x66, "Num7": 0x67, "Num8": 0x68, "Num9": 0x69,
    "NumMul": 0x6A, "NumAdd": 0x6B, "NumSub": 0x6D, "NumDec": 0x6E, "NumDiv": 0x6F,
    "NumLock": 0x90, "ScrollLock": 0x91,
    ";": 0xBA, "=": 0xBB, ",": 0xBC, "-": 0xBD, ".": 0xBE, "/": 0xBF,
    "`": 0xC0, "[": 0xDB, "\\": 0xDC, "]": 0xDD, "'": 0xDE,
}
for _i in range(1, 25):
    _NAMED["F%d" % _i] = 0x6F + _i          # F1 = 0x70
for _c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789":
    _NAMED[_c] = ord(_c)                     # 영문/숫자는 VK == ASCII 대문자

# 조합키. 순서 = 표시 순서.
MODIFIERS = {"Ctrl": 0x11, "Shift": 0x10, "Alt": 0x12, "Win": 0x5B}

# 확장 키 플래그가 필요한 키 (scan code 앞에 E0 이 붙는 키).
# 이 플래그가 없으면 방향키가 숫자패드 2/4/6/8 로 해석되는 앱이 있다.
EXTENDED_VKS = {0x21, 0x22, 0x23, 0x24, 0x25, 0x26, 0x27, 0x28,
                0x2C, 0x2D, 0x2E, 0x6F, 0x90, 0x5B, 0x5C}

_LOWER = {k.lower(): k for k in list(_NAMED) + list(MODIFIERS)}
_ALIASES = {"escape": "Esc", "return": "Enter", "del": "Delete", "ins": "Insert",
            "pgup": "PageUp", "pgdn": "PageDown", "control": "Ctrl",
            "arrowup": "Up", "arrowdown": "Down", "arrowleft": "Left",
            "arrowright": "Right"}


def key_names():
    """콤보 박스용 키 이름 목록 (자주 쓰는 것 먼저)."""
    first = ["Up", "Down", "Left", "Right", "Enter", "Space", "Tab", "Esc",
             "Backspace", "Delete", "PageUp", "PageDown", "Home", "End"]
    rest = [k for k in _NAMED if k not in first]
    return first + rest


def _canon(token):
    t = token.strip()
    low = t.lower()
    if low in _ALIASES:
        return _ALIASES[low]
    return _LOWER.get(low)


def _raw_vk(token):
    """이름 없는 키는 'VK_xx'(16진) 로 적는다 - 키 캡처가 이름을 모를 때 쓴다."""
    low = token.strip().lower()
    if not low.startswith("vk_"):
        return 0
    try:
        code = int(low[3:], 16)
    except ValueError:
        return 0
    return code if 0 < code < 0xFF else 0


def parse_key(text):
    """'Ctrl+Shift+A' -> (['Ctrl','Shift'], 0x41). 모르는 키면 ValueError.

    '+' 키 자체는 'NumAdd' 또는 'Shift+=' 로 적는다 ('+' 는 구분자).
    """
    parts = [p for p in (text or "").split("+") if p.strip()]
    if not parts:
        raise ValueError("empty key")
    mods = []
    for p in parts[:-1]:
        name = _canon(p)
        if name not in MODIFIERS:
            raise ValueError("unknown modifier '%s'" % p.strip())
        if name not in mods:
            mods.append(name)
    raw_vk = _raw_vk(parts[-1])
    if raw_vk:
        return mods, raw_vk
    key = _canon(parts[-1])
    if key is None:
        raise ValueError("unknown key '%s'" % parts[-1].strip())
    if key in MODIFIERS:
        # 조합키 단독 입력 ('Shift' 한 번 누르기) 도 허용
        return mods, MODIFIERS[key]
    return mods, _NAMED[key]


def normalize(text):
    """표기를 정리한 키 이름. 'ctrl+c' -> 'Ctrl+C'."""
    mods, vk = parse_key(text)
    order = [m for m in MODIFIERS if m in mods]
    return "+".join(order + [vk_name(vk)])


def vk_name(vk):
    for name, code in _NAMED.items():
        if code == vk:
            return name
    for name, code in MODIFIERS.items():
        if code == vk:
            return name
    return "VK_%02X" % vk


def modifier_vks(mods):
    return [MODIFIERS[m] for m in MODIFIERS if m in mods]
