---
name: qt-clicked-passes-checked-bool
description: "QPushButton.clicked 는 checked(bool)를 넘긴다 — 기본 인자를 가진 슬롯에 직접 연결 금지"
metadata:
  node_type: memory
  type: reference
---

`QAbstractButton.clicked` 는 **`checked`(bool)** 를 함께 emit 한다. PySide 는 슬롯의 시그니처를 보고
받을 수 있는 만큼 인자를 넘기므로,

```python
def on_connect(self, reverse=False):   # 위험
    ...
btn.clicked.connect(self.on_connect)   # checked 가 reverse 로 들어갈 수 있다
```

처럼 **기본값 인자를 가진 슬롯에 직접 연결하면 그 bool 이 옵션 인자로 새어 들어간다.** 체크 불가
버튼이면 값이 항상 False 라 "우연히" 동작해, 나중에 버튼을 checkable 로 바꾸는 순간 조용히 깨진다.

**How to apply:** 옵션이 다른 두 동작은 **방향별로 얇은 슬롯을 따로** 두고 공통 구현을 부르게 한다.

```python
def on_connect_attrs(self):          self._connect_in_direction("src", "dst")
def on_connect_attrs_reverse(self):  self._connect_in_direction("dst", "src")
```

`lambda _checked=False, x=v: ...` 로 흡수하는 방법도 있고, 이 저장소에도 그 패턴이 쓰인다
(A00145 Match 탭의 Create 버튼). 슬롯이 여러 줄이면 위처럼 이름 있는 슬롯이 읽기 좋다.

사례: A00145_RigConnect v01.24 양방향 Connect ([[wip-a00145-connect-both-directions]]).
