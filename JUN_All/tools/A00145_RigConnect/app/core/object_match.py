# -*- coding: utf-8 -*-
"""
object_match - 이름이 비슷한 **오브젝트** 찾기 (Connect Closest 탭 'Match by Name').

Connect 탭이 어트리뷰트 이름으로 하던 매칭을 오브젝트 이름으로 한다.

    Driver : ["ctrl_L_arm", "ctrl_L_hand"]
    Driven : ["rig:jnt_L_leg", "|grp|rig:jnt_L_arm", "rig:jnt_L_hand"]
    ->       ["|grp|rig:jnt_L_arm", "rig:jnt_L_hand"]   (driver 순서 그대로)

점수 계산은 [`attr_match`](attr_match.py) 를 그대로 쓴다 — 토큰 역색인 + IDF 로
`ctrl_L_arm` 과 `jnt_L_arm` 을 잇고, 양쪽에 다 있는 접두어는 IDF 가 알아서 0 으로
만든다. 이 모듈이 더하는 것은 **오브젝트 이름을 비교 가능한 형태로 만드는 일**뿐이다.

## 왜 이름을 그대로 넘기면 안 되는가

마야 오브젝트 이름은 어트리뷰트 이름과 달리 **경로와 네임스페이스를 달고 다닌다.**

- `|grp|rig:jnt_L_arm` 을 통째로 토큰화하면 `grp` · `rig` 가 토큰으로 섞인다. 한쪽
  리스트에만 경로가 붙어 있으면(리스트를 채운 방법이 달라 흔하다) coverage 가 그만큼
  깎여 **같은 오브젝트인데 문턱을 못 넘는다.**
- 그래서 비교는 **말단 이름**으로 한다(`|` 뒤). 네임스페이스는 옵션이다 —
  `ignore_namespace=True`(기본)면 `rig:jnt_L_arm` -> `jnt_L_arm`. 레퍼런스 리그와
  로컬 리그를 잇는 경우가 이 툴에서는 기본에 가깝다.
- 대신 **결과는 언제나 원래 이름(경로 포함)으로 돌려준다.** 말단 이름만 돌려주면
  동명 노드가 있는 씬에서 엉뚱한 노드를 잡는다 — 비교용 이름과 실제 이름을 갈라 두고,
  매칭 결과의 인덱스로 원래 이름을 되찾는다(동명 노드 안전).

## 짝이 없는 자리

`attr_match` 와 똑같이 `(Null)` 로 채운다. 연결은 `driver[i] <-> driven[i]` 를
**순서로** 짝짓기 때문에, 못 찾은 자리를 그냥 비우면 그 뒤가 통째로 한 칸 밀려
**엉뚱한 오브젝트끼리 조용히 연결된다.**

이 모듈은 **순수 파이썬**이다(maya import 없음). 씬 존재 여부는 연결 단계
(`closest_connector`)가 이미 검사한다.
"""

from . import attr_match


# 표식과 기본 문턱값은 어트리뷰트 매칭과 **같은 것**을 쓴다. 두 화면이 같은 규칙으로
# 동작해야 하고, 값이 갈리면 문서/툴팁도 갈린다.
NULL_TARGET = attr_match.NULL_TARGET
DEFAULT_MIN_SCORE = attr_match.DEFAULT_MIN_SCORE


def compare_name(name, ignore_namespace=True):
    """오브젝트 이름을 비교용 이름으로 줄인다.

        '|grp|rig:jnt_L_arm'  ->  'jnt_L_arm'      (ignore_namespace=True)
        '|grp|rig:jnt_L_arm'  ->  'rig:jnt_L_arm'  (False)

    컴포넌트(`pCube1.vtx[0]`)는 그대로 둔다 — 오브젝트 매칭 대상이 아니지만, 리스트에
    섞여 들어와도 조용히 다른 것으로 바뀌지 않게 한다.
    """
    text = (name or "").split("|")[-1]
    if ignore_namespace:
        node, dot, comp = text.partition(".")
        node = node.split(":")[-1]
        text = node + dot + comp
    return text


def match_objects(sources, candidates, exact=False, unique=True,
                  min_score=DEFAULT_MIN_SCORE, ignore_namespace=True):
    """sources 각 항목에 이름이 가장 비슷한 candidates 항목을 찾는다.

    Args:
        sources: 기준이 되는 오브젝트 이름들(보통 Driver). **순서가 결과 순서다.**
        candidates: 짝을 찾을 오브젝트 이름들(보통 Driven 후보).
        exact: True 면 **이름이 완전히 같은 것만**(유사도 계산 없음, min_score 무시).
        unique: True 면 후보 하나가 두 번 쓰이지 않는다(sources 순서대로 선점).
        min_score: coverage 하한(0~1). 이보다 낮으면 "못 찾음".
        ignore_namespace: True 면 네임스페이스를 뗀 이름으로 비교한다.

    Returns:
        rows: [{"source": 원래 이름, "target": 원래 이름 or None,
                "score": 0~1, "ambiguous": bool, "best": 문턱 미달 최선 후보 or None}, ...]
              길이 = len(sources), 순서 = sources 순서.
    """
    sources = list(sources or [])
    candidates = list(candidates or [])

    src_keys = [compare_name(s, ignore_namespace) for s in sources]
    cand_keys = [compare_name(c, ignore_namespace) for c in candidates]

    if exact:
        matches, unmatched = attr_match.match_exact_names(
            src_keys, cand_keys, unique=unique)
    else:
        matches, unmatched = attr_match.match_attributes(
            src_keys, cand_keys, unique=unique, min_score=min_score)

    # 문턱을 못 넘은 자리의 "최선 후보" 도 로그에 보여 준다(문턱만 낮추면 되는지 판단용).
    best_by_index = dict((row["source_index"], row) for row in unmatched)

    aligned = attr_match.align_matches(src_keys, matches)

    rows = []
    for i, match in enumerate(aligned):
        miss = best_by_index.get(i)
        rows.append({
            "source": sources[i],
            # 비교는 줄인 이름으로 했지만, 돌려주는 것은 **원래 이름**이다.
            "target": candidates[match["index"]] if match else None,
            "score": match["score"] if match else (miss["score"] if miss else 0.0),
            "ambiguous": bool(match and match["ambiguous"]),
            "best": miss["best"] if miss else None,
        })
    return rows


def aligned_targets(rows, null=NULL_TARGET):
    """`match_objects` 결과 -> 짝이 없는 자리를 `null` 로 채운 이름 목록."""
    return [row["target"] if row["target"] else null for row in rows]
