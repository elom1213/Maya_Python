# Python Script by Ji Hun Park
# last Update date : 2026-06-17
# A00210_FileManager - git sync (UI/DCC 비의존)
#
# 중앙 데이터 리포(records/thumbs)를 시스템 git 으로 pull/push 한다.
# GitPython 의존 없이 subprocess 로 PATH 의 git 을 호출한다.
# 자격증명은 캐시된 git creds 에 의존한다(별도 입력받지 않음).
#
# 모든 메서드는 (ok: bool, output: str) 을 반환하고, 예외로 죽지 않는다.

import os
import subprocess

# Windows 에서 콘솔 창이 깜빡이지 않게 한다.
_NO_WINDOW = 0
if os.name == "nt":
    _NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)

GITIGNORE_CONTENT = "# Maya 원본 파일은 이 데이터 리포에 두지 않는다 (안전망)\n*.mb\n*.ma\n__pycache__/\n"


class GitSync:

    def __init__(self, store_dir, remote="origin", branch="main"):
        self.store_dir = os.path.abspath(store_dir) if store_dir else ""
        self.remote = remote or "origin"
        self.branch = branch or "main"

    # ---------------------------------------------------------------- run

    def _run(self, *args):
        """git 명령 실행 → (ok, output)."""
        if not self.store_dir:
            return False, "Store directory is not set."

        try:
            proc = subprocess.run(
                ["git"] + list(args),
                cwd=self.store_dir,
                capture_output=True,
                text=True,
                creationflags=_NO_WINDOW,
            )
        except FileNotFoundError:
            return False, "git not found. Install git and ensure it is on PATH."
        except OSError as exc:
            return False, f"git failed to start: {exc}"

        out = (proc.stdout or "") + (proc.stderr or "")
        return proc.returncode == 0, out.strip()

    # -------------------------------------------------------------- state

    def is_repo(self):
        return os.path.isdir(os.path.join(self.store_dir, ".git"))

    def _write_skeleton(self):
        """records/ thumbs/ .gitignore 기본 구조 생성."""
        os.makedirs(os.path.join(self.store_dir, "records"), exist_ok=True)
        os.makedirs(os.path.join(self.store_dir, "thumbs"), exist_ok=True)

        gitignore = os.path.join(self.store_dir, ".gitignore")
        if not os.path.isfile(gitignore):
            with open(gitignore, "w", encoding="utf-8") as f:
                f.write(GITIGNORE_CONTENT)

    # ------------------------------------------------------------- public

    def ensure_repo(self, remote_url=""):
        """store_dir 을 git repo 로 준비한다.

        - 이미 repo 면 그대로 둔다.
        - remote_url 이 있고 store_dir 이 비어있으면 clone 시도.
        - 아니면 git init + (remote_url 있으면 remote add) + 스켈레톤 생성.
        """
        if not self.store_dir:
            return False, "Store directory is not set."

        os.makedirs(self.store_dir, exist_ok=True)

        if self.is_repo():
            return True, "Repository already initialized."

        logs = []

        is_empty = not os.listdir(self.store_dir)

        if remote_url and is_empty:
            ok, out = self._run_in_parent_clone(remote_url)
            logs.append(out)
            if ok:
                return True, "\n".join(logs)
            # remote_url 이 있는데 clone 실패 → 로컬 init 으로 '조용히' 폴백하지 않는다.
            # (인증/네트워크/권한 문제를 사용자가 인지하도록. 중앙 리포와 끊긴 빈 repo 생성 방지.)
            logs.append(
                "Clone failed. Check the Remote URL, your network, and git "
                "credentials / repo access. No local repository was created."
            )
            return False, "\n".join([l for l in logs if l])

        ok, out = self._run("init")
        logs.append(out)

        ok, out = self._run("checkout", "-B", self.branch)
        logs.append(out)

        if remote_url:
            self._run("remote", "remove", self.remote)
            ok, out = self._run("remote", "add", self.remote, remote_url)
            logs.append(out)

        self._write_skeleton()

        return True, "\n".join([l for l in logs if l])

    def _run_in_parent_clone(self, remote_url):
        """store_dir 위치로 clone. (빈 폴더 가정)"""
        parent = os.path.dirname(self.store_dir)
        target = os.path.basename(self.store_dir)

        try:
            proc = subprocess.run(
                ["git", "clone", "-b", self.branch, remote_url, target],
                cwd=parent,
                capture_output=True,
                text=True,
                creationflags=_NO_WINDOW,
            )
        except FileNotFoundError:
            return False, "git not found. Install git and ensure it is on PATH."
        except OSError as exc:
            return False, f"git clone failed to start: {exc}"

        out = (proc.stdout or "") + (proc.stderr or "")
        return proc.returncode == 0, out.strip()

    def pull(self):
        if not self.is_repo():
            return False, "Not a git repository. Run Init/Clone first."
        return self._run("pull", self.remote, self.branch)

    def push(self, message):
        if not self.is_repo():
            return False, "Not a git repository. Run Init/Clone first."

        logs = []

        ok, out = self._run("add", "-A")
        logs.append(out)

        # 변경이 없으면 commit 은 실패(반환 1)하지만 오류는 아니다.
        ok_commit, out_commit = self._run("commit", "-m", message)
        logs.append(out_commit)

        if not ok_commit and "nothing to commit" in out_commit.lower():
            logs.append("No changes to commit. Pushing anyway.")

        ok_push, out_push = self._run("push", self.remote, self.branch)
        logs.append(out_push)

        return ok_push, "\n".join([l for l in logs if l])

    def status(self):
        if not self.is_repo():
            return False, "Not a git repository."
        return self._run("status", "-s", "-b")
