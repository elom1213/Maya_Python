---
title: 릴리즈 배치 — dev 트리와 릴리즈본은 폴더 모양이 다르다
aliases: [Release Layout, 릴리즈 배치, IS_RELEASE, 릴리즈본, Maya_Tool_Release, dragDrop, userSetup]
tags: [maya-python, release, packaging, sys-path, framework]
updated: 2026-09-22
---

# 릴리즈 배치 — dev 트리와 릴리즈본은 폴더 모양이 다르다

`JUN_All/dev/release_builder_QT` 가 만드는 **릴리즈본**은 개발 트리를 그대로 복사한 것이 아니다.
**툴 하나가 혼자 설 수 있게** 다시 포장한 것이라 폴더 모양이 다르고, 그래서 툴의 진입 파일
(`launch.py` · `launcher.py`)은 **두 배치에서 모두 돌아야 한다.**

| | dev 트리 | 릴리즈본 ([`Maya_Tool_Release`](https://github.com/elom1213/Maya_Tool_Release)) |
|---|---|---|
| 툴 | `JUN_All/tools/<툴>` | `<repo>/tools/<툴>` |
| `Framework` | `JUN_All/Framework` — 모든 툴이 **공유** | `<툴 폴더>/Framework` — 툴마다 **사본** |
| `config.py` (`DEV_MODE`) | `JUN_All/config.py` | **없음** |
| `dev/reloader_v02` | 있음 | **없음** (빌더가 `dev` 를 제외한다) |
| 안내 문서 | `JUN_All/docs/*.md` | `<툴 폴더>/docs/*.md` |

`..`/`..` 를 올라가면 dev 에서는 `JUN_All`, 릴리즈본에서는 **저장소 루트**가 나온다.
이름은 둘 다 "`tools` 를 담은 폴더" 지만, **그 안에 든 것이 다르다.**

---

## 1. 그래서 무엇이 깨졌나 (2026-09-21)

진입 파일들이 `../..` **한 곳만** `sys.path` 에 올리고 곧바로 `import config` 를 했다.
릴리즈본에서 그 자리엔 `config.py` 가 없다.

```
# Error: ModuleNotFoundError: file .../tools/A00470_MaterialTool/launch.py line 24:
#        No module named 'config'
```

`config` 를 넘겼더라도 **다음 줄에서 또 막혔다** — `from Framework...` 역시
저장소 루트가 아니라 **툴 폴더 안**을 봐야 하기 때문이다.

릴리즈본을 클린 경로에서 import 해 본 결과 **11개 중 8개**가 이 이유로 열리지 않았다
(`A00030` `A00040` `A00050` `A00110` `A00170` `A00180` `A00190` `A00290`).
한 툴의 버그가 아니라 **진입 파일을 복사해 쓴 모든 툴의 공통 함정**이었다.

---

## 2. 진입 파일의 규약

경로를 하드코딩으로 단정하지 말고 **있는 것을 보고 정한다.**

```python
import sys, os

TOOL_ROOT = os.path.dirname(os.path.abspath(__file__))

# tools 패키지를 담은 폴더 (dev: JUN_All, 릴리즈: 저장소 루트)
ROOT = os.path.abspath(os.path.join(TOOL_ROOT, "..", ".."))

# 툴 폴더 안에 Framework 가 동봉돼 있으면 릴리즈본이다.
IS_RELEASE = os.path.isdir(os.path.join(TOOL_ROOT, "Framework"))

# Framework 가 실제로 있는 곳과 tools 패키지 루트를 둘 다 sys.path 에 올린다.
for _path in ((TOOL_ROOT, ROOT) if IS_RELEASE else (ROOT,)):
    if _path not in sys.path:
        sys.path.append(_path)


if IS_RELEASE:
    # 릴리즈본에는 config.py 도 dev/reloader_v02 도 없다 - 리로드 없이 그냥 연다.
    DEV_MODE = False
else:
    import config as jun_config                 # JUN_All/config.py
    DEV_MODE = bool(getattr(jun_config, "DEV_MODE", False))
```

지켜야 할 것 세 가지:

1. **`IS_RELEASE` 일 때 `import config` 를 하지 않는다.**
   `config` 는 흔한 이름이다. 다른 툴 폴더가 먼저 `sys.path` 에 올라가 있으면
   그쪽 `config.py` 가 `sys.modules` 를 차지해 **엉뚱한 `DEV_MODE` 를 읽는다.**
   릴리즈본엔 `dev/` 가 없으니 리로드 경로로 들어가서도 안 된다 — `DEV_MODE = False` 로 못 박는다.
2. **maya.cmds 툴(`launcher.py`)은 경로를 `from . import <본체>` 보다 먼저 잡는다.**
   본체 모듈이 `from Framework...` 를 모듈 수준에서 하므로, `run()` 안에서 `sys.path` 를
   손대면 **이미 늦다**(A00030/A00040/A00050 이 그래서 깨졌다).
3. **툴 안에서 최상위 `import config` 를 쓰지 않는다** — 툴 자기 설정은 `from . import config`.
   같은 이유로 `app` 패키지도 `tools.<툴>.app...` 로 import 한다.

---

## 3. 검증하는 법

**dev 트리가 `sys.path` 에 남아 있으면 검증이 거짓말을 한다.** dev 의 `Framework` 가 잡혀
동봉본이 없어도 통과한 것처럼 보인다. 그래서 "남의 PC" 를 이렇게 흉내 낸다.

```python
DEV_MARK = "0030_maya_python_JUN"
sys.path[:] = [p for p in sys.path if DEV_MARK not in p.replace("\\", "/")]

for k in list(sys.modules):                     # 이미 잡힌 모듈도 비운다
    if k == "config" or k.split(".")[0] in ("Framework", "tools", "dev"):
        del sys.modules[k]

sys.path.insert(0, RELEASE_ROOT)
```

그런 다음 `importlib.import_module("tools.<툴>")` 로 전 툴을 쓸어 보고,
Qt 툴은 `run(True)` 까지 불러 **창이 뜨는지 + `Framework` 가 동봉본에서 왔는지** 확인한다
(`sys.modules["Framework.themes.theme_manager"].__file__` 가 릴리즈 폴더 안이어야 한다).

> [!note] `__init__.py` 가 없는 standalone 툴
> `A00210_FileManager` 처럼 `__init__.py` 가 없는 툴은 `import tools.<툴>` 이 **아무것도
> 하지 않고 통과**한다. 통과를 근거로 삼지 말고 `tools.<툴>.launch` 를 직접 import 해야 한다.

---

## 4. 알아둘 제약 — 릴리즈본은 툴마다 `Framework` 사본을 갖는다

한 마야 세션에서 여러 툴을 열면 `import Framework` 는 **먼저 열린 툴의 사본**으로 고정된다
(`sys.modules` 캐시). 툴들을 같은 시점에 함께 릴리즈하면 사본이 같아 문제가 없지만,
한 툴만 오래 묵혀 두면 **옛 `Framework` 가 세션 전체에 쓰인다.**

피하려면 릴리즈를 툴 단위가 아니라 **한 번에 전부** 내보내는 편이 안전하다.
(`Framework` 를 저장소 루트에 하나만 두는 배치로 바꾸면 사라지는 문제지만,
그러려면 릴리즈 저장소의 폴더 구조와 `install.bat` 의 경로 등록을 함께 바꿔야 한다.)

---

## 5. 드롭 설치 파일(`__dragDrop_<번호>.py`) 규약

셸프 버튼을 만드는 파일이다. **남의 PC 의 셸프는 내 셸프와 다르게 생겼다** — 여기서 사고가 난다.

### 5.1 셸프 자식이 전부 버튼인 것은 아니다 (2026-09-22)

```python
shelf_buttons = cmds.shelfLayout(current_tab, q=True, childArray=True) or []

for btn in shelf_buttons:

    # childArray 는 버튼 말고 구분선(separator) 등도 준다.
    # shelfButton 이 아닌 것에 shelfButton 질의를 하면 RuntimeError 가 난다.
    try:
        cmd = cmds.shelfButton(btn, q=True, command=True)
    except RuntimeError:
        continue

    if "<툴>.run(True)" in str(cmd):
        cmds.deleteUI(btn)
```

`try` / `except` 없이 쓰면 **구분선이 하나라도 있는 셸프**에서 이렇게 죽는다.

```
# Error: RuntimeError: ... __dragDrop_A00470.py line 74: Object 'separator21' not found.
```

버튼이 생기지 않고 거기서 멈춘다. **구분선을 안 쓰는 셸프에서는 영영 재현되지 않으므로**
"내 마야에서 되니까 괜찮다" 가 통하지 않는다. 드롭 파일 55개가 전부 이 버그를 갖고 있었다.

### 5.2 헤드리스로 검증하는 법

`shelfLayout` 은 GUI 전용이라 `mayapy` 로는 못 부른다. 대신 **`maya.cmds` 를 대역으로 세워**
셸프를 흉내 내면 루프 자체는 검증된다 — 구분선을 섞어 넣고, 구분선에 대한 `shelfButton` 질의가
`RuntimeError` 를 던지게 만든다. 드롭 파일을 `importlib` 로 읽어 `install_shelf_button()` 을 부르고

- 예외 없이 끝나는지
- 새 버튼이 하나 생기는지
- **같은 툴의 옛 버튼만** 지워지는지

를 본다. 옛(안 고친) 파일로 같은 테스트를 돌려 **실제로 실패하는지**까지 확인해야 의미가 있다.

> 최종 확인은 여전히 마야 GUI 에서 사람이 한다 — 구분선을 넣은 셸프에 드롭해 본다.

### 5.3 드롭 파일은 `Framework` 를 import 하지 않는다

드롭 파일은 `sys.path` 에 저장소 루트만 넣는다. 릴리즈본에서 `Framework` 는 **툴 폴더 안**이라
지금 구조로는 import 되지 않는다. 셸프 설치 로직을 `Framework` 공용 헬퍼로 빼고 싶다면
드롭 파일에도 §2 의 `IS_RELEASE` 규약을 먼저 넣어야 한다.

---

## 6. 설치 스크립트(`Maya_Tool_Release/scripts/`) 규약

### 6.1 `userSetup.py` 는 이름이 고정이다

**마야는 `userSetup.py` 라는 이름의 파일만 실행한다.** `userSetup_001.py` 는 아무도 읽지 않는다.
예전 `setup_app_dir.py` 는 덮어쓰기를 피하려고 번호를 붙여 새 파일을 만들었는데,
그래서 **두 번째 설치부터 경로 등록이 조용히 무효**가 됐다(그러고도 "Complete" 라고 말했다).

지금은 표식으로 감싼 블록 하나만 갈아 끼운다.

```python
# >>> JUN TOOLS >>>
...
# <<< JUN TOOLS <<<
```

사용자가 직접 쓴 내용은 남기고, 몇 번을 돌려도 결과가 같으며(idempotent),
저장소를 옮기면 다음 설치에서 경로가 갱신된다.

### 6.2 git 출력은 UTF-8, 콘솔은 cp949

`subprocess.run(..., text=True)` 는 **로케일**(한국어 Windows = cp949)로 디코딩한다.
git 은 **UTF-8** 로 내므로 커밋 제목에 한글이 들어가면 `UnicodeDecodeError` 가 난다.
게다가 그 예외는 리더 스레드에서 터져서 **`run()` 은 조용히 `stdout=None` 을 돌려준다.**

읽기와 쓰기를 **둘 다** 고쳐야 한다 — 읽기만 고치면 `print` 에서 다시 깨진다.

```python
for stream in (sys.stdout, sys.stderr):
    try:
        stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

subprocess.run(cmd, cwd=ROOT, capture_output=True, encoding="utf-8", errors="replace")
```

> [!warning] 고친 스크립트는 **다음 업데이트부터** 듣는다
> `install.bat` 은 클론 안에 이미 있는 **옛 `scripts/update.py`** 로 업데이트를 돌린다.
> 그래서 이미 배포된 PC 는 한 번 더 같은 증상을 본다.
> **릴리즈 저장소의 커밋 제목은 ASCII 로 쓴다** — 그러면 애초에 걸리지 않는다
> (본문은 한글이어도 된다. `reset --hard` 출력에는 제목만 나온다).

---

## 7. 관련 문서

- [`release_builder_QT.md`](release_builder_QT.md) — 릴리즈를 만드는 개발 툴
- [`A00470_MaterialTool.md`](A00470_MaterialTool.md) — 이 문제가 처음 드러난 툴
- [`plans/release_install_dragdrop_fix_plan.md`](plans/release_install_dragdrop_fix_plan.md) — 5·6장 작업의 계획서
- [`WORKLOG.md`](WORKLOG.md) — 2026-09-21 · 2026-09-22 항목
