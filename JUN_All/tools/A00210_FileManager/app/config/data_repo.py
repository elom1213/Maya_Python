# Python Script by Ji Hun Park
# last Update date : 2026-06-18
# A00210_FileManager - bundled default data-repo config
#
# 이 파일은 '중앙 데이터 리포'(records/thumbs/lineage/path_structures)의 기본 위치를
# 툴과 함께 배포한다. release_builder_QT 가 app/ 전체를 복사하므로 자동으로 배포에 포함된다.
# 배포받은 사용자는 Store Repo 를 따로 clone/설정하지 않아도 Pull 한 번이면 아래 URL 을
# DEFAULT_STORE_DIR 로 자동 clone 한 뒤 동기화한다(main_window.on_pull 참고).
#
# 데이터 리포를 옮기거나 포크하면 여기 URL/브랜치만 바꿔 다시 배포하면 된다.

import os

# 중앙 데이터 리포(git). private 면 사용자에게 GitHub 접근 권한 + 캐시된 git 자격증명이 필요하다.
DATA_REPO_URL = "https://github.com/elom1213/JUN_FileManager_data.git"
DATA_REPO_BRANCH = "master"
DATA_REPO_REMOTE = "origin"

# 배포 PC 에서 중앙 리포를 clone 해 넣을 기본 로컬 폴더(= 툴의 Store Repo 경로).
# prefs.json 과 같은 ~/.jun_filemanager 아래에 둬 PC 마다 일관되게 한다.
DEFAULT_STORE_DIR = os.path.join(
    os.path.expanduser("~"),
    ".jun_filemanager",
    "JUN_FileManager_data",
)
