"""
ARKit Facial Import for Maya
============================

Live Link Face 앱이 export 한 ARKit 페이셜 CSV를 Maya 리그의 블렌드셰이프
weight 키프레임 애니메이션으로 임포트하고, 같은 이름의 WAV(또는 MOV에서 추출)를
씬 사운드로 함께 임포트한다.

지침: maya_arkit_converter/GUIDELINES.md (v3)

주요 동작
  - 블렌드셰이프 노드 자동탐지 + 드롭다운 선택 (노드명 하드코딩 금지)
  - CSV 열 ↔ weight 별칭 이름을 대소문자 무시로 매칭 (열 순서 무관)
  - 녹화 FPS(Source) / 출력 FPS(Target) 분리, 30 선택 시 다운샘플 + 씬 FPS 변경
  - 헤드/눈 회전 열은 무시(리포트만)
  - CSV와 같은 stem의 WAV 임포트, 없으면 같은 stem의 MOV 등에서 ffmpeg로 추출
  - setKeyframe(time=, value=) 로 시간 직접 지정 (currentTime 미사용)

실행 (Maya Script Editor, Python):
  import arkit_facial_import
  arkit_facial_import.show()
"""

import os
import csv
import shutil
import subprocess
from collections import OrderedDict

import maya.cmds as cmds
import maya.mel as mel
import maya.OpenMayaUI as omui

# PySide2(2022~2024) / PySide6(2025+) 양쪽 지원
try:
    from PySide2 import QtWidgets, QtCore
    from shiboken2 import wrapInstance
except ImportError:
    from PySide6 import QtWidgets, QtCore
    from shiboken6 import wrapInstance


# ---------------------------------------------------------------------------
# 상수
# ---------------------------------------------------------------------------

# ARKit 표준 52개 블렌드셰이프 이름 (소문자). 노드 자동탐지·매칭 기준.
ARKIT_NAMES = {
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
}

# CSV에서 블렌드셰이프 매칭 대상이 아닌 메타 열 (리포트의 '건너뜀'에서도 제외)
META_COLS = {"timecode", "blendshapecount", "frame", "time"}

# WAV가 없을 때 추출 대상으로 볼 동영상 확장자
VIDEO_EXTS = (".mov", ".mp4", ".m4v", ".mkv", ".avi", ".mxf", ".webm")

# CSV stem에서 떼고 동영상/WAV와 매칭할 접미사. 예: 'DHA_..._Face_raw.csv'(CSV)
# 와 'DHA_..._Face.mov'(동영상)를 같은 클립으로 본다.
STEM_STRIP_SUFFIXES = ("_raw",)

# 정수 FPS -> Maya time unit
FPS_UNIT = {15: "game", 24: "film", 25: "pal", 30: "ntsc",
            48: "show", 50: "palf", 60: "ntscf"}

# Windows에서 subprocess 콘솔창 숨김
_NO_WINDOW = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0


# ---------------------------------------------------------------------------
# 블렌드셰이프 노드 탐색 / 타깃 매핑
# ---------------------------------------------------------------------------

def get_blendshape_targets(bs_node):
    """블렌드셰이프 노드의 weight 별칭을 { 소문자이름: 'node.alias' } 로 반환."""
    targets = OrderedDict()
    aliases = cmds.aliasAttr(bs_node, q=True) or []
    # aliases = [alias0, plug0, alias1, plug1, ...]
    for i in range(0, len(aliases) - 1, 2):
        alias, plug = aliases[i], aliases[i + 1]
        if plug.startswith("weight"):
            targets[alias.lower()] = "{0}.{1}".format(bs_node, alias)
    return targets


def list_blendshape_nodes():
    return cmds.ls(type="blendShape") or []


def score_node(bs_node):
    """노드의 weight 별칭 중 ARKit 이름과 일치하는 개수."""
    return len(set(get_blendshape_targets(bs_node).keys()) & ARKIT_NAMES)


def detect_best_node(nodes=None):
    """ARKit 이름을 가장 많이 가진 블렌드셰이프 노드를 반환. 없으면 None."""
    nodes = nodes if nodes is not None else list_blendshape_nodes()
    best, best_score = None, 0
    for n in nodes:
        s = score_node(n)
        if s > best_score:
            best, best_score = n, s
    return best


# ---------------------------------------------------------------------------
# ffmpeg / 오디오
# ---------------------------------------------------------------------------

def find_ffmpeg():
    """ffmpeg / ffprobe 경로를 반환. 탐색 = 시스템 PATH (지침 v3).

    번들 exe·UI 경로 지정으로 확장하려면 이 함수만 수정하면 된다.
    """
    return shutil.which("ffmpeg"), shutil.which("ffprobe")


def _has_audio_stream(ffprobe, src):
    """ffprobe로 오디오 스트림 유무 확인. ffprobe 없으면 True(ffmpeg가 판단)."""
    if not ffprobe:
        return True
    try:
        out = subprocess.run(
            [ffprobe, "-v", "error", "-select_streams", "a",
             "-show_entries", "stream=index", "-of", "csv=p=0", src],
            capture_output=True, text=True, creationflags=_NO_WINDOW,
        )
        return bool(out.stdout.strip())
    except OSError:
        return True


def _extract_wav(ffmpeg, src, dst, overwrite):
    """ffmpeg로 동영상에서 WAV(PCM 16bit) 추출. 성공하면 True."""
    cmd = [
        ffmpeg, "-y" if overwrite else "-n", "-i", src,
        "-vn", "-map", "0:a:0", "-c:a", "pcm_s16le", dst,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True,
                          creationflags=_NO_WINDOW)
    return proc.returncode == 0


def _candidate_stems(csv_path):
    """CSV 경로에서 매칭에 쓸 후보 stem 목록을 만든다.

    원본 stem과, STEM_STRIP_SUFFIXES(예: '_raw')를 떼어낸 stem을 함께 반환.
    예: '..._Face_raw.csv' -> ['..._Face_raw', '..._Face']
    """
    stem = os.path.splitext(csv_path)[0]
    stems = [stem]
    dirp, base = os.path.dirname(stem), os.path.basename(stem)
    low = base.lower()
    for suf in STEM_STRIP_SUFFIXES:
        if low.endswith(suf) and len(base) > len(suf):
            stripped = os.path.join(dirp, base[:-len(suf)])
            if stripped not in stems:
                stems.append(stripped)
    return stems


def resolve_audio(csv_path, overwrite, log):
    """CSV와 같은 stem(또는 _raw 제거 stem)의 WAV를 반환. 없으면 동영상에서 추출.

    반환: WAV 절대경로(str) 또는 None.
    """
    stems = _candidate_stems(csv_path)

    # 1) 기존 WAV (덮어쓰기 아닐 때) - 후보 stem 순서대로
    if not overwrite:
        for stem in stems:
            wav = stem + ".wav"
            if os.path.exists(wav):
                log("오디오: 기존 WAV 사용 -> {0}".format(os.path.basename(wav)))
                return wav

    # 2) 후보 stem의 동영상에서 추출
    for stem in stems:
        video = next((stem + ext for ext in VIDEO_EXTS
                      if os.path.exists(stem + ext)), None)
        if not video:
            continue
        wav = stem + ".wav"          # 동영상 stem 기준으로 WAV 생성
        ffmpeg, ffprobe = find_ffmpeg()
        if not ffmpeg:
            log("오디오: ffmpeg 를 PATH에서 못 찾음 -> 오디오 건너뜀")
            return wav if os.path.exists(wav) else None
        if not _has_audio_stream(ffprobe, video):
            log("오디오: 동영상에 오디오 스트림 없음 -> 건너뜀 ({0})"
                .format(os.path.basename(video)))
            return None
        if _extract_wav(ffmpeg, video, wav, overwrite):
            log("오디오: {0} 에서 추출 -> {1}".format(
                os.path.basename(video), os.path.basename(wav)))
            return wav
        log("오디오: ffmpeg 추출 실패 ({0})".format(os.path.basename(video)))
        return wav if os.path.exists(wav) else None

    # 3) overwrite 였지만 동영상이 없는 경우 - 기존 WAV 사용
    for stem in stems:
        wav = stem + ".wav"
        if os.path.exists(wav):
            log("오디오: 기존 WAV 사용 -> {0}".format(os.path.basename(wav)))
            return wav

    log("오디오: WAV·동영상 모두 없음 -> 건너뜀")
    return None


def extend_timeline(start, end, log):
    """타임슬라이더 in/out 및 애니메이션 범위를 임포트 구간만큼 확장(줄이지 않음)."""
    try:
        new_min = min(cmds.playbackOptions(q=True, minTime=True), start)
        new_max = max(cmds.playbackOptions(q=True, maxTime=True), end)
        anim_min = min(cmds.playbackOptions(q=True, animationStartTime=True), new_min)
        anim_max = max(cmds.playbackOptions(q=True, animationEndTime=True), new_max)
        cmds.playbackOptions(animationStartTime=anim_min, animationEndTime=anim_max,
                             minTime=new_min, maxTime=new_max)
        log("타임라인 in/out 확장: {0} ~ {1}".format(int(new_min), int(new_max)))
    except Exception as e:
        log("타임라인 확장 실패 (무시): {0}".format(e))


def import_audio(wav_path, offset_frame, log):
    """WAV를 씬 사운드로 임포트하고 타임슬라이더에 표시."""
    wav_fwd = wav_path.replace("\\", "/")
    snd = cmds.sound(file=wav_fwd, offset=offset_frame)
    try:
        slider = mel.eval('$tmpVar=$gPlayBackSlider')
        cmds.timeControl(slider, e=True, sound=snd, displaySound=True)
    except Exception as e:  # 타임슬라이더 표시는 실패해도 사운드 노드는 유지
        log("오디오: 타임슬라이더 표시 실패 (무시): {0}".format(e))
    log("오디오: 사운드 노드 생성 '{0}' (offset={1})".format(snd, offset_frame))
    return snd


# ---------------------------------------------------------------------------
# CSV -> 블렌드셰이프 임포트
# ---------------------------------------------------------------------------

def import_facial(csv_path, bs_node, start_frame=1,
                  source_fps=60, target_fps=30,
                  do_audio=True, overwrite_wav=False, log=None):
    """ARKit CSV를 블렌드셰이프 키프레임으로 임포트한다.

    반환: 결과 요약 dict.
    """
    if log is None:
        log = lambda m: None

    if not os.path.exists(csv_path):
        raise IOError("CSV 파일을 찾을 수 없습니다: {0}".format(csv_path))
    if not bs_node or not cmds.objExists(bs_node):
        raise ValueError("블렌드셰이프 노드를 찾을 수 없습니다: {0}".format(bs_node))

    targets = get_blendshape_targets(bs_node)
    if not targets:
        raise ValueError("'{0}' 에 weight 별칭이 없습니다.".format(bs_node))

    # 출력 FPS -> 씬 FPS 변경
    unit = FPS_UNIT.get(int(target_fps), "{0}fps".format(int(target_fps)))
    try:
        cmds.currentUnit(time=unit)
        log("씬 FPS 설정: {0}fps ({1})".format(target_fps, unit))
    except RuntimeError:
        log("씬 FPS 설정 실패, 씬 기본값 유지")

    # 다운샘플 step
    step = max(1, int(round(float(source_fps) / float(target_fps))))
    log("다운샘플 step={0} (녹화 {1}fps -> 출력 {2}fps)".format(
        step, source_fps, target_fps))

    with open(csv_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise IOError("CSV 헤더가 없습니다.")

        # 헤더 -> 매칭되는 weight 사전 (루프 전 1회)
        col_to_plug = OrderedDict()
        unmatched = []
        for col in reader.fieldnames:
            lc = col.lower()
            if lc in META_COLS:
                continue
            plug = targets.get(lc)
            if plug:
                col_to_plug[col] = plug
            else:
                unmatched.append(col)

        if not col_to_plug:
            raise ValueError("CSV 열과 매칭되는 블렌드셰이프가 없습니다. "
                             "노드 선택을 확인하세요.")

        applied_shapes = set()
        bad_values = 0
        out_frame = start_frame
        kept = 0

        cmds.undoInfo(openChunk=True)
        try:
            for i, row in enumerate(reader):
                if i % step != 0:          # 다운샘플: step 간격만 유지
                    continue
                for col, plug in col_to_plug.items():
                    raw = row.get(col, "")
                    if raw is None or raw.strip() == "":
                        continue
                    try:
                        value = float(raw)
                    except ValueError:
                        bad_values += 1
                        continue
                    cmds.setKeyframe(plug, time=out_frame, value=value)
                    applied_shapes.add(col)
                out_frame += 1
                kept += 1
        finally:
            cmds.undoInfo(closeChunk=True)

    end_frame = start_frame + kept - 1 if kept else start_frame

    # 타임라인 in/out 확장
    if kept:
        extend_timeline(start_frame, end_frame, log)

    # 오디오
    audio_node = None
    if do_audio:
        wav = resolve_audio(csv_path, overwrite_wav, log)
        if wav:
            try:
                audio_node = import_audio(wav, start_frame, log)
            except Exception as e:
                log("오디오 임포트 실패 (무시): {0}".format(e))

    summary = {
        "frames": kept,
        "start_frame": start_frame,
        "end_frame": end_frame,
        "applied_shapes": sorted(applied_shapes),
        "unmatched_cols": unmatched,
        "bad_values": bad_values,
        "audio_node": audio_node,
    }
    return summary


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------

def _maya_main_window():
    ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(ptr), QtWidgets.QWidget) if ptr else None


class ARKitImportDialog(QtWidgets.QDialog):
    OBJECT_NAME = "ARKitFacialImportDialog"

    def __init__(self, parent=None):
        super(ARKitImportDialog, self).__init__(parent or _maya_main_window())
        self.setObjectName(self.OBJECT_NAME)
        self.setWindowTitle("ARKit Facial Import")
        self.setMinimumWidth(460)
        self._build_ui()
        self.refresh_nodes()

    # --- UI 구성 ---------------------------------------------------------
    def _build_ui(self):
        form = QtWidgets.QFormLayout()

        # CSV 경로
        self.csv_edit = QtWidgets.QLineEdit()
        browse = QtWidgets.QPushButton("Browse")
        browse.clicked.connect(self.browse_csv)
        csv_row = QtWidgets.QHBoxLayout()
        csv_row.addWidget(self.csv_edit)
        csv_row.addWidget(browse)
        form.addRow("CSV 파일:", csv_row)

        # 블렌드셰이프 노드
        self.node_combo = QtWidgets.QComboBox()
        refresh = QtWidgets.QPushButton("자동탐지")
        refresh.clicked.connect(self.refresh_nodes)
        node_row = QtWidgets.QHBoxLayout()
        node_row.addWidget(self.node_combo)
        node_row.addWidget(refresh)
        form.addRow("블렌드셰이프 노드:", node_row)

        # 시작 프레임
        self.start_spin = QtWidgets.QSpinBox()
        self.start_spin.setRange(-100000, 100000)
        self.start_spin.setValue(1)
        form.addRow("시작 프레임:", self.start_spin)

        # FPS
        self.src_spin = QtWidgets.QSpinBox()
        self.src_spin.setRange(1, 240)
        self.src_spin.setValue(60)
        self.tgt_combo = QtWidgets.QComboBox()
        self.tgt_combo.addItems(["30", "60"])
        fps_row = QtWidgets.QHBoxLayout()
        fps_row.addWidget(QtWidgets.QLabel("녹화"))
        fps_row.addWidget(self.src_spin)
        fps_row.addSpacing(12)
        fps_row.addWidget(QtWidgets.QLabel("출력"))
        fps_row.addWidget(self.tgt_combo)
        fps_row.addStretch()
        form.addRow("FPS:", fps_row)

        # 오디오 옵션
        self.audio_check = QtWidgets.QCheckBox("오디오도 임포트 (WAV/MOV 추출)")
        self.audio_check.setChecked(True)
        self.overwrite_check = QtWidgets.QCheckBox("기존 WAV 덮어쓰기")
        audio_row = QtWidgets.QHBoxLayout()
        audio_row.addWidget(self.audio_check)
        audio_row.addWidget(self.overwrite_check)
        audio_row.addStretch()
        form.addRow("오디오:", audio_row)

        # 임포트 버튼
        self.import_btn = QtWidgets.QPushButton("Import Animation")
        self.import_btn.clicked.connect(self.run_import)

        # 로그
        self.log_text = QtWidgets.QPlainTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(160)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(self.import_btn)
        layout.addWidget(QtWidgets.QLabel("로그:"))
        layout.addWidget(self.log_text)

    # --- 동작 ------------------------------------------------------------
    def log(self, msg):
        self.log_text.appendPlainText(msg)
        self.log_text.repaint()

    def browse_csv(self):
        start_dir = os.path.dirname(self.csv_edit.text()) or ""
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "ARKit CSV 선택", start_dir, "CSV Files (*.csv)")
        if path:
            self.csv_edit.setText(path)

    def refresh_nodes(self):
        nodes = list_blendshape_nodes()
        self.node_combo.clear()
        if not nodes:
            self.log("씬에 블렌드셰이프 노드가 없습니다.")
            return
        self.node_combo.addItems(nodes)
        best = detect_best_node(nodes)
        if best:
            self.node_combo.setCurrentText(best)
            self.log("자동탐지: '{0}' (ARKit 매칭 {1}개)".format(
                best, score_node(best)))

    def run_import(self):
        csv_path = self.csv_edit.text().strip()
        bs_node = self.node_combo.currentText().strip()
        if not csv_path:
            self.log("[오류] CSV 파일을 선택하세요.")
            return
        if not bs_node:
            self.log("[오류] 블렌드셰이프 노드를 선택하세요.")
            return

        self.log("-" * 48)
        try:
            summary = import_facial(
                csv_path, bs_node,
                start_frame=self.start_spin.value(),
                source_fps=self.src_spin.value(),
                target_fps=int(self.tgt_combo.currentText()),
                do_audio=self.audio_check.isChecked(),
                overwrite_wav=self.overwrite_check.isChecked(),
                log=self.log,
            )
        except Exception as e:
            self.log("[실패] {0}".format(e))
            return

        self.log("[완료] 프레임 {0}개 ({1}~{2}), 셰이프 {3}개 적용".format(
            summary["frames"], summary["start_frame"],
            summary["end_frame"], len(summary["applied_shapes"])))
        if summary["unmatched_cols"]:
            self.log("  · 매칭 안 됨(건너뜀) {0}개: {1}".format(
                len(summary["unmatched_cols"]),
                ", ".join(summary["unmatched_cols"])))
        if summary["bad_values"]:
            self.log("  · 숫자 변환 실패 값 {0}개 건너뜀".format(
                summary["bad_values"]))


_dialog = None


def show():
    """UI를 띄운다. 이미 떠 있는 같은 창이 있으면 닫고 새로 띄운다.

    reload 후에는 모듈 전역 _dialog 가 None 으로 초기화되므로, 그것에만 의존하지 않고
    objectName 으로 떠 있는 창을 모두 찾아 닫는다 (셸프 버튼 재실행 시 창 중복 방지).
    """
    global _dialog
    for w in QtWidgets.QApplication.topLevelWidgets():
        if w.objectName() == ARKitImportDialog.OBJECT_NAME:
            try:
                w.close()
                w.deleteLater()
            except Exception:
                pass
    _dialog = ARKitImportDialog()
    _dialog.show()
    return _dialog


if __name__ == "__main__":
    show()
