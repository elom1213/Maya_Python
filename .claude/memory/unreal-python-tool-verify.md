---
name: unreal-python-tool-verify
description: UE 파이썬 API 는 헤드리스 커맨드렛으로 확인한다 + 플러그인 Content/Python 자동 실행/자동 마운트
metadata: 
  node_type: memory
  type: reference
  originSessionId: 559dfd30-01bc-4110-8708-a1499b043ca1
  modified: 2026-08-14T03:40:42.059Z
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
- **`UE_ADDITIONAL_PLUGIN_PATHS` 환경변수**(Windows 구분자 `;`, 에디터 전용)에 플러그인 **상위 폴더**를 넣으면
  프로젝트 `Plugins/` 가 비어 있어도 로드된다 → `Mounting External plugin <이름>`.
  프로젝트 파일을 안 건드리므로 **툴 배포는 복사 말고 이 방식**. 시작 시 1회만 읽음(재시작 필요).
  커맨드라인 `-PLUGIN=<경로>` 도 동일. 같은 이름 플러그인이 두 곳에 있으면 엔진이 하나만 채택한다

**C++ 없이 입력 위젯 만드는 법** (Editor Utility Widget 없이):
`@unreal.uenum()`+`unreal.uvalue()` → 드롭다운, `unreal.uproperty(bool)` → 체크박스로 놓고
`unreal.EditorDialog.show_object_details_view(title, obj, options)` 로 띄운다. 실측 확인됨.
모달이고 **디테일 뷰라 실시간 반영은 불가**(PostEditChangeProperty 를 파이썬에서 못 잡는다) → OK 에 일괄 적용.
`@unreal.uclass()` 는 모듈이 리로드돼 재등록돼도 문제없다(3회 연속 확인). 오브젝트는 GC 되지 않게 참조를 붙잡을 것.

**파이썬 클래스가 없는 UObject 접근**: `unreal.find_object(None, "/Script/<Module>.Default__<Class>")` 로
CDO 를 잡으면 된다. 단 그때는 프로퍼티 이름이 **C++ 원본 이름**(snake_case 아님). `save_config` 는 없다.

**함정**: 모든 플러그인의 `Content/Python` 이 **같은 `sys.path`** 에 올라간다 →
최상위 패키지에 `tools`/`app`/`utils` 같은 일반 명사 금지 ([[standalone-app-package-collision]] 과 같은 함정).

관련: [[jun-ue-plugin-repo]]
