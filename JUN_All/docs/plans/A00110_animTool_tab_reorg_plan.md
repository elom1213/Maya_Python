---
title: A00110_animTool 탭 재분류 계획서
aliases: [animTool 탭 정리, tab reorg]
tags: [plan, maya-python, animtool, ui]
updated: 2026-08-14
---

# A00110_animTool — 탭 · 하위 탭 재분류 계획서

> **목적**: 기능은 **하나도 바꾸지 않고** 탭 구조만 논리적으로 다시 나눈다.
> 그 다음 단계로 SmartLayer 의 **Curve Filters** 기능을 이식할 자리를 미리 만들어 둔다.
> (이식 자체는 이 계획서의 범위가 아니다 — 12장에 전제만 정리)

> [!done] **상태: 재분류 완료 — `tools/A00110_animTool_V02` (v02.00, 2026-08-14)**. 11장 1~5단계 끝.
> 재분류판은 **새 툴 폴더 V02** 로 갈랐고, **V01 은 재분류 전(v01.41) 상태로 방치**한다.
> 결정된 것: 상위 탭 이름은 **Key / Timing / Curve / Transfer / Bake / View**(6-3 권장안),
> `Graph` → **`Hold`** 라벨 변경 적용. 6-1(Retime) · 6-2(Curve Bake) 는 **대상이 없어 무효** —
> SmartLayer UI 를 실제로 확인하니 Curve Filters 는 **Smooth / Intensity / Interpolate 3종 +
> Use Quaternions** 가 전부다(12장 갱신).
> **11장 6단계(Curve Filters 이식)도 완료 — V02 v02.01.** 세 필터를 직접 구현해 `Curve` 탭에
> 더했다(Smooth / Intensity / Interp). 구현·검증 내용은 `docs/A00110_animTool_V02.md` §5.4.

---

## 1. 문제

지금 상위 탭은 6개인데 **크기(개념의 넓이)가 서로 다르다.**

| 상위 탭 | 성격 | 하위 |
|---|---|---|
| **Key Edit** | 8개 기능을 담은 **카테고리** | 하위 탭 8 |
| Copy Key / Mirror Key / Bake / Follow / Graph Focus | 기능 **하나** | 없음 |

- `Key Edit` 만 카테고리라서, 새 기능은 자연히 `Key Edit` 로 들어가 계속 비대해진다
  (실제로 v01.37 Euler, v01.40 Pose Key 가 상위 탭에서 이리로 내려왔다).
- 반대로 `Copy Key` · `Mirror Key` · `Follow` 는 **"애니메이션을 다른 오브젝트로 옮긴다"** 는
  같은 개념인데 서로 남남처럼 나열돼 있다.
- Curve Filters 6종이 들어오면 이 불균형이 더 커진다. **지금 정리해 두는 게 맞다.**

---

## 2. 현재 기능 전수 (13개) — 하나도 빠뜨리지 않는다

| # | 기능 | 현재 위치 | 무엇을 하나 |
|---|------|-----------|-------------|
| 1 | Move Keys | Key Edit > Move Keys | 구간 키를 앞/뒤로 이동, 구간 키 삭제 |
| 2 | Fill Keys | Key Edit > Fill Keys | 구간 전 프레임에 키 채우기(기존 키 방치) |
| 3 | Pose Key | Key Edit > Pose Key | 현재 프레임에 6축 포즈 키 |
| 4 | Hold (Graph) | Key Edit > Graph | 그래프 에디터에서 고른 키 구간을 Hold (+`Shift+A`) |
| 5 | Offset & Hold | Key Edit > Offset & Hold | 리스트 컨트롤러 키를 hold + offset 구조로 재배치 |
| 6 | Stagger Offset | Key Edit > Stagger | 리스트 순서 × Offset 계단식 이동 |
| 7 | Euler Filter | Key Edit > Euler | 구간 한정 오일러 필터 |
| 8 | Delete All Keys | Key Edit > Delete All | 리스트 오브젝트의 모든 키 삭제 |
| 9 | Copy Key | Copy Key | Base[i] → Target[i] 구간 키 복사(+축 반전) |
| 10 | Mirror Key | Mirror Key | 좌우 미러(구간 / 현재 프레임, 토큰 페어링) |
| 11 | Bake | Bake | 리스트를 구간 dense 키로 굽기 |
| 12 | Follow | Follow | follower 가 target 을 따라가도록 매치 베이크(blend) |
| 13 | Graph Focus | Graph Focus | 그래프 에디터를 현재 프레임 ± margin 으로 프레이밍 |

---

## 3. 분류 원칙

기준을 **"사용자가 무엇을 바꾸려 하는가"** 하나로 통일한다. 도구 이름이나 구현이 아니라 **의도**다.

| 원칙 | 뜻 |
|------|-----|
| **① 무엇이 바뀌나** | 키의 **존재** / 키의 **시점** / 커브의 **값** / **오브젝트 간 이동** / **굽기** / **보기** |
| **② 상위 탭은 전부 카테고리** | 상위 탭 = 개념, 하위 탭 = 기능. 예외를 두지 않는다 |
| **③ 한 화면 = 한 기능** | 지금 규칙 유지(접이식 아님, 하위 탭) |
| **④ 라벨은 짧게, 전체 이름은 툴팁** | 창 폭 520 기준. `ElideRight` 유지 |

---

## 4. 새 구조 (상위 6 / 하위 13 — Curve Filters 이식 후 16)

```
[Key] [Timing] [Curve] [Transfer] [Bake] [View]
 │      │       │        │          │      │
 │      │       │        │          │      └ Graph Focus
 │      │       │        │          └ Bake
 │      │       │        ├ Copy Key
 │      │       │        ├ Mirror Key
 │      │       │        └ Follow
 │      │       ├ Euler
 │      │       ├ Smooth                                    ← 이식 예정
 │      │       ├ Intensity                                 ← 이식 예정
 │      │       └ Interp                                    ← 이식 예정
 │      ├ Move
 │      ├ Hold
 │      ├ Offset
 │      └ Stagger
 ├ Pose Key
 ├ Fill Keys
 └ Delete All
```

| 상위 탭 | 한 줄 정의 | 하위 탭 (지금) | Curve Filters 이식 후 |
|---------|-----------|----------------|----------------------|
| **Key** | 키를 **만들고 지운다** | Pose Key · Fill Keys · Delete All | (동일) |
| **Timing** | 키를 **시간축에서 재배치**한다 | Move · Hold · Offset · Stagger | (동일) |
| **Curve** | 커브의 **값·형태**를 다듬는다 | Euler | + **Smooth · Intensity · Interp** |
| **Transfer** | 애니메이션을 **다른 오브젝트로** 옮긴다 | Copy Key · Mirror Key · Follow | (동일) |
| **Bake** | 결과를 **키로 굽는다** | Bake | (동일) |
| **View** | **보기**를 돕는다(씬을 안 바꾼다) | Graph Focus | (동일) |

**개수 검산**: 3+4+1+3+1+1 = **13** (2장과 일치). 이식 후 Curve 가 4개가 되어 **16**.

> **View 가 하위 1개인 이유**: `Graph Focus` 는 **씬을 바꾸지 않는 유일한 기능**이다.
> 다른 카테고리에 넣으면 "실행하면 씬이 바뀐다"는 나머지 탭의 공통 성질이 깨진다.
> 앞으로 보기 보조 기능(커브 색/가시성 토글 등)이 생기면 여기로 들어온다.
>
> **하위가 하나인 카테고리(Curve·Bake·View)도 하위 탭 바를 남긴다** — Euler·Bake 페이지에는
> 제목 그룹박스가 없어서, 탭 바가 없으면 기능 이름이 화면에서 사라진다.

---

## 5. 이동 매핑 (기존 13개 — 전부 자리 있음)

| 기능 | 지금 | 새 위치 | 라벨 변경 |
|------|------|---------|-----------|
| Pose Key | Key Edit > Pose Key | **Key > Pose Key** | — |
| Fill Keys | Key Edit > Fill Keys | **Key > Fill Keys** | — |
| Delete All Keys | Key Edit > Delete All | **Key > Delete All** | — |
| Move Keys | Key Edit > Move Keys | **Timing > Move** | `Move Keys` → `Move` |
| Hold | Key Edit > **Graph** | **Timing > Hold** | `Graph` → **`Hold`** (아래 참고) |
| Offset & Hold | Key Edit > Offset & Hold | **Timing > Offset** | `Offset & Hold` → `Offset` |
| Stagger Offset | Key Edit > Stagger | **Timing > Stagger** | — |
| Euler Filter | Key Edit > Euler | **Curve > Euler** | — |
| Copy Key | 상위 탭 | **Transfer > Copy Key** | — |
| Mirror Key | 상위 탭 | **Transfer > Mirror Key** | — |
| Follow | 상위 탭 | **Transfer > Follow** | — |
| Bake | 상위 탭 | **Bake > Bake** | — |
| Graph Focus | 상위 탭 | **View > Graph Focus** | — |

> **`Graph` → `Hold` 로 바꾸는 이유**: 이 하위 탭이 하는 일은 *Hold 만들기* 이고, `Graph` 라는
> 이름은 **`Graph Focus`(View)** 와 헷갈린다. 기능·핫키(`Shift+A`)는 그대로다.
> 라벨만 바꾸는 것이라 되돌리기도 쉽다 — **원치 않으시면 `Graph` 유지 가능**.

---

## 6. 판단이 갈렸던 3가지 → 결정 결과

### 6-1. ~~`Retime` 을 Timing 에 둘까, Curve 에 둘까~~ → **대상 없음**
`curve_retime_widget.py` 라는 **파일명만 보고 기능이라 적었던 것**이 잘못이었다. SmartLayer UI
(v0.91.0 Beta)를 실제로 확인하니 Curve Filters 탭에 **Retime 은 없다**. `remove_spikes_widget` ·
`curve_bake_widget` 도 마찬가지로 화면에 없다 — 파일은 있으나 UI 에 노출되지 않는다.

### 6-2. ~~`Curve Bake` 가 `Fill Keys` 와 겹치나~~ → **대상 없음** (위와 같은 이유)

### 6-3. 상위 탭 이름 → **Key / Timing / Curve / Transfer / Bake / View 채택**
하위 탭 라벨도 함께 정리했다: `Move Keys`→`Move`, `Graph`→**`Hold`**(하는 일이 Hold 이고
`Graph Focus` 와 헷갈렸다), `Offset & Hold`→`Offset`.

---

## 7. 창 폭 · 라벨

- 상위 6개(`Key` `Timing` `Curve` `Transfer` `Bake` `View`)는 지금 6개(`Key Edit`…`Graph Focus`)보다
  **짧아서** 폭 여유가 생긴다.
- 하위 탭 최대는 **Timing 4개**(이식 후 Curve 4개)로, 예전 `Key Edit` 8개보다 적다 → **가장 빡빡했던 곳이 풀렸다.**
- 전체 이름은 지금처럼 **탭 툴팁**에, 폭 부족 시 `ElideRight`.

---

## 8. 구현 방식 — "옮기기만" 한다

구조 변경의 위험을 최소화하는 핵심: **페이지 빌더 함수를 손대지 않는다.**

- 확인 결과 `_build_copy_key_tab` · `_build_mirror_key_tab` · `_build_bake_tab` ·
  `_build_follow_tab` · `_build_graph_focus_tab` 은 **모두 `JUN_mod_fit_tab_page_v01` 을 반환**한다.
  즉 **지금 그대로 하위 탭 페이지로 꽂을 수 있다**(`_build_sub_tabs` 가 `getattr` 로 호출).
- 바뀌는 코드는 사실상 **표(튜플) + 상위 탭 6줄**뿐이다:

```python
# 지금
KEY_EDIT_PAGES = (...8개...)
self.tabs.addTab(self._build_key_edit_tab(), "Key Edit")
self.tabs.addTab(self._build_copy_key_tab(), "Copy Key")
...

# 바꾼 뒤 — 카테고리마다 PAGES 튜플 하나 + 공통 빌더 하나
KEY_PAGES      = (("Pose Key", "...", "_build_pose_key_page"), ...)
TIMING_PAGES   = (("Move", "...", "_build_move_keys_page"), ...)
CURVE_PAGES    = (("Euler", "...", "_build_euler_filter_page"), ...)
TRANSFER_PAGES = (("Copy Key", "...", "_build_copy_key_tab"), ...)   # 기존 빌더 그대로
BAKE_PAGES     = (("Bake", "...", "_build_bake_tab"), )
VIEW_PAGES     = (("Graph Focus", "...", "_build_graph_focus_tab"), )

CATEGORIES = (("Key", KEY_PAGES), ("Timing", TIMING_PAGES), ("Curve", CURVE_PAGES),
              ("Transfer", TRANSFER_PAGES), ("Bake", BAKE_PAGES), ("View", VIEW_PAGES))
```

- `_build_key_edit_tab` 은 **카테고리 공용 빌더**(`_build_category_tab(pages)`)로 일반화한다.
  `_build_sub_tabs` 는 그대로 재사용.
- **위젯 속성 이름(`self.le_start`, `self.cb_translate` …)은 하나도 바꾸지 않는다** → 핸들러·매니저·
  핫키(`Shift+A`)·`hotkey_manager` 모두 무영향.
- `self.key_edit_tabs` 참조는 카테고리별 이름(`self.timing_tabs` 등)으로 바뀌지만, 검색 결과
  **다른 곳에서 쓰이지 않는다**(탭 인덱스에 의존하는 코드 없음 — 확인 완료).

---

## 9. 리스크와 대응

| 리스크 | 대응 |
|--------|------|
| 사용자가 `Copy Key` 탭을 못 찾는다 | 문서 5장에 **old → new 매핑 표**(이 문서 5장)를 그대로 싣고, WORKLOG 에도 남긴다 |
| 창 높이 자동 맞춤(`_fit_window`)이 깨진다 | 상위·하위 **모든 페이지가 `JUN_mod_fit_tab_page_v01`** 이어야 한다는 기존 규칙 유지. 기존 5개 빌더가 이미 그 타입이라 추가 작업 없음 |
| 하위 탭이 2단으로 깊어져 클릭이 늘어난다 | 상위 6 × 하위 최대 5 = **2단 고정**(지금과 같음). 자주 쓰는 기능이 뒤로 숨지 않도록 각 카테고리 **첫 하위 탭을 대표 기능**으로 둔다(Key→Pose Key, Timing→Move, Transfer→Copy Key) |
| 문서/포트폴리오가 옛 구조를 가리킨다 | `docs/A00110_animTool.md` 5장·6장·7장 헤딩 갱신, 포트폴리오 §4-1 문구 확인 |

---

## 10. 검증 계획 (mayapy headless)

`QApplication` 을 `standalone.initialize()` **앞에** 두고 창을 만든 뒤:

1. **기능 보존** — 상위 6개 × 하위 전부를 순회하며 페이지가 예외 없이 생성되는지
2. **위젯 보존** — 재분류 전 스냅샷한 `self.__dict__` 의 **위젯 속성 이름 집합이 그대로**인지
   (이름이 하나라도 사라지면 어떤 핸들러가 깨진 것)
3. **탭 라벨/툴팁** — 상위 6, 하위 19(이식 전 13) 라벨과 툴팁이 표대로인지
4. **실행 경로** — 각 카테고리에서 대표 동작 1개씩 실제 실행(예: Timing>Move 로 키 이동,
   Transfer>Copy Key 로 복사)해 **결과가 재분류 전과 동일**한지
5. **창 크기** — 상위/하위 탭 전환 시 `_fit_window` 가 현재 페이지 높이에 맞추는지(줄지 않는지)
6. **핫키** — `Shift+A`(Hold) 가 그대로 동작하는지

---

## 11. 작업 단계

| 단계 | 내용 | 산출 |
|------|------|------|
| 1 | 이 계획서 확정(6장 3가지 결정) | 이 문서 |
| 2 | `main_window.py` 재분류 — 카테고리 튜플 + `_build_category_tab` | V01 v01.41 → **V02 v02.00** |
| 3 | headless 검증(10장) | 검증 로그 |
| 4 | `docs/A00110_animTool.md` 5~7장 구조 갱신 + old→new 매핑 표 | 문서 |
| 5 | WORKLOG · 메모리 · (해당되면) 포트폴리오 | 문서 |
| 6 | **그 다음** Curve Filters 이식 (별도 계획서) | v01.43~ |

---

## 12. Curve Filters 이식 전제 (다음 단계)

- **원본**: `C:\Users\USER\Documents\maya\scripts\_SmartLayer` (v0.91.0 Beta) — 상위 탭 3개
  (`Smart Layer` · `Extra Tools` · `Curve Filters`).
- **실제 UI 로 확인한 Curve Filters 구성** (스크린샷: `tools/A00110_animTool_V02/ref/ref_01.png` — `ref/` 는 git 제외):

  | 섹션 | 컨트롤 |
  |------|--------|
  | **Use Quaternions** (탭 전역, 기본 ON) | 회전을 오일러 채널별이 아니라 쿼터니언으로 처리(짐벌락 회피) |
  | **Smooth** | `Iterations`(기본 3) · `Strength`(기본 100) · **Rough↔Smooth 양방향 슬라이더**(중앙) · 원클릭 `-100` `-50` `50` `100` |
  | **Intensity** | **Minus↔Plus 양방향 슬라이더**(중앙) 하나 |
  | **Interpolate** | **Ease-In↔Ease-Out** · **Linear↔Ease-In-Out** 슬라이더 2개 + 프리셋 버튼 4개 |

  체인지로그(v0.9)의 서술과 일치한다: gaussian smooth / intensity /
  interpolation(Ease-in, Ease-out, Linear, Ease-in-Out) / 모든 필터가 쿼터니언 지원.
- **이식 대상은 3종 + 전역 옵션 1개.** 새 `Curve` 탭의 하위 탭이 `Euler` 포함 **4개**가 된다.
- **조작 방식이 우리 것과 같다**: 세 필터 모두 **가운데가 0인 양방향 슬라이더**다. 드래그 중에는
  원본 기준으로 다시 계산하고(누적 아님) 조작이 멎으면 한 항목으로 기록하는 **settle 커밋 모델** —
  이 저장소의 `A00110` **Stagger Offset**, `A00380` **Peak** 에서 이미 구현·검증한 패턴을 재사용한다.
  (놓았을 때 중앙 복귀인지 값 유지인지는 실제로 확인할 것.)
- **소스는 컴파일된 `.pyc`(hybrid)** 다. 상용 라이선스 툴이므로 **디컴파일하지 않는다.**
  이 저장소가 해 온 방식대로 — `A00430_DemBone`(논문만 읽고 재구현), 레거시 MEL 이식 —
  **UI 에서 동작을 관찰하고 결과 커브를 실측해 새로 구현**한다.
- **아직 모르는 것 (이식 계획서 전에 실측할 것)**:
  `Iterations` 와 `Strength` 의 관계 / `Intensity` 가 무엇을 기준으로 증폭하는지(평균값·첫 키·이웃 키) /
  `Interpolate` 가 탄젠트를 바꾸는지 키 값을 다시 굽는지 / 대상 선택 규칙(씬 선택인지 그래프 에디터
  키 선택인지) / 쿼터니언 경로가 오일러 채널을 어떻게 되돌려 쓰는지.
