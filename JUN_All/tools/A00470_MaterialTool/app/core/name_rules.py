# -*- coding: utf-8 -*-
# Python Script by Ji Hun Park
# last Update date : 2026-09-16
# A00470_MaterialTool - 이름 규칙 진단 엔진 (maya.cmds 무의존)
#
# 이름을 구분자(`_`)로 쪼갠 **토큰**과, 프로파일이 정한 **슬롯(role)** 을 맞춰 보고
# 어디가 틀렸는지 말한다. 핵심 판단은 세 가지다.
#
# 1) **토큰을 슬롯에 어떻게 맞출 것인가** — 앞에서부터 짝짓기만 하면 토큰 하나가
#    빠졌을 때 그 뒤가 전부 밀려 "전부 틀림" 이 된다. 예를 들어 `MT_SYN_Sett002_Pantss`
#    는 `MANU` 가 빠진 이름인데, 순서대로 붙이면 SYN=MANU, Sett002=character ... 로
#    읽혀 사람에게 쓸모없는 리포트가 나온다. 그래서 **정렬(alignment)** 로 푼다 —
#    match / 슬롯 누락 / 토큰 잉여 세 가지 수를 두는 DP 로 점수가 가장 높은 대응을
#    고른다(Needleman-Wunsch 와 같은 꼴). "MANU 가 생략됐다" 는 그 결과로 나온다.
#
# 2) **틀린 토큰을 어떻게 고칠지 제안** — 규칙마다 `repair()` 를 둔다. 열거형은 가장
#    가까운 값(편집 거리), `SetXXX` 형식은 알파벳/숫자를 갈라 다시 조립한다.
#    `SYN -> SIN`, `Sett002 -> Set002`, `Pantss -> Pants`. 제안이 있으면 정렬 점수도
#    조금 올린다(오타는 "그 자리에 오려던 토큰" 이라는 뜻이므로).
#
# 3) **꼬리 숫자** — 이름 맨 끝의 숫자가 마지막 토큰에 **붙어** 있으면 경고하고,
#    `_002` 처럼 구분자로 갈라져 있으면 넘어간다.
#
# 규칙의 종류(literal / enum / pattern / regex / any)는 전부 JSON 으로 표현된다.

import re


# ==========================================================================
# 정렬 점수
# ==========================================================================
# 규칙을 만족하는 토큰이 제일 좋고(MATCH), 오타지만 고칠 수 있으면 그다음(SOFT),
# 전혀 아니면 감점(MISMATCH). 슬롯을 비우는 것(MISSING)보다 토큰을 버리는 것
# (EXTRA)을 더 아프게 둬서, 어지간하면 토큰을 슬롯에 채워 읽도록 한다.

SCORE_MATCH = 4
SCORE_SOFT = 2
SCORE_MISMATCH = -1
SCORE_MISSING = -2
SCORE_EXTRA = -3


# 토큰 판정 결과
STATUS_OK = "ok"            # 규칙을 만족
STATUS_BAD = "bad"          # 그 자리에 왔지만 규칙을 어김
STATUS_MISSING = "missing"  # 슬롯에 올 토큰이 없음(생략)
STATUS_EXTRA = "extra"      # 규칙에 없는 자리에 낀 토큰


# ==========================================================================
# 문자열 거리
# ==========================================================================

def edit_distance(a, b):
    """Levenshtein 거리. 오타 판정에만 쓰므로 단순 DP 로 충분하다."""
    a = a or ""
    b = b or ""

    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)

    previous = list(range(len(b) + 1))

    for i, ca in enumerate(a, start=1):
        current = [i]
        for j, cb in enumerate(b, start=1):
            current.append(min(
                previous[j] + 1,            # 삭제
                current[j - 1] + 1,         # 삽입
                previous[j - 1] + (ca != cb)  # 치환
            ))
        previous = current

    return previous[-1]


def _threshold(text):
    """이 길이의 단어에서 "오타" 로 봐 줄 최대 거리.

    짧은 단어는 한 글자만 달라도 다른 단어다(`CHN` 과 `SIN` 은 2글자 차이 - 남).
    """
    length = max(len(text or ""), 1)
    if length <= 4:
        return 1
    return 2


def is_typo_of(text, target):
    """text 가 target 의 오타로 보이는가(대소문자 차이 포함)."""
    if not text or not target:
        return False
    if text.lower() == target.lower():
        return True
    return edit_distance(text, target) <= _threshold(target)


# ==========================================================================
# 토큰 규칙
# ==========================================================================

class TokenRule(object):
    """한 슬롯의 규칙. 기본형은 "아무 글자나 와도 되는" 토큰이다."""

    type_name = "any"

    def __init__(self, spec):
        self.spec = dict(spec or {})
        self.role = self.spec.get("role") or self.spec.get("name") or "token"
        self.optional = bool(self.spec.get("optional", False))
        self.repeat = bool(self.spec.get("repeat", False))
        self.case_sensitive = bool(self.spec.get("case_sensitive", True))
        self._hint = self.spec.get("hint")

    # -- 설명 -------------------------------------------------------------

    def describe(self):
        """로그에 찍는 기대값 설명(영어). JSON 의 `hint` 로 덮어쓸 수 있다."""
        return self._hint or self.default_hint()

    def default_hint(self):
        return "any text"

    def placeholder(self):
        """고칠 값을 알 수 없을 때 제안 이름에 넣는 자리표시."""
        return "{" + self.role + "}"

    # -- 판정 -------------------------------------------------------------

    def is_valid(self, text):
        return bool(text)

    def _repair(self, text):
        return None

    def repair(self, text):
        """고칠 값 제안. **반드시 규칙을 만족하는 값만** 돌려준다."""
        if self.is_valid(text):
            return None
        fixed = self._repair(text)
        if fixed and self.is_valid(fixed):
            return fixed
        return None


class LiteralRule(TokenRule):
    """한 글자도 다르면 안 되는 고정 토큰 (`MT`, `MANU`)."""

    type_name = "literal"

    def __init__(self, spec):
        super(LiteralRule, self).__init__(spec)
        self.value = self.spec.get("value", "")

    def default_hint(self):
        return "exactly '{0}'".format(self.value)

    def placeholder(self):
        return self.value

    def is_valid(self, text):
        if self.case_sensitive:
            return text == self.value
        return (text or "").lower() == self.value.lower()

    def _repair(self, text):
        return self.value if is_typo_of(text, self.value) else None


class EnumRule(TokenRule):
    """정해진 값 중 하나여야 하는 토큰 (캐릭터 이름, 의상 부위)."""

    type_name = "enum"

    def __init__(self, spec):
        super(EnumRule, self).__init__(spec)
        self.values = list(self.spec.get("values") or [])

    def default_hint(self):
        return "one of : {0}".format(", ".join(self.values))

    def is_valid(self, text):
        if self.case_sensitive:
            return text in self.values
        lowered = (text or "").lower()
        return any(lowered == v.lower() for v in self.values)

    def _repair(self, text):
        if not text:
            return None

        # 대소문자만 틀린 경우가 가장 흔하다 - 거리 계산 전에 먼저 본다.
        for value in self.values:
            if text.lower() == value.lower():
                return value

        best, best_distance = None, None
        for value in self.values:
            distance = edit_distance(text, value)
            if distance <= _threshold(value) and (best_distance is None or distance < best_distance):
                best, best_distance = value, distance

        return best


class PatternRule(TokenRule):
    """접두사 + 고정 자릿수 숫자 (`Set` + 3자리 -> `Set000` ~ `Set999`)."""

    type_name = "pattern"

    def __init__(self, spec):
        super(PatternRule, self).__init__(spec)
        self.prefix = self.spec.get("prefix", "")
        self.digits = int(self.spec.get("digits", 1))
        flags = 0 if self.case_sensitive else re.IGNORECASE
        self._regex = re.compile(
            "^{0}[0-9]{{{1}}}$".format(re.escape(self.prefix), self.digits), flags)

    def default_hint(self):
        return "'{0}' followed by {1} digit(s) : {0}{2} - {0}{3}".format(
            self.prefix, self.digits, "0" * self.digits, "9" * self.digits)

    def is_valid(self, text):
        return bool(text) and bool(self._regex.match(text))

    def _repair(self, text):
        if not text:
            return None

        # 앞의 글자와 뒤의 숫자를 갈라 다시 조립한다 (`Sett002` -> `Set` + `002`).
        match = re.match(r"^([^0-9]*)([0-9]*)$", text)
        if not match:
            return None

        head, number = match.group(1), match.group(2)

        if not number:
            return None
        if head and not is_typo_of(head, self.prefix):
            return None

        if len(number) > self.digits:
            # 자릿수가 넘치면 뒷자리를 남긴다 (`Set0002` -> `Set002`).
            number = number[-self.digits:]

        return "{0}{1}".format(self.prefix, number.zfill(self.digits))


class RegexRule(TokenRule):
    """직접 쓴 정규식. 고칠 값은 제안하지 않는다(무엇이 맞는지 알 수 없으므로)."""

    type_name = "regex"

    def __init__(self, spec):
        super(RegexRule, self).__init__(spec)
        self.pattern = self.spec.get("regex", ".*")
        flags = 0 if self.case_sensitive else re.IGNORECASE
        self._regex = re.compile(self.pattern, flags)

    def default_hint(self):
        return "matching /{0}/".format(self.pattern)

    def is_valid(self, text):
        return bool(text) and bool(self._regex.match(text))


RULE_TYPES = {
    "literal": LiteralRule,
    "enum": EnumRule,
    "pattern": PatternRule,
    "regex": RegexRule,
    "any": TokenRule,
}


def make_rule(spec):
    """JSON 의 토큰 스펙 -> 규칙 객체. 모르는 타입은 `any` 로 (프로파일이 깨지지 않게)."""
    rule_type = (spec or {}).get("type", "any")
    return RULE_TYPES.get(rule_type, TokenRule)(spec)


# ==========================================================================
# 진단 결과
# ==========================================================================

class TokenResult(object):
    """토큰 하나(또는 비어 있는 슬롯 하나)의 판정."""

    def __init__(self, status, text="", role="", index=None,
                 expected="", suggestion=None, placeholder=""):
        self.status = status
        self.text = text
        self.role = role
        self.index = index          # 이름 안에서 몇 번째 토큰인지(1-based). 누락이면 None
        self.expected = expected
        self.suggestion = suggestion
        self.placeholder = placeholder

    @property
    def ok(self):
        return self.status == STATUS_OK

    def __repr__(self):
        return "TokenResult({0}, {1!r}, role={2!r})".format(
            self.status, self.text, self.role)


class NameReport(object):
    """이름 하나의 진단 결과."""

    def __init__(self, name, profile_name="", pattern=""):
        self.name = name
        self.profile_name = profile_name
        self.pattern = pattern
        self.results = []
        self.warnings = []
        self.suggested_name = ""

    # -- 요약 -------------------------------------------------------------

    @property
    def bad_tokens(self):
        """규칙을 어긴 토큰 텍스트들(잉여 토큰 포함) - 사용자가 눈으로 찾을 목록."""
        return [r.text for r in self.results
                if r.status in (STATUS_BAD, STATUS_EXTRA)]

    @property
    def missing_roles(self):
        """생략된 슬롯의 이름(고정값이면 그 값)."""
        return [(r.placeholder or r.role) for r in self.results
                if r.status == STATUS_MISSING]

    @property
    def ok(self):
        return (not self.bad_tokens) and (not self.missing_roles) and (not self.warnings)

    def __repr__(self):
        return "NameReport({0!r}, ok={1})".format(self.name, self.ok)


# ==========================================================================
# 프로파일
# ==========================================================================

class NameProfile(object):
    """프로파일 JSON 하나를 담고, 이름을 진단한다."""

    def __init__(self, data):
        self.data = dict(data or {})
        self.name = self.data.get("name") or "profile"
        self.description = self.data.get("description") or ""
        self.separator = self.data.get("separator") or "_"
        self.checks = dict(self.data.get("checks") or {})

        self.rules = [make_rule(spec) for spec in (self.data.get("tokens") or [])]

        # 반복 슬롯(`extra`)은 개수가 정해지지 않으므로 정렬에서 빼고 꼬리로 받는다.
        self.fixed_rules = [r for r in self.rules if not r.repeat]
        self.tail_rule = next((r for r in self.rules if r.repeat), None)

        self.pattern = self.data.get("pattern") or self._default_pattern()

    @classmethod
    def from_file(cls, name, loader=None):
        """프로파일 이름으로 읽어 만든다(loader 를 주면 그것으로 읽는다 - 테스트용)."""
        if loader is None:
            from tools.A00470_MaterialTool.app.core import profiles as profile_io
            loader = profile_io.load_profile_data
        return cls(loader(name))

    def _default_pattern(self):
        parts = []
        for rule in self.rules:
            if isinstance(rule, LiteralRule):
                parts.append(rule.value)
            elif rule.repeat:
                parts.append("{" + rule.role + "...}")
            else:
                parts.append("{" + rule.role + "}")
        return self.separator.join(parts)

    # ------------------------------------------------------------------
    # 진단
    # ------------------------------------------------------------------

    def bare_name(self, name):
        """경로와 네임스페이스를 떼어 낸 이름(`|grp|rig:MT_...` -> `MT_...`)."""
        return (name or "").split("|")[-1].split(":")[-1]

    def check(self, name):
        """이름 하나를 진단해 NameReport 를 돌려준다."""
        report = NameReport(name, profile_name=self.name, pattern=self.pattern)

        bare = self.bare_name(name)
        tokens = bare.split(self.separator) if bare else []

        report.results = self._align(tokens)

        warning = self._trailing_digit_warning(tokens, report.results)
        if warning:
            report.warnings.append(warning)

        report.suggested_name = self._suggest(report.results, tokens)

        return report

    def check_many(self, names):
        return [self.check(n) for n in (names or [])]

    # ------------------------------------------------------------------
    # 토큰 <-> 슬롯 정렬
    # ------------------------------------------------------------------

    def _pair_score(self, rule, token):
        if rule.is_valid(token):
            return SCORE_MATCH
        if rule.repair(token):
            return SCORE_SOFT
        return SCORE_MISMATCH

    def _align(self, tokens):
        """DP 로 토큰과 고정 슬롯을 맞춘 뒤 TokenResult 목록을 만든다.

        수는 셋이다 - 슬롯과 토큰을 짝짓기 / 슬롯을 비우기(생략) / 토큰을 버리기(잉여).
        꼬리 반복 슬롯이 있으면 남은 토큰은 공짜로 거기에 들어간다.
        """
        rules = self.fixed_rules
        rows, cols = len(rules), len(tokens)

        neg = float("-inf")
        dp = [[neg] * (cols + 1) for _ in range(rows + 1)]
        back = [[None] * (cols + 1) for _ in range(rows + 1)]
        dp[0][0] = 0

        def relax(i, j, score, step):
            if score > dp[i][j]:
                dp[i][j] = score
                back[i][j] = step

        for i in range(rows + 1):
            for j in range(cols + 1):
                if dp[i][j] == neg:
                    continue

                # 슬롯 i 와 토큰 j 를 짝짓는다.
                if i < rows and j < cols:
                    relax(i + 1, j + 1,
                          dp[i][j] + self._pair_score(rules[i], tokens[j]),
                          ("match", i, j))

                # 슬롯 i 에 올 토큰이 없다(생략).
                if i < rows:
                    penalty = 0 if rules[i].optional else SCORE_MISSING
                    relax(i + 1, j, dp[i][j] + penalty, ("missing", i, None))

                # 토큰 j 가 규칙에 없는 자리에 끼었다.
                if j < cols:
                    relax(i, j + 1, dp[i][j] + SCORE_EXTRA, ("extra", None, j))

        # 마지막 고정 슬롯까지 맞춘 뒤, 남은 토큰은 꼬리 슬롯이 받는다.
        tail_free = self.tail_rule is not None
        best_j, best_score = 0, neg
        for j in range(cols + 1):
            if dp[rows][j] == neg:
                continue
            rest = cols - j
            score = dp[rows][j] + (0 if tail_free else SCORE_EXTRA * rest)
            if score > best_score:
                best_score, best_j = score, j

        # 역추적
        steps = []
        i, j = rows, best_j
        while (i, j) != (0, 0):
            step = back[i][j]
            if step is None:
                break
            steps.append(step)
            kind = step[0]
            if kind == "match":
                i, j = i - 1, j - 1
            elif kind == "missing":
                i = i - 1
            else:
                j = j - 1
        steps.reverse()

        results = []
        for kind, rule_index, token_index in steps:
            if kind == "match":
                rule, token = rules[rule_index], tokens[token_index]
                valid = rule.is_valid(token)
                results.append(TokenResult(
                    STATUS_OK if valid else STATUS_BAD,
                    text=token, role=rule.role, index=token_index + 1,
                    expected=rule.describe(),
                    suggestion=None if valid else rule.repair(token),
                    placeholder=rule.placeholder()))
            elif kind == "missing":
                rule = rules[rule_index]
                results.append(TokenResult(
                    STATUS_MISSING, text="", role=rule.role,
                    expected=rule.describe(),
                    suggestion=rule.placeholder() if isinstance(rule, LiteralRule) else None,
                    placeholder=rule.placeholder()))
            else:
                token = tokens[token_index]
                results.append(TokenResult(
                    STATUS_EXTRA, text=token, role="", index=token_index + 1,
                    expected="not expected at this position"))

        # 꼬리 토큰 (`extra` 슬롯). 꼬리 슬롯이 없으면 전부 잉여다.
        for offset, token in enumerate(tokens[best_j:]):
            index = best_j + offset + 1
            if self.tail_rule is None:
                results.append(TokenResult(
                    STATUS_EXTRA, text=token, index=index,
                    expected="not expected at this position"))
                continue
            valid = self.tail_rule.is_valid(token)
            results.append(TokenResult(
                STATUS_OK if valid else STATUS_BAD,
                text=token, role=self.tail_rule.role, index=index,
                expected=self.tail_rule.describe(),
                placeholder=self.tail_rule.placeholder()))

        return results

    # ------------------------------------------------------------------
    # 꼬리 숫자
    # ------------------------------------------------------------------

    def _trailing_digit_warning(self, tokens, results):
        """이름 맨 끝의 숫자가 마지막 토큰에 **붙어** 있으면 경고 문구를 만든다.

        `_002` 처럼 구분자로 갈라진 숫자는 통과시킨다. `Set002` 처럼 **고정 슬롯이
        원래 숫자로 끝나는** 경우도 통과시킨다 - 그건 규칙이 요구한 숫자다.
        """
        if not self.checks.get("trailing_digit", False):
            return None
        if not tokens:
            return None

        last = tokens[-1]
        if not last or not last[-1].isdigit():
            return None
        if last.isdigit():
            return None     # 언더바로 갈라진 숫자 토큰 - 허용

        # 마지막 토큰을 받은 슬롯을 찾는다(꼬리 슬롯이 아니고, 규칙을 만족하면 통과).
        for result in results:
            if result.index == len(tokens):
                tail_role = self.tail_rule.role if self.tail_rule else None
                if result.ok and result.role and result.role != tail_role:
                    return None
                break

        return ("the name ends with a digit stuck to '{0}' - "
                "separate it with '{1}' ('{2}') or remove it".format(
                    last, self.separator, self._split_trailing_digits(last)))

    def _split_trailing_digits(self, token):
        """`extra3` -> `extra_3`. 꼬리 숫자를 구분자로 떼어 낸 모양."""
        match = re.match(r"^(.*?)([0-9]+)$", token)
        if not match or not match.group(1):
            return token
        return "{0}{1}{2}".format(match.group(1), self.separator, match.group(2))

    # ------------------------------------------------------------------
    # 고친 이름 제안
    # ------------------------------------------------------------------

    def _suggest(self, results, tokens):
        """규칙에 맞게 고친 이름. 고칠 값을 모르는 자리는 `{role}` 로 남긴다."""
        parts = []

        for result in results:
            if result.status == STATUS_EXTRA:
                continue                      # 규칙에 없는 토큰은 뺀다
            if result.status == STATUS_OK:
                parts.append(result.text)
            else:
                parts.append(result.suggestion or result.placeholder or result.role)

        if not parts:
            return ""

        # 꼬리 숫자는 구분자로 떼어 낸 모양을 제안한다.
        if self.checks.get("trailing_digit", False) and tokens:
            last = tokens[-1]
            if parts[-1] == last and last and last[-1].isdigit() and not last.isdigit():
                parts[-1] = self._split_trailing_digits(last)

        return self.separator.join(parts)
