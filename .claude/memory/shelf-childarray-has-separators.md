---
name: shelf-childarray-has-separators
description: 셸프의 childArray 는 버튼만 주지 않는다 — 구분선에 shelfButton 질의를 하면 RuntimeError, 드롭 설치가 거기서 죽는다
metadata:
  type: reference
---

`cmds.shelfLayout(tab, q=True, childArray=True)` 는 셸프의 **모든 자식**을 준다.
버튼뿐 아니라 **구분선(`separator`)** 도 섞여 있다.

```python
cmds.shelfButton("separator21", q=True, command=True)
# RuntimeError: Object 'separator21' not found.
```

드롭 설치 파일(`__dragDrop_<번호>.py`)의 **중복 버튼 제거 루프**가 여기서 죽어
**셸프 버튼이 아예 안 생긴다**. 반드시 감싼다.

```python
for btn in shelf_buttons:
    try:
        cmd = cmds.shelfButton(btn, q=True, command=True)
    except RuntimeError:
        continue
```

★ **구분선을 안 쓰는 셸프에서는 영영 재현되지 않는다.** 내 마야에서 멀쩡하다는 것이
근거가 되지 않는 종류의 버그다 — 2026-09-22 에 남의 PC 에서야 드러났고, 그때
드롭 파일 **55개 전부**가 같은 코드였다(방어 0개).

검증은 `shelfLayout` 이 GUI 전용이라 `mayapy` 로 안 된다. **`maya.cmds` 를 대역으로 세워**
구분선을 섞은 셸프를 흉내 내고, 구분선 질의가 `RuntimeError` 를 던지게 만들면 루프는 검증된다
(`importlib` 로 드롭 파일을 읽어 `install_shelf_button()` 호출). 옛 파일로 돌려 **실제로 실패하는지**
까지 봐야 의미가 있다. 최종 확인은 여전히 사람이 GUI 에서.

자세한 것은 `JUN_All/docs/Release_Layout.md` §5. 배치 쪽은 [[release-layout-launch-py]].
