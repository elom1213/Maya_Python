# A00500_reloader — Reload (사용 안내)

마야 안에서 **Framework / tools 모듈을 전부 다시 읽는** 개발용 셸프 버튼이다.
예전에는 `dev/reloader_mayaScript_v02.py` 의 네 줄을 스크립트 에디터에 붙여 넣어 썼는데,
다른 툴처럼 `__dragDrop_A00500.py` 로 셸프에 설치해 쓴다.

- 버전: `v01.00` (`app/config/version.py`)
- 위치: `JUN_All/dev/A00500_reloader` — 배포 대상이 아니라 **개발 도구**라 `tools/` 가 아닌 `dev/` 에 있다
  (`A00510_release_builder` 와 같은 자리). 릴리즈본에는 `dev/` 가 실리지 않는다 — [Release_Layout](Release_Layout.md)
- 창이 없다. 누르면 리로드하고 결과를 뷰포트 메시지와 스크립트 에디터에 적는다.
- 두 번째 드롭 파일 `__dragDrop_A00500_pycache.py` 는 `Clear pyc` 버튼 — `JUN_All` 아래 `__pycache__` 전부 삭제(옛 `dev/remove_pycache.py`). 파일을 옮긴 뒤 옛 .pyc 가 섞여 이상할 때만 누른다.

---

## 1. 설치 / 실행

`dev/A00500_reloader/__dragDrop_A00500.py` 를 마야 뷰포트로 드래그&드롭하면 현재 셸프에 `Reload` 버튼이 생긴다.
버튼은 다음을 실행한다.

```python
import dev.A00500_reloader as A00500_reloader
A00500_reloader.run(True)
```

## 2. 누르면 무슨 일이 일어나나 (순서)

1. `JUN_All/config.py` 리로드 — `DEV_MODE` 를 바꾼 것이 바로 먹는다. **꺼져 있으면 아무것도 하지 않고** `skipped - DEV_MODE is OFF`.
2. 리로더 자신(`app/core/reloader.py`, `app/config/reload_packages.py`) 리로드 — 패키지 목록이나 리로드 로직을 고친 것이 바로 먹는다.
3. `RELOAD_PACKAGES` = `Framework`, `tools` — **`sys.modules` 에 올라와 있는 것만**, 깊은 모듈부터 `importlib.reload`.
   한 번도 import 되지 않은 툴은 건드리지 않는다.
4. 보고: 뷰포트에 `Reload N module(s) reloaded`, 실패가 있으면 `M failed - see Script Editor` 와 함께 스크립트 에디터에 모듈별 에러.

> [!warning] 전부 리로드는 떠 있는 다른 툴 창을 닫을 수 있다
> `tools.*` 의 launch 모듈 최상단(`window_instance = None`)이 다시 실행되면서 떠 있던 창의 유일한
> 파이썬 참조가 끊긴다. 그래서 **각 툴의 셸프 버튼은 전부가 아니라 자기 자신 + Framework 만**
> 리로드한다(`reload_for_tool`). 이 버튼은 "지금 떠 있는 것 상관없이 코드를 전부 새로 읽고 싶을 때" 누른다.

## 3. 각 툴의 launch.py 와의 관계

모든 툴의 `launch.py` 는 지금도 이렇게 부른다 — 바꾸지 않았다.

```python
from dev.reloader_v02 import reload_for_tool
reload_for_tool("tools.A00440_SetTool")
```

`dev/reloader_v02.py` 는 **얇은 재노출**만 남았다. 로직은 `dev/A00500_reloader/app/core/reloader.py` 에 있고,
새 코드는 `dev.A00500_reloader.app.core.reloader` 를 직접 쓴다.

## 4. 구조

```
dev/
├── reloader_v02.py                 # 재노출 (launch.py 들이 쓰는 import 경로 유지)
└── A00500_reloader/
    ├── __init__.py                 # from .launch import run
    ├── __dragDrop_A00500.py        # 셸프 설치 (Reload)
    ├── __dragDrop_A00500_pycache.py # 셸프 설치 (Clear pyc)
    ├── launch.py                   # run(reload_module=True) -> (ok, failed)
    ├── icon/A00500_reloader.svg|.png
    ├── app/
    │   ├── config/version.py
    │   ├── config/reload_packages.py   # RELOAD_PACKAGES = ["Framework", "tools"]  (옛 dev/reload_path_list.py)
    │   ├── core/reloader.py            # modules_of / reload_package / reload_all / reload_for_tool  (옛 dev/reloader_v02.py)
    │   └── core/pycache.py             # find_pycache / remove_pycache  (옛 dev/remove_pycache.py)
    └── legacy/                     # 옛 세대 보존 (README 참고, import 되지 않는다)
        ├── reloader_mayaScript_v02.py  # 붙여 넣어 쓰던 네 줄
        ├── reloader_v01.py · reload_moduleList_v01.py · reloader_mayaScript_v01.py
        └── README.md
```

- `reload_package(name)` 은 `(ok 목록, (모듈, 에러) 목록)` 을 돌려준다. 예전에는 print 만 하고 아무것도 돌려주지 않았다.
- 검증: mayapy 2024 — `run(True)` 로 Framework · tools 모듈 리로드와 개수, 재노출 import, `DEV_MODE` 꺼짐 경로, 드롭 파일의 셸프 명령 실행. 마야 GUI 에서 드롭 설치는 아직 확인 전.
