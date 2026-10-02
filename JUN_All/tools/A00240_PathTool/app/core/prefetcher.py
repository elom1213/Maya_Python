# Python Script by Ji Hun Park
# last Update date : 2026-10-02
# A00240_PathTool - background folder prefetcher (UI/DCC 비의존)
#
# v01.17 : Adaptive 트리의 **선읽기**. 화면에 보이는(아직 안 읽은) 폴더의 한 겹을 백그라운드
#          스레드에서 미리 읽어 둔다 -> 펼칠 때 기다리지 않고, 빈 폴더는 펼치기 전에 화살표가 사라진다.
#
# Qt 를 쓰지 않는다. UI 는 타이머로 take_results() 를 불러 결과를 메인 스레드에서 반영한다
# (스레드에서 위젯을 건드리지 않기 위해서).
#
# 순서는 **최근 요청 먼저**(LIFO) - 큰 폴더를 연 뒤 다른 폴더를 열면 나중에 연 쪽이 먼저 읽힌다.
# 한 번의 요청 안에서는 위에서 아래 순서.

import threading
from collections import deque

from . import tree_scanner


class Prefetcher:

    def __init__(self, workers=4):
        self._cond = threading.Condition()
        self._todo = deque()          # (generation, path) - 오른쪽에서 꺼낸다(LIFO)
        self._queued = set()          # 이번 세대에 이미 요청한 경로(중복 요청 방지)
        self._results = deque()       # (path, children)
        self._inflight = 0
        self._gen = 0
        self._workers = workers
        self._threads = []
        self._stopped = False

    # ------------------------------------------------------------ 메인 스레드용

    def reset(self):
        """새 트리를 빌드할 때 - 대기 중인 요청과 결과를 버린다(읽는 중인 것은 세대로 버려진다)."""
        with self._cond:
            self._gen += 1
            self._todo.clear()
            self._queued.clear()
            self._results.clear()

    def request(self, paths):
        """paths(폴더 경로들)를 읽도록 요청한다. 이미 요청한 경로는 건너뛴다."""
        with self._cond:
            fresh = [p for p in paths if p not in self._queued]
            if not fresh:
                return
            self._queued.update(fresh)
            # 오른쪽에서 꺼내므로 뒤집어 넣어야 목록의 앞(위쪽 폴더)부터 읽힌다.
            self._todo.extend((self._gen, p) for p in reversed(fresh))
            self._ensure_threads()
            self._cond.notify_all()

    def take_results(self):
        """지금까지 읽힌 결과 [(path, children), ...] 를 꺼낸다(꺼낸 것은 지워진다)."""
        with self._cond:
            out = list(self._results)
            self._results.clear()
            return out

    def busy(self):
        """아직 읽을 것 · 읽는 중인 것 · 안 꺼낸 결과가 있는가."""
        with self._cond:
            return bool(self._todo or self._inflight or self._results)

    def stop(self):
        with self._cond:
            self._stopped = True
            self._todo.clear()
            self._cond.notify_all()

    # ------------------------------------------------------------ 작업 스레드

    def _ensure_threads(self):
        self._threads = [t for t in self._threads if t.is_alive()]
        while len(self._threads) < self._workers:
            t = threading.Thread(target=self._run, name="A00240-prefetch", daemon=True)
            t.start()
            self._threads.append(t)

    def _run(self):
        while True:
            with self._cond:
                while not self._todo and not self._stopped:
                    self._cond.wait()
                if self._stopped:
                    return
                gen, path = self._todo.pop()
                self._inflight += 1
            try:
                children = tree_scanner.scan_children(path)
            except Exception:  # noqa: BLE001 - 스레드가 죽지 않게. 못 읽으면 펼칠 때 다시 읽는다.
                children = None
            with self._cond:
                self._inflight -= 1
                if children is not None and gen == self._gen:
                    self._results.append((path, children))
