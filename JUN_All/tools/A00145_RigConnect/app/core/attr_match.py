# -*- coding: utf-8 -*-
"""
attr_match - 이름이 비슷한 어트리뷰트 찾기 (Connect 탭 'Match from Source').

오브젝트 A 의 어트리뷰트 목록이 주어졌을 때, 오브젝트 B 의 어트리뷰트 중 **가장 비슷한
이름**을 A 의 순서 그대로 찾아 준다.

    A: ["brow_up", "brow_down"]
    B: ["lod0_mesh_body_eye_L_up", "lod0_mesh_body_eye_L_down",
        "lod0_mesh_body_brow_up",  "lod0_mesh_body_brow_down"]
    ->  ["lod0_mesh_body_brow_up", "lod0_mesh_body_brow_down"]

이 모듈은 **순수 파이썬**이다(maya import 없음). 그래서 DCC 없이 단독으로 테스트/벤치마크할
수 있고, UI 와도 완전히 분리된다.

## 왜 편집 거리(Levenshtein/difflib)를 쓰지 않는가

가장 단순한 방법은 모든 (A, B) 쌍의 문자열 유사도를 재는 것이다. 하지만 어트리뷰트가
1000개씩 주어지면 1000 x 1000 = 100만 쌍이고, 쌍마다 O(L^2) 짜리 편집 거리를 돌리면
**O(n·m·L^2)** — 파이썬에서 분 단위다. 실용적이지 않다.

게다가 정확도도 낮다. `brow_up` 과 `lod0_mesh_body_brow_up` 은 길이 차가 커서 편집 거리
기준으로는 "많이 다른" 문자열인데, 사람이 보기엔 명백히 같은 것을 가리킨다.

## 이 모듈의 방식 — 역색인(inverted index) + IDF 가중 토큰 매칭

1. 이름을 토큰으로 쪼갠다. 구분자(`_`, `-`, `.`)와 camelCase 경계 양쪽을 본다.
   `lod0_mesh_body_brow_up` -> `[lod0, mesh, body, brow, up]`
   `browInnerUp`            -> `[brow, inner, up]`
   덕분에 표기 스타일이 달라도(`browUp` vs `brow_up`) 매칭된다.
2. 후보(B) 전체를 **한 번만** 훑어 `토큰 -> 후보 인덱스` 역색인을 만든다.
3. 토큰마다 **IDF** 가중치 `log(1 + m/df)` 를 준다. `lod0` `mesh` `body` 처럼 모든 후보에
   나오는 토큰은 가중치가 0 에 가깝고, `brow` 처럼 드문 토큰이 점수를 지배한다.
   **"흔한 접두어는 자동으로 무시된다"** — 접두어 목록을 사람이 지정할 필요가 없다.
4. 질의(A 의 어트리뷰트 하나)는 자기 토큰의 포스팅 리스트만 모아 **후보 전체가 아니라 그
   토큰을 공유하는 소수만** 점수 계산한다.
5. 점수 = `coverage` (질의의 IDF 중 후보가 설명하는 비율, 0~1) 를 주 지표로 삼고,
   precision / 연속 토큰 / 접미 일치 / 부분 문자열 / 길이 근접을 **작은 가산점**으로 얹어
   동점을 가른다. 가산점은 전부 coverage 보다 훨씬 작아 순위를 뒤집지 못한다.

복잡도는 아래 `complexity_notes()` 와 `docs/A00145_RigConnect.md` 참고.
"""

import heapq
import math
import re
from difflib import SequenceMatcher


# 구분자(영숫자가 아닌 모든 문자)로 자르고, 다시 camelCase 경계에서 자른다.
_SEPARATOR = re.compile(r"[^0-9A-Za-z]+")
_CAMEL = re.compile(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])")

# 순위용 가산점. 전부 coverage(0~1) 보다 작아 주 지표를 뒤집지 않는다.
PRECISION_WEIGHT = 0.25     # 후보 쪽도 질의로 설명되는가 (짧고 딱 맞는 후보 선호)
BONUS_CONTIGUOUS = 0.05     # 질의 토큰이 후보에 그 순서 그대로 연속 등장
BONUS_SUFFIX = 0.03         # 후보가 질의 토큰으로 끝난다 (접두어 규칙 이름에 흔함)
BONUS_SUBSTRING = 0.04      # 질의 문자열이 후보에 그대로 들어 있다
LENGTH_WEIGHT = 0.02        # 길이가 비슷할수록 조금 유리

# 이 아래 coverage 는 "못 찾음" 으로 본다 (UI 에서 조절 가능).
DEFAULT_MIN_SCORE = 0.4

# 폴백(문자 단위 비교) 하한과 척도 변환.
#
# difflib 비율은 coverage 와 **척도가 다르다**. 아무 관계 없는 두 이름도 글자만 겹치면
# 0.4~0.5 가 예사로 나온다(예: identification vs wibble_frobnicate = 0.45). 그대로
# min_score 와 비교하면 엉뚱한 매칭이 통과한다. 그래서 0.5 를 0 으로 놓고 1.0 을 1 로
# 늘려, 같은 문턱값이 양쪽에서 같은 뜻을 갖게 만든다.
_FALLBACK_FLOOR = 0.5


def _scale_ratio(ratio):
    """difflib 비율(0~1)을 coverage 와 같은 척도로 옮긴다. 0.5 이하는 0."""
    return max(0.0, (ratio - _FALLBACK_FLOOR) / (1.0 - _FALLBACK_FLOOR))

# 1등과 coverage 가 이 차이 안이면 "동점" 으로 보고 모호하다고 표시한다.
_AMBIGUOUS_EPS = 1e-9


def tokenize(name):
    """이름을 소문자 토큰 리스트로 쪼갠다 (순서 보존).

    >>> tokenize("lod0_mesh_body_brow_up")
    ['lod0', 'mesh', 'body', 'brow', 'up']
    >>> tokenize("browInnerUp")
    ['brow', 'inner', 'up']
    """
    tokens = []

    for chunk in _SEPARATOR.split(name or ""):
        if not chunk:
            continue
        for piece in _CAMEL.split(chunk):
            if piece:
                tokens.append(piece.lower())

    return tokens


def _is_subsequence_contiguous(needle, haystack):
    """needle 이 haystack 안에 **연속으로** 등장하는가 (둘 다 토큰 리스트)."""
    n, h = len(needle), len(haystack)
    if not n or n > h:
        return False
    first = needle[0]
    for i in range(h - n + 1):
        if haystack[i] == first and haystack[i:i + n] == needle:
            return True
    return False


class AttributeIndex(object):
    """후보 이름 목록에 대한 역색인. **한 번 만들어 여러 질의에 재사용한다.**

    이게 이 모듈의 핵심이다 — 질의마다 후보 전체를 훑지 않기 때문에 n 개 질의의 비용이
    n x m 이 아니라 n x (토큰을 공유하는 후보 수) 로 줄어든다.
    """

    def __init__(self, names):
        self.names = list(names or [])

        count = len(self.names)

        self.tokens = []        # 후보별 토큰 리스트(순서 보존)
        self.token_sets = []    # 후보별 토큰 집합(교집합 계산용)
        self.lower = []         # 후보별 소문자 원문(부분 문자열 판정용)
        self.postings = {}      # 토큰 -> [후보 인덱스, ...]

        for j, name in enumerate(self.names):
            tokens = tokenize(name)
            token_set = set(tokens)

            self.tokens.append(tokens)
            self.token_sets.append(token_set)
            self.lower.append((name or "").lower())

            for token in token_set:
                self.postings.setdefault(token, []).append(j)

        # IDF: 흔한 토큰일수록 0 에 가깝다.
        self.idf = dict(
            (token, math.log(1.0 + count / float(len(posting))))
            for token, posting in self.postings.items())

        # 후보에 아예 없는 토큰은 "가장 드문 토큰" 취급 (df = 1).
        self.unknown_idf = math.log(1.0 + count) if count else 1.0

        # 후보별 IDF 총합 (precision 의 분모)
        self.weight = [sum(self.idf[t] for t in ts) for ts in self.token_sets]

    def __len__(self):
        return len(self.names)

    # ------------------------------------------------------------ 점수

    def _token_idf(self, token):
        return self.idf.get(token, self.unknown_idf)

    def _score(self, j, q_tokens, q_set, q_weight, q_lower):
        """후보 j 의 (순위 점수, coverage). 공유 토큰이 없으면 (0, 0)."""

        candidate_set = self.token_sets[j]

        shared = 0.0
        for token in q_set:
            if token in candidate_set:
                shared += self._token_idf(token)

        if shared <= 0.0:
            return 0.0, 0.0

        coverage = shared / q_weight if q_weight > 0 else 0.0
        precision = shared / self.weight[j] if self.weight[j] > 0 else 0.0

        rank = coverage + PRECISION_WEIGHT * precision

        # --- 동점을 가르는 작은 가산점들 ---
        candidate_lower = self.lower[j]

        if q_lower and q_lower in candidate_lower:
            rank += BONUS_SUBSTRING

        # 연속/접미 판정은 coverage 가 높을 때만 의미가 있어 그때만 계산한다(비용 절약).
        if coverage > 0.999:
            candidate_tokens = self.tokens[j]
            if _is_subsequence_contiguous(q_tokens, candidate_tokens):
                rank += BONUS_CONTIGUOUS
            if candidate_tokens[-len(q_tokens):] == q_tokens:
                rank += BONUS_SUFFIX

        longest = max(len(candidate_lower), len(q_lower)) or 1
        rank += LENGTH_WEIGHT * (1.0 - abs(len(candidate_lower) - len(q_lower)) / float(longest))

        return rank, coverage

    # ------------------------------------------------------------ 질의

    def _gather(self, q_set, q_weight, min_score):
        """질의 토큰을 공유하는 후보 인덱스 집합.

        **IDF 질량 기반의 정확한 가지치기**를 쓴다. 드문(=IDF 높은) 토큰부터 포스팅을
        모으다가, *아직 안 모은* 토큰들의 IDF 합이 `min_score * q_weight` 에 못 미치면
        멈춘다. 그 시점 이후의 토큰만 공유하는 후보는 coverage 가 문턱을 넘을 수
        **없으므로**, 버려도 문턱 이상의 정답을 놓치지 않는다(휴리스틱이 아니라 증명 가능).

        실전 효과: `lod0` `mesh` `body` 같은 보일러플레이트 토큰은 IDF 가 0 에 가까워
        항상 뒤로 밀리고, 그 거대한 포스팅 리스트는 아예 읽지 않는다.
        """
        present = [t for t in q_set if t in self.postings]
        if not present:
            return set()

        # 포스팅이 짧다 == 드물다 == IDF 가 높다. 정렬 키를 df 로 쓰면 IDF 내림차순과 같다.
        present.sort(key=lambda t: len(self.postings[t]))

        remaining = sum(self._token_idf(t) for t in present)
        need = min_score * q_weight

        gathered = set()
        for token in present:
            # 최소 하나는 모은다(못 찾은 질의의 "가장 가까운 후보" 보고를 위해).
            if gathered and remaining < need:
                break
            gathered.update(self.postings[token])
            remaining -= self._token_idf(token)

        return gathered

    def _fallback(self, name, top_k):
        """토큰이 하나도 안 겹칠 때만 도는 문자 단위 비교 (드문 경로).

        `browup` 처럼 구분자 없이 붙여 쓴 이름이나 철자가 살짝 다른 이름을 구제한다.

        SequenceMatcher 는 두 번째 시퀀스를 캐시하므로 질의를 seq2 에 고정하고 후보를
        갈아 끼운다. real_quick_ratio / quick_ratio 로 값싸게 걸러 낸다(둘 다 실제
        비율의 상한이라, 이 단계에서 버려도 정답을 놓치지 않는다).

        점수는 `_scale_ratio` 로 coverage 와 같은 척도에 올려 돌려준다.
        """
        low = (name or "").lower()
        if not low:
            return []

        matcher = SequenceMatcher(None, "", low, autojunk=False)
        scored = []

        for j, candidate in enumerate(self.lower):
            matcher.set_seq1(candidate)
            if matcher.real_quick_ratio() < _FALLBACK_FLOOR:
                continue
            if matcher.quick_ratio() < _FALLBACK_FLOOR:
                continue
            score = _scale_ratio(matcher.ratio())
            if score > 0.0:
                scored.append((score, score, j))

        return heapq.nlargest(top_k, scored)

    def query(self, name, top_k=8, min_score=0.0):
        """name 과 가장 비슷한 후보 상위 top_k.

        min_score 를 주면 그 문턱을 못 넘는 것이 확실한 후보를 수집 단계에서 건너뛴다
        (`_gather` 참고). 문턱 이상의 결과는 그대로 나온다.

        Returns:
            [(순위 점수, coverage, 후보 인덱스), ...] — 순위 내림차순.
        """
        q_tokens = tokenize(name)
        if not q_tokens:
            return []

        q_set = set(q_tokens)
        q_weight = sum(self._token_idf(t) for t in q_set)
        q_lower = (name or "").lower()

        gathered = self._gather(q_set, q_weight, min_score)
        if not gathered:
            return self._fallback(name, top_k)

        scored = []
        for j in gathered:
            rank, coverage = self._score(j, q_tokens, q_set, q_weight, q_lower)
            if coverage > 0.0:
                scored.append((rank, coverage, j))

        return heapq.nlargest(top_k, scored)


# =========================================================== 공개 API

def match_attributes(sources, candidates, unique=True,
                     min_score=DEFAULT_MIN_SCORE, top_k=8):
    """sources 각 항목에 가장 비슷한 candidates 항목을 **sources 순서대로** 찾는다.

    Args:
        sources: 오브젝트 A 의 어트리뷰트 이름들(찾고 싶은 것). 순서가 결과 순서다.
        candidates: 오브젝트 B 의 어트리뷰트 이름들(찾을 대상).
        unique: True 면 후보 하나가 두 번 쓰이지 않는다(source 순서대로 greedy 선점).
        min_score: coverage 하한. 이보다 낮으면 "못 찾음" 으로 본다.
        top_k: 후보 하나당 보관할 상위 후보 수. unique 모드에서 이미 쓰인 후보를
            건너뛰고 다음 후보로 넘어가는 데 쓰인다.

    Returns:
        (matches, unmatched)
        matches  : [{"source", "target", "index", "score", "ambiguous"}, ...]
                   sources 순서. `ambiguous` 는 같은 coverage 를 가진 후보가 또 있어
                   가산점으로만 승부가 갈렸다는 뜻(이름이 변별력이 없는 경우).
        unmatched: [{"source", "best", "score"}, ...] — best 는 문턱을 못 넘은 최선 후보
    """
    index = AttributeIndex(candidates)

    matches = []
    unmatched = []
    used = set()

    for source in (sources or []):

        hits = index.query(source, top_k=top_k, min_score=min_score)

        best_name = index.names[hits[0][2]] if hits else None
        best_score = hits[0][1] if hits else 0.0

        chosen = None
        for _rank, coverage, j in hits:
            if coverage < min_score:
                break               # 내림차순이라 이후는 볼 필요 없다
            if unique and j in used:
                continue
            chosen = (coverage, j)
            break

        if chosen is None:
            unmatched.append({"source": source,
                              "best": best_name,
                              "score": best_score})
            continue

        coverage, j = chosen
        used.add(j)

        # 1등과 coverage 가 같은 후보가 또 있으면 이름만으로는 가릴 수 없었다는 뜻.
        ambiguous = sum(1 for _r, c, _j in hits
                        if c >= coverage - _AMBIGUOUS_EPS) > 1

        matches.append({"source": source,
                        "target": index.names[j],
                        "index": j,
                        "score": coverage,
                        "ambiguous": ambiguous})

    return matches, unmatched


def complexity_notes():
    """이 알고리즘의 복잡도 요약 (문서/About 에서 그대로 쓴다)."""
    return [
        "n = source attributes, m = candidate attributes,",
        "t = tokens per name (small constant), L = name length,",
        "g = candidates sharing a token with the query (g << m in practice).",
        "",
        "Index build (once) : O(m * L)",
        "Per query          : O(g * t + g * log k)",
        "Total              : O(m * L + n * (g * t + g * log k))",
        "Worst case (every name shares a rare token) : O(n * m * t)",
        "Naive pairwise edit distance, for comparison: O(n * m * L^2)",
        "",
        "min_score prunes g exactly: token postings are read rarest-first and",
        "stop once the remaining tokens cannot lift coverage to the threshold,",
        "so boilerplate tokens (lod0, mesh, body) are never scanned.",
    ]
