# A00210_FileManager — Maya > **Export** 하위탭 작업 계획서 (세트 규칙 솎아내기 · 범위 진단 · Bake & Export FBX)

> **작성** 2026-10-26 · 상태: **계획 — 구현 전** (§13 질문의 답이 없으면 권장안으로 진행) · 대상 Maya **2023 이상** 파일, 실행은 이 PC 의 mayapy(2024)
> 선례: [`A00210_FileManager_maya_reference_plan.md`](A00210_FileManager_maya_reference_plan.md) (Maya 탭 · mayapy 워커 · 코드 배치) ·
> [`A00560_JaliBatch_plan.md`](A00560_JaliBatch_plan.md) (표 + 워커 배치 처리 · Skip/Overwrite/backup) ·
> A00480_FileTool Export 탭 (`export_ops` FBX 선택 내보내기 · 메모리 `fbx-export-selected-scope`) · A00330 Quick Rename > Insert (`insert_ops` 자리 규칙) ·
> A00340 Rules 탭 (`select_rules` 규칙 하나 = json 하나)
> 사용 안내는 구현 뒤 `docs/A00210_FileManager.md` §4-E 로.

이 문서만 보고 바로 만들 수 있게 **파일 · 함수 시그니처 · job/result json · UI 배치 · 검증 · 실측 항목**까지 적었다.
§2 결정표의 "권장" 은 §13 에서 다른 답이 오면 바꾼다. **코드는 §8 M0 실측 뒤에 시작한다** — 베이크 · FBX 의 사실 몇 개는 추정으로 두면 설계가 흔들린다.

---

## 0. 요청과 산출물

| # | 요청 (사용자 2026-10-26) | 산출물 · 어디서 다루나 |
|---|------|--------|
| **R1** | A00210 Maya 탭에 **Export 하위탭** 신설 | `app/maya/ui/export_tab.py`, `maya_tab.py` 에 `addTab` 한 줄 (§4) |
| **R2** | 마야 파일 여러 개(.ma/.mb, 2023+) 를 고른 뒤 **규칙에 맞는 세트**(예 `Bake`) 가 있는지 솎아낸다. 세트는 최상위에도, 다른 세트의 자식으로도 있을 수 있다. 있으면 알리고 다음 작업, 없으면 그대로 넘어간다 | 규칙 json(§3.1) + `Check Sets` 버튼 → mayapy 워커 `probe` 작업(§5.3) → 표의 `Set` 열 · 없는 파일은 체크 해제 + `skipped` |
| **R3** | 파일마다 **타임라인 범위 · fps** 진단 · 표시 (`anim_01.mb 0 - 6000 30fps`) | 같은 `probe` 작업이 `playbackOptions min/max · ast/aet` · `currentUnit time` · 저장 버전을 읽어 표 `Start · End · FPS · Version` 열에 (§5.3) |
| **R4** | **`Bake & Export`**: 세트 안 모든 오브젝트 · 하위 오브젝트의 translate · rotate · scale 베이크 → **FBX** 를 지정 경로로. 의도 = 아바타 최상위 본을 세트에 넣고 전 본 베이크 → 언리얼 임포트. 파일당 30fps 6000 프레임 정도 | 워커 `export` 작업(§5.4): 열기 → (레퍼런스 임포트 · 네임스페이스 제거) → 세트 → 노드 수집 → `bakeResults` → FBX 선택 내보내기. **원본 마야 파일은 저장하지 않는다** |
| **R5** | 파일 이름: 원본 이름의 **원하는 자리에 글자 추가**(`anim_01` → `anim_bake_01`) · **찾기/바꾸기** · **미리보기** | `app/maya/core/export_naming.py` (순수 파이썬, §5.2) + 표 `Output` 열 라이브 미리보기 · 충돌 검사 |
| **R6** | 베이크 · 추출 모두 **팝업 게이지**로 진행도 | 공용 `MOD_mayapyProcess_qt_v01.run_job` 의 진행률 팝업 — 파일 단위 + 파일 안 단계(open / import / bake / export) (§7) |
| **R7** | **베이크 없이 FBX 만** 내보내기 | `Export Only` 버튼 = 같은 작업에서 `bake: false` (§5.4) |
| **R8** | 베이크에 쓸 **하드웨어(CPU · GPU · 메모리) 목록 + 선택** — 어려우면 후속 버전 | **v2 로 미룬다**(§12). v1 은 자원 요약 한 줄(읽기 전용) 만. 설계 방향: mayapy 워커 N 개 병렬 + CPU 친화도 (§12.1) |
| 산출물 | | A00210 **v01.41** (`Export` 하위탭) · Framework `core/maya_fbx.py` 승격(A00480 재노출) · 워커 `probe` / `export` · 문서 · CHANGELOG · WORKLOG · 메모리 |

---

## 1. 진단 — 지금 있는 것 (그대로 쓰는 것 · 옮기는 것)

| 있는 것 | 어디 | Export 탭에서 |
|------|------|------|
| Maya 탭 틀 — `MayaTab`(QTabWidget) 에 `Reference` 하위탭 하나. "다음 하위탭은 `addTab` 한 줄" | `app/maya/ui/maya_tab.py` | `Export` 를 두 번째 탭으로 |
| 마야 파일 고르기 — 공용 폴더 트리(`JUN_mod_fileTree_qt_v01`, `checkable_files`, ma/mb/fbx) + `Add Checked` / `Browse...` + Maya File TSL(`attach_uuids=False`, Up/Down/Sort 끔) + Reveal/Copy 메뉴 | `reference_tab.py` 안에 박혀 있다 | **`maya_file_picker.py` 위젯으로 뽑아** 두 탭이 같이 쓴다 (D3) |
| mayapy 칸 — `mayapy [....] [Browse...] [Detect]`, prefs `mayapy_path` | `reference_tab.py` 안 | **`maya_tab.py` 로 올려** 하위탭 공용 (D4) |
| mayapy 워커 러너 · QProcess 진행률 팝업 · `JUNMSG` 프로토콜 · Cancel 플래그 | `Framework/core/mayapy_runner.py` · `Framework/qt/MOD_mayapyProcess_qt_v01.py` (A00210 은 재노출) | 그대로. 워커에 작업 종류 두 개를 더한다 |
| 워커 — `scan` / `import` 작업, 같은 폴더 모듈을 **평범한 import** (sys.path = 자기 폴더) | `app/maya/core/maya_worker.py` | `probe` / `export` 추가. **Framework 를 import 하게** sys.path 를 A00560 워커 방식으로 (D2) |
| 열기 헬퍼 — `open_scene`(저장된 로드 상태 그대로, `executeScriptNodes=False`, `prompt=False`, `ignoreVersion`) · `open_scene_no_refs` · `top_level_reference_nodes` · `reference_file` | `ref_scanner.py` | `probe` · `export` 가 `open_scene` 을 쓴다 |
| 레퍼런스 임포트 · 네임스페이스 제거 — `importReference` 루프(올라온 중첩까지) · `remove_all_namespaces` | `ref_importer.py` | `export` 의 선택 단계에서 **함수 재사용** (D7) — 저장은 하지 않는다 |
| FBX — `ensure_fbx_plugin` · `fbx_options`(IncludeChildren / InputConnections 한시 변경) · `collect_export_nodes`(joint 아래 non-joint 가지치기) · `get_unique_filepath` | A00480 `app/core/fbx_plugin.py` · `export_ops.py` | **툴 간 import 금지**(릴리즈 규칙) → `Framework/core/maya_fbx.py` 로 승격, A00480 재노출 (D2) |
| 베이크 — `bakeResults(simulation, sampleBy 1, preserveOutsideKeys, disableImplicitControl, smart)` | A00110_V02 `bake_manager.py` | 플래그 조합만 참고(§5.4). 코드는 워커 모듈에 새로 (툴 간 import 금지) |
| 자리 삽입 규칙 — `0` 앞 · `n` 앞 n 글자 뒤 · `-1` 끝 · `-n` 뒤 (n−1) 글자 앞, 밖이면 당긴다 | A00330 `insert_ops.insert_index` | 규칙을 **같게** 새 순수 모듈에 (D9). 거기에 **토큰 자리** 모드를 더한다 |
| 규칙 하나 = json 하나(name · description · 파일 이름은 name 을 따라감 · Rename 이 파일도 바꿈 · 폴더 안 .json 만 지움 · 깨진 json 은 errors) | A00340 `select_rules.py` | 같은 태도로 `set_rules.py` (D5). 데이터는 다르다(오브젝트 목록 ↔ 세트 이름 규칙) |
| 시간 단위 ↔ fps 표 (`ntsc` = 30 …) | `Framework/jali/time_units.py` `unit_name` · `fps_of_unit` | 워커가 `currentUnit -q time` 결과를 fps 로 바꿀 때 |
| 표 + 편집 가능한 Start 열 + Status 열, Existing(Skip / Overwrite / Overwrite with backup) | A00560 `batch_tab.py` · `jobs.py` | 모양 · 상수 이름을 따른다 (코드는 복제하지 않고 새로) |
| 얼린 exe 가 워커 .py 를 디스크에서 읽어야 함 → `launch.spec` `datas` | A00210 `launch.spec`(`app/maya/core` 만) · A00560(`Framework/core` · `jali` 도) | `Framework/core` · `Framework/jali` 추가 (D2) |
| prefs 프로파일 (`~/.jun_filemanager/profiles/<name>.json`, `DEFAULTS`) | `app/core/prefs.py` | Export 탭 설정 키 추가 (§3.4) |

### 릴리즈 제약 (바뀌지 않는 사실)
- A00210 은 **마야 밖 standalone**(PySide6) — `maya.cmds` 가 필요한 일은 전부 **mayapy 워커**. UI 프로세스는 Maya 를 import 하지 않는다.
- **툴 폴더는 다른 툴을 import 하지 않는다**(릴리즈본은 툴 하나 + Framework 만 복사된다, 메모리 `release-layout-launch-py`). 공유할 코드는 Framework 로.
- 워커가 import 하는 모듈은 **디스크에 .py 로** 있어야 한다(mayapy 가 읽는다) → 얼린 exe 는 spec `datas`.

---

## 2. 설계 결정 (권장안 — §13 에서 확인)

| ID | 결정 | 권장 | 이유 |
|----|------|------|------|
| **D1** | 코드 배치 | `app/maya/core/{set_rules, export_naming, export_jobs, scene_probe, bake_export}.py` + `app/maya/ui/{export_tab, export_table, set_rule_dialog, maya_file_picker, mayapy_bar}.py`. 워커 `maya_worker.py` 에 `probe` · `export` 분기 | Reference 계획 §4.1 그대로 — `app/maya/` 폴더째 분리 단위, 밖 import 는 Framework · prefs 뿐 |
| **D2** | FBX 공용화 | A00480 `fbx_plugin.ensure_fbx_plugin` · `export_ops.fbx_options` · `collect_export_nodes` · `get_unique_filepath` · `short_name` → **`Framework/core/maya_fbx.py`**. A00480 두 모듈은 `from Framework.core.maya_fbx import ...` 재노출(동작 동일). 워커 sys.path 는 A00560 방식(dev = JUN_All, 릴리즈 = 툴 폴더 안 Framework) + spec `datas` 에 `Framework/core` · `Framework/jali` | 툴 간 import 금지. A00480 의 FBX 선택 내보내기는 이미 실측된 방식(씬 안 건드림) |
| **D3** | 파일 고르기 위젯 | `MayaFilePicker(log, parent)` = 폴더 트리 + Add Checked / Browse / Checked 라벨 + Maya File TSL(Clear). API `file_paths()` · `selected_file_paths()` · `add_files()` · `filesChanged` 시그널. **Reference 탭도 이것을 쓰게 리팩터**(동작 변화 없음). 두 탭의 목록은 **독립** | 코드 중복 없이, 탭마다 다른 파일 묶음을 다룰 수 있게 |
| **D4** | mayapy 칸 | `MayapyBar(prefs, log)` 를 `maya_tab.py` 가 하위탭 **아래**에 한 번 둔다. 하위탭은 `mayapy_path()` 콜러블을 받는다 | 같은 값을 두 곳에 두면 어긋난다 |
| **D5** | 규칙 저장 | **규칙 하나 = json 하나**, 기본 폴더 `~/.jun_filemanager/export_rules/`, **폴더 경로를 바꿀 수 있다**(prefs `export_rules_dir`, `Rules Folder...`) | 사용자 요구(A00340 때와 같다: 폴더 복사 = 공유). 폴더를 NAS 로 돌리면 팀 공유 |
| **D6** | 규칙 내용 | `set_name` + `match`(`exact` 기본 / `contains` / `regex`) + `ignore_namespace`(기본 true). 세트의 **부모 세트는 보지 않는다** — 씬의 모든 `objectSet` 을 잎 이름으로 맞춘다 | "최상위에도, 임의 세트의 자식으로도" 를 한 번에 덮는다(세트는 DG 노드라 `ls -type objectSet` 에 다 나온다) |
| **D7** | 네임스페이스 · 레퍼런스 | 옵션 **`Import References & Remove Namespaces`** 기본 ON. export 작업에서 **베이크 전에** 로드된 최상위 레퍼런스를 전부 `importReference`(올라온 중첩까지) → `remove_all_namespaces`. 언로드 레퍼런스는 그대로(노드가 없다) | ① 레퍼런스 노드에 6000 프레임 베이크 = 레퍼런스 **편집** 수만 개(느림 · 메모리) ② 언리얼 본 이름에 `CHN:` 이 남지 않게 (M0-3 실측) |
| **D8** | 세트 찾기 시점 | `probe` 는 **열자마자**(임포트 전) `ls -type objectSet` 로 찾는다(`ignore_namespace` 로 `CHN:Bake` 도 `Bake`). `export` 는 D7 뒤에 다시 찾는다(이름이 바뀌었으므로) | probe 는 빨라야 한다. export 는 정확해야 한다 |
| **D9** | 베이크 대상 · 방법 | 대상 = 매칭 세트들의 멤버(트랜스폼 · 조인트, 컴포넌트는 그 오브젝트, 하위 세트는 펼침) + **모든 자손 트랜스폼**. `Joints Only` 기본 ON = joint 아래 non-joint 가지치기(`collect_export_nodes`). 채널 = T · R · S 체크(기본 전부). `cmds.bakeResults(nodes, time=(s,e), attribute=[...], simulation=True, sampleBy=1, disableImplicitControl=True, preserveOutsideKeys=False, minimizeRotation=True, sparseAnimCurveBake=False)` **한 번 호출**. `Euler Filter` 옵션(기본 OFF) → `filterCurve` | 사용자 의도(전 본 베이크 → UE). `simulation=True` 가 컨스트레인트 · HIK · IK 리그에서 안전. 한 번 호출 = 가장 빠르다(M0-4 가 시간을 잰다) |
| **D10** | FBX 내보내기 | 베이크한 노드를 **명시 선택** + `FBXExportIncludeChildren false`(가지친 게 있을 때) + `FBXExportInputConnections false` + `FBXExportBakeComplexAnimation false` + `playbackOptions min/max` = 범위(FBX 타임스팬 = UE "Exported Time"). 그 밖 FBX 옵션은 플러그인 현재값 | A00480 과 같은 "씬 안 건드리는" 방식. 원본 파일은 **저장하지 않는다**(베이크 · 임포트는 메모리에서만) |
| **D11** | 범위 | 표 `Start` · `End` 는 probe 가 채운 **타임라인(min/max)**, 셀 편집 가능. `Range` 콤보: `Timeline (per file)` 기본 / `Animation range (per file)`(ast/aet) / `Custom (all files)` 두 스핀 | 요청 그대로(타임라인). 손으로 고칠 길을 남긴다 |
| **D12** | 이름 규칙 | 순서: ① Find/Replace(평문, 전부, Case 토글) → ② Insert — `Token` 모드(기본, `_` 로 나눈 토큰 사이, `after token k`, `-1` = 끝) / `Char` 모드(A00330 Position 규칙) → `.fbx`. 기본값 Token · k=1 · text `bake` → `anim_01` → `anim_bake_01`. 결과 이름이 겹치면 두 행 빨강 + 실행 막음 | 요청 예시를 기본값 한 번에 재현. Prefix/Suffix 는 k=0 / −1 로 덮인다 |
| **D13** | 출력 폴더 · 기존 파일 | `Export Folder` 한 칸(prefs `export_fbx_dir`, 비면 **원본 옆**). `Existing`: `Overwrite`(기본) / `Skip existing` / `Overwrite with backup`(`backup/<name>_NN.fbx`, `backup.py` 재사용) | UE 로 보내는 FBX 는 보통 덮어쓴다. 백업은 선택지로 |
| **D14** | 두 버튼 | `Bake & Export` / `Export Only` — 같은 `export` 작업, `bake` 플래그만 다르다. Export Only 는 파일 안 키가 그대로 나간다(컨스트레인트로만 움직이는 조인트는 애니가 없다 — 툴팁에 적는다) | R7 |
| **D15** | 진행률 · 취소 | 팝업 1 개, 전체 = 파일 수. 파일 안 비중 open 0.10 · import 0.15 · bake 0.60 · export 0.15. **`bakeResults` 는 한 호출이라 그 안의 진행은 못 보인다** → 메시지 `anim_01.mb : baking 6001 frames x 78 nodes...` + 팝업의 경과 시간. Cancel 은 **파일 경계**에서(워커 플래그) | 공용 러너 그대로. 베이크 안 취소는 M0-5 (청크 베이크) 결과가 좋을 때만 v2 |
| **D16** | 결과 기록 | 워커 result json 을 UI 로그에 요약 + `<Export Folder>/_bake_export_report_<YYYYMMDD_HHMMSS>.json` 에 그대로 저장(파일 · 세트 · 범위 · 노드 수 · 소요 초 · 상태 · 에러) | 6000 프레임 × N 파일은 오래 돈다 — 끝난 뒤 무엇이 됐는지 남아야 한다 |
| **D17** | 버전 2023+ | probe 가 `fileInfo -q version`(저장한 마야) 을 읽어 `Version` 열에. **2023 미만은 노랑 경고, 막지 않는다**. mayapy 버전보다 새 파일도 경고(`ignoreVersion` 으로 열린다) | 요청은 "2023 이상 파일" 가정 — 가정 밖 파일을 알려 주는 선에서 |
| **D18** | 하드웨어 선택(R8) | **v2**. v1 은 `Resources: CPU <이름> <n>C/<n>T · RAM <n> GB · GPU <이름>` 한 줄(읽기 전용, PowerShell `Get-CimInstance` 1 회, 실패해도 무시) | §12.1 설계. 조인트 베이크는 CPU 단일 스레드 DG 평가라 GPU 선택은 의미가 없고, 실효 수단은 **mayapy 병렬 N 개** |

---

## 3. 데이터 형식

### 3.1 규칙 json — `<export_rules_dir>/<name>.json`

```json
{
  "name": "Bake",
  "description": "avatar root bone set for UE export",
  "set_name": "Bake",
  "match": "exact",
  "ignore_namespace": true
}
```

- `match`: `exact`(잎 이름 ==) · `contains`(부분 문자열) · `regex`(`re.fullmatch`). 대소문자 구분.
- `ignore_namespace`: `CHN:rig:Bake` → `Bake` 로 비교. false 면 네임스페이스 포함 전체 이름으로 비교.
- 파일 이름 = `name` 을 `sanitize`(Windows 금지 문자 → `_`, 끝 `.`/공백 제거). `Rename` 은 json 의 `name` 과 파일 둘 다. `Delete` 는 규칙 폴더 **바로 안**의 .json 만.
- 깨진 json 은 `load_rules()` 가 `errors` 로 돌려주고 건드리지 않는다. 기본 규칙: 폴더가 비어 있으면 위 `Bake` 하나를 만든다.

### 3.2 워커 job — `probe`

```json
{"job": "probe",
 "files": ["C:/.../anim_01.mb", "C:/.../anim_02.ma"],
 "rule": {"set_name": "Bake", "match": "exact", "ignore_namespace": true},
 "result": "<job_dir>/result.json", "cancel_flag": "<job_dir>/cancel.flag"}
```

result:

```json
{"files": [
  {"file": "C:/.../anim_01.mb", "ok": true, "error": "",
   "version": "2024", "fps": 30.0, "unit": "ntsc",
   "playback": [0.0, 6000.0], "anim": [0.0, 6000.0],
   "sets": [{"name": "CHN:Bake", "members": 1, "nodes": 78}],
   "references": {"loaded": 1, "unloaded": 0},
   "seconds": 4.2}
 ],
 "mayapy_version": "2024"}
```

- `sets[].nodes` = 멤버 + 자손 트랜스폼 수(가지치기 전) — 표 `Set` 열 `Bake (1 → 78)`.
- `sets` 가 비면 UI 가 그 행을 **체크 해제** + Status `no set`.

### 3.3 워커 job — `export`

```json
{"job": "export",
 "rule": {"set_name": "Bake", "match": "exact", "ignore_namespace": true},
 "bake": true,
 "channels": ["translate", "rotate", "scale"],
 "joints_only": true,
 "euler_filter": false,
 "import_references": true,
 "existing": "overwrite",
 "report": "D:/out/_bake_export_report_20261026_153000.json",
 "items": [
   {"file": "C:/.../anim_01.mb", "start": 0, "end": 6000, "out_fbx": "D:/out/anim_bake_01.fbx"},
   {"file": "C:/.../anim_03.mb", "start": 0, "end": 7000, "out_fbx": "D:/out/anim_bake_03.fbx"}
 ],
 "result": "...", "cancel_flag": "..."}
```

result:

```json
{"results": [
  {"file": "...anim_01.mb", "status": "exported", "out_fbx": "D:/out/anim_bake_01.fbx",
   "sets": ["Bake"], "nodes": 78, "pruned": 4, "frames": 6001, "fps": 30.0,
   "imported_references": 1, "namespaces_removed": 2,
   "seconds": {"open": 6.1, "import": 3.0, "bake": 142.5, "export": 4.8}, "error": ""},
  {"file": "...anim_03.mb", "status": "failed", "error": "bake failed : ...", "seconds": {...}}
 ],
 "exported": 1, "skipped": 0, "failed": 1, "cancelled": false}
```

`status` ∈ `exported` / `skipped`(세트 없음 · existing=skip 에 파일 있음) / `failed`. 실패한 파일은 **다음 파일로 계속**(A00560 Q7 과 같다).

### 3.4 prefs 프로파일 키 (`app/core/prefs.py` `DEFAULTS` 에 추가)

| 키 | 기본 | 뜻 |
|----|------|----|
| `export_rules_dir` | `""` → `~/.jun_filemanager/export_rules` | 규칙 폴더 |
| `export_rule` | `"Bake"` | 마지막에 고른 규칙 이름 |
| `export_fbx_dir` | `""` | Export Folder (비면 원본 옆) |
| `export_existing` | `"overwrite"` | `overwrite` / `skip` / `backup` |
| `export_naming` | `{"find": "", "replace": "", "case": true, "mode": "token", "position": 1, "text": "bake"}` | 이름 규칙 |
| `export_range_mode` | `"timeline"` | `timeline` / `anim` / `custom` |
| `export_custom_range` | `[0, 100]` | Custom 범위 |
| `export_bake_channels` | `["translate", "rotate", "scale"]` | |
| `export_joints_only` | `true` | |
| `export_euler_filter` | `false` | |
| `export_import_references` | `true` | D7 |

---

## 4. 코드 배치 — 바뀌는 파일

```
JUN_All/
├── Framework/core/maya_fbx.py                       # 신규 (D2) - A00480 fbx_plugin + export_ops 의 FBX 부분 승격
├── tools/A00480_FileTool/app/core/
│   ├── fbx_plugin.py                                # 수정 - Framework 재노출 (ensure_fbx_plugin, FBX_PLUGIN)
│   └── export_ops.py                                # 수정 - fbx_options · collect_export_nodes · get_unique_filepath · short_name 재노출, export_sets 는 그대로
└── tools/A00210_FileManager/
    ├── launch.spec                                  # 수정 - datas += Framework/core, Framework/jali (워커가 import)
    ├── CHANGELOG.md · app/config/version.py         # 01.41
    ├── app/core/prefs.py                            # 수정 - §3.4 키
    └── app/maya/
        ├── core/
        │   ├── maya_worker.py                       # 수정 - sys.path(A00560 방식) · job "probe" / "export" 분기
        │   ├── set_rules.py                         # 신규 - 규칙 json CRUD (순수 파이썬)           §5.1
        │   ├── export_naming.py                     # 신규 - 이름 규칙 · 미리보기 · 충돌 (순수 파이썬) §5.2
        │   ├── export_jobs.py                       # 신규 - UI 설정 -> job dict · 검사 (순수 파이썬) §3.2 · §3.3
        │   ├── scene_probe.py                       # 신규 - 열어서 버전 · fps · 범위 · 세트 (maya.cmds, 워커 안) §5.3
        │   ├── bake_export.py                       # 신규 - 열기 -> 임포트 -> 세트 -> 수집 -> 베이크 -> FBX (maya.cmds, 워커 안) §5.4
        │   └── set_match.py                         # 신규 - 세트 이름 매칭 · 멤버 펼치기 (maya.cmds lazy, probe · export 공용) §5.3
        └── ui/
            ├── maya_tab.py                          # 수정 - Export 탭 추가, MayapyBar 를 탭 아래로 (D4)
            ├── mayapy_bar.py                        # 신규 - reference_tab 의 mayapy 행을 뽑음 (D4)
            ├── maya_file_picker.py                  # 신규 - reference_tab 의 트리 + Maya File 을 뽑음 (D3)
            ├── reference_tab.py                     # 수정 - 위 둘을 쓰도록 (동작 동일)
            ├── export_tab.py                        # 신규 - 흐름 · 옵션 · 버튼                      §6
            ├── export_table.py                      # 신규 - 파일 표 (QTableWidget 서브클래스)       §6.2
            └── set_rule_dialog.py                   # 신규 - 규칙 New / Edit 대화상자                §6.3
```

- `maya/` 안은 **상대 import**(`from ..core import export_naming`). 워커가 쓰는 core 모듈은 `try: from . import x / except ImportError: import x` 폴백(기존 ref_scanner 와 같다). `scene_probe` · `bake_export` 는 `Framework.core.maya_fbx` · `Framework.jali.time_units` · 같은 폴더 `ref_scanner` · `ref_importer` · `backup` 을 쓴다.
- 워커 sys.path: 자기 폴더(기존) + `TOOL_ROOT`(릴리즈본의 Framework) 또는 `JUN_All`(dev) — A00560 `worker.py` 머리글 그대로 복사.

---

## 5. 알고리즘 — 모듈별 함수

### 5.1 `core/set_rules.py` (순수 파이썬, A00340 `select_rules` 와 같은 모양)

```python
class SetRule(object):            # name, set_name, match, ignore_namespace, description, path
MATCHES = ("exact", "contains", "regex")
DEFAULT_RULES_DIR = os.path.join(os.path.expanduser("~"), ".jun_filemanager", "export_rules")

def rules_dir(prefs_value)          -> str      # 비면 DEFAULT_RULES_DIR, 폴더 보장
def rule_path(name, rules_dir)      -> str
def load_rules(rules_dir)           -> (rules: [SetRule], errors: [(path, str)])   # 이름순, 비어 있으면 기본 "Bake" 생성
def save_rule(rule, rules_dir)      -> path     # 유효성: name · set_name 비면 ValueError, regex 는 re.compile 검사
def rename_rule(rule, new_name, rules_dir) -> SetRule
def delete_rule(rule, rules_dir)                # 폴더 바로 안의 .json 만
def rule_to_job(rule)               -> {"set_name", "match", "ignore_namespace"}
```

### 5.2 `core/export_naming.py` (순수 파이썬)

```python
class NamingSpec(object):   # find, replace, case_sensitive, mode ("token" | "char"), position (int), text, ext=".fbx"

def replace_text(stem, find, replace, case_sensitive=True) -> str      # 전부 치환, find 비면 그대로
def insert_char(stem, position, text) -> (str, clamped)                 # A00330 규칙: 0 앞 · n 앞 n 글자 뒤 · -1 끝 · -n 뒤 (n-1) 글자 앞, 밖이면 당김
def insert_token(stem, position, text, sep="_") -> (str, clamped)       # 토큰 사이: 0 = 맨 앞 토큰, k = k 번째 토큰 뒤, -1 = 끝. text 비면 그대로
def output_stem(stem, spec) -> (str, notes: [str])                      # ① replace ② insert, notes 에 "clamped" · "empty name" 등
def preview(files, spec, out_dir="") -> [Row]   # Row: file, stem, out_name, out_path, notes, collision(bool)
    # out_dir 비면 원본 폴더. collision = 같은 out_path(normcase) 가 둘 이상. 이름이 비거나 금지 문자면 notes + invalid
def invalid_characters(name) -> str             # Windows 금지 문자 (token_naming 의 NAME_FILE 과 같은 집합)
```

예: `anim_01` · spec(mode token, position 1, text `bake`) → `anim_bake_01`; `anim_01` · (char, 4, `_bake`) → `anim_bake_01`; find `anim` → `walk` 뒤 insert → `walk_bake_01`.

### 5.3 `core/set_match.py` + `core/scene_probe.py` (워커 안, maya.cmds)

```python
# set_match.py
def leaf(name) -> str                               # "CHN:rig:Bake" -> "Bake"  (DAG 경로는 세트에 없다)
def name_matches(set_name, rule) -> bool            # exact / contains / regex, ignore_namespace 면 leaf 로
def find_sets(rule) -> [str]                        # cmds.ls(type="objectSet") 중 매칭 (기본 세트 defaultObjectSet 등 제외)
def set_members_dag(set_name) -> [long paths]       # 멤버 펼치기: 하위 세트 재귀, 컴포넌트는 오브젝트, 트랜스폼/조인트만 (A00480 export_rules._set_nodes 와 같은 규칙)
def collect_targets(set_names, joints_only) -> (kept, pruned)   # 멤버마다 Framework.core.maya_fbx.collect_export_nodes(root, [], joints_only) 합집합(순서 유지, 중복 제거)

# scene_probe.py
def probe_file(path, rule, log) -> dict             # §3.2 result 의 한 항목
    ref_scanner.open_scene(path)                    # 저장된 로드 상태 그대로, 스크립트 노드 X
    version  = cmds.fileInfo("version", q=True)     # ["2024"] 또는 [] -> ""      (M0-1)
    unit     = cmds.currentUnit(q=True, time=True); fps = time_units.fps_of_unit(unit)
    playback = [playbackOptions(q, min), (q, max)];  anim = [(q, ast), (q, aet)]
    sets     = [{"name": s, "members": len(cmds.sets(s, q=True) or []), "nodes": len(collect_targets([s], False)[0])} for s in find_sets(rule)]
    references = loaded / unloaded 수 (ref_scanner.top_level_reference_nodes + referenceQuery isLoaded)
def probe(files, rule, log, progress, should_cancel) -> dict    # 파일마다, 실패는 ok=False + error, 취소는 파일 경계
```

### 5.4 `core/bake_export.py` (워커 안, maya.cmds) — 파일 하나의 순서

```python
CHANNEL_ATTRS = {"translate": ("tx","ty","tz"), "rotate": ("rx","ry","rz"), "scale": ("sx","sy","sz")}

def export_one(item, job, log, step) -> dict          # §3.3 results 한 항목. 예외는 잡아 status failed
    # 0. existing 정책: skip 이면 파일 있을 때 바로 skipped. backup 이면 backup.backup_file(out_fbx) (확장자 .fbx 그대로)
    # 1. open      step(0.00) ref_scanner.open_scene(file); maya_fbx.ensure_fbx_plugin()
    # 2. import    step(0.10) job["import_references"] 면: 로드된 최상위 레퍼런스 노드 큐 -> importReference (올라온 중첩도) -> ref_importer.remove_all_namespaces()
    #              (ref_importer.import_into_file 의 4~6 단계와 같은 코드 - 함수로 뽑아 재사용: ref_importer.import_loaded_references(log) 신설)
    # 3. sets      step(0.25) set_match.find_sets(rule)  -> 없으면 status skipped, error "set not found"
    # 4. targets   collect_targets(sets, joints_only) -> kept (베이크 · 내보낼 노드), pruned
    #              kept 가 비면 failed "nothing to export"
    # 5. range     cmds.playbackOptions(min=start, max=end, ast=start, aet=end)    # FBX 타임스팬 (D10)
    # 6. bake      step(0.25) job["bake"] 면:
    #                 attrs = [a for ch in channels for a in CHANNEL_ATTRS[ch]]
    #                 cmds.bakeResults(kept, time=(start, end), attribute=attrs, simulation=True, sampleBy=1,
    #                                  disableImplicitControl=True, preserveOutsideKeys=False, minimizeRotation=True,
    #                                  sparseAnimCurveBake=False, removeBakedAttributeFromLayer=False, bakeOnOverrideLayer=False,
    #                                  controlPoints=False, shape=False)
    #                 euler_filter 면 cmds.filterCurve(kept 의 rx/ry/rz 커브)
    #              아니면 (Export Only) 건너뛴다
    # 7. export    step(0.85) cmds.select(kept)
    #                 with maya_fbx.fbx_options(include_children=False if pruned else None, input_connections=False,
    #                                           bake_complex_animation=False):     # fbx_options 에 이 키 추가 (D10)
    #                     cmds.file(out_fbx, force=True, options="v=0;", typ="FBX export", pr=True, es=True)
    #              out_fbx 폴더 없으면 os.makedirs
    # 8. 결과 dict (nodes=len(kept), pruned, frames=end-start+1, fps, seconds 단계별). 씬은 저장하지 않는다 - 다음 파일 open 이 덮는다

def export_all(job, log, progress, should_cancel) -> dict    # §3.3 result. 파일 경계 취소. report 경로가 있으면 json 저장
```

- `preserveOutsideKeys=False`: 범위 밖 키는 쓸모가 없다(FBX 타임스팬 밖). ± 비교는 M0-4.
- `bakeResults` 가 레퍼런스 노드에 걸리면 레퍼런스 편집이 된다 — D7 이 기본 ON 인 이유. 사용자가 끄면 그대로 베이크(느릴 수 있다고 툴팁).
- Export Only 에서 조인트에 키가 없으면 FBX 에 애니가 없다 — 로그 `[WARN] <file> : no animCurve on exported nodes` (export 전에 `listConnections type animCurve` 로 한 번 센다).

### 5.5 `core/export_jobs.py` (순수 파이썬)

```python
def probe_job(files, rule) -> dict                 # 파일 없으면 ValueError
def export_job(rule, rows, bake, channels, joints_only, euler_filter, import_references, existing, report_path) -> dict
    # rows = [{"file", "start", "end", "out_fbx"}] (체크된 · 세트 있는 · 충돌 없는 행만). start <= end 검사, channels 비면 ValueError
def report_path(export_dir) -> str                 # "<dir>/_bake_export_report_<YYYYMMDD_HHMMSS>.json"
```

### 5.6 `maya_worker.py` 분기 (추가분)

```python
elif kind == "probe":
    result = scene_probe.probe(job["files"], job["rule"], log=log, progress=progress, should_cancel=should_cancel)
elif kind == "export":
    result = bake_export.export_all(job, log=log, progress=progress, should_cancel=should_cancel)
```

진행률: `progress(i + sub, total, "<file> : <단계>")`. `sub` 는 D15 비중의 누적(open 0 → import 0.10 → bake 0.25 → export 0.85 → 1.0).

---

## 6. UI 배치 (Maya > Export)

```
┌ Maya ────────────────────────────────────────────────────────────────────────┐
│ [Reference] [Export]                                                          │
│ ┌ Tree (공용 폴더 트리, 파일 체크, ma/mb) ──────────────────────────────────┐ │
│ └──────────────────────────────────────────────────────────────────────────┘ │
│ [Add Checked] [Browse...]  Checked in tree: 0                                 │
│ ┌ Maya File (TSL) ──────────┐  Rule [Bake        ▾] [New] [Edit] [Rename] [Delete] [Rules Folder...] │
│ │ anim_01.mb                │  set "Bake" · exact · ignore namespace                                 │
│ │ anim_02.mb                │                                                                       │
│ │ anim_03.mb       [Clear]  │  [Check Sets]                                                         │
│ └───────────────────────────┘                                                                       │
│ ┌ Files ─────────────────────────────────────────────────────────────────────────────────────────┐ │
│ │ ☑ │ File        │ Set            │ Start │ End  │ FPS │ Ver  │ Output             │ Status      │ │
│ │ ☑ │ anim_01.mb  │ Bake (1 → 78)  │ 0     │ 6000 │ 30  │ 2024 │ anim_bake_01.fbx   │ ready       │ │
│ │ ☐ │ anim_02.mb  │ -              │ 2     │ 5000 │ 30  │ 2024 │ anim_bake_02.fbx   │ no set      │ │
│ │ ☑ │ anim_03.mb  │ Bake (1 → 78)  │ 0     │ 7000 │ 30  │ 2023 │ anim_bake_03.fbx   │ ready       │ │
│ └────────────────────────────────────────────────────────────────────────────────────────────────┘ │
│ Range [Timeline (per file) ▾]  Custom Start [0   ] End [100 ]                                       │
│ ┌ Naming ───────────────────────────────────────────────────────────────────────────────────────┐  │
│ │ Find [        ] Replace [        ] [x] Case     Insert [Token ▾] after token [1 ] text [bake ] │  │
│ │ Preview: anim_01.mb  ->  anim_bake_01.fbx                                                      │  │
│ └───────────────────────────────────────────────────────────────────────────────────────────────┘  │
│ Export Folder [D:/out                                   ] [Browse...] [Open]  Existing [Overwrite ▾] │
│ Bake [x] Translate [x] Rotate [x] Scale   [x] Joints Only   [ ] Euler Filter   [x] Import References & Remove Namespaces │
│ Resources: CPU AMD Ryzen 9 3900X 12C/24T · RAM 64 GB · GPU NVIDIA RTX A2000          (v1 읽기 전용) │
│ [        Bake & Export        ]  [        Export Only        ]                                       │
│ mayapy [C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe] [Browse...] [Detect]     ← MayaTab 공용   │
└───────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 6.1 흐름

1. 파일을 담는다(`MayaFilePicker`). 담기면 표에 행이 생기고 `Output` 열이 바로 채워진다(probe 전에도 이름 미리보기는 된다). `Set · Start · End · FPS · Ver` 는 `-`.
2. 규칙을 고른다. `New` / `Edit` 는 §6.3 대화상자. 규칙을 바꾸면 표의 `Set` 열이 `-` 로 돌아간다(다시 Check Sets).
3. **`Check Sets`** → `probe` 작업(mayapy, 진행률 팝업). 끝나면 행마다 Set · 범위 · fps · 버전 채움. 세트 없는 행 = 체크 해제 · Status `no set`. 범위 콤보가 `Timeline` 이면 playback, `Animation range` 면 ast/aet 로 Start/End 셀을 채운다(이후 셀 편집 가능). 로그 `[OK] Check Sets : 3 file(s), 2 with set "Bake", 1 without.`
4. 이름 · 폴더 · 옵션을 고친다. `Output` 열은 Naming 칸이 바뀔 때마다 갱신. 충돌 행은 빨강 + Status `name collision`, 금지 문자는 `invalid name`.
5. **`Bake & Export`** / **`Export Only`** → 확인 팝업(파일 n 개 · 범위 · 출력 폴더 · Existing · 옵션 요약) → `export` 작업. 체크된 행 중 Status 가 `ready` 인 것만. probe 를 안 했으면(Set 열 `-`) **먼저 Check Sets 를 하라고 막는다** — 범위를 모르면 베이크할 수 없다.
6. 끝나면 행 Status `exported` / `skipped` / `failed (사유)`, 로그 요약, 보고서 json 경로 로그. `Open` 으로 출력 폴더.

### 6.2 `export_table.py` — `ExportTable(QTableWidget)`

- 열 `("", "File", "Set", "Start", "End", "FPS", "Ver", "Output", "Status")`. 편집 가능 = ☑ · Start · End 만(`QTableWidgetItem` 플래그). File 은 `UserRole` 에 절대 경로, 툴팁 경로, 더블클릭 = Reveal(`path_context`).
- API: `set_files(paths)`(기존 행 유지 · 새 행 추가 · 빠진 행 제거) · `apply_probe(result)` · `set_output_names(rows)` · `checked_rows()` → `[{"file","start","end","out_fbx","status"}]` · `set_status(file, text, color)` · `fill_range(mode, custom)`.
- 색: 세트 없음 · 충돌 · 실패 = `null_item_color()`(빨강 계열), Version < 2023 = `[WARN]` 노랑(`Framework.core.log_levels` 색), exported = `[OK]` 초록.
- 열 폭: File · Output 은 Stretch, 숫자 열은 ResizeToContents.

### 6.3 `set_rule_dialog.py` — `SetRuleDialog(rule=None)`

`Name` · `Set name` · `Match`(콤보 Exact / Contains / Regex) · `[x] Ignore namespace` · `Description`. OK 에서 `set_rules.save_rule` 유효성(regex 컴파일 포함) → 틀리면 라벨에 빨간 메시지, 닫지 않는다. `Edit` 는 같은 창에 값 채움(이름 바꾸면 rename).

### 6.4 `export_tab.py` 가 받는 것

`ExportTab(log, prefs, mayapy_path, parent)` — `prefs` = `{"load", "save"}`(Reference 와 같다), `mayapy_path` = `MayapyBar.path` 콜러블. `load_prefs()` / `save_prefs()` 는 §3.4 키만 읽고 쓴다(바뀔 때마다 저장 — mayapy 칸의 `editingFinished` 저장과 같은 태도).

### 6.5 `maya_tab.py`

```python
self.mayapy_bar = MayapyBar(prefs=self._prefs, log=self._log)
self.reference_tab = ReferenceTab(log=..., prefs=..., mayapy_path=self.mayapy_bar.path)
self.export_tab    = ExportTab(log=..., prefs=..., mayapy_path=self.mayapy_bar.path)
self.tabs.addTab(self.reference_tab, "Reference"); self.tabs.addTab(self.export_tab, "Export")
layout.addWidget(self.tabs); layout.addWidget(self.mayapy_bar)
```

ReferenceTab 의 `mayapy_path()` · `_require_mayapy()` 는 콜러블을 쓰도록만 바꾼다(`_require_mayapy` 는 두 탭이 같은 문구를 쓰므로 `mayapy_bar.require(parent)` 로 올린다).

---

## 7. 진행률 팝업

| 작업 | 전체 | 파일 안 | 메시지 예 |
|------|------|--------|-----------|
| `probe` | 파일 수 | open 0 → 1 | `anim_01.mb : opening` · `anim_01.mb : 1 set, 0 - 6000 @ 30 fps` |
| `export` | 파일 수 | open 0.00 · import 0.10 · (sets · targets 0.25) · bake 0.25 → 0.85 · export 0.85 → 1.00 | `anim_01.mb : baking 6001 frames x 78 nodes (translate, rotate, scale)...` · `anim_01.mb : exporting anim_bake_01.fbx` |

- `bakeResults` 는 한 호출이다 — 그 동안 게이지는 0.25 에 머물고 **경과 시간만 간다**. 팝업 제목 아래 `Baking... this step reports no progress` 를 적어 멈춘 것처럼 보이지 않게 한다. (청크 베이크로 안의 진행을 보이는 것은 M0-5 결과를 보고 v2.)
- Cancel: 플래그 → 워커가 **다음 파일로 넘어가기 전**에 멈춘다. 베이크 중이면 그 파일이 끝날 때까지(수 분) 걸린다 — `[WARN] Cancel requested - stopping after the current file (a bake in progress cannot be interrupted).` 공용 러너의 `cancel_grace_sec` 기본 120 s 는 **이 작업에선 짧다**(6000 프레임 베이크가 그보다 길 수 있다) → `run_job(..., cancel_grace_sec=1800)` 으로 넘긴다(공용 러너는 인자가 이미 있다).

---

## 8. M0 — 코드 전에 mayapy 로 확정할 사실 (반나절)

스크립트는 scratchpad, 결과는 이 문서 §15 에 적는다. 합성 씬 = 조인트 체인 10 개 × 3 가지(aim/parent constraint · IK · 키 직접) + `Bake` 세트 변형 + 레퍼런스 버전.

| # | 확인할 것 | 쓰는 곳 | 추정이면 위험한 이유 |
|---|-----------|---------|------|
| M0-1 | `.mb` 를 연 뒤 `cmds.fileInfo("version", q=True)` · `cmds.file(q=True, version=True)`(없을 수 있다) 가 무엇을 주나. 2023 으로 저장한 파일이 없으면 2024 값만 확인 | D17 `Version` 열 | 빈 값이면 열이 비어 사용자가 "2023 이상" 을 확인할 수 없다 |
| M0-2 | `currentUnit -q time` 이 30 fps 에서 `ntsc` 인지, 29.97 등 `time_units.fps_of_unit` 이 다 받나 | `FPS` 열 | 표가 틀린 fps 를 보이면 UE 임포트 설정이 어긋난다 |
| M0-3 | **네임스페이스 안 조인트(`CHN:root`) 를 FBX 로 내보내 다시 임포트하면 노드 이름이 무엇인가**(콜론 유지? `_` 치환?) — 레퍼런스 상태 · 임포트+ns 제거 상태 둘 다 | D7 기본값 | ns 가 남으면 UE 본 이름이 `CHN:root` — 스켈레톤 매칭 실패 |
| M0-4 | 컨스트레인트로 움직이는 조인트 78 개 × 6001 프레임 `bakeResults(simulation=True, disableImplicitControl=True)` **소요 시간**(mayapy) · 커브가 생겼나 · 컨스트레인트가 끊겼나 · 결과 월드 행렬이 베이크 전과 같나(샘플 50 프레임, 1e-4). `simulation=False` 와 시간 · 값 비교. `preserveOutsideKeys` True/False 차이 | D9 · D15 메시지 · 사용자 기대 시간 | 시간을 모르면 팝업 안내 · 취소 유예를 정할 수 없다 |
| M0-5 | (선택) 청크 베이크: 500 프레임씩 `bakeResults(disableImplicitControl=False, preserveOutsideKeys=True)` 반복 뒤 마지막에 컨스트레인트 삭제 → 한 번 베이크와 값이 같나 · 시간 | v2 안 진행률 · 취소 | 같지 않으면 청크는 쓰지 않는다(지금 설계는 한 호출) |
| M0-6 | `FBXExportBakeComplexAnimation -q` 기본값(플러그인 로드 직후) · false 로 둔 채 베이크 커브가 다 나가나 · **FBX 타임스팬이 `playbackOptions min/max` 를 따르나**(재임포트 후 `FBXImportSetTake`/키 범위로 확인) | D10 | UE "Exported Time" 이 틀린 구간을 읽는다 |
| M0-7 | 레퍼런스된 리그가 든 실제 애니 파일(사용자 샘플 1 개) `open_scene` 시간 · `importReference` 시간 · 메모리(작업 관리자) | §7 · D7 · §12 병렬 수 | 파일당 1 분이면 6000 프레임 × 10 파일은 커피 두 잔 — 사용자에게 미리 말할 수 있어야 한다 |
| M0-8 | 레퍼런스 **안**에 정의된 세트(`CHN:Bake`) 가 `ls -type objectSet` 에 나오나 · `sets -q` 멤버가 long name 으로 오나 · 임포트 + ns 제거 뒤 이름 `Bake` 로 바뀌나 · 다른 세트 안에 든 `Bake` 도 같은 결과인가 | D6 · D8 | 규칙이 세트를 못 찾으면 전부 `no set` 으로 넘어간다 |
| M0-9 | 세트 멤버가 **조인트 하나(루트)** 일 때 `collect_export_nodes(joints_only=True)` 가 자손 조인트 전부 + non-joint 가지치기 결과 수 · 조인트 아래 그룹 안 조인트가 함께 빠지는 규칙(A00480 그대로) 이 아바타 리그에서 문제 없나 | D9 | 본이 빠지면 UE 스켈레톤이 깨진다 |
| M0-10 | `disableImplicitControl=True` 뒤 `Export Only` 와 같은 조건(베이크 없음)에서 컨스트레인트 조인트 FBX 에 애니가 없는지(경고 문구 근거) | D14 툴팁 | — |

---

## 9. 단계 (M1 ~ M7)

| 단계 | 내용 | 산출 · 검증 | 커밋 단위 |
|------|------|------------|-----------|
| **M0** | §8 실측 | §15 표 채움, 추정 → 사실 | 문서 커밋 |
| **M1** | Framework 승격 `core/maya_fbx.py`(`FBX_PLUGIN` · `ensure_fbx_plugin` · `fbx_options`(+`bake_complex_animation` 키) · `collect_export_nodes` · `get_unique_filepath` · `short_name` · `is_joint`) + A00480 두 모듈 재노출 + 문서 `docs/Framework_maya_fbx.md` | A00480 기존 mayapy 검증 스크립트 재실행(동작 동일) · `python -c "import Framework.core.maya_fbx"` Maya 밖 OK | `refactor(Framework)` |
| **M2** | 순수 모듈 `set_rules.py` · `export_naming.py` · `export_jobs.py` + 단위 테스트(python, Maya 없이) | 이름 규칙 24 케이스(§10-A) · 규칙 CRUD 12 · job 검사 6 | `feat(A00210)` ① |
| **M3** | 워커: `set_match.py` · `scene_probe.py` · `bake_export.py` · `maya_worker.py` 분기 · `ref_importer.import_loaded_references` 뽑기 · sys.path · `launch.spec` datas | mayapy 합성 씬 §10-B 전부 | `feat(A00210)` ② |
| **M4** | UI: `maya_file_picker.py` · `mayapy_bar.py` 뽑기(Reference 리팩터) · `export_table.py` · `set_rule_dialog.py` · `export_tab.py` · `maya_tab.py` · prefs 키 | 오프스크린(QApplication, 가짜 워커 = python 스크립트가 JUNMSG 를 찍음) §10-C · Reference 탭 기존 오프스크린 14 항목 그대로 통과 | `feat(A00210)` ③ |
| **M5** | 문서 `docs/A00210_FileManager.md` §4-E · 구조 트리 · CHANGELOG 01.41 · version.py · docs/README · WORKLOG · 포트폴리오 EN/KR 한 줄 · 메모리 `wip-a00210-maya-export-tab` + 이 계획서 진행표 | — | `docs(A00210)` |
| **M6** | **사용자 GUI 확인** — 실제 애니 파일 3 개(복사본) 로 Check Sets → Bake & Export → UE 임포트 | 결과를 §15 에 | 수정 커밋 |
| **M7 (v2)** | §12 — 병렬 워커 · 자원 선택 · (M0-5 가 좋으면) 청크 베이크 진행률 | 별도 계획서 | — |

---

## 10. 검증 목록

### A. 순수 파이썬 (Maya 없이, `python -I`)
- `export_naming`: `anim_01` + token(1,`bake`) → `anim_bake_01` · char(4,`_bake`) 동일 · token(0) 앞 · token(-1) 끝 · 토큰 수보다 큰 k 는 끝(clamped 노트) · 토큰 없는 이름(`anim`) · find/replace 전부 치환 · Case 토글 · 빈 text 는 그대로 · 금지 문자 → invalid · 두 파일이 같은 결과 → collision · out_dir 비면 원본 폴더 · 확장자 `.ma`/`.mb` 둘 다 `.fbx`.
- `set_rules`: 기본 폴더 생성 + `Bake` 기본 규칙 · save/load 왕복 · rename 이 파일 이름도 · delete 는 폴더 밖 경로 거부 · 깨진 json 은 errors · regex 틀리면 ValueError · 이름 금지 문자 sanitize.
- `export_jobs`: start > end 거부 · channels 비면 거부 · report 경로 형식.

### B. mayapy (합성 씬, `maya.standalone`)
1. `Bake` 최상위 세트 / 다른 세트 안 `Bake` / 레퍼런스 안 `CHN:Bake` / 세트 없음 → `probe.sets` 각각 1 · 1 · 1 · 0 (`ignore_namespace` false 면 레퍼런스 케이스 0).
2. `probe` 의 version · fps(`ntsc` → 30) · playback(2, 5000) · anim 값이 저장한 값과 같다. .ma · .mb 둘 다.
3. `export` 베이크: 컨스트레인트 체인 → 베이크 뒤 월드 행렬 50 프레임 샘플 == 베이크 전(1e-4) · FBX 재임포트 조인트 수 == kept · 키 범위 == (start, end) · 노드 이름에 `:` 없음(D7 ON).
4. `joints_only`: 조인트 아래 로케이터 · 메시가 FBX 에 없다. OFF 면 있다.
5. `Export Only`: 키가 직접 있는 체인은 키 그대로 · 컨스트레인트 체인은 애니 없음 + `[WARN]` 로그.
6. `existing`: skip 은 있는 파일을 두고 `skipped` · overwrite 는 mtime 갱신 · backup 은 `backup/<name>_01.fbx`.
7. 원본 .mb 의 mtime · 내용 해시가 **전후 동일**(저장 안 함).
8. 세트 없는 파일은 `skipped` 로 다음 파일 계속 · 깨진 파일(없는 경로) 은 `failed` 로 계속 · 취소 플래그를 1 번째 파일 뒤에 만들면 2 번째에서 멈춤 · `cancelled: true`.
9. 보고서 json 이 result 와 같다.
10. 워커 종료 코드 0 · 에러 경로에서도 `uninitialize` 뒤 종료.

### C. 오프스크린 UI (PySide6, 가짜 워커)
- 파일 담기 → 표 행 · Output 미리보기 즉시 · Naming 변경 → Output 갱신 · 충돌 두 행 빨강 + 버튼 막힘 · 규칙 New/Edit/Rename/Delete → 콤보 · prefs 저장 · Check Sets(가짜 probe 결과) → 열 채움 · 세트 없는 행 체크 해제 · Range 콤보 → Start/End 재채움 · 셀 편집 값이 job 에 들어감 · probe 전 Bake & Export 막힘 · Existing/옵션이 job 에 들어감 · mayapy 없음 안내 · Reference 탭 기존 동작(스캔 · 임포트 흐름) 변화 없음 · 창 최소 크기가 지금 A00210 창에서 늘지 않음(표는 Stretch, Naming 은 한 줄).

---

## 11. 위험 · 한계

| 위험 | 대응 |
|------|------|
| 6000 프레임 × 수십 본 베이크가 파일당 수 분 — 팝업이 멈춘 듯 보임 | D15 문구 + 경과 시간. M0-4 로 기대치를 문서에 적는다. v2 병렬 |
| 베이크 중 취소 불가 | 파일 경계 취소 + `cancel_grace_sec` 1800. 그래도 kill 되면 FBX 가 반쯤 쓰일 수 있다 → export 는 임시 이름(`<name>.fbx.part`) 으로 쓰고 끝나면 `os.replace` |
| `bakeResults` 가 애니 레이어 · HIK 리그에서 결과가 다름 | `simulation=True` · `bakeOnOverrideLayer=False` · `removeBakedAttributeFromLayer=False`. HIK 는 M6 실제 파일에서 본다 |
| 레퍼런스 임포트가 느리거나 실패(없는 파일) | 실패하면 그 파일 `failed`(저장 안 하니 피해 없음). 언로드 레퍼런스는 손대지 않는다 |
| 조인트 아래 그룹 안의 조인트가 `joints_only` 에 빠짐(A00480 규칙) | 로그 `pruned` 목록 + `Joints Only` 끄는 길. M0-9 로 실제 리그 확인 |
| 같은 출력 이름 → 덮어씀 | 표 충돌 검사로 실행 전에 막는다 |
| mayapy 가 파일보다 옛 버전 | `ignoreVersion` 으로 열지만 Version 열 경고 |
| 얼린 exe 에서 워커가 Framework 를 못 찾음 | spec `datas` + 워커 sys.path(A00560 과 동일) · 릴리즈 빌드 뒤 `mayapy worker job` 1 회 실행 확인 |

---

## 12. 범위 밖 · 후속 (v2)

### 12.1 하드웨어 선택 (R8) — 설계 방향

- **사실**: 조인트 베이크(`bakeResults`) 는 DG 평가라 **CPU 코어 하나**를 쓴다. mayapy 에는 뷰포트가 없어 GPU 는 쓰이지 않는다(GPU 오버라이드 디포머가 있어도 조인트 베이크엔 무관). 메모리는 프로세스마다 씬 하나(M0-7 실측치).
- **그래서 실효 수단** = **mayapy 워커 N 개 병렬**(파일을 N 묶음으로 나눠 각자 `export` 작업) + 프로세스 **CPU 친화도**(`psutil.Process.cpu_affinity` 또는 `start /affinity`). GPU 는 목록에 보이되 "not used by joint baking" 으로 표기.
- UI: `Resources` 줄 아래 `Workers [N ▾]`(1 ~ 물리 코어 수, 기본 1) · `CPU affinity [All ▾ | P-cores | 0-11 | ...]` · `RAM per worker ≈ <M0-7 값> GB → max N`. `Get-CimInstance Win32_Processor / Win32_VideoController / Win32_ComputerSystem` 1 회.
- 러너: `MOD_mayapyProcess_qt_v01.run_jobs(parent, mayapy, jobs, worker, ...)` — QProcess N 개, 진행률 = 전체 파일 수 기준 합산, 로그 앞에 `[W1]` 태그, Cancel 은 모든 플래그. 공용 러너 확장이므로 **별도 계획서**.

### 12.2 그 밖
- 청크 베이크로 베이크 **안** 진행률 · 취소(M0-5 가 동치일 때).
- `.ma` 머리글(`requires maya` · `currentUnit`) · 꼬리(`sceneConfigurationScriptNode` 의 `playbackOptions`) **텍스트 파싱**으로 mayapy 없이 빠른 진단 — v1 은 mayapy 한 길만(세트 멤버는 레퍼런스가 로드돼야 보여서 어차피 연다).
- fps 변환(파일 fps ≠ 출력 fps) · FBX 버전/ASCII 옵션 · 메시 · 블렌드셰이프 내보내기 · UE 임포트 설정 자동화 · 베이크 결과를 마야 파일로 저장.
- A00480 Export 탭(in-Maya) 과의 통합 — 다른 실행 환경(현재 씬 ↔ 디스크 파일) 이라 합치지 않는다.

---

## 13. 질문 (답이 없으면 권장안으로)

| # | 질문 | 권장 |
|---|------|------|
| Q1 | 규칙 폴더 기본 위치 — `~/.jun_filemanager/export_rules/`(A00210 prefs 옆, PC 별) 로 두고 `Rules Folder...` 로 NAS 등 공유 폴더를 가리킬 수 있게 하면 되나? 아니면 A00210 의 **데이터 리포**(git 동기화, records 옆) 에 넣어 Pull/Push 로 공유할까 | 권장 = 폴더 + 경로 변경. 데이터 리포 통합은 규칙이 늘어나면 |
| Q2 | 네임스페이스 — `Import References & Remove Namespaces` 기본 **ON** 이 맞나(UE 본 이름 `CHN:root` 방지). 레퍼런스를 그대로 두고 내보내야 하는 경우가 있나 | ON. M0-3 결과가 "FBX 가 ns 를 알아서 뗀다" 면 기본 OFF 로 바꾸고 보고 |
| Q3 | 범위 기본 = 타임라인(min/max). 애니메이션 범위(ast/aet) 나 "키가 있는 범위" 가 더 맞는 파일이 섞여 있나 | 타임라인 + 콤보 |
| Q4 | 세트 멤버가 **최상위 본** 하나일 때 `Joints Only` 기본 ON — 본 아래 매달린 메시 · 로케이터 · 컨스트레인트 노드를 FBX 에서 뺀다. 본 계층 안에 **그룹(transform) 밑 조인트**가 있는 리그인가(그렇다면 그 조인트가 함께 빠진다 → OFF 로 두거나 규칙을 바꿔야 한다) | ON. 사용자 리그 1 개를 M0-9 에서 본다 |
| Q5 | 같은 이름의 FBX 가 이미 있을 때 기본 — `Overwrite` | Overwrite |
| Q6 | 이름 규칙 기본값 `anim_01 → anim_bake_01`(token 1 뒤 `bake`) 로 두면 되나 | 예 |
| Q7 | `Export Only` 에 **베이크 없이도 `Import References & Remove Namespaces`** 를 적용하나 | 예(같은 옵션 공유) |
| Q8 | 보고서 json 을 출력 폴더에 남기는 것(`_bake_export_report_<시각>.json`) 이 UE 임포트 폴더를 더럽히나 | 남긴다. 거슬리면 `export_report_dir` 키로 다른 폴더 |
| Q9 | M6 GUI 확인용 **실제 애니 파일 3 개 경로**(복사해서 쓴다) 와 UE 프로젝트의 임포트 결과를 봐 줄 수 있나 | 필요 |

---

## 14. 진행표 (재개용 — 단계가 끝날 때마다 갱신)

| 단계 (§9) | 상태 | 커밋 | 메모 |
|-----------|------|------|------|
| 계획서 | **완료** | 이 문서 | §13 답 대기 |
| M0 실측 | 대기 | | §15 에 기록 |
| M1 Framework `maya_fbx` | 대기 | | |
| M2 순수 모듈 | 대기 | | |
| M3 워커 | 대기 | | |
| M4 UI | 대기 | | |
| M5 문서 | 대기 | | |
| M6 사용자 GUI 확인 | 대기 | | |
| M7 (v2) 병렬 · 자원 | 미착수 | | 별도 계획서 |

---

## 15. M0 실측 결과 (채울 자리)

| # | 결과 | 설계에 반영 |
|---|------|------------|
| M0-1 | | |
| M0-2 | | |
| M0-3 | | |
| M0-4 | | |
| M0-5 | | |
| M0-6 | | |
| M0-7 | | |
| M0-8 | | |
| M0-9 | | |
| M0-10 | | |
