# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-23
# Framework - Windows 셸 통합: 시작 메뉴 바로가기(.lnk) 만들기 + 시작 화면 고정. Qt · Maya 비의존.
#
# standalone PySide 툴(A00220_BackupTool · A00240_PathTool 등)이 `File > Add to Start Menu` 로
# 자기 바로가기를 시작 메뉴에 넣을 때 쓴다. JUN_Video_Tool(0110) 의 app/core/shell_integration.py
# 를 공용으로 옮긴 것이다(타입 힌트 제거 - PySide2/py3.7 툴에서도 import 되게).
#
# 동작
# ----
# - 시작 메뉴: `%APPDATA%/Microsoft/Windows/Start Menu/Programs/<App Name>.lnk` 를 만든다.
#   대상은 **pythonw.exe + launch.py**(콘솔 창 없음), 작업 폴더는 툴 루트, 아이콘은 툴의 .ico.
#   PyInstaller exe(frozen) 면 대상은 exe 자신, 아이콘도 exe 의 0번.
# - 바로가기에 **AppUserModelID** 를 넣는다. 그래야 바로가기로 띄운 창과 `python launch.py` 로
#   띄운 창이 같은 작업표시줄 버튼으로 묶이고, 고정했을 때 아이콘이 python 이 아니라 툴 아이콘이 된다.
#   .lnk 의 AppUserModelID 는 WScript.Shell 로는 못 쓰므로 PowerShell 의 Add-Type(C#) 으로
#   IShellLinkW + IPropertyStore 를 직접 호출한다(pywin32 의존 없음, Windows 10/11 기본 탑재).
# - 시작 화면 고정("Pin to Start")은 셸 동사가 보이는 환경에서만 시도한다. Windows 11 은 결과를
#   알려 주지 않으므로 호출부는 "요청했다" 까지만 말하고 수동 고정 방법을 안내한다.
#
# 지원 OS : **Windows 10 · 11** 공통. 쓰는 것이 전부 양쪽에 기본 탑재된 것뿐이다 -
#   PowerShell 5.1(Add-Type 이 C# 을 .NET Framework 로 컴파일) · IShellLinkW/IPropertyStore COM ·
#   `%APPDATA%/Microsoft/Windows/Start Menu/Programs`. 셸 동사 이름은 영어/한국어 둘 다 매칭한다.
#   "Pin to Start" 동사는 OS/빌드에 따라 없을 수 있는데(특히 Win10 1607+ 는 프로그램의 자가 고정을 막는다),
#   그때는 "unavailable" 로 돌아오고 사용자가 앱 목록에서 우클릭 -> 시작 화면에 고정 하면 된다.
#   바로가기 자체(앱 목록 · 검색에 뜨는 것)는 동사와 무관하게 항상 만들어진다.
#
# 사용
# ----
#     from Framework.core import shell_integration as shell
#
#     spec = shell.launch_spec(tool_root, icon_path)            # dev / frozen 자동 판별
#     lnk = shell.add_to_start_menu("JUN Path Tool", "Dnable.JUN.A00240.PathTool", spec,
#                                   description="JUN Path Tool - path shortcuts")
#     shell.pin_shortcut(lnk, "start")                          # "pinned" | "already" | "unavailable"
#
# 툴 폴더를 옮긴 뒤 다시 부르면 같은 .lnk 를 덮어써 경로가 갱신된다.

import os
import subprocess
import sys
import tempfile


class ShellIntegrationError(Exception):
    pass


def is_supported():
    return sys.platform.startswith("win")


def _subprocess_flags():
    """Windows 면 콘솔 창 억제 플래그, 그 외 0."""
    if is_supported():
        return getattr(subprocess, "CREATE_NO_WINDOW", 0)
    return 0


# ======================================================================
# 실행 명령 (바로가기 대상)
# ======================================================================

class LaunchSpec(object):
    """바로가기가 실행할 명령.

    target    : 실행 파일 (pythonw.exe 또는 frozen exe)
    arguments : 인자 문자열 ('"<root>/launch.py"' 또는 빈 문자열)
    workdir   : 작업 폴더 (툴 루트)
    icon      : 바로가기 아이콘 파일 (.ico 또는 exe)
    """

    def __init__(self, target, arguments, workdir, icon):
        self.target = target
        self.arguments = arguments
        self.workdir = workdir
        self.icon = icon

    @property
    def command_line(self):
        if self.arguments:
            return '"{0}" {1}'.format(self.target, self.arguments)
        return '"{0}"'.format(self.target)

    def __repr__(self):
        return "LaunchSpec(target={0!r}, arguments={1!r}, workdir={2!r}, icon={3!r})".format(
            self.target, self.arguments, self.workdir, self.icon)


def launch_spec(tool_root, icon="", executable=None, entry="launch.py"):
    """툴을 실행하는 명령을 만든다.

    - dev(소스) 실행 : 지금 도는 Python 의 **pythonw.exe** + `<tool_root>/launch.py` (콘솔 창 없음).
      pythonw.exe 가 없으면 python.exe 그대로.
    - PyInstaller exe(frozen) : exe 자신, 인자 없음. 아이콘은 exe (_MEIPASS 의 .ico 는 실행 때마다
      바뀌는 임시 폴더라 바로가기에 못 쓴다).
    """
    tool_root = os.path.abspath(tool_root)
    if getattr(sys, "frozen", False) and executable is None:
        exe = os.path.abspath(sys.executable)
        return LaunchSpec(target=exe, arguments="", workdir=os.path.dirname(exe), icon=exe)

    exe = os.path.abspath(executable or sys.executable)
    if os.path.basename(exe).lower() == "python.exe":
        w = os.path.join(os.path.dirname(exe), "pythonw.exe")
        if os.path.isfile(w):
            exe = w
    icon = os.path.abspath(icon) if icon else exe
    return LaunchSpec(target=exe, arguments='"{0}"'.format(os.path.join(tool_root, entry)),
                      workdir=tool_root, icon=icon)


# ======================================================================
# 경로
# ======================================================================

def start_menu_dir():
    appdata = os.environ.get("APPDATA") or os.path.join(os.path.expanduser("~"), "AppData", "Roaming")
    return os.path.join(appdata, "Microsoft", "Windows", "Start Menu", "Programs")


def start_menu_shortcut(app_name):
    """`<Programs>/<app_name>.lnk`"""
    return os.path.join(start_menu_dir(), "{0}.lnk".format(app_name))


# ======================================================================
# PowerShell (C# 은 PowerShell 5.1 의 Add-Type 이 컴파일한다 - Windows 10/11 기본 탑재)
# ======================================================================

_CSHARP = r'''
using System;
using System.Text;
using System.Runtime.InteropServices;
using System.Runtime.InteropServices.ComTypes;
namespace JunShell {
  [ComImport, Guid("000214F9-0000-0000-C000-000000000046"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
  interface IShellLinkW {
    void GetPath([Out, MarshalAs(UnmanagedType.LPWStr)] StringBuilder f, int c, IntPtr fd, uint fl);
    void GetIDList(out IntPtr p);
    void SetIDList(IntPtr p);
    void GetDescription([Out, MarshalAs(UnmanagedType.LPWStr)] StringBuilder s, int c);
    void SetDescription([MarshalAs(UnmanagedType.LPWStr)] string s);
    void GetWorkingDirectory([Out, MarshalAs(UnmanagedType.LPWStr)] StringBuilder s, int c);
    void SetWorkingDirectory([MarshalAs(UnmanagedType.LPWStr)] string s);
    void GetArguments([Out, MarshalAs(UnmanagedType.LPWStr)] StringBuilder s, int c);
    void SetArguments([MarshalAs(UnmanagedType.LPWStr)] string s);
    void GetHotkey(out short h);
    void SetHotkey(short h);
    void GetShowCmd(out int c);
    void SetShowCmd(int c);
    void GetIconLocation([Out, MarshalAs(UnmanagedType.LPWStr)] StringBuilder s, int c, out int i);
    void SetIconLocation([MarshalAs(UnmanagedType.LPWStr)] string s, int i);
    void SetRelativePath([MarshalAs(UnmanagedType.LPWStr)] string s, uint r);
    void Resolve(IntPtr h, uint f);
    void SetPath([MarshalAs(UnmanagedType.LPWStr)] string s);
  }
  [ComImport, Guid("886D8EEB-8CF2-4446-8D02-CDBA1DBDCF99"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
  interface IPropertyStore {
    void GetCount(out uint c);
    void GetAt(uint i, out PropertyKey k);
    void GetValue(ref PropertyKey k, out PropVariant v);
    void SetValue(ref PropertyKey k, ref PropVariant v);
    void Commit();
  }
  [StructLayout(LayoutKind.Sequential, Pack = 4)]
  struct PropertyKey { public Guid fmtid; public uint pid; }
  [StructLayout(LayoutKind.Explicit, Size = 24)]
  struct PropVariant { [FieldOffset(0)] public ushort vt; [FieldOffset(8)] public IntPtr p; }
  [ComImport, Guid("00021401-0000-0000-C000-000000000046")]
  class CShellLink {}
  public static class Lnk {
    static readonly Guid AUM = new Guid("9F4C2855-9F79-4B39-A8D0-E1D42DE1D5F3");
    public static void Create(string lnk, string target, string args, string wd, string icon, string aumid, string desc) {
      var link = (IShellLinkW)new CShellLink();
      link.SetPath(target);
      link.SetArguments(args);
      link.SetWorkingDirectory(wd);
      link.SetIconLocation(icon, 0);
      link.SetDescription(desc);
      var store = (IPropertyStore)link;
      var key = new PropertyKey { fmtid = AUM, pid = 5 };
      var pv = new PropVariant { vt = 31, p = Marshal.StringToCoTaskMemUni(aumid) };
      try { store.SetValue(ref key, ref pv); store.Commit(); }
      finally { Marshal.FreeCoTaskMem(pv.p); }
      ((IPersistFile)link).Save(lnk, true);
    }
    public static string ReadAumid(string lnk) {
      var link = (IShellLinkW)new CShellLink();
      ((IPersistFile)link).Load(lnk, 0);
      var key = new PropertyKey { fmtid = AUM, pid = 5 };
      PropVariant pv;
      ((IPropertyStore)link).GetValue(ref key, out pv);
      return pv.vt == 31 ? Marshal.PtrToStringUni(pv.p) : "";
    }
  }
}
'''

_PS_CREATE = r'''
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
Add-Type -TypeDefinition (Get-Content -Raw -LiteralPath $env:JUN_CS)
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $env:JUN_LNK) | Out-Null
[JunShell.Lnk]::Create($env:JUN_LNK, $env:JUN_TARGET, $env:JUN_ARGS, $env:JUN_WD, $env:JUN_ICON, $env:JUN_AUMID, $env:JUN_DESC)
'OK:' + [JunShell.Lnk]::ReadAumid($env:JUN_LNK)
'''

_PS_READ_AUMID = r'''
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
Add-Type -TypeDefinition (Get-Content -Raw -LiteralPath $env:JUN_CS)
'AUMID:' + [JunShell.Lnk]::ReadAumid($env:JUN_LNK)
'''

_PS_PIN = r'''
$ErrorActionPreference = 'Continue'   # 열거 중 비종료 오류로 멈추지 않게 (결과는 출력으로 판정)
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$shell = New-Object -ComObject Shell.Application
$item = $shell.Namespace((Split-Path -Parent $env:JUN_LNK)).ParseName((Split-Path -Leaf $env:JUN_LNK))
$names = @($item.Verbs() | ForEach-Object { $_.Name.Replace('&', '') })
if ($names | Where-Object { $_ -match $env:JUN_UNPIN }) { 'ALREADY'; exit 0 }
$verb = $item.Verbs() | Where-Object { $_.Name.Replace('&', '') -match $env:JUN_PIN } | Select-Object -First 1
if ($verb) { $verb.DoIt(); 'PINNED' } else { 'UNAVAILABLE' }
'''


def _run_ps(script, env_extra, timeout=60.0):
    if not is_supported():
        raise ShellIntegrationError("Shortcuts are only supported on Windows.")
    td = tempfile.mkdtemp(prefix="jun_shell_")
    try:
        cs = os.path.join(td, "lnk.cs")
        ps = os.path.join(td, "run.ps1")
        with open(cs, "w", encoding="utf-8") as f:
            f.write(_CSHARP)
        # PowerShell 5.1 은 BOM 없는 UTF-8 스크립트를 ANSI 로 읽으므로 BOM 을 붙인다 (한글 동사 이름)
        with open(ps, "w", encoding="utf-8-sig") as f:
            f.write(script)
        env = dict(os.environ)
        env.update(env_extra)
        env["JUN_CS"] = cs
        try:
            proc = subprocess.run(
                ["powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
                 "-File", ps],
                capture_output=True, env=env, timeout=timeout, creationflags=_subprocess_flags())
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise ShellIntegrationError("PowerShell failed: {0}".format(exc))
    finally:
        for name in ("lnk.cs", "run.ps1"):
            try:
                os.remove(os.path.join(td, name))
            except OSError:
                pass
        try:
            os.rmdir(td)
        except OSError:
            pass
    out = _decode(proc.stdout)
    if proc.returncode != 0:
        err = _decode(proc.stderr).strip().splitlines()
        raise ShellIntegrationError(err[0] if err else "PowerShell exited with code {0}.".format(proc.returncode))
    return out


def _decode(data):
    """PowerShell 출력 디코딩. 스크립트가 UTF-8 로 맞추지만, 그 전에 난 오류(파일을 못 읽는 등)는
    콘솔 코드페이지(한국어 Windows 는 cp949)로 나오므로 UTF-8 이 깨지면 로컬 코드페이지로 다시 읽는다."""
    if not data:
        return ""
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        pass
    try:
        return data.decode("mbcs")
    except (UnicodeDecodeError, LookupError):
        return data.decode("utf-8", "replace")


# ======================================================================
# 공개 API
# ======================================================================

def create_shortcut(lnk, spec, aumid, description=""):
    """바로가기 `lnk` 를 만들거나 덮어쓴다. 만든 뒤 AppUserModelID 를 다시 읽어 확인한다."""
    out = _run_ps(_PS_CREATE, {
        "JUN_LNK": lnk, "JUN_TARGET": spec.target, "JUN_ARGS": spec.arguments or "",
        "JUN_WD": spec.workdir, "JUN_ICON": spec.icon, "JUN_AUMID": aumid,
        "JUN_DESC": description or "",
    })
    if "OK:{0}".format(aumid) not in out:
        raise ShellIntegrationError("Shortcut was written but its app ID could not be verified.")
    return lnk


def read_shortcut_aumid(lnk):
    """바로가기에 들어 있는 AppUserModelID. 없거나 실패면 빈 문자열."""
    try:
        out = _run_ps(_PS_READ_AUMID, {"JUN_LNK": lnk})
    except ShellIntegrationError:
        return ""
    for line in out.splitlines():
        if line.startswith("AUMID:"):
            return line[6:].strip()
    return ""


def add_to_start_menu(app_name, aumid, spec, description=""):
    """시작 메뉴 Programs 에 `<app_name>.lnk` 를 만든다(있으면 갱신). 만든 .lnk 경로를 돌려준다."""
    return create_shortcut(start_menu_shortcut(app_name), spec, aumid, description or app_name)


_VERBS = {
    "start": ("Pin to Start|시작 화면에 고정", "Unpin from Start|시작 화면에서 고정 해제"),
    "taskbar": ("Pin to taskbar|작업 표시줄에 고정", "Unpin from taskbar|작업 표시줄에서 고정 해제"),
}


def pin_shortcut(lnk, where="start"):
    """셸 동사로 시작 화면("start") / 작업표시줄("taskbar")에 고정한다.

    반환: "pinned" | "already" | "unavailable".
    - 작업표시줄 동사는 Windows 10 1809+ / 11 에서 보통 없다(프로그램의 자가 고정을 Windows 가 막았다).
    - Windows 11 은 "Pin to Start" 도 결과를 돌려주지 않으므로 "pinned" 는 **요청했다** 는 뜻이다.
    """
    pin, unpin = _VERBS[where]
    try:
        out = _run_ps(_PS_PIN, {"JUN_LNK": lnk, "JUN_PIN": pin, "JUN_UNPIN": unpin})
    except ShellIntegrationError:
        return "unavailable"
    if "ALREADY" in out:
        return "already"
    return "pinned" if "PINNED" in out else "unavailable"


def start_menu_message(app_name, pinned):
    """`Add to Start Menu` 뒤에 사용자에게 보여 줄 안내문(영어). 툴마다 같은 문장을 쓴다."""
    # Windows 10 은 시작 메뉴 왼쪽 앱 목록, Windows 11 은 'All apps' - 둘 다 가리키는 문장으로 쓴다.
    text = "'{0}' was added to the Start menu (app list and Start search).".format(app_name)
    where = "open the Start menu app list (All apps on Windows 11)"
    if pinned in ("pinned", "already"):
        # Windows 11 은 고정 결과를 알려 주지 않으므로 '요청했다' 까지만 말한다
        text += ("\n\nIt was also pinned to Start. If you do not see it among the pinned tiles, "
                 "{0}, right-click '{1}' and choose 'Pin to Start'.".format(where, app_name))
    else:
        text += ("\n\nTo pin it to Start, {0}, right-click '{1}' and choose "
                 "'Pin to Start'.".format(where, app_name))
    text += "\n\nIf you move the tool folder, click this menu item again to update the shortcut."
    return text
