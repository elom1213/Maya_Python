# Python Script by Ji Hun Park
# last Update date : 2026-10-01
# A00490_KeyboardTool - Win32 창 열거 + 키 전송 (ctypes, UI/DCC 비의존)
#
# Windows 10 / 11 둘 다에 있는 user32 / kernel32 API 만 쓴다
# (EnumWindows, PostMessageW, SendInput, GetGUIThreadInfo, AttachThreadInput,
#  QueryFullProcessImageNameW - 모두 Vista 이후 고정 API).
#
# 전송 방식 두 가지:
#   background : 대상 창에 WM_KEYDOWN/WM_KEYUP 을 PostMessage. 포커스를 안 뺏는다.
#                여러 창에 동시에 보낼 수 있다. 단, 키보드 상태(Ctrl/Shift)는 못 바꾸므로
#                조합키는 안 먹는 앱이 많다. 앱이 직접 GetAsyncKeyState 로 읽으면(게임 등) 안 먹는다.
#   foreground : 대상 창을 앞으로 가져와 SendInput. 실제 키보드와 같아서 거의 다 먹지만
#                누를 때마다 포커스가 그 창으로 옮겨진다.
#
# 관리자 권한으로 뜬 창에는 둘 다 안 들어간다 (UIPI). 이 툴도 관리자로 실행해야 한다.

import sys
import ctypes
from ctypes import wintypes

from . import keys

IS_WINDOWS = sys.platform == "win32"

WM_KEYDOWN, WM_KEYUP = 0x0100, 0x0101
WM_SYSKEYDOWN, WM_SYSKEYUP = 0x0104, 0x0105
INPUT_KEYBOARD = 1
KEYEVENTF_EXTENDEDKEY, KEYEVENTF_KEYUP = 0x0001, 0x0002
MAPVK_VK_TO_VSC = 0
SW_RESTORE = 9
GW_OWNER = 4
GWL_EXSTYLE = -20
WS_EX_TOOLWINDOW = 0x00000080
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
DWMWA_CLOAKED = 14

if IS_WINDOWS:
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    try:
        dwmapi = ctypes.WinDLL("dwmapi")
    except OSError:
        dwmapi = None

    ULONG_PTR = ctypes.c_size_t

    class KEYBDINPUT(ctypes.Structure):
        _fields_ = [("wVk", wintypes.WORD), ("wScan", wintypes.WORD),
                    ("dwFlags", wintypes.DWORD), ("time", wintypes.DWORD),
                    ("dwExtraInfo", ULONG_PTR)]

    class MOUSEINPUT(ctypes.Structure):
        # 공용체 크기를 맞추려고만 둔다 (64bit 에서 INPUT 이 40 바이트여야 SendInput 이 받는다)
        _fields_ = [("dx", wintypes.LONG), ("dy", wintypes.LONG),
                    ("mouseData", wintypes.DWORD), ("dwFlags", wintypes.DWORD),
                    ("time", wintypes.DWORD), ("dwExtraInfo", ULONG_PTR)]

    class _INPUTUNION(ctypes.Union):
        _fields_ = [("ki", KEYBDINPUT), ("mi", MOUSEINPUT)]

    class INPUT(ctypes.Structure):
        _fields_ = [("type", wintypes.DWORD), ("u", _INPUTUNION)]

    class GUITHREADINFO(ctypes.Structure):
        _fields_ = [("cbSize", wintypes.DWORD), ("flags", wintypes.DWORD),
                    ("hwndActive", wintypes.HWND), ("hwndFocus", wintypes.HWND),
                    ("hwndCapture", wintypes.HWND), ("hwndMenuOwner", wintypes.HWND),
                    ("hwndMoveSize", wintypes.HWND), ("hwndCaret", wintypes.HWND),
                    ("rcCaret", wintypes.RECT)]

    WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    user32.EnumWindows.argtypes = [WNDENUMPROC, wintypes.LPARAM]
    user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
    user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    user32.GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    user32.IsWindowVisible.argtypes = [wintypes.HWND]
    user32.IsWindow.argtypes = [wintypes.HWND]
    user32.IsIconic.argtypes = [wintypes.HWND]
    user32.GetWindow.argtypes = [wintypes.HWND, wintypes.UINT]
    user32.GetWindow.restype = wintypes.HWND
    user32.GetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int]
    user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    user32.GetWindowThreadProcessId.restype = wintypes.DWORD
    user32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
    user32.MapVirtualKeyW.argtypes = [wintypes.UINT, wintypes.UINT]
    user32.MapVirtualKeyW.restype = wintypes.UINT
    user32.SendInput.argtypes = [wintypes.UINT, ctypes.POINTER(INPUT), ctypes.c_int]
    user32.SendInput.restype = wintypes.UINT
    user32.GetForegroundWindow.restype = wintypes.HWND
    user32.SetForegroundWindow.argtypes = [wintypes.HWND]
    user32.BringWindowToTop.argtypes = [wintypes.HWND]
    user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
    user32.AttachThreadInput.argtypes = [wintypes.DWORD, wintypes.DWORD, wintypes.BOOL]
    user32.GetGUIThreadInfo.argtypes = [wintypes.DWORD, ctypes.POINTER(GUITHREADINFO)]
    user32.GetAncestor.argtypes = [wintypes.HWND, wintypes.UINT]
    user32.GetAncestor.restype = wintypes.HWND
    user32.GetAsyncKeyState.argtypes = [ctypes.c_int]
    user32.GetAsyncKeyState.restype = ctypes.c_short
    kernel32.GetCurrentThreadId.restype = wintypes.DWORD
    kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.QueryFullProcessImageNameW.argtypes = [
        wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]


class WindowInfo(object):
    """열거된 최상위 창 하나."""

    __slots__ = ("hwnd", "title", "process", "class_name", "pid")

    def __init__(self, hwnd, title, process, class_name, pid):
        self.hwnd = hwnd
        self.title = title
        self.process = process
        self.class_name = class_name
        self.pid = pid

    def label(self):
        return "[%s]  %s" % (self.process or "?", self.title)


# ------------------------------------------------------------------ 창 열거

def _window_text(hwnd):
    n = user32.GetWindowTextLengthW(hwnd)
    buf = ctypes.create_unicode_buffer(n + 1)
    user32.GetWindowTextW(hwnd, buf, n + 1)
    return buf.value


def _class_name(hwnd):
    buf = ctypes.create_unicode_buffer(256)
    user32.GetClassNameW(hwnd, buf, 256)
    return buf.value


def _process_name(pid):
    h = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not h:
        return ""
    try:
        size = wintypes.DWORD(1024)
        buf = ctypes.create_unicode_buffer(size.value)
        if kernel32.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(size)):
            return buf.value.replace("/", "\\").split("\\")[-1]
        return ""
    finally:
        kernel32.CloseHandle(h)


def _is_cloaked(hwnd):
    """Win10/11 의 다른 가상 데스크톱 · UWP 대기 창은 visible 이어도 cloaked 다.

    다른 가상 데스크톱 창은 키를 받을 수 있으니 목록에 남기고 싶지만, 숨은 UWP 껍데기
    (설정 · 계산기 백그라운드 등) 가 같이 섞여 나오므로 cloaked 는 뺀다.
    """
    if dwmapi is None:
        return False
    val = ctypes.c_int(0)
    try:
        res = dwmapi.DwmGetWindowAttribute(
            wintypes.HWND(hwnd), DWMWA_CLOAKED, ctypes.byref(val), ctypes.sizeof(val))
    except Exception:
        return False
    return res == 0 and val.value != 0


def list_windows(exclude_pids=()):
    """작업 표시줄에 보일 만한 최상위 창 목록 (Z 순서 = 최근 사용 순)."""
    if not IS_WINDOWS:
        return []
    found = []

    def _cb(hwnd, _lp):
        if not user32.IsWindowVisible(hwnd):
            return True
        if user32.GetWindow(hwnd, GW_OWNER):
            return True                       # 대화상자 · 팝업 (소유자 창이 있음)
        if user32.GetWindowLongW(hwnd, GWL_EXSTYLE) & WS_EX_TOOLWINDOW:
            return True
        title = _window_text(hwnd)
        if not title.strip():
            return True
        if _is_cloaked(hwnd):
            return True
        pid = wintypes.DWORD(0)
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if pid.value in exclude_pids:
            return True
        found.append(WindowInfo(int(hwnd), title, _process_name(pid.value),
                                _class_name(hwnd), pid.value))
        return True

    user32.EnumWindows(WNDENUMPROC(_cb), 0)
    return found


def is_window(hwnd):
    return bool(IS_WINDOWS and user32.IsWindow(hwnd))


def window_title(hwnd):
    return _window_text(hwnd) if is_window(hwnd) else ""


def is_key_down(vk):
    """물리 키가 눌려 있는가 (Stop 단축키 감시용)."""
    return bool(IS_WINDOWS and (user32.GetAsyncKeyState(vk) & 0x8000))


# ------------------------------------------------------------------ 공통

def _scan(vk):
    return user32.MapVirtualKeyW(vk, MAPVK_VK_TO_VSC) & 0xFF


def _thread_of(hwnd):
    return user32.GetWindowThreadProcessId(hwnd, None)


# ------------------------------------------------------------------ background

def _focus_child(hwnd):
    """그 창 스레드의 키보드 포커스 자식 (메모장의 Edit 등). 없으면 창 자신.

    GetGUIThreadInfo 는 스레드별 입력 상태라 배경 창에서도 마지막 포커스를 돌려준다.
    포커스가 다른 최상위 창(같은 스레드의 다른 창)에 있으면 대상 창 자신에게 보낸다.
    """
    info = GUITHREADINFO()
    info.cbSize = ctypes.sizeof(GUITHREADINFO)
    if user32.GetGUIThreadInfo(_thread_of(hwnd), ctypes.byref(info)) and info.hwndFocus:
        root = user32.GetAncestor(info.hwndFocus, 2)   # GA_ROOT
        if root and int(root) == int(hwnd):
            return info.hwndFocus
    return hwnd


def _key_lparam(vk, up):
    lp = 1 | (_scan(vk) << 16)
    if vk in keys.EXTENDED_VKS:
        lp |= 1 << 24
    if up:
        lp |= (1 << 30) | (1 << 31)
    return lp


def post_key(hwnd, vk, mods, hold, sleep):
    """PostMessage 로 한 번 누르기. 창이 사라졌으면 False."""
    if not is_window(hwnd):
        return False
    target = _focus_child(hwnd)
    alt = "Alt" in mods
    down_msg = WM_SYSKEYDOWN if alt else WM_KEYDOWN
    up_msg = WM_SYSKEYUP if alt else WM_KEYUP
    mod_vks = keys.modifier_vks(mods)
    for m in mod_vks:
        user32.PostMessageW(target, WM_KEYDOWN, m, _key_lparam(m, False))
    ok = user32.PostMessageW(target, down_msg, vk, _key_lparam(vk, False) | (0x20000000 if alt else 0))
    sleep(hold)
    user32.PostMessageW(target, up_msg, vk, _key_lparam(vk, True) | (0x20000000 if alt else 0))
    for m in reversed(mod_vks):
        user32.PostMessageW(target, WM_KEYUP, m, _key_lparam(m, True))
    return bool(ok)


# ------------------------------------------------------------------ foreground

def _kb_input(vk, up):
    flags = KEYEVENTF_KEYUP if up else 0
    if vk in keys.EXTENDED_VKS:
        flags |= KEYEVENTF_EXTENDEDKEY
    inp = INPUT()
    inp.type = INPUT_KEYBOARD
    inp.u.ki = KEYBDINPUT(vk, _scan(vk), flags, 0, 0)
    return inp


def _send(inputs):
    arr = (INPUT * len(inputs))(*inputs)
    return user32.SendInput(len(inputs), arr, ctypes.sizeof(INPUT)) == len(inputs)


def send_key(vk, mods, hold, sleep):
    """지금 포커스를 가진 창에 SendInput 으로 한 번 누르기."""
    mod_vks = keys.modifier_vks(mods)
    ok = _send([_kb_input(m, False) for m in mod_vks] + [_kb_input(vk, False)])
    sleep(hold)
    ok = _send([_kb_input(vk, True)] + [_kb_input(m, True) for m in reversed(mod_vks)]) and ok
    return ok


def foreground_window():
    return int(user32.GetForegroundWindow() or 0) if IS_WINDOWS else 0


def activate(hwnd):
    """hwnd 를 앞으로. 성공하면 True.

    Windows 는 포그라운드가 아닌 프로세스의 SetForegroundWindow 를 막는다(깜빡임만).
    현재 포그라운드 스레드에 입력을 잠깐 붙이면(AttachThreadInput) 허용된다 - Win10/11 동일.
    """
    if not is_window(hwnd):
        return False
    if foreground_window() == int(hwnd):
        return True
    if user32.IsIconic(hwnd):
        user32.ShowWindow(hwnd, SW_RESTORE)
    me = kernel32.GetCurrentThreadId()
    fg = user32.GetForegroundWindow()
    fg_thread = _thread_of(fg) if fg else 0
    attached = False
    if fg_thread and fg_thread != me:
        attached = bool(user32.AttachThreadInput(me, fg_thread, True))
    try:
        user32.BringWindowToTop(hwnd)
        user32.SetForegroundWindow(hwnd)
    finally:
        if attached:
            user32.AttachThreadInput(me, fg_thread, False)
    return foreground_window() == int(hwnd)
