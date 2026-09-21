---
name: mplug-asmobject-lifetime
description: MPlug.asMObject() 데이터는 그 MObject 가 살아 있는 동안만 유효 — 지역 변수로 두고 MFnMesh 만 반환하면 쓰레기 값을 읽는다
metadata:
  type: reference
---

`MPlug.asMObject()` 가 돌려준 데이터는 **그 MObject 가 살아 있는 동안만** 유효하다.

```python
def bad(plug):
    data = plug.asMObject()
    return om.MFnMesh(data)      # data 가 여기서 풀린다

pts = bad(plug).getPoints()      # 1e19 같은 쓰레기 값이 섞여 나온다
```

실제로 겪었다 — 위치 차이가 `inf` / `1e19` 로 찍히고, 값이 호출마다 달라진다.
**MObject 를 호출부가 붙들고 있다가 다 읽은 뒤에 놓아야 한다.**

```python
data, fn = open_mesh(plug)
points = fn.getPoints(om.MSpace.kObject)
del fn, data
```

덤: 마야 standalone(mayapy) 에서는 `cmds.refresh()` 로 DG 가 평가되지 않는다.
셰이프의 현재 값을 보려면 `shape.outMesh` 같은 **플러그를 읽어 평가를 강제**한다
([[mayapy-headless-verify]]).
