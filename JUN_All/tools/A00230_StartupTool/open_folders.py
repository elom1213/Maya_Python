# Python Script by Ji Hun Park
# last Update date : 2026-06-18
# A00230_StartupTool - open configured folders on Windows boot
#
# 부팅(로그인) 시 config/startup.json 의 폴더들을 탐색기 창으로 팝업한다.
# 경로는 환경변수(%USERPROFILE% 등)를 쓰므로 PC 가 바뀌어도 동일하게 동작한다.
# 폴더 + 툴을 함께 띄우는 부팅 진입점은 startup.py 이며, 이 파일은 폴더 로직 모듈로도 쓰인다.
#
#   python open_folders.py        (폴더만 단독 실행 / 테스트)
#   python startup.py             (폴더 + 툴 실행)
#   install.py 로 Startup 에 등록하면 부팅 시 startup.py 가 자동 실행된다.

import os
import sys
import json

# config/startup.json 위치는 이 스크립트 기준으로 해석 (repo 경로가 어디든 동작).
# 폴더 목록만 읽으며, startup.py 가 추가하는 "tools" 키는 무시한다.
HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(HERE, "config", "startup.json")


def _strip_line_comments(text):
    """Drop full-line // comments so the JSON stays editable by toggling entries on/off."""
    lines = []
    for line in text.splitlines():
        if line.lstrip().startswith("//"):
            continue
        lines.append(line)
    return "\n".join(lines)


def load_config(path=CONFIG_PATH):
    """Read folders.json. Returns (folders, open_missing). Tolerates full-line // comments."""
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    data = json.loads(_strip_line_comments(text))
    folders = data.get("folders", [])
    open_missing = bool(data.get("open_missing", False))
    return folders, open_missing


def resolve_path(raw):
    """Expand environment variables (%VAR%) and ~ in a path string."""
    return os.path.normpath(os.path.expandvars(os.path.expanduser(raw)))


def open_folders(folders, open_missing=False):
    """Open each enabled folder in Explorer. Returns (opened, skipped, missing) lists."""
    opened, skipped, missing = [], [], []
    seen = set()

    for entry in folders:
        raw = entry.get("path", "")
        if not raw:
            continue
        if not entry.get("enabled", True):
            skipped.append(raw)
            continue

        path = resolve_path(raw)

        # 중복 경로는 한 번만 (대소문자 무시 - Windows)
        key = path.lower()
        if key in seen:
            continue
        seen.add(key)

        exists = os.path.isdir(path)
        if not exists and not open_missing:
            missing.append(path)
            continue

        try:
            os.startfile(path)  # 탐색기 창으로 폴더 팝업
            opened.append(path)
        except OSError as exc:
            print("[A00230] failed to open: %s (%s)" % (path, exc), file=sys.stderr)
            missing.append(path)

    return opened, skipped, missing


def main():
    try:
        folders, open_missing = load_config()
    except FileNotFoundError:
        print("[A00230] config not found: %s" % CONFIG_PATH, file=sys.stderr)
        return 1
    except (ValueError, OSError) as exc:
        print("[A00230] failed to read config: %s" % exc, file=sys.stderr)
        return 1

    opened, skipped, missing = open_folders(folders, open_missing)

    print("[A00230] opened %d, skipped %d, missing %d"
          % (len(opened), len(skipped), len(missing)))
    for p in missing:
        print("[A00230] missing (skipped): %s" % p, file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
