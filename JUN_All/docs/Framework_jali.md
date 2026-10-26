# Framework/jali — JALI 립싱크 공용 코어

`A00540_JaliLipSync` 의 `app/core` 를 2026-10-26 에 공용으로 올린 것. **`A00540`(마야 안에서 바로 키) · `A00560_JaliBatch`(mayapy 워커로
클립 N 개) · `A00570_JaliReview`(검수)** 가 같은 코드를 쓴다. 릴리즈본은 툴 간 import 금지([Release_Layout](Release_Layout.md))라
Framework 에 두어야 세 툴의 릴리즈에 모두 동봉된다. A00540 의 `app/core/*.py` 는 얇은 재노출이다(tests 132 그대로 통과).

| 모듈 | 의존 | 내용 |
|------|------|------|
| `lipsync_data.py` | 순수 파이썬 | VisemeNet 결과 `<name>.txt`(22열 · 100fps) + `.visemenet.json` 읽기 · 검증, `find_wav()`, `wav_seconds()` |
| `mapping.py` | 순수 파이썬 | `mappings/<이름>.json` 읽기 · 검증 (`nodes` 역할표 · `viseme_scale` · `jali{scale, range, fixed_default}` · `targets`), `combine()`. **매핑 json 은 이 폴더에** (`angela_jali_visemenet` · `jali_slider_dummy_in`) |
| `sequence.py` | 순수 파이썬 | `Clip` · `layout(clips, start, hold, fps)` → `[Segment]`(클립 길이는 wav) · `write_sequence_wav()` |
| `time_units.py` | 순수 파이썬 | fps ↔ 마야 시간 단위 이름 (`30 = ntsc`) — standalone 과 in-Maya 가 같은 표 |
| `clip_manifest.py` | 순수 파이썬 | 클립 폴더의 `jali_clips.manifest.json` (A00560 이 쓰고 A00570 이 읽는다): 설정 + 클립마다 start · end · frames · status(generated / edited / failed) |
| `keyer.py` | maya.cmds | `resolve_targets`(Auto 네임스페이스 / Manual node_map) · `sample` · `check_targets` · `apply_sequence` · `apply` · `remove` (undo 한 번) |
| `scene.py` | maya.cmds | `marker_of(mapping)` · `find_rigs()` · `attach_sound()` |
| `bake.py` | maya.cmds | JUN_JALI `bake_ctl_keys` 이식 — DUMMY_IN 의 키를 컨트롤러 채널로 복사(`copy`) 또는 `bakeResults`, `cleanup_dummy_in()` · `rename_curves()`(`JALI_<ctl>_<attr>`) · `baked_channels()` (레퍼런스된 컨트롤러에서도 동작) |
| `clip_stamp.py` | 파싱은 순수 / 쓰기 · 읽기는 cmds | 클립 `.mb` 의 fileInfo `jun_jali_clip`(컨트롤러 경로 · mtime · 매핑 · fps · start · end · frames · keys · 시각 · 툴), `controller_changed()` |

standalone(A00560 UI 프로세스)은 **순수 파이썬 모듈만** import 한다 — maya.cmds 모듈은 import 자체에 마야가 필요하다.

## mayapy 러너 (같은 날 승격, A00210 에서)

| 모듈 | 내용 |
|------|------|
| `Framework/core/mayapy_runner.py` | mayapy 찾기(`candidates` · `find_mayapy`), `write_job`, `command(mayapy, job, worker)`, 프로토콜 `JUNMSG {json}` 파싱, 워커용 `emit_log` · `emit_progress`. **워커 스크립트 경로는 툴이 넘긴다** |
| `Framework/qt/MOD_mayapyProcess_qt_v01.py` | `run_job(parent, mayapy, job, worker, title, message, log)` — QProcess + 공용 진행률 팝업 + Cancel(플래그 파일, 작업 단위 경계에서 멈춤, 120 초 뒤 kill) |

A00210 의 `app/maya/core/mayapy_runner.py` · `ui/mayapy_process.py` 는 자기 워커(`maya_worker.py`) 경로를 채워 넘기는 재노출이다.
워커 규약: `maya.standalone.initialize` 뒤 **모든 경로에서 `uninitialize` → `os._exit(code)`**, stdout 은 `-u`.

## 쓰는 법 (A00560 워커의 클립 한 개)

```python
from Framework.jali import keyer, lipsync_data, sequence, mapping, bake, clip_stamp
cmds.currentUnit(time="ntsc")                                   # fps 먼저 (keyer 는 씬 fps 로 샘플)
cmds.file(controller, reference=True, namespace="JALI")
data = lipsync_data.load(txt); seg = sequence.layout([sequence.Clip(txt, data, wav)], start, 0, 30.0)[0]
keyer.apply_sequence([seg], mapping.load_mapping("jali_slider_dummy_in"), "JALI:")
baked = bake.bake_ctl_keys(nodes=bake.controllers("JALI:"), mode="copy"); bake.cleanup_dummy_in("JALI:"); bake.rename_curves(baked)
clip_stamp.write(clip_stamp.make(wav, txt, controller, "jali_slider_dummy_in", 30.0, seg.start, seg.end, seg.key_frames, keys, tool))
```

관련 문서: [A00540_JaliLipSync](A00540_JaliLipSync.md) · [A00560_JaliBatch](A00560_JaliBatch.md) · [A00570_JaliReview](A00570_JaliReview.md) ·
JUN_JALI `docs/0090_jali_slider_ctl_plan.md`(컨트롤러 구조 · 원본 `bake_ctl_keys`).
