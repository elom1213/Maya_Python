# 수정 계획서 — 릴리즈본 설치(install) 크래시 · 드롭 설치 실패

- **작성일**: 2026-09-21
- **대상 1**: `Maya_Tool_Release` 저장소 (`scripts/update.py` · `scripts/setup_app_dir.py` · `tools/userSetup.py`)
- **대상 2**: `Maya_Python` 의 `JUN_All/tools/*/__dragDrop_*.py` **55개**
- **기준 커밋**: `Maya_Python` `f6ef90d` / `Maya_Tool_Release` `52512d7`
- **상태**: **완료 (2026-09-22)** — 아래 "실행 결과" 참고

> [!done] 실행 결과 (2026-09-22)
> 계획대로 A · B · C 를 모두 고쳤다. 계획에 없던 것 하나를 더했다 —
> **`install.bat` 이 `update.py` 의 종료 코드를 보게** 했다. 그러지 않으면 새로 넣은
> "실패하면 exit 1" 이 아무 효과가 없다(배치가 그대로 다음 단계로 넘어간다).
>
> 검증: 드롭 파일 **55/55**(구분선 섞인 가짜 셸프, 옛 파일은 같은 테스트에서 실패 확인) ·
> `setup_app_dir.py` **17항목**(임시 폴더 5가지 경우) · `update.py` 는 한글 제목 클론에서
> 증상 재현 후 통과 + 원격이 죽었을 때 `exit 1`.
> **드롭의 최종 확인(마야 GUI)은 아직 남아 있다.**
>
> 실행하며 확인한 사실 두 가지:
> - **이 PC 에도 죽은 `userSetup_001.py` 가 있었다** — C 가 남의 PC 만의 일이 아니었다.
> - 임시 클론 실험에서 `reset --hard` 가 미커밋 새 `update.py` 를 되돌려 **옛 코드가 실행**됐다.
>   A 장에 적은 닭-달걀이 실제로 그렇게 동작한다는 뜻이다.

다른 PC 에서 보고된 두 증상을 파고들다 **세 번째 문제**(설치가 조용히 무효가 되는 것)를 함께 찾았다.
세 가지는 원인이 서로 다르고 고치는 저장소도 다르다.

| | 증상 | 원인이 있는 곳 | 심각도 |
|---|---|---|---|
| **A** | `install.bat` 실행 중 `UnicodeDecodeError` 트레이스백 | `Maya_Tool_Release/scripts/update.py` | 중 (겁주지만 업데이트 자체는 된다) |
| **B** | 드롭 설치가 `Object 'separator21' not found` 로 실패 | 드롭 파일 55개 전부 | **높음** (셸프 버튼이 안 생긴다) |
| **C** | `userSetup_004.py` 가 만들어지고 **마야가 읽지 않는다** | `Maya_Tool_Release/scripts/setup_app_dir.py` | **높음** (설치가 조용히 아무것도 안 한다) |

---

## A. install 중 `UnicodeDecodeError` — 한글 커밋 제목을 cp949 로 읽는다

### 증상

```
>> git reset --hard origin/master
Exception in thread Thread-3 (_readerthread):
  ...
UnicodeDecodeError: 'cp949' codec can't decode byte 0xeb in position 39: illegal multibyte sequence
None
```

### 원인 (재현 확인)

`scripts/update.py` 의 `run_git()` 이 이렇게 돼 있다.

```python
result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, shell=True)
print(result.stdout)
```

`text=True` 는 **로케일 인코딩**(한국어 Windows = `cp949`)으로 디코딩한다.
`git reset --hard origin/master` 는 `HEAD is now at 52512d7 fix(all tools): 다른 PC 에서...` 처럼
**커밋 제목을 그대로 되뱉는데**, git 은 그것을 **UTF-8** 로 낸다. → 디코딩 실패.

실패는 `subprocess` 의 **리더 스레드**에서 나므로 `subprocess.run` 은 예외를 올리지 않는다.
대신 `result.stdout` 이 `None` 이 되고(로그의 `None` 이 그것이다), 스레드 트레이스백만 콘솔에 찍힌다.

> **git 자체는 정상 실행됐다.** 파이썬이 출력을 못 읽었을 뿐이라 `reset` 은 적용됐다.
> 하지만 **진짜 실패해도 똑같이 조용하다** — 에러가 나도 못 본다. 이게 더 큰 문제다.

### 왜 하필 지금 터졌나

릴리즈 저장소의 커밋 제목은 **지금까지 전부 영어**였다.

```
feat(A00470_MaterialTool): add material name / assignment tool (v01.07)
fix(install.bat): ASCII-only + force CRLF so cmd parses it on any PC   <- 같은 교훈을 이미 한 번 겪었다
```

2026-09-21 에 올린 `52512d7` 이 **한글 + em dash(`—`)를 쓴 첫 커밋 제목**이다.

### 고침 (두 군데 다 고쳐야 한다 — 실측)

읽기만 고치면 **`print` 에서 또 터진다.** 콘솔도 cp949 라 `—`(U+2014)를 못 찍는다.
실제로 확인한 결과:

| 방식 | 결과 |
|---|---|
| `text=True` (현재) | `UnicodeDecodeError` → `stdout = None` |
| `encoding="utf-8"` 만 | 읽기는 되지만 `print` 에서 `UnicodeEncodeError: 'cp949' codec can't encode character '\u2014'` |
| `encoding="utf-8"` **+ stdout 재설정** | 통과 |

```python
import sys, subprocess

# 콘솔(cp949)도 함께 고쳐야 print 에서 다시 깨지지 않는다.
for stream in (sys.stdout, sys.stderr):
    try:
        stream.reconfigure(encoding="utf-8", errors="replace")   # Python 3.7+
    except Exception:
        pass


def run_git(cmd):

    print("\n>>> " + " ".join(cmd))

    result = subprocess.run(
        cmd,
        cwd=ROOT,
        capture_output=True,
        encoding="utf-8",          # git 출력은 UTF-8 이다 (로케일 아님)
        errors="replace",          # 깨진 바이트가 있어도 죽지 않는다
    )

    if result.stdout:
        print(result.stdout)

    if result.stderr:
        print(result.stderr)

    if result.returncode != 0:     # 지금은 실패해도 조용히 넘어간다
        print("[ERROR] git failed (exit %d)" % result.returncode)

    return result.returncode
```

- `shell=True` 도 뺀다. 리스트 인자에 `shell=True` 는 Windows 에서 인용 규칙이 꼬일 여지만 만든다.
- `run_git` 이 종료 코드를 돌려주게 해서, `fetch` / `reset` 이 실패하면 **거기서 멈추고 알린다.**

### ★ 이 고침만으로는 지금 PC 가 낫지 않는다 (닭-달걀)

`install.bat` 은 **클론 안에 이미 있는 옛 `update.py`** 로 업데이트를 돌린다.
즉 고친 `update.py` 는 **다음 업데이트부터** 효과가 있다. 지금 클론들은 한 번 더 같은 트레이스백을 본다.

대응 선택지 (사용자가 정할 것):

1. **릴리즈 저장소 커밋 제목을 ASCII 로 쓰는 관례를 세운다.** 앞으로의 제목만 영어로 두면
   같은 일이 다시 안 생긴다. 본문(body)은 한글이어도 된다 — `reset` 출력에는 제목만 나온다.
2. 이미 푸시된 `52512d7` 의 제목은 **건드리지 않는다.** 고치려면 히스토리 재작성이 필요하고
   전역 규칙이 금지한다. 사실만 적어 둔다.
3. 당장 겪는 PC 는 트레이스백을 **무시해도 된다** — 업데이트는 적용됐다.
   찜찜하면 그 PC 에서 `git pull` 을 직접 한 번 돌리면 된다.

---

## B. 드롭 설치 실패 — `Object 'separator21' not found`

### 증상

```
# Error: RuntimeError: file .../tools/A00470_MaterialTool\__dragDrop_A00470.py line 74:
#        Object 'separator21' not found.
```

버튼이 생기지 않고 그 자리에서 멈춘다.

### 원인

`__dragDrop_<번호>.py` 의 **중복 버튼 제거 루프**다.

```python
shelf_buttons = cmds.shelfLayout(current_tab, q=True, childArray=True) or []

for btn in shelf_buttons:

    cmd = cmds.shelfButton(btn, q=True, command=True)      # <- line 74

    if "A00470_MaterialTool.run(True)" in str(cmd):
        cmds.deleteUI(btn)
```

`childArray` 는 셸프의 **모든 자식**을 준다. 셸프에는 버튼만 있는 게 아니라 **구분선(`separator`)** 도 있다.
`cmds.shelfButton("separator21", q=True, ...)` 는 "그 이름의 **shelfButton** 이 없다" 며 `RuntimeError` 를 던진다.

**구분선을 한 번도 안 쓴 셸프에서는 절대 재현되지 않는다** — 그래서 지금까지 안 걸렸다.
남의 PC 셸프에 구분선이 있었을 뿐, **우리 코드가 원래 틀렸다.**

### 범위

| | 개수 | 방어 코드 있는 것 |
|---|---|---|
| dev 트리 `JUN_All/tools/*/__dragDrop_*.py` | **55** | **0** |
| 릴리즈본에 나가 있는 것 | 10 | 0 |

루프 본문은 55개가 **글자까지 동일**하다(툴 이름만 다르다). 한 툴의 버그가 아니라 복사된 공통 버그다.

### 고침

`try` / `except` 가 확실하다 — 어떤 컨트롤 종류가 와도 막힌다.

```python
for btn in shelf_buttons:

    # childArray 는 버튼 말고 구분선(separator) 등도 준다.
    # shelfButton 이 아닌 것에 shelfButton 질의를 하면 RuntimeError 가 난다.
    try:
        cmd = cmds.shelfButton(btn, q=True, command=True)
    except RuntimeError:
        continue

    if "A00470_MaterialTool.run(True)" in str(cmd):
        cmds.deleteUI(btn)
```

- `cmds.objectTypeUI(btn) != "shelfButton"` 로 거르는 쪽이 읽기는 좋지만
  **반환 문자열을 헤드리스로 확인할 수 없다**(`shelfLayout` 은 GUI 가 필요하다).
  마야 GUI 에서 확인되면 `try` / `except` 와 **함께** 쓰는 형태로 바꾼다. 확인 전에는 `try` / `except` 만 둔다.
- 55개를 손으로 고치지 않는다. 루프 본문이 동일하므로 **스크립트로 일괄 치환**한다
  (앞선 `launch.py` 61개 작업과 같은 방식).

### 함께 볼 것 — 드롭 파일도 릴리즈 배치를 모른다

드롭 파일은 `JUN_ALL_ROOT`(= 릴리즈본에선 저장소 루트) 만 `sys.path` 에 넣는다.
지금은 `Framework` 를 import 하지 않으므로 문제가 없지만, **셸프 설치 로직을 `Framework` 공용
헬퍼로 빼려면** 드롭 파일도 [`Release_Layout.md`](../Release_Layout.md) 의 `IS_RELEASE` 규약을
따라야 한다. 이번 수정에서는 **공용화하지 않는다** — 55개에 같은 3줄만 넣는다(변경 폭 최소).

---

## C. ★ 설치가 조용히 무효가 된다 — `userSetup_004.py`

### 증상 (보고된 로그에 같이 찍혀 있었다)

```
userSetup.py created
C:/Users/rock1/Documents/maya/scripts\userSetup_004.py
```

### 원인

`scripts/setup_app_dir.py` 가 **덮어쓰기를 피하려고** 번호를 붙인다.

```python
user_setup_path = get_unique_filepath(user_setup_path)   # 이미 있으면 userSetup_001.py, _002.py ...

with open(user_setup_path, "w", encoding="utf-8") as f:
    f.write(user_setup_code)
```

**마야는 `userSetup.py` 라는 이름의 파일만 실행한다.** `userSetup_004.py` 는 **아무도 읽지 않는다.**

즉 — **두 번째 설치부터는 경로 등록이 전혀 되지 않는다.** 그런데도 스크립트는
"Install / Update Complete" 라고 말한다. `_004` 까지 갔다는 것은 그 PC 에서 설치를 5번 돌렸고
**첫 번째 것만 살아 있다**는 뜻이다. 저장소를 다른 경로(`W:\Install\Addons\...`)로 옮겼다면
살아 있는 그 `userSetup.py` 는 **옛 경로**를 가리키고 있다.

### 고침 — 덮어쓰지도, 새 파일을 만들지도 않는다. **표식 블록만 갈아 끼운다**

```python
BEGIN = "# >>> JUN TOOLS >>>"
END   = "# <<< JUN TOOLS <<<"

block = (
    BEGIN + "\n"
    "import sys\n\n"
    'TOOLS_ROOT = r"%s"\n\n' % TOOLS_ROOT +
    "if TOOLS_ROOT not in sys.path:\n"
    "    sys.path.append(TOOLS_ROOT)\n\n"
    'print("JUN Tools Loaded")\n'
    + END + "\n"
)

path = os.path.join(maya_scripts_dir, "userSetup.py")

text = ""
if os.path.exists(path):
    with open(path, encoding="utf-8") as f:
        text = f.read()

if BEGIN in text and END in text:
    head, rest = text.split(BEGIN, 1)
    _, tail = rest.split(END, 1)
    text = head + block + tail          # 옛 경로가 박힌 블록을 새 경로로 교체
else:
    text = (text.rstrip() + "\n\n" if text.strip() else "") + block

with open(path, "w", encoding="utf-8") as f:
    f.write(text)
```

- **사용자의 기존 `userSetup.py` 내용은 지키면서** 우리 블록만 갱신한다 — 원래 `get_unique_filepath`
  가 지키려던 것이 이것이다.
- 몇 번을 돌려도 결과가 같다(**idempotent**). 저장소를 옮겨도 다음 설치에서 바로잡힌다.
- 기존에 만들어진 `userSetup_001..004.py` 는 **지우지 않는다**(사용자 파일일 수 있다).
  대신 "읽히지 않는 파일이 N개 있다, 지워도 된다" 고 **알린다.**

### 곁다리 1 — 저장소에 딸린 `tools/userSetup.py`

```
TOOLS_ROOT = r"G:\D_link_dir/02_Maya_python_Jun"
```

이 파일은 **다른 PC 에 없는 `G:` 경로**를 가리키는 샘플이고, 놓인 위치(`<repo>/tools/`)는
마야가 `userSetup.py` 를 찾는 곳이 아니라 **실행되지도 않는다.** 혼란만 준다 → **삭제 제안**.
(사용자 확인 후 지운다. 지금은 손대지 않는다.)

### 곁다리 2 — 등록 경로가 셸프 명령과 어긋난다

`setup_app_dir.py` 는 `<repo>/tools` 를 `sys.path` 에 넣는다. 그런데 셸프 명령과 드롭 파일은
`<repo>` 를 넣고 `import tools.<툴>` 을 한다. 지금은 셸프 명령이 **스스로 경로를 넣으므로**
동작하지만 등록되는 경로가 둘이라 헷갈린다. → `<repo>` 로 통일하는 것을 제안한다(별도 판단).

---

## 작업 순서

1. **B 먼저** (실제로 못 쓰게 막는 것) — `Maya_Python` dev 트리 드롭 파일 55개 일괄 수정.
2. **C** — `Maya_Tool_Release/scripts/setup_app_dir.py` 를 표식 블록 방식으로.
3. **A** — `Maya_Tool_Release/scripts/update.py` 인코딩 · 종료 코드 확인.
4. 릴리즈된 툴 10개를 다시 빌드해 릴리즈 저장소에 반영.
5. 문서: [`Release_Layout.md`](../Release_Layout.md) 에 "드롭 파일 규약" 한 절 추가,
   `WORKLOG.md` 항목, 메모 갱신.

## 커밋 구성 (저장소가 둘이라 나뉜다)

| # | 저장소 | 내용 |
|---|--------|------|
| 1 | `Maya_Python` | `fix(dragDrop): skip non-shelfButton children when removing duplicates` (55 files + docs) |
| 2 | `Maya_Tool_Release` | `fix(install): write one idempotent JUN block into userSetup.py` |
| 3 | `Maya_Tool_Release` | `fix(update): read git output as UTF-8 and report failures` |
| 4 | `Maya_Tool_Release` | 툴 10개 재빌드 |

> 릴리즈 저장소 커밋 제목은 **ASCII 로 쓴다** (A 장의 이유).
> 푸시는 그 턴에 요청이 있을 때만 한다.

## 검증 계획

| 항목 | 방법 | 헤드리스 가능? |
|---|---|---|
| A. update.py 인코딩 | 한글 제목 커밋이 있는 클론에서 `py scripts/update.py` 실행 | ✅ (재현 + 수정안까지 이미 확인) |
| C. userSetup 블록 | 임시 `Documents/maya/scripts` 를 만들어 ① 파일 없음 ② 남의 내용 있음 ③ 우리 블록 있음(경로 다름) 세 경우 실행 | ✅ |
| B. 드롭 루프 | **구분선이 있는 셸프**에 드롭 → 버튼 생성 + 중복 제거 동작 | ❌ **마야 GUI 필요** (`shelfLayout` 이 GUI 전용) |
| B. 문법 / 일괄치환 | 55개 `py_compile` + 치환 결과 diff 확인 | ✅ |

> **B 의 최종 확인은 마야 GUI 에서 사람이 해야 한다.** 구분선을 하나 넣은 셸프를 만들어 두고
> 드롭 → 버튼 생성 → 다시 드롭 → 중복이 지워지는지까지 본다.

## 손대지 않는 것

- 이미 푸시된 `52512d7` 의 커밋 제목 (히스토리 재작성 금지).
- 릴리즈본의 `Framework` **툴별 사본** 구조 — 별개 주제다([`Release_Layout.md`](../Release_Layout.md) §4).
- 사용자 PC 에 이미 생긴 `userSetup_001..004.py` — 알리기만 한다.
- 셸프 설치 로직의 `Framework` 공용화 — 이번엔 변경 폭을 최소로 둔다.
