---
name: unreal-python-tool-verify
description: UE 파이썬 API 는 헤드리스 커맨드렛으로 확인한다 + 플러그인 Content/Python 자동 실행/자동 마운트
metadata: 
  node_type: memory
  type: reference
  originSessionId: 559dfd30-01bc-4110-8708-a1499b043ca1
  modified: 2026-08-14T02:16:35.393Z
---

언리얼 파이썬 툴 작업 시 검증 방법과, 실측으로 확인된 동작들 (2026-08-14, `MANU_Engine_Prebuilt` 5.7.4).

**헤드리스 검증** ([[mayapy-headless-verify]] 의 언리얼 판):
```
UnrealEditor-Cmd.exe <Project>.uproject -run=pythonscript -script="<verify.py>" \
    -unattended -nosplash -nullrhi -AbsLog="<log>"
```
- 빈 `.uproject`(Modules 없음) + `Content/` + `Plugins/` 만 있으면 스크래치 프로젝트로 충분하다 → 사내 프로젝트를 건드리지 않고 검증 가능
- 결과는 로그의 `LogPython` 카테고리에서 grep

**확인된 동작**
- 활성화된 플러그인의 `Content/Python` 이 `sys.path` 에 올라가고 그 안의 `init_unreal.py` 가 자동 실행된다
- `.uplugin` 에 `"EnabledByDefault": true` 를 넣으면 **`.uproject` 에 등록하지 않아도** 자동 마운트된다 (`LogPluginManager: Mounting Project plugin ...`)
- `unreal.EditorDialog` = `UEditorDialogLibrary` (**EditorScriptingUtilities 플러그인**). `show_message(title, msg, AppMsgType.OK_CANCEL, AppReturnType.CANCEL)` → `AppReturnType`
- `-unattended` 면 다이얼로그가 **4번째 인자(기본값)를 즉시 반환**해서 헤드리스가 멈추지 않는다
- `unreal.ToolMenus.get()` 은 커맨드렛에서도 살아 있어 메뉴 등록 코드까지 검증된다

**함정**: 모든 플러그인의 `Content/Python` 이 **같은 `sys.path`** 에 올라간다 →
최상위 패키지에 `tools`/`app`/`utils` 같은 일반 명사 금지 ([[standalone-app-package-collision]] 과 같은 함정).

관련: [[jun-ue-plugin-repo]]
