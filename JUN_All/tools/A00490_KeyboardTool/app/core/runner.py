# Python Script by Ji Hun Park
# last Update date : 2026-10-01
# A00490_KeyboardTool - key sequence runner (Qt/DCC 비의존, 백그라운드 스레드)
#
# 순서:  for loop:  for step:  repeat step.count:  (모든 대상 창에) 누르기 -> step.interval 대기
# 대기는 짧게 쪼개 자면서 Stop(이벤트) 과 Stop 단축키(F9) 를 본다.
# UI 는 on_log / on_progress / on_finished 콜백만 넘긴다 (Qt 신호의 emit 을 넘기면
# 큐 연결로 메인 스레드에서 처리된다).

import time
import threading

from . import keys
from . import win32

METHOD_BACKGROUND = "background"
METHOD_FOREGROUND = "foreground"

STOP_HOTKEY_NAME = "F9"
STOP_HOTKEY_VK = 0x78

#: 키를 누르고 떼기까지 (초). 너무 짧으면 무시하는 앱이 있다.
KEY_HOLD = 0.03
_TICK = 0.02


class Step(object):
    __slots__ = ("key", "count", "interval")

    def __init__(self, key, count=1, interval=1.0):
        self.key = key
        self.count = int(count)
        self.interval = float(interval)

    def to_dict(self):
        return {"key": self.key, "count": self.count, "interval": self.interval}

    @classmethod
    def from_dict(cls, d):
        return cls(d.get("key", ""), d.get("count", 1), d.get("interval", 1.0))


def validate(steps):
    """[(row, message)] - 비었으면 실행 가능."""
    errors = []
    if not steps:
        errors.append((-1, "No steps. Add at least one key."))
    for i, s in enumerate(steps):
        try:
            keys.parse_key(s.key)
        except ValueError as e:
            errors.append((i, "Step %d: %s" % (i + 1, e)))
        if s.count < 1:
            errors.append((i, "Step %d: count must be 1 or more" % (i + 1)))
        if s.interval < 0:
            errors.append((i, "Step %d: interval must be 0 or more" % (i + 1)))
    return errors


class SequenceRunner(object):
    """키 시퀀스를 스레드에서 실행한다.

    targets : [(hwnd, label)] - 비어 있으면 '지금 포커스를 가진 창' (SendInput) 에 보낸다.
    loop_count : loop=True 일 때 반복 횟수, 0 = 무한.
    """

    def __init__(self, steps, targets, method=METHOD_BACKGROUND, loop=False,
                 loop_count=0, start_delay=0.0,
                 on_log=None, on_progress=None, on_finished=None):
        self.steps = list(steps)
        self.targets = list(targets)
        self.method = method
        self.loop = loop
        self.loop_count = int(loop_count)
        self.start_delay = float(start_delay)
        self._log = on_log or (lambda msg: None)
        self._progress = on_progress or (lambda text: None)
        self._finished = on_finished or (lambda reason: None)
        self._stop = threading.Event()
        self._thread = None
        self._stop_reason = ""
        # SendInput 으로 보낸 F9 는 GetAsyncKeyState 에도 잡혀 Stop 으로 읽힌다
        # -> SendInput 을 쓰고(foreground / 대상 없음) 시퀀스에 F9 가 있으면 감시를 끈다.
        injects = method == METHOD_FOREGROUND or not self.targets
        has_f9 = any(keys.parse_key(s.key)[1] == STOP_HOTKEY_VK for s in self.steps)
        self._watch_hotkey = not (injects and has_f9)

    # ------------------------------------------------------------ 제어

    def start(self):
        self._thread = threading.Thread(target=self._run, name="A00490_runner")
        self._thread.daemon = True
        self._thread.start()

    def stop(self, reason="Stopped."):
        if not self._stop.is_set():
            self._stop_reason = reason
            self._stop.set()

    def is_running(self):
        return bool(self._thread and self._thread.is_alive())

    def hotkey_enabled(self):
        return self._watch_hotkey

    # ------------------------------------------------------------ 내부

    def _sleep(self, seconds):
        """seconds 동안 기다린다. 도중에 멈추면 False."""
        end = time.perf_counter() + max(0.0, seconds)
        while True:
            if self._stop.is_set():
                return False
            if self._watch_hotkey and win32.is_key_down(STOP_HOTKEY_VK):
                self.stop("Stopped by %s." % STOP_HOTKEY_NAME)
                return False
            left = end - time.perf_counter()
            if left <= 0:
                return True
            time.sleep(min(_TICK, left))

    def _hold(self, seconds):
        # 키를 누르고 있는 짧은 시간 - 중간에 끊지 않는다 (눌린 채로 남지 않게)
        time.sleep(seconds)

    def _press(self, vk, mods):
        """한 번 누르기를 모든 대상에. 살아 있는 대상 수를 돌려준다."""
        if not self.targets:
            win32.send_key(vk, mods, KEY_HOLD, self._hold)
            return 1

        alive = []
        for hwnd, label in self.targets:
            if not win32.is_window(hwnd):
                self._log("[WARN] Window closed, removed from targets: %s" % label)
                continue
            alive.append((hwnd, label))
            if self.method == METHOD_FOREGROUND:
                if win32.activate(hwnd):
                    win32.send_key(vk, mods, KEY_HOLD, self._hold)
                else:
                    self._log("[WARN] Could not bring to front, skipped: %s" % label)
            else:
                if not win32.post_key(hwnd, vk, mods, KEY_HOLD, self._hold):
                    self._log("[WARN] Send failed: %s" % label)
        self.targets = alive
        return len(alive)

    def _run(self):
        reason = "Finished."
        prev_fg = win32.foreground_window()
        try:
            if self.start_delay > 0:
                self._log("Starting in %.1f s ..." % self.start_delay)
                self._progress("Waiting %.1f s" % self.start_delay)
                if not self._sleep(self.start_delay):
                    return

            parsed = [(s, keys.parse_key(s.key)) for s in self.steps]
            loop_no = 0
            while True:
                loop_no += 1
                loop_text = ("Loop %d" % loop_no if not self.loop else
                             "Loop %d/%s" % (loop_no, self.loop_count or "inf"))
                if self.loop:
                    self._log("-- %s" % loop_text)
                for si, (step, (mods, vk)) in enumerate(parsed):
                    self._log("Step %d/%d : %s x %d, every %.2f s"
                              % (si + 1, len(parsed), step.key, step.count, step.interval))
                    for n in range(step.count):
                        if self._stop.is_set():
                            return
                        self._progress("%s | Step %d/%d | %s %d/%d"
                                       % (loop_text, si + 1, len(parsed), step.key,
                                          n + 1, step.count))
                        if self._press(vk, mods) == 0:
                            reason = "All target windows are closed."
                            return
                        if not self._sleep(step.interval):
                            return
                if not self.loop or (self.loop_count and loop_no >= self.loop_count):
                    return
        except Exception as e:                       # 스레드 예외는 UI 로 보낸다
            reason = "Error: %s" % e
            self._log("[ERROR] %s" % e)
        finally:
            if self._stop.is_set():
                reason = self._stop_reason or "Stopped."
            # foreground 는 원래 쓰던 창으로 돌려준다
            if self.method == METHOD_FOREGROUND and self.targets and prev_fg:
                try:
                    win32.activate(prev_fg)
                except Exception:
                    pass
            self._finished(reason)
