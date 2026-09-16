---
name: wip-a00310-searchtool-rules
description: "A00310_SearchTool Search > Rules — 규칙 레지스트리 구조(규칙 추가 = 함수 하나 + register 한 줄, UI 무수정)와 Standalone 규칙"
metadata:
  node_type: memory
  type: project
---

`A00310_SearchTool` 은 **상위 탭 Selection / Search**, Search 아래 **하위 탭 Token / Rules**
(v01.02, 2026-09-16). Token 은 예전 Search(이름 토큰) 그대로고, **Rules 가 새로 붙은 쪽**이다.
접두사 — Selection `sel_*` · Token `sch_*` · Rules `rul_*`.

**★ 규칙은 늘어나는 것이 전제다.** `app/core/select_rules.py` 의 레지스트리에 모이고,
UI 는 `all_rules()` 를 **그대로 그린다**. 그래서 규칙 추가 = **함수 하나 + `register()` 한 줄**,
**UI 코드는 안 고친다.** (테스트로 고정: register 후 창을 다시 띄우면 목록에 저절로 나타난다.)

```python
def _rule_x(obj):
    return (False, "왜 안 맞는지") if 안맞으면 else (True, "")

register(SelectRule("x", "X", "한 줄 설명.", _rule_x))
```

- 판정 함수는 **`(맞는가, 이유)`** 를 돌려준다. 이유를 함께 주는 것이 핵심 — 로그에
  "빠진 것마다 왜" 가 찍힌다("3개 맞았다" 보다 쓸모 있다). UI 는 앞 20줄만 적고 나머지는 개수로.
- 규칙을 **여러 개 고르면 AND**(`filter_objects(objects, keys)`).
- `select_by_rules(objects, keys, invert)` → `(선택한 것, [(오브젝트, 이유), ...])`.

**규칙 `Standalone`** — 연결도 히스토리도 없는 노드. 잡아내는 것은 컨스트레인트(걸린 쪽 **+
드라이버 쪽**) · 디포머(`geometryFilter` 상속 전부) · 히스토리 · 어트리뷰트 연결(**양방향**).
통과시키는 것은 머티리얼 배정 · 디스플레이 레이어/셋 멤버십 · 부모가 있는 것.
판정에 밟은 함정은 전부 [[node-purity-signals]] 에 있다 — **그걸 먼저 읽을 것.**

> 이름은 사용자가 `Get Pure` 를 제안했고 "더 좋은 이름이면 그걸로" 라 해서 `Standalone` 으로
> 놓았다. `Get` 은 이 툴에서 **리스트를 채우는 버튼 이름**이라 규칙 이름에 들어가면 한 단어가
> 두 뜻이 되고, `Pure` 만으로는 무엇으로부터 순수한지가 안 드러난다. 되돌리려면
> `register(...)` 의 **라벨 인자 한 줄**만 바꾸면 된다.

검증: 규칙 판정 19케이스 + UI 13항목(mayapy + 오프스크린 Qt) 전부 통과. **마야 GUI 육안 확인은
아직.** 관련: [[qt-exclusive-radio-uncheck-ignored]], [[framework-log-widget]]
