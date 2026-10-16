# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-16
# A00480_FileTool - Import > CSV 로직 (ARKit 페이셜 CSV -> 키프레임, 오디오)
"""
csv_ops - Live Link Face 가 내보낸 ARKit 페이셜 CSV 를 노드의 키프레임으로 임포트한다 (v01.10).

`A00200_CSV_tool/arkit_facial_import.py` 를 옮긴 것이다 (원본은 보존). 옮기며 달라진 것:

  1. 로그는 전부 영어 (원본은 한국어).
  2. 키를 받는 노드가 **블렌드셰이프만이 아니다** - CSV 열 이름과 같은 이름의 어트리뷰트를 가진
     노드라면 무엇이든 된다 (예: ARKit 52 어트리뷰트를 단 페이셜 컨트롤). 블렌드셰이프는 weight 별칭을,
     그 밖의 노드는 스칼라 어트리뷰트를 `node_targets` 가 { 소문자 이름: 플러그 } 로 모은다.
     후보 노드 탐색(`list_candidate_nodes`)도 블렌드셰이프 + ARKit 이름 어트리뷰트를 가진 노드 전부.
  3. 결과는 summary dict + 로그 콜백 - UI 는 로그창에 쌓기만 한다.
  4. (v01.11) Value Scale - CSV 값에 곱해서 키를 건다 (`import_facial(value_scale=)`).

동작 (원본 그대로)
  - CSV 열 <-> 어트리뷰트 이름을 대소문자 무시로 매칭 (열 순서 무관). 메타 열(Timecode 등)은 건너뛴다.
  - 녹화 FPS(Source) / 출력 FPS(Target) 분리 - step = round(source / target) 으로 다운샘플, 씬 FPS 를 Target 으로.
  - 헤드/눈 회전 열처럼 매칭 안 되는 열은 리포트만.
  - CSV 와 같은 stem(`_raw` 를 뗀 stem 포함)의 WAV 를 씬 사운드로, 없으면 같은 stem 의 동영상에서 ffmpeg 로 추출.
  - setKeyframe(time=, value=) 로 시간을 직접 지정 (currentTime 미사용). 한 번의 undo.
"""

import os
import csv
import shutil
import subprocess
from collections import OrderedDict

from Framework.core.maya_undo import undo_chunk


def _cmds():
    import maya.cmds as cmds
    return cmds


# ---------------------------------------------------------------------------
# 상수
# ---------------------------------------------------------------------------

#: ARKit 표준 52개 블렌드셰이프 이름 (소문자). 후보 노드 점수 매기기 기준.
ARKIT_NAMES = frozenset({
    "eyeblinkleft", "eyelookdownleft", "eyelookinleft", "eyelookoutleft",
    "eyelookupleft", "eyesquintleft", "eyewideleft",
    "eyeblinkright", "eyelookdownright", "eyelookinright", "eyelookoutright",
    "eyelookupright", "eyesquintright", "eyewideright",
    "jawforward", "jawleft", "jawright", "jawopen",
    "mouthclose", "mouthfunnel", "mouthpucker", "mouthleft", "mouthright",
    "mouthsmileleft", "mouthsmileright", "mouthfrownleft", "mouthfrownright",
    "mouthdimpleleft", "mouthdimpleright", "mouthstretchleft", "mouthstretchright",
    "mouthrolllower", "mouthrollupper", "mouthshruglower", "mouthshrugupper",
    "mouthpressleft", "mouthpressright", "mouthlowerdownleft", "mouthlowerdownright",
    "mouthupperupleft", "mouthupperupright",
    "browdownleft", "browdownright", "browinnerup",
    "browouterupleft", "browouterupright",
    "cheekpuff", "cheeksquintleft", "cheeksquintright",
    "nosesneerleft", "nosesneerright", "tongueout",
})

#: 후보 노드를 찾을 때 `ls("*.<name>")` 로 찔러 볼 어트리뷰트 이름 (대표 몇 개 - 52개 전부 돌 필요 없다).
PROBE_ATTRS = ("jawOpen", "eyeBlinkLeft", "mouthSmileLeft", "browInnerUp", "cheekPuff")

#: CSV 에서 어트리뷰트 매칭 대상이 아닌 메타 열 (리포트의 '건너뜀'에서도 제외)
META_COLS = frozenset({"timecode", "blendshapecount", "frame", "time"})

#: WAV 가 없을 때 추출 대상으로 볼 동영상 확장자
VIDEO_EXTS = (".mov", ".mp4", ".m4v", ".mkv", ".avi", ".mxf", ".webm")

#: CSV stem 에서 떼고 동영상/WAV 와 매칭할 접미사. '..._Face_raw.csv' 와 '..._Face.mov' 를 같은 클립으로 본다.
STEM_STRIP_SUFFIXES = ("_raw",)

#: 정수 FPS -> Maya time unit
FPS_UNIT = {15: "game", 24: "film", 25: "pal", 30: "ntsc",
            48: "show", 50: "palf", 60: "ntscf"}

#: Target FPS 콤보 항목
TARGET_FPS_CHOICES = (30, 60)

# Windows 에서 subprocess 콘솔창 숨김
_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0


# ---------------------------------------------------------------------------
# 노드 -> 키를 받을 플러그
# ---------------------------------------------------------------------------

def is_blendshape(node):
    cmds = _cmds()
    try:
        return cmds.nodeType(node) == "blendShape"
    except Exception:
        return False


def blendshape_targets(bs_node):
    """블렌드셰이프 노드의 weight 별칭을 { 소문자이름: 'node.alias' } 로."""
    cmds = _cmds()
    targets = OrderedDict()
    aliases = cmds.aliasAttr(bs_node, q=True) or []
    # aliases = [alias0, plug0, alias1, plug1, ...]
    for i in range(0, len(aliases) - 1, 2):
        alias, plug = aliases[i], aliases[i + 1]
        if plug.startswith("weight"):
            targets[alias.lower()] = "{0}.{1}".format(bs_node, alias)
    return targets


def attribute_targets(node):
    """일반 노드의 **스칼라 어트리뷰트**를 { 소문자이름: 'node.attr' } 로 (v01.10).

    사용자 정의 어트리뷰트가 먼저, 그다음 나머지 스칼라(translateX 같은 기본 채널 포함 - CSV 열과
    이름이 같을 때만 쓰이므로 해가 없다). 별칭(aliasAttr)도 listAttr 에 나오므로 함께 잡힌다.
    """
    cmds = _cmds()
    targets = OrderedDict()
    user = cmds.listAttr(node, userDefined=True, scalar=True) or []
    rest = cmds.listAttr(node, scalar=True) or []
    for attr in list(user) + [a for a in rest if a not in user]:
        if "." in attr or "[" in attr:
            continue                                   # 컴파운드 자식 · 멀티 원소는 뺀다
        key = attr.lower()
        if key not in targets:
            targets[key] = "{0}.{1}".format(node, attr)
    return targets


def node_targets(node):
    """노드가 받을 수 있는 플러그 { 소문자이름: 플러그 }. 블렌드셰이프는 weight 별칭, 그 밖은 스칼라 어트리뷰트."""
    if is_blendshape(node):
        targets = blendshape_targets(node)
        if targets:
            return targets
    return attribute_targets(node)


def score_node(node):
    """노드의 플러그 이름 중 ARKit 52 이름과 일치하는 개수."""
    return len(set(node_targets(node).keys()) & ARKIT_NAMES)


def list_candidate_nodes():
    """키를 받을 후보 노드 - 모든 블렌드셰이프 + ARKit 이름 어트리뷰트를 가진 노드 (첫 등장 순서, 중복 없음).

    블렌드셰이프가 아닌 노드는 PROBE_ATTRS 로 `ls("*.jawOpen")` 처럼 찔러 찾는다 (씬 전체 listAttr 보다 싸다).
    네임스페이스 안의 노드도 잡도록 recursive.
    """
    cmds = _cmds()
    found = []
    for node in cmds.ls(type="blendShape") or []:
        if node not in found:
            found.append(node)
    for attr in PROBE_ATTRS:
        try:
            plugs = cmds.ls("*.{0}".format(attr), recursive=True) or []
        except Exception:
            plugs = []
        for plug in plugs:
            node = plug.split(".", 1)[0]
            if node not in found:
                found.append(node)
    return found


def detect_best_node(nodes=None):
    """ARKit 이름을 가장 많이 가진 노드. 없으면 None."""
    nodes = nodes if nodes is not None else list_candidate_nodes()
    best, best_score = None, 0
    for node in nodes:
        score = score_node(node)
        if score > best_score:
            best, best_score = node, score
    return best


# ---------------------------------------------------------------------------
# ffmpeg / 오디오
# ---------------------------------------------------------------------------

def find_ffmpeg():
    """ffmpeg / ffprobe 경로 (시스템 PATH). 번들 exe 로 바꾸려면 여기만 고친다."""
    return shutil.which("ffmpeg"), shutil.which("ffprobe")


def _has_audio_stream(ffprobe, src):
    """ffprobe 로 오디오 스트림 유무. ffprobe 가 없으면 True (ffmpeg 가 판단)."""
    if not ffprobe:
        return True
    try:
        out = subprocess.run(
            [ffprobe, "-v", "error", "-select_streams", "a",
             "-show_entries", "stream=index", "-of", "csv=p=0", src],
            capture_output=True, text=True, creationflags=_NO_WINDOW)
        return bool(out.stdout.strip())
    except OSError:
        return True


def _extract_wav(ffmpeg, src, dst, overwrite):
    """ffmpeg 로 동영상에서 WAV(PCM 16bit) 추출. 성공하면 True."""
    cmd = [ffmpeg, "-y" if overwrite else "-n", "-i", src,
           "-vn", "-map", "0:a:0", "-c:a", "pcm_s16le", dst]
    proc = subprocess.run(cmd, capture_output=True, text=True, creationflags=_NO_WINDOW)
    return proc.returncode == 0


def candidate_stems(csv_path):
    """CSV 경로의 매칭용 stem 후보 - 원본 stem 과 STEM_STRIP_SUFFIXES 를 뗀 stem."""
    stem = os.path.splitext(csv_path)[0]
    stems = [stem]
    dirp, base = os.path.dirname(stem), os.path.basename(stem)
    low = base.lower()
    for suffix in STEM_STRIP_SUFFIXES:
        if low.endswith(suffix) and len(base) > len(suffix):
            stripped = os.path.join(dirp, base[:-len(suffix)])
            if stripped not in stems:
                stems.append(stripped)
    return stems


def resolve_audio(csv_path, overwrite, log):
    """CSV 와 같은 stem 의 WAV 경로. 없으면 동영상에서 추출. 못 찾으면 None."""
    stems = candidate_stems(csv_path)

    # 1) 기존 WAV (덮어쓰기가 아닐 때)
    if not overwrite:
        for stem in stems:
            wav = stem + ".wav"
            if os.path.exists(wav):
                log("Audio : using existing WAV -> {0}".format(os.path.basename(wav)))
                return wav

    # 2) 동영상에서 추출
    for stem in stems:
        video = next((stem + ext for ext in VIDEO_EXTS if os.path.exists(stem + ext)), None)
        if not video:
            continue
        wav = stem + ".wav"
        ffmpeg, ffprobe = find_ffmpeg()
        if not ffmpeg:
            log("Audio : ffmpeg not found on PATH -> audio skipped")
            return wav if os.path.exists(wav) else None
        if not _has_audio_stream(ffprobe, video):
            log("Audio : no audio stream in {0} -> skipped".format(os.path.basename(video)))
            return None
        if _extract_wav(ffmpeg, video, wav, overwrite):
            log("Audio : extracted {0} -> {1}".format(
                os.path.basename(video), os.path.basename(wav)))
            return wav
        log("Audio : ffmpeg extraction failed ({0})".format(os.path.basename(video)))
        return wav if os.path.exists(wav) else None

    # 3) 덮어쓰기였지만 동영상이 없다 - 기존 WAV
    for stem in stems:
        wav = stem + ".wav"
        if os.path.exists(wav):
            log("Audio : using existing WAV -> {0}".format(os.path.basename(wav)))
            return wav

    log("Audio : no WAV or video next to the CSV -> skipped")
    return None


def extend_timeline(start, end, log):
    """타임슬라이더 in/out 과 애니메이션 범위를 임포트 구간만큼 넓힌다 (줄이지 않는다)."""
    cmds = _cmds()
    try:
        new_min = min(cmds.playbackOptions(q=True, minTime=True), start)
        new_max = max(cmds.playbackOptions(q=True, maxTime=True), end)
        anim_min = min(cmds.playbackOptions(q=True, animationStartTime=True), new_min)
        anim_max = max(cmds.playbackOptions(q=True, animationEndTime=True), new_max)
        cmds.playbackOptions(animationStartTime=anim_min, animationEndTime=anim_max,
                             minTime=new_min, maxTime=new_max)
        log("Timeline extended : {0} ~ {1}".format(int(new_min), int(new_max)))
    except Exception as e:
        log("Timeline not extended (ignored) : {0}".format(e))


def import_audio(wav_path, offset_frame, log):
    """WAV 를 씬 사운드로 임포트하고 타임슬라이더에 표시. 반환: sound 노드."""
    cmds = _cmds()
    import maya.mel as mel
    snd = cmds.sound(file=wav_path.replace("\\", "/"), offset=offset_frame)
    try:
        slider = mel.eval("$tmpVar=$gPlayBackSlider")
        cmds.timeControl(slider, e=True, sound=snd, displaySound=True)
    except Exception as e:                      # 타임슬라이더 표시 실패해도 사운드 노드는 유지
        log("Audio : could not show on the time slider (ignored) : {0}".format(e))
    log("Audio : sound node '{0}' (offset {1})".format(snd, offset_frame))
    return snd


# ---------------------------------------------------------------------------
# CSV -> 키프레임
# ---------------------------------------------------------------------------

def read_csv_header(csv_path):
    """CSV 헤더 열 이름 목록 (미리보기 · 매칭 확인용). 없으면 []."""
    with open(csv_path, "r", newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        for row in reader:
            return [c.strip() for c in row]
    return []


def match_columns(columns, targets):
    """CSV 열 -> 플러그 (대소문자 무시). 반환 (OrderedDict{col: plug}, [매칭 안 된 열])."""
    col_to_plug = OrderedDict()
    unmatched = []
    for col in columns:
        lc = col.strip().lower()
        if lc in META_COLS:
            continue
        plug = targets.get(lc)
        if plug:
            col_to_plug[col] = plug
        else:
            unmatched.append(col)
    return col_to_plug, unmatched


def import_facial(csv_path, node, start_frame=1, source_fps=60, target_fps=30,
                  do_audio=True, overwrite_wav=False, value_scale=1.0, log=None):
    """ARKit CSV 를 node 의 키프레임으로 임포트한다. 반환: summary dict.

    node : 블렌드셰이프 노드 또는 CSV 열과 같은 이름의 어트리뷰트를 가진 아무 노드.
    value_scale : 키 값 = CSV 값 x value_scale (v01.11). CSV 는 [0, 1] 이라, [0, 10] 을 받는
                  AdvancedSkeleton 페이셜 컨트롤에는 10. 기본 1.0 = 그대로.
    """
    cmds = _cmds()
    if log is None:
        log = lambda m: None

    if not csv_path or not os.path.exists(csv_path):
        raise IOError("CSV file not found : {0}".format(csv_path))
    if not node or not cmds.objExists(node):
        raise ValueError("Node not found : {0}".format(node))

    targets = node_targets(node)
    if not targets:
        raise ValueError("'{0}' has no attribute to key.".format(node))
    log("Node : {0} ({1}, {2} attribute(s), {3} ARKit)".format(
        node, "blendShape" if is_blendshape(node) else cmds.nodeType(node),
        len(targets), len(set(targets) & ARKIT_NAMES)))

    # 출력 FPS -> 씬 FPS
    unit = FPS_UNIT.get(int(target_fps), "{0}fps".format(int(target_fps)))
    try:
        cmds.currentUnit(time=unit)
        log("Scene FPS : {0} ({1})".format(target_fps, unit))
    except RuntimeError:
        log("Scene FPS not changed (unit '{0}' refused) - scene default kept".format(unit))

    value_scale = float(value_scale)
    if value_scale != 1.0:
        log("Value scale : x{0:g} (key = CSV value x {0:g})".format(value_scale))

    step = max(1, int(round(float(source_fps) / float(target_fps))))
    log("Downsample step {0} (recorded {1} fps -> output {2} fps)".format(
        step, source_fps, target_fps))

    with open(csv_path, "r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise IOError("CSV has no header row.")

        col_to_plug, unmatched = match_columns(reader.fieldnames, targets)
        if not col_to_plug:
            raise ValueError("No CSV column matches an attribute of '{0}'. "
                             "Check the node.".format(node))

        applied = set()
        bad_values = 0
        out_frame = start_frame
        kept = 0
        audio_node = None

        # 키 · 타임라인 · 사운드 노드를 **한 번의 undo** 로 (playbackOptions 도 undo 항목이라 밖에 두면
        # 첫 undo 가 타임라인만 되돌린다 - 원본은 키만 묶었다).
        with undo_chunk():
            for i, row in enumerate(reader):
                if i % step != 0:                 # 다운샘플 - step 간격만 남긴다
                    continue
                for col, plug in col_to_plug.items():
                    raw = row.get(col, "")
                    if raw is None or raw.strip() == "":
                        continue
                    try:
                        value = float(raw) * value_scale
                    except ValueError:
                        bad_values += 1
                        continue
                    cmds.setKeyframe(plug, time=out_frame, value=value)
                    applied.add(col)
                out_frame += 1
                kept += 1

            end_frame = start_frame + kept - 1 if kept else start_frame
            if kept:
                extend_timeline(start_frame, end_frame, log)

            if do_audio:
                wav = resolve_audio(csv_path, overwrite_wav, log)
                if wav:
                    try:
                        audio_node = import_audio(wav, start_frame, log)
                    except Exception as e:
                        log("Audio : import failed (ignored) : {0}".format(e))

    return {
        "node": node,
        "frames": kept,
        "start_frame": start_frame,
        "end_frame": end_frame,
        "applied": sorted(applied),
        "unmatched_cols": unmatched,
        "bad_values": bad_values,
        "audio_node": audio_node,
        "value_scale": value_scale,
    }


def summary_lines(summary):
    """summary dict -> 로그 줄들 (UI 공용)."""
    lines = ["[OK] CSV import : {0} frame(s) ({1} ~ {2}), {3} attribute(s) keyed on {4}".format(
        summary["frames"], summary["start_frame"], summary["end_frame"],
        len(summary["applied"]), summary["node"])]
    scale = summary.get("value_scale", 1.0)
    if scale != 1.0:
        lines.append("       values scaled x{0:g}".format(scale))
    if summary["unmatched_cols"]:
        lines.append("       unmatched (skipped) {0} : {1}".format(
            len(summary["unmatched_cols"]), ", ".join(summary["unmatched_cols"])))
    if summary["bad_values"]:
        lines.append("       {0} value(s) were not numbers - skipped".format(summary["bad_values"]))
    if summary["audio_node"]:
        lines.append("       audio : {0}".format(summary["audio_node"]))
    return lines
