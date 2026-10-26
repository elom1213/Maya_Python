# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-10-26
# A00210_FileManager / Maya 탭 > Export - 자원 요약 한 줄 (v1 읽기 전용, 순수 파이썬)  (v01.41)
#
# 설계 D18: 하드웨어 **선택**은 v2(병렬 워커). v1 은 `Resources: CPU ... · RAM ... · GPU ...` 한 줄만 보인다.
# PowerShell Get-CimInstance 한 번 - UI 는 QProcess 로 비동기 실행하고 끝나면 parse() 로 글자를 만든다. 실패하면 빈 문자열.

import os
import json


def command():
    """[powershell, ...] - CPU 이름 · 코어/스레드 · 메모리 바이트 · GPU 이름을 json 한 줄로."""
    script = ("$c = Get-CimInstance Win32_Processor | Select-Object -First 1; "
              "$m = (Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory; "
              "$g = @(Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name); "
              "@{cpu=$c.Name; cores=$c.NumberOfCores; threads=$c.NumberOfLogicalProcessors; ram=$m; gpu=$g} | ConvertTo-Json -Compress")
    return ["powershell", "-NoProfile", "-NonInteractive", "-Command", script]


def parse(text):
    """PowerShell 출력 -> 'CPU <name> <n>C/<n>T · RAM <n> GB · GPU <name>' (실패하면 '')."""
    text = (text or "").strip()
    start = text.find("{")
    if start < 0:
        return ""
    try:
        data = json.loads(text[start:])
    except ValueError:
        return ""
    parts = []
    cpu = " ".join(str(data.get("cpu") or "").split())
    if cpu:
        cores, threads = data.get("cores"), data.get("threads")
        ct = " {0}C/{1}T".format(cores, threads) if cores and threads else ""
        parts.append("CPU {0}{1}".format(cpu, ct))
    try:
        ram = float(data.get("ram") or 0) / (1024.0 ** 3)
        if ram > 0:
            parts.append("RAM {0:.0f} GB".format(ram))
    except (TypeError, ValueError):
        pass
    gpu = data.get("gpu")
    if isinstance(gpu, str):
        gpu = [gpu]
    gpu = [str(g).strip() for g in (gpu or []) if str(g).strip()]
    if gpu:
        parts.append("GPU " + ", ".join(gpu))
    return " · ".join(parts)


def cpu_count():
    return os.cpu_count() or 1
