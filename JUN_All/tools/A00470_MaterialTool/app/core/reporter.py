# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-09-16
# A00470_MaterialTool - 진단 결과를 사람이 읽는 글로 (maya.cmds 무의존)
#
# 로그는 그대로 클립보드에 들어가 남에게 전달되는 글이다. 그래서 두 가지를 지킨다.
#   - **짧은 쪽이 기본** : 틀린 토큰만 나열하고, 이유는 Detailed 에서 편다.
#   - **고칠 이름을 항상 같이 준다** : "틀렸다" 로 끝나면 받은 사람이 다시 물어야 한다.
#
# UI 문자열과 로그는 영어로 쓴다(저장소 규칙).

from tools.A00470_MaterialTool.app.core.name_rules import (
    STATUS_BAD,
    STATUS_EXTRA,
    STATUS_MISSING,
)


INDENT = "  "


def format_report(report, detailed=False, usage=None):
    """이름 하나의 리포트를 줄 목록으로.

    Args:
        report: NameReport
        detailed: True 면 틀린 토큰마다 기대 규칙을 한 줄씩 편다.
        usage: {머티리얼: [메시, ...]} - detailed 일 때 어디에 쓰였는지 덧붙인다.
    """
    lines = [report.name]

    if report.ok:
        lines.append(INDENT + "ok")
    else:
        bad = report.bad_tokens
        if bad:
            lines.append(INDENT + "invalid tokens : " + ", ".join(bad))

        if detailed:
            lines.extend(_detail_lines(report))

        missing = report.missing_roles
        if missing:
            lines.append(INDENT + "missing tokens : " + ", ".join(missing))

        for warning in report.warnings:
            lines.append(INDENT + "warning : " + warning)

        if report.suggested_name and report.suggested_name != report.name:
            lines.append(INDENT + "suggested name : " + report.suggested_name)

    if detailed and usage:
        meshes = usage.get(report.name) or []
        if meshes:
            lines.append(INDENT + "used by : " + _short_list(meshes))

    return lines


def _detail_lines(report):
    """틀린 토큰마다 "무엇을 기대했는지 + 무엇으로 고치면 되는지" 한 줄씩."""
    rows = []

    for result in report.results:
        if result.status not in (STATUS_BAD, STATUS_MISSING, STATUS_EXTRA):
            continue

        position = "[{0}]".format(result.index) if result.index else "[-]"
        label = result.text or (result.placeholder or result.role)

        if result.status == STATUS_MISSING:
            reason = "missing '{0}' - expected {1}".format(result.role, result.expected)
        elif result.status == STATUS_EXTRA:
            reason = "unexpected token - {0}".format(result.expected)
        else:
            reason = "invalid '{0}' - expected {1}".format(result.role, result.expected)

        if result.suggestion and result.suggestion != result.text:
            reason += "   (suggest : {0})".format(result.suggestion)

        rows.append((position, label, reason))

    if not rows:
        return []

    width = max(len(label) for _p, label, _r in rows)

    return [INDENT + "{0} {1}  {2}".format(position, label.ljust(width), reason)
            for position, label, reason in rows]


def _short_list(items, limit=3):
    """`pCube1, pCube2 (+3 more)` - 로그가 메시 이름으로 넘치지 않게."""
    names = [i.split("|")[-1] for i in items]
    if len(names) <= limit:
        return ", ".join(names)
    return "{0} (+{1} more)".format(", ".join(names[:limit]), len(names) - limit)


def format_batch(reports, profile, detailed=False, include_valid=False, usage=None):
    """여러 이름의 리포트를 한 덩이 글로. 클립보드에 들어가는 것이 이 문자열이다."""
    reports = list(reports or [])
    failed = [r for r in reports if not r.ok]
    passed = [r for r in reports if r.ok]

    lines = [
        "=== Material name check : profile '{0}' ===".format(
            getattr(profile, "name", "")),
        "pattern : {0}".format(getattr(profile, "pattern", "")),
        "checked : {0} material(s)   ok : {1}   failed : {2}".format(
            len(reports), len(passed), len(failed)),
    ]

    if not reports:
        lines.append("")
        lines.append("No material to check. List the materials first.")
        return "\n".join(lines)

    shown = reports if include_valid else failed

    if not shown:
        lines.append("")
        lines.append("Every material name follows the rule.")
        return "\n".join(lines)

    for report in shown:
        lines.append("")
        lines.extend(format_report(report, detailed=detailed, usage=usage))

    return "\n".join(lines)
