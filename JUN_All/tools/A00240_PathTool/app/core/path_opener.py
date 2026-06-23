# Python Script by Ji Hun Park
# last Update date : 2026-06-19
# A00240_PathTool - open a path in the OS file explorer (UI/DCC 비의존)
#
# 폴더면 그 폴더를 열고, 파일이면 폴더를 열어 그 파일을 선택한다.
# Windows 우선(os.startfile / explorer), macOS·Linux 폴백 제공.

# 구현은 Framework 로 승격됨(여러 툴이 공유). 기존 호출부(path_opener.open_path)가
# 그대로 동작하도록 re-export 만 남긴다.
from Framework.core.file_opener import open_path  # noqa: F401  (re-export)
