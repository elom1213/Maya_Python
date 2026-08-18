# A00450_manipulatorTool — Manipulator Tool (사용 안내)

오브젝트를 선택하면 나오는 **이동 / 회전 / 스케일 매니퓰레이터의 축(빨강·초록·파랑) 굵기**를
슬라이더로 **라이브** 조절하고, `Reset` 으로 원래 굵기로 되돌리는 툴이다.

- 버전: `v01.00` (`app/config/version.py`)
- 위치: `JUN_All/tools/A00450_manipulatorTool`
- 형태: 아키텍처 (B) — Maya 내 PySide 툴

---

## 1. 설치 / 실행

### 드래그&드롭 설치
`__dragDrop_A00450.py` 를 Maya 뷰포트로 드래그&드롭 → 현재 셸프에 **`ManipTool`** 버튼 설치.

셸프 아이콘은 `icon/A00450_manipulatorTool.png`(32×32). 없으면 마야 기본 `pythonFamily.png` 로
폴백한다. 벡터 원본은 같은 폴더의 `.svg` 이고, 고칠 때는 svg 를 고친 뒤 `dev/build_icons.py` 로
다시 래스터화한다.

### 코드로 실행
```python
import tools.A00450_manipulatorTool as A00450_manipulatorTool
A00450_manipulatorTool.run(True)     # True 면 DEV_MODE 에서 리로드
```

---

## 2. UI

### Axis Thickness

| 슬라이더 | 하는 일 |
|----------|---------|
| `All` | Move / Rotate / Scale 세 굵기를 **한 번에** 같은 값으로 |
| `Move` / `Rotate` / `Scale` | 그 도구를 쓸 때의 굵기를 **따로** 지정 |

- 슬라이더를 끄는 **동안** 값이 마야에 들어가고 매니퓰레이터가 다시 그려진다(라이브).
- 지금 마야에서 활성인 도구의 줄은 **`▸` 표시 + 강조색**으로 보인다.
- 범위는 `1.0 ~ 20.0`. 하한이 1.0 인 이유는 3장 참고.

### Picking & Size (global)

세 도구가 공유하는 값이라 따로 묶었다.

| 슬라이더 | 하는 일 | 기본값 |
|----------|---------|--------|
| `Pick Radius` | 축 주변 **클릭 판정 반경** | 4.0 |
| `Handle Size` | 축 끝의 화살촉·박스 크기 | 30.0 |
| `Manip Scale` | 매니퓰레이터 **전체 배율** | 1.0 |

> **굵게 한다고 잘 집히는 것은 아니다.**
> `Axis Thickness` 는 **그려지는 두께**이고, 실제로 클릭이 먹는 범위는 `Pick Radius` 다. 둘은 별개다.
> "매니퓰레이터가 잘 안 집힌다" 가 목적이라면 **`Pick Radius` 를 같이 올려야** 한다.

### 버튼

| 버튼 | 하는 일 |
|------|---------|
| `Reset` | **이 창을 연 시점**의 값으로 전부 되돌린다 (굵기·픽·핸들·스케일) |
| `Maya Default` | 마야 공장 초기값 `2.0 / 4.0 / 30.0 / 1.0` 로 되돌린다 |

`Pin` 은 창을 다른 마야 창 위에 고정한다.

---

## 3. 마야가 실제로 무엇을 조절할 수 있는가

전부 `cmds.manipOptions` 하나에 몰려 있다. Maya 2024 `mayapy` 로 실측한 값이다.

| 플래그 | 뜻 | 기본값 | 하한 |
|--------|-----|--------|------|
| `-lineSize` | 축 선의 굵기 | `2.0` | **1.0 미만은 전부 1.0 으로 잘린다** (0 / −1 도 1.0) |
| `-linePick` | 축의 클릭 판정 반경 | `4.0` | 1.0 |
| `-handleSize` | 핸들(화살촉 등) 크기 | `30.0` | 0 은 무시(값 유지) |
| `-scale` | 매니퓰레이터 전체 배율 | `1.0` | 0 은 무시(값 유지) |
| `-forceRefresh` | 지금 떠 있는 매니퓰레이터를 다시 그린다 | — | — |

상한은 사실상 없다(`lineSize 200` 도 그대로 들어간다). 슬라이더 상한은 실용 범위로 정한 값이다.

값을 쓴 뒤에는 **되읽어서** UI 에 반영한다 — 하한 클램프 때문에 "쓴 값 ≠ 들어간 값" 이 될 수 있다.

---

## 4. ⚠️ 이동/회전/스케일별 굵기는 마야에 없다

`manipMoveContext` / `manipRotateContext` / `manipScaleContext` 의 플래그를 전부 확인했지만
크기·굵기 관련은 하나도 없다(`activeHandle` 류뿐). **`manipOptions` 는 전역**이라 세 도구가
같은 값을 공유한다.

그래서 이 툴은 값을 셋으로 나눠 들고 있다가, **도구가 바뀌는 순간 그 도구의 값을 전역에 밀어 넣는다.**

```
ManipState.sizes = {move: 3.0, rotate: 8.0, scale: 5.0}
        │
        └─ scriptJob(event=["ToolChanged", ...])  →  manipOptions(lineSize = sizes[활성 도구])
```

사용자에게는 "도구별로 따로 정한다"로 보이지만, 실제로는 **전역 값 하나를 도구 전환 시점에 갈아
끼우는 것**이다. 마야가 그 이상을 제공하지 않는다. 창을 닫으면 감시가 끊기므로, 그때 마지막으로
적용돼 있던 값이 그대로 남는다(원래대로 돌리려면 닫기 전에 `Reset`).

### 활성 도구 판별의 함정

컨텍스트 이름이 `moveSuperContext` / **`RotateSuperContext`** / `scaleSuperContext` 로,
**회전만 대문자로 시작한다.** 그래서 이름을 소문자로 낮춰 부분 일치로 본다.

또 이 컨텍스트들은 **GUI 마야에서만 생성**된다 — headless(`mayapy`)에서는 `currentCtx()` 가
`None` 이고 `scriptJob` 도 `None` 을 돌려준다. 그래서 감시 등록 실패를 예외가 아니라
**반환값 `None`** 으로 판정하고, 실패하면 로그에 한 줄 남긴 뒤 슬라이더 조작만으로 동작한다.

---

## 5. 구조

```
A00450_manipulatorTool/
├── __dragDrop_A00450.py     # 셸프 버튼 설치
├── launch.py                # run() : 창 재사용(objectName) + brown_dark 테마
├── icon/                    # svg 원본 + 32x32 png
└── app/
    ├── config/version.py
    ├── core/manip_manager.py   # manipOptions 래퍼 + ManipState (UI 무의존)
    └── ui/
        ├── main_window.py      # 창 / 메뉴 / Pin / 로그
        ├── manip_tab.py        # 슬라이더 배선
        └── slider_row.py       # label + slider + spinbox 한 줄 위젯
```

- `QSlider` 는 정수만 다루므로 `1/step` 배로 확대해 정수 칸으로 쓴다(`step=0.1` → 10배).
- 스핀박스는 `setKeyboardTracking(False)` — 타이핑 도중 값이 되쓰이면 `0.1` 이 `0.100` 으로 잘린다.
- 창을 닫으면 `closeEvent` → `ManipTab.shutdown()` 으로 `scriptJob` 을 끊는다.
  늦게 도는 job 이 죽은 위젯을 건드리는 경우까지 `RuntimeError` 로 받아 감시를 정리한다.
