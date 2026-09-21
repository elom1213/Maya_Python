# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-09-16
# A00470_MaterialTool - 진단 결과를 사람이 읽는 글로 (maya.cmds 무의존)
#
# 로그는 그대로 클립보드에 들어가 남에게 전달되는 글이다. 그래서 두 가지를 지킨다.
#   - **짧은 쪽이 기본** : 틀린 토큰만 나열하고, 이유는 Detailed 에서 편다.
#   - **고칠 이름을 항상 같이 준다** : "틀렸다" 로 끝나면 받은 사람이 다시 물어야 한다.
#
# ── 줄 하나 = (글, 종류) ★ (v01.07) ─────────────────────────────────────
# 리포트는 **두 벌**로 나간다 — 로그창에는 색이 있는 HTML, 클립보드에는 그냥 글.
# 같은 내용을 두 군데서 따로 만들면 반드시 어긋나므로, 줄을 만들 때 **종류표**를 같이
# 달아 두고(`(text, kind)`) 두 렌더러가 그 목록 하나를 읽는다.
#
# 종류는 색을 정한다 — 틀린 이름은 **빨강**, 제안 이름은 **초록**. 표(Status 열)에서 쓰는
# 색과 같은 값이라 표와 로그가 같은 말을 한다.
#
# ── 줄 순서 · 무엇을 기본으로 보일지 (v01.07) ────────────────────────────
# 기본 리포트는 **이름 + 고칠 이름** 두 줄이다. 사용자가 제일 먼저 보고 싶은 것은
# "그래서 뭐라고 고치면 되나" 라서 제안을 이름 바로 아래에 붙인다(예전에는 맨 아래였다).
#
# **틀린 토큰 · 빠진 토큰 목록은 `Detailed` 일 때만** 편다 — 고칠 이름만 있으면 되는
# 대부분의 경우에 줄만 늘리기 때문이다. 순서는
# **이름 -> 제안 이름 -> 틀린 토큰 -> (토큰별 이유) -> 빠진 토큰** 이다.
#
# UI 문자열과 로그는 영어로 쓴다(저장소 규칙).

from tools.A00470_MaterialTool.app.core.name_rules import (
    STATUS_BAD,
    STATUS_EXTRA,
    STATUS_MISSING,
)


INDENT = "  "

#: 줄 종류 - 색을 정하는 데만 쓴다.
KIND_PLAIN = "plain"
KIND_NAME_BAD = "name_bad"        # 규칙을 어긴 이름 (빨강)
KIND_NAME_OK = "name_ok"          # 규칙을 지킨 이름 (초록)
KIND_SUGGESTED = "suggested"      # 고칠 이름 (초록)

#: 색 - Name Check 표의 Status 열과 같은 값.
COLOR_BAD = "#e2786e"
COLOR_OK = "#78c88c"

_KIND_COLORS = {
    KIND_NAME_BAD: COLOR_BAD,
    KIND_NAME_OK: COLOR_OK,
    KIND_SUGGESTED: COLOR_OK,
}


def report_lines(report, detailed=False, usage=None):
    """이름 하나의 리포트를 `(글, 종류)` 목록으로.

    순서는 **이름 -> 제안 이름 -> 틀린 토큰 -> (상세) -> 빠진 토큰 -> 경고** 다.

    Args:
        report: NameReport
        detailed: True 면 틀린 토큰마다 기대 규칙을 한 줄씩 편다.
        usage: {머티리얼: [메시, ...]} - detailed 일 때 어디에 쓰였는지 덧붙인다.
    """
    lines = [(report.name, KIND_NAME_OK if report.ok else KIND_NAME_BAD)]

    if report.ok:
        lines.append((INDENT + "ok", KIND_PLAIN))
    else:
        # 고칠 이름을 **맨 위에** - 사용자가 제일 먼저 찾는 줄이다.
        if report.suggested_name and report.suggested_name != report.name:
            lines.append((INDENT + "suggested name : " + report.suggested_name,
                          KIND_SUGGESTED))

        # 토큰 목록은 **Detailed 일 때만** 편다 (v01.07). 기본 리포트에서 사람이 실제로
        # 쓰는 줄은 "그래서 뭐라고 고치면 되나" 하나라서, 나머지는 물어볼 때만 보인다.
        if detailed:
            bad = report.bad_tokens
            if bad:
                lines.append((INDENT + "invalid tokens : " + ", ".join(bad),
                              KIND_PLAIN))

            lines.extend((text, KIND_PLAIN) for text in _detail_lines(report))

            missing = report.missing_roles
            if missing:
                lines.append((INDENT + "missing tokens : " + ", ".join(missing),
                              KIND_PLAIN))

        for warning in report.warnings:
            lines.append((INDENT + "warning : " + warning, KIND_PLAIN))

    if detailed and usage:
        meshes = usage.get(report.name) or []
        if meshes:
            lines.append((INDENT + "used by : " + _short_list(meshes), KIND_PLAIN))

    return lines


def format_report(report, detailed=False, usage=None):
    """이름 하나의 리포트를 **글 목록**으로 (색 없이)."""
    return [text for text, _kind in
            report_lines(report, detailed=detailed, usage=usage)]


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


def batch_lines(reports, profile, detailed=False, include_valid=False, usage=None):
    """여러 이름의 리포트를 `(글, 종류)` 목록으로. 두 렌더러가 이것만 읽는다."""
    reports = list(reports or [])
    failed = [r for r in reports if not r.ok]
    passed = [r for r in reports if r.ok]

    lines = [
        ("=== Material name check : profile '{0}' ===".format(
            getattr(profile, "name", "")), KIND_PLAIN),
        ("pattern : {0}".format(getattr(profile, "pattern", "")), KIND_PLAIN),
        ("checked : {0} material(s)   ok : {1}   failed : {2}".format(
            len(reports), len(passed), len(failed)), KIND_PLAIN),
    ]

    if not reports:
        lines.append(("", KIND_PLAIN))
        lines.append(("No material to check. List the materials first.", KIND_PLAIN))
        return lines

    shown = reports if include_valid else failed

    if not shown:
        lines.append(("", KIND_PLAIN))
        lines.append(("Every material name follows the rule.", KIND_PLAIN))
        return lines

    for report in shown:
        lines.append(("", KIND_PLAIN))
        lines.extend(report_lines(report, detailed=detailed, usage=usage))

    return lines


def format_batch(reports, profile, detailed=False, include_valid=False, usage=None):
    """여러 이름의 리포트를 한 덩이 글로. **클립보드에 들어가는 것이 이 문자열이다.**"""
    return "\n".join(text for text, _kind in batch_lines(
        reports, profile, detailed=detailed, include_valid=include_valid,
        usage=usage))


def format_batch_html(reports, profile, detailed=False, include_valid=False,
                      usage=None):
    """같은 리포트를 **색이 있는 HTML** 로. 로그창에 넣는 것이 이 문자열이다.

    글자 그대로 보여야 하므로 `<`·`&` 를 이스케이프하고, 들여쓰기 공백은 HTML 에서
    뭉개지므로 `&nbsp;` 로 바꾼다.
    """
    return lines_to_html(batch_lines(
        reports, profile, detailed=detailed, include_valid=include_valid,
        usage=usage))


def lines_to_html(lines):
    """`(글, 종류)` 목록 -> 한 덩이 HTML."""
    out = []

    for text, kind in lines:
        body = _escape(text)
        color = _KIND_COLORS.get(kind)
        if color:
            body = '<span style="color:{0};">{1}</span>'.format(color, body)
        out.append(body)

    return "<br>".join(out)


def _escape(text):
    """HTML 로 들어가도 글자 그대로 보이게."""
    return (str(text)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace(" ", "&nbsp;"))
