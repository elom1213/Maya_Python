# SetXXX 오브젝트 이름 규칙

> 코스튬 세트(SetXXX) 씬의 마야 오브젝트 이름을 **모두 같은 규칙**으로 짓기 위한 약속이다.
> 이름을 짓는 툴은 `A00330_NamingTool` 의 **Rename > Token** 탭, 프로파일 **`Dnable_Set_v001`** 이다 (5장).

---

## 1. 이름 형식

```
{캐릭터}_{좌우}_{세트}_{파츠}_{넘버링}_{오브젝트종류}
```

토큰은 `_` 로 잇는다. **대소문자까지 아래 표 그대로** 쓴다 (`Top` O / `top` X, `geo` O / `Geo` X).

| 자리 | 토큰 | 쓸 수 있는 값 | 설명 |
|------|------|---------------|------|
| 1 | 캐릭터 | `CHN` `DHA` `LUN` `SIN` `TBM` | 다섯 중 하나 |
| 2 | 좌우 | `l` `r` `n` | 왼쪽 `l`, 오른쪽 `r`. **좌우 구분이 없으면 `n`** (예: 상의, 바지) |
| 3 | 세트 | `Set` + 세 자리 번호 | 예: `Set008` |
| 4 | 파츠 | `Top` `Pants` `Shoes` `Accessory` | 넷 중 하나 |
| 5 | 넘버링 | `01` `02` `03` … / `xx` | 같은 종류 오브젝트가 **여러 개**일 때 두 자리 번호. **하나뿐이면 `xx`** |
| 6 | 오브젝트종류 | `geo` `grp` | 지오메트리 `geo`, 그룹 `grp` |

> 이름에는 **영문 · 숫자 · `_`** 만 쓴다. 다른 글자(`-`, 공백 등)는 마야가 조용히 `_` 로 바꿔 버린다.

---

## 2. 그룹 이름

세트의 여러 파츠를 묶는 그룹은 **파츠 자리를 쓰지 않는다** — 한 파츠의 것이 아니기 때문이다.
그룹은 하나뿐이므로 넘버링은 `xx` 다.

```
{캐릭터}_{좌우}_{세트}_{넘버링}_grp        예: SIN_n_Set008_xx_grp
```

---

## 3. 예시

### 예시 1 — 세트 008 의 신발 · 바지 · 상의 (파츠마다 하나씩)

```
SIN_n_Set008_xx_grp
├── SIN_n_Set008_Shoes_xx_geo
├── SIN_n_Set008_Pants_xx_geo
└── SIN_n_Set008_Top_xx_geo
```

### 예시 2 — 세트 008 의 액세서리가 3 개

```
SIN_n_Set008_xx_grp
├── SIN_n_Set008_Accessory_01_geo
├── SIN_n_Set008_Accessory_02_geo
└── SIN_n_Set008_Accessory_03_geo
```

### 예시 3 — 신발이 좌 · 우 따로 있을 때 (1장 규칙을 그대로 적용)

```
SIN_n_Set008_xx_grp
├── SIN_l_Set008_Shoes_xx_geo
└── SIN_r_Set008_Shoes_xx_geo
```

좌우는 넘버링이 아니라 **좌우 자리(`l` / `r`)** 로 구분한다. 왼쪽 · 오른쪽에 하나씩이면 넘버링은 `xx` 다.

---

## 4. 자주 틀리는 것

| 틀린 이름 | 고친 이름 | 이유 |
|-----------|-----------|------|
| `SIN_Set008_Top_xx_geo` | `SIN_n_Set008_Top_xx_geo` | 좌우 자리를 빼면 안 된다 — 구분이 없으면 `n` |
| `SIN_n_Set008_Top_01_geo` (상의 하나) | `SIN_n_Set008_Top_xx_geo` | 하나뿐이면 번호 대신 `xx` |
| `SIN_n_Set008_Accessory_1_geo` | `SIN_n_Set008_Accessory_01_geo` | 번호는 두 자리 |
| `SIN_n_Set8_Top_xx_geo` | `SIN_n_Set008_Top_xx_geo` | 세트 번호는 세 자리 |
| `sin_n_Set008_top_xx_geo` | `SIN_n_Set008_Top_xx_geo` | 대소문자는 1장 표 그대로 |
| `SIN_n_Set008_Shoes_L_geo` | `SIN_l_Set008_Shoes_xx_geo` | 좌우는 넘버링 자리가 아니라 2번째 자리에, 소문자 `l` / `r` |

---

## 5. 툴로 이름 짓기 — `A00330_NamingTool`

### 5-1. 프로파일 `Dnable_Set_v001`

**Rename > Token** 탭의 Profile 에서 **`Dnable_Set_v001`** 을 고르면 1장 규칙대로 칸 6개가 나온다.
캐릭터 · 좌우 · 파츠 · 오브젝트종류는 **타이핑하지 않고 콤보에서 고른다**(`Enum` 칸) — 오타가 날 수 없다.

```
 Token 1     Token 2   Token 3    Token 4     Token 5     Token 6
 [Enum]      [Enum]    [Custom]   [Enum]      [Numbering] [Enum]
 character   side                 part        Start [1]   type
 [SIN    v]  [n  v]    [Set008]   [Shoes  v]  Pad 0 [2]   [geo v]
 Preview : SIN_n_Set008_Shoes_01_geo -> next node SIN_n_Set008_Shoes_02_geo
```

| 칸 | 할 일 |
|----|-------|
| Token 1 character | 캐릭터 고르기 |
| Token 2 side | `n` / `l` / `r` 고르기 |
| Token 3 | 세트 이름을 **직접 입력** (예: `Set008`) |
| Token 4 part | 파츠 고르기 |
| Token 5 | 번호 — Start `1`, Pad 0 `2` 면 `01, 02, 03 …` |
| Token 6 type | `geo` / `grp` 고르기 |

- 캐릭터 · 좌우 · 파츠 · 오브젝트종류 칸은 **정해진 규칙이라 바꿀 수 없다** — 값 목록을 고치거나, 다른 종류의 칸으로 바꾸거나,
  지울 수 없다(칸 위 `Enum` 콤보가 회색). 값 중에서 고르기만 한다.
- 칸을 바꿔도 **프로파일 파일은 그대로**다 (`Save` 를 눌러야 저장된다). 이번 작업에만 쓰려면 Save 하지 않는다.
- 맨 아래 **`Preview`** 줄에서 첫 이름이 1장 규칙과 맞는지 보고 **Rename** 을 누른다. Undo 한 번으로 되돌아간다.

### 5-2. 지오메트리 — 파츠마다 한 번씩

Token 탭은 Objects 리스트의 오브젝트를 **위에서부터 차례로** 번호 매겨 바꾼다. 파츠가 다르면 이름이 다르므로
**파츠마다 따로** 돌린다.

1. 이름을 지을 지오메트리를 선택 → Objects 의 **Select Base** (리스트 순서 = 번호 순서).
2. 칸을 고른다 — 캐릭터 · 좌우 · `SetXXX` · 파츠 · `geo`.
3. 넘버링:
   - **여러 개**(예시 2) — Token 5 를 `Numbering` 그대로 (`01, 02, 03`).
   - **하나뿐**(예시 1, 3) — Token 5 의 콤보를 `Custom` 으로 바꾸고 `xx` 를 적는다.
4. `Preview` 확인 → **Rename**.

> **주의 — Token 탭은 고른 오브젝트 아래의 transform 자손 이름까지 함께 바꾼다.**
> 지오메트리 아래에 다른 오브젝트가 붙어 있으면 그것도 같은 규칙의 번호 이름이 된다.
> 그래서 **그룹은 Token 탭으로 짓지 않는다**(아래 5-3).

### 5-3. 그룹 — Quick Rename 으로

그룹을 Token 탭으로 바꾸면 안의 지오메트리 이름까지 덮어쓴다. 그룹은 이름 하나만 바꾸는
**Quick Rename > Selection** 탭으로 짓는다.

1. 그룹 **하나만** 선택한다.
2. **Change New** 에 그룹 이름을 적는다 (예: `SIN_n_Set008_xx_grp`). **Start (Index) 는 비워 둔다.**
3. **New Apply** — 선택이 하나이고 Start 가 비었으면 번호 없이 적은 이름 그대로 바뀐다.

(마야에서 직접 이름을 바꿔도 된다. 이름이 2장 형식과 같기만 하면 된다.)

### 5-4. 프로파일 파일

프로파일은 툴 폴더의 `data/token_profiles/Dnable_Set_v001.json` 이다. Enum 칸의 값 목록은 이 파일에 있다.
**규칙(캐릭터 추가 등)은 툴 관리자만 바꾼다** — 공유된 툴에는 값 목록을 고치는 버튼이 없다.
바뀐 규칙은 툴 업데이트로 팀에 다시 나눈다.

```json
{"rule": "enum", "role": "character", "values": ["CHN", "DHA", "LUN", "SIN", "TBM"], "value": "CHN"}
```

`values` · `role` 은 `A00470_MaterialTool` 의 머티리얼 이름 규칙 파일(`data/profiles/Set_v001.json`)과 같은
모양이다.
