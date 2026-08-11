# AdvancedSkeleton — MetaHuman Animator 창의 `Connect Face Animation` / `Bake to standard Face Controls` 알고리즘 분석

> 대상 코드: `C:\Users\USER\Desktop\JP\0020_maya_plugin\0040_AdvancedSkeleton`
> AdvancedSkeleton **Version 6.801** (`AdvancedSkeleton.mel` 헤더)
> 작성일: 2026-08-11
> 동기: **UE 5.7 에서 커브가 베이크된 MetaHuman 페이셜 애니메이션**을 마야 MetaHuman 페이셜
> 컨트롤러에 옮기려고 이 두 버튼을 썼는데, 의도대로 베이크되지 않는 경우가 있어 원인을 찾기 위함.

---

## 0. 결론 먼저

**이 두 버튼은 "커브 → 컨트롤러" 범용 리타깃 도구가 아니다.** `MetaHuman Animator` 가 뱉는
**특정 이름 규약의 FBX** 를 AdvancedSkeleton 페이스 리그에 붙이기 위한, **손실을 감수한 근사 변환**이다.

1. **`Connect Face Animation`** — 씬에 있는 `root_CTRL_expressions_*` **애니메이션 커브 노드**를
   복제해서 MetaHuman ControlPanel 컨트롤(`CTRL_L_brow_down` 등)의 `translateY`/`translateX` 에
   **직접 connectAttr** 한다. 매핑은 코드에 하드코딩된 **104개 이름 × L/R** 이 전부다.
2. **`Bake to standard Face Controls`** — 그렇게 만들어진 ControlPanel → SDK → `blendWeighted` 네트워크에서
   **"MetaHuman 패널이 기여한 몫만" 골라 새 blendWeighted 로 합산**하고, 그걸 임시 transform 의 `.tx` 에
   물려 `bakeResults` 한 뒤, 결과 키를 AS 표준 페이스 컨트롤(`ctrlBrow_R.translateX` 등)에 `pasteKey` 한다.

**정확히 베이크되지 않는 근본 이유는 세 층이다.**

| 층 | 내용 |
|----|------|
| **① 구조적** | MetaHuman 은 `board control → raw control(CTRL_expressions_*)` 이 다대다 매핑이다. AS 는 그 **역방향**을 raw 하나당 board 하나로 되돌린다 — 원리상 완전 복원이 불가능하다. |
| **② 커버리지** | 매핑 테이블이 **104개**뿐이다. 코드 주석이 "Skip / UnKnown / no equivalent" 로 명시한 항목들은 **의도적으로 버려진다**. 나머지는 `warning` 만 뜨고 무시된다. |
| **③ 알고리즘 손실** | 양방향(±) 컨트롤을 만들려고 **0 근처 키를 잘라내고 → 값을 -1 배 → `pasteKey -option merge`** 하는 휴리스틱을 쓴다. 키가 촘촘하지 않거나 양쪽이 동시에 0이 아니면 **값이 덮어써진다**. |

거기에 더해, 아래 6장에 정리한 **조용히 실패하는 지점**(로그도 안 남는 skip)과 **실제 코드 버그 1건**
(`tongueTwistRight` 의 병합 타깃 누락)이 있다.

---

## 1. 코드 위치

세 파일에 **완전히 동일한 사본**이 들어 있다 (바이트 단위 동일함을 확인). 어느 UI 에서 열든 같은 코드이며,
**패치한다면 세 곳 모두** 고쳐야 한다.

| proc | AdvancedSkeleton.mel | panel/panel.mel | picker/picker.mel |
|------|----------------------|-----------------|-------------------|
| `asMetaHumanAnimatorUI` | 15021 | — | — |
| `asMetaHumanAnimatorConnect` | **15097** | 4964 | 5685 |
| `asMetaHumanAnimatorConnectHead` | 15059 | 4926 | 5647 |
| `asMetaHumanAnimatorDeleteAnimation` | 15318 | — | — |
| `asMetaHumanAnimatorBake` | **15343** | 5210 | 5931 |

관련 헬퍼: `asFaceAddMetaHumanControlPanel` (46753), `asDsSdk` (64627),
`asEnsureOutputBlendWeighted` (65463), `asCtrlToBw` (65491), `asGoToBuildPoseOptions` (12640).

---

## 2. 전제: 리그가 어떤 모양이어야 하는가

### 2-1. MetaHuman ControlPanel 이 붙어 있어야 한다

`asFaceAddMetaHumanControlPanel` 이 `AdvancedSkeletonFiles/div/asMetaHuman.ma` 를 임포트한다.
이 파일에는 **`CTRL_*` transform 177개**(MetaHuman 페이스 보드 그대로의 이름)가 들어 있고,
`GRP_faceGUI` / `FRM_faceGUI` 아래에 놓인다. 각 컨트롤은 `translateX/Y` 만 열려 있고
**translate limit 이 -1~1** 로 걸려 있다(예: `CTRL_L_eye` → `.mntl -1 -1 0`, `.mxtl 1 1 0`).

`Connect` 는 시작할 때 이걸 확인한다:

```mel
if (!`objExists ($nameSpace+"FRM_faceGUI")`)
    error ($nameSpace+"FRM_faceGUI not found. The rig does not have MetaHuman ControlPanel added.");
```

### 2-2. 패널 → AS 컨트롤의 구동 그래프

`asFaceAddMetaHumanControlPanel` 이 `asDsSdk` 를 수백 번 호출해 SDK 를 건다. `asDsSdk` 는
**드라이버 쪽에 blendWeighted 가 있으면 그 output 을 드라이버로 삼는다**:

```mel
$driverBw = `asCtrlToBw $driver`;                 // CTRL_R_brow_down.ty -> bwCTRL_R_brow_down_translateY
if (`objExists $driverBw`) $driveSource = $driverBw+".output";
```

결과적으로 그래프는 항상 이 모양이다. **Bake 는 정확히 이 모양을 가정하고 역추적한다.**

```
CTRL_R_brow_down.translateY
        │
        ▼
bwCTRL_R_brow_down_translateY   (blendWeighted, 패널 컨트롤의 "출력 bw")
        │ .output
        ▼
  animCurveUU  (SDK 커브: 드라이버값 → 드리븐값, 선형 2키)
        │
        ▼
bwSDKctrlBrow_R_translateX      (blendWeighted, 드리븐 쪽 "입력 합산 bw")
        │
        ▼
SDKctrlBrow_R.translateX  →  ctrlBrow_R  (실제 AS 페이스 컨트롤)
```

- 하나의 패널 컨트롤이 **여러 AS 컨트롤 어트리뷰트**를 동시에 구동할 수 있다.
  예: `CTRL_R_brow_down.ty → ctrlBrow_R.tx (가중치 -0.9)` **와** `→ ctrlBrow_R.ty (-0.1)`.
- 반대로 하나의 AS 컨트롤 어트리뷰트에 **여러 드라이버의 SDK 커브가 blendWeighted 로 합산**된다
  (MetaHuman 패널 + Emotions + Phonemes + 애니메이터 수동값 …).

---

## 3. `Connect Face Animation` — 알고리즘

### 3-1. 입력 요구사항 (여기서 대부분 실패한다)

```mel
string $requiredObj[]={"root"};
for ($obj in $requiredObj)
    if (!`objExists $obj`)
        error ("Required object:\""+$obj+"\" does not exists. Make sure a MetaHuman-Animator FBX-Animation file is imported.");
...
$a = "root_CTRL_expressions_" + $as[$i] + $side;      // 예: root_CTRL_expressions_browDownL
if (!`objExists $a`) { warning (...); continue; }
```

즉 씬에 다음이 **그 이름 그대로** 있어야 한다.

| 필요한 것 | 정확한 형태 |
|-----------|-------------|
| 노드 | `root` — **네임스페이스 없이**, 정확히 이 이름 |
| 애니메이션 커브 노드 | `root_CTRL_expressions_<이름><L\|R>` (좌우) 또는 `root_CTRL_expressions_<이름>` (센터) |

> **`objExists` 로 찾는 것은 어트리뷰트가 아니라 `animCurve` 노드 이름**이다.
> 마야가 FBX 임포트로 `root.CTRL_expressions_browDownL` 에 애니메이션을 얹으면 커브 노드 이름이
> 관례상 `root_CTRL_expressions_browDownL` 이 되는 것에 **의존**하고 있다.
> 그래서 아래 상황이면 전부 조용히(=warning 만 뜨고) 실패한다.
>
> - **네임스페이스로 임포트**했다 → `ns:root`, `ns:root_CTRL_expressions_*` → 못 찾음
> - 씬에 이미 `root` 가 있어 마야가 **`root1` 로 리네임**했다 → 못 찾음
> - 커브 노드가 **다른 이름으로 생성**됐다(리네임, 다른 익스포터, 커브 최적화 후 재생성 등)
> - 애니메이션이 **어트리뷰트가 아니라 blendShape 웨이트/모프 타겟**으로 들어왔다

### 3-2. 매핑 — 하드코딩 104개

`$as`(MetaHuman raw control 이름) ↔ `$bs`(AS 패널 컨트롤) 두 배열을 인덱스로 짝짓는다.
**둘 다 104개**로 길이는 맞는다(확인함). 부록 A 에 전체 표가 있다.

| 분류 | 개수 | 의미 |
|------|------|------|
| 전체 | 104 | × 좌/우 (센터 전용은 1회) |
| 특수 처리 대상(`$as` 가 양방향 컨트롤에 얹히는 것) | 54 | 0 근처 키 제거 + 선형 탄젠트가 **강제 적용됨** |
| 그중 **음수 방향 → 병합** | 27 | Holder 임시 노드에 받았다가 -1 배 해서 양수 커브에 merge |
| 단순 직결 | 50 | 커브를 그대로 `translateY` 에 연결 |

`$bs` 항목 규칙:
- `"brow_down"` 처럼 어트리뷰트가 없으면 → **기본 `.translateY`** 가 붙는다.
- `"eye.translateX"` 처럼 명시되면 그걸 쓴다(10개).
- `"HolderXxx"` 로 시작하면 → **실제 컨트롤이 아니라 임시 transform**(음수 방향 처리용, 27개).

**좌우/센터 판정**:

```mel
if (!`objExists $a` && `objExists ("root_CTRL_expressions_"+$as[$i])`)
    { if ($x==1) { $a=...(센터); $b=$nameSpace+"CTRL_C_"+$bs[$i]; } if ($x==-1) continue; }
```
→ `<이름>L`/`<이름>R` 가 없고 접미사 없는 커브가 있으면 **센터 컨트롤(`CTRL_C_*`)** 로 취급하고,
왼쪽 패스에서는 건너뛴다(중복 방지).

### 3-3. 연결 자체

```mel
$animCurve = `substitute "[.]" $nonNsName "_"`;   // CTRL_L_eye.translateY -> CTRL_L_eye_translateY
if (`objExists $animCurve`) delete $animCurve;
duplicate -n $animCurve $a;                       // 원본 root_* 커브를 복제
if (!`getAttr -settable $b`) { warning; continue; }
connectAttr ($animCurve+".output") $b;
```

- 원본을 **복제**해서 쓰므로 원본 `root_*` 커브는 남는다.
- 커브 노드 이름이 **`<컨트롤>_<어트리뷰트>`(네임스페이스 제거)** 로 고정된다.
  → 3-4 의 병합 타깃이 이 이름을 문자열로 지목한다.
- **값 스케일이 없다.** MetaHuman raw control 은 0~1, 패널 컨트롤 translate 도 0~1 범위라
  그대로 꽂는다.

### 3-4. 핵심 — 양방향(±) 컨트롤 병합 (여기가 손실 지점)

MetaHuman raw control 은 **단방향 0~1** 이 두 개다(`eyeLookUpL`, `eyeLookDownL`).
AS 패널 컨트롤은 **하나의 축이 ±** 다(`CTRL_L_eye.translateY` = 위 +, 아래 −).
그래서 다음 휴리스틱을 쓴다.

```mel
// (A) 양수/음수 양쪽 모두에 적용
$keyXValues=`keyframe -q -tc $animCurve`;
$keyYValues=`keyframe -q -vc $animCurve`;
for ($z=1;$z<size($keyXValues);$z++)                       // ← z 가 1 부터!
    if ($keyYValues[$z]<0.001 && $keyYValues[$z]>-0.001)
        cutKey -t $keyXValues[$z] $animCurve;              // 0 근처 키 제거
if (!`objExists $animCurve`) continue;
keyTangent -itt linear -ott linear $animCurve;             // 탄젠트 전부 선형

// (B) 음수 방향에만 적용
scaleKey -vs -1 -vp 0 ... $animCurve;                      // 값 부호 반전
selectKey -k $animCurve; copyKey;
$target = "CTRL_"+$side+"_eye_translateY";                 // 양수 쪽 커브 노드 이름
if (`objExists $target`) pasteKey -option merge -copies 1 -connect 0 ... {$target};
else warning ("Target animationCurve:\""+$target+"\" not found.");
```

동작을 그림으로:

```
eyeLookUpL  : 0 0 0 .4 .8 .4 0 0 0        ─cut0─►  · · · .4 .8 .4 · · ·   (양수 커브 = 최종 목적지)
eyeLookDownL: 0 0 0  0  0  0 0 .6 .9      ─cut0─►  · · ·  ·  ·  · · .6 .9
                                          ─×(-1)─► · · ·  ·  ·  · · -.6 -.9
                                          ─merge─►
최종        : · · · .4 .8 .4 · -.6 -.9    → 키가 없는 구간은 **양옆 키를 선형 보간**
```

**이 방식이 만드는 문제**

| # | 문제 | 조건 |
|---|------|------|
| 1 | **0 구간이 사라진다** — 0 키를 지우므로 "올라갔다 0으로 돌아왔다 다시 올라감" 이 **계속 올라간 상태로 보간**된다 | 키가 듬성듬성할수록 심각. 매 프레임 베이크된 데이터면 영향 적음 |
| 2 | **양쪽이 동시에 0이 아니면 음수가 양수를 덮어쓴다** | `pasteKey -option merge` 는 같은 시간의 키를 **교체**한다. 솔버 결과에서 up/down 이 동시에 살아 있는 프레임에서 발생 |
| 3 | **첫 키(index 0)는 절대 제거되지 않는다** (`$z=1` 시작) | 음수 커브의 첫 키가 0이면 그 0이 양수 커브의 첫 키 위에 merge 되어 **첫 프레임 값이 0으로 지워진다** |
| 4 | **탄젠트가 전부 선형이 된다** | 원본이 스플라인/최적화된 커브면 모양이 바뀐다 |
| 5 | **양수 커브가 없으면 음수 애니메이션이 통째로 버려진다** | `root_CTRL_expressions_eyeLookUpL` 이 FBX 에 없으면 `$target` 부재 → warning 후 down 이 사라짐 |

> **정리**: 이 알고리즘은 **MetaHuman Animator 가 내보내는 "매 프레임 키가 찍힌 조밀한 커브"** 를 전제한다.
> UE 에서 **키 최적화(compression)된 커브**를 뽑아 왔다면 1번·4번이 곧바로 눈에 띄는 오차가 된다.

### 3-5. 확인된 코드 버그 — `tongueTwistRight` 의 병합 타깃 누락

`$as` 에는 `tongueTwistRight` 가 있고, 음수 분기 조건이 `gmatch $as[$i] "*Right*"` 라 **분기에 들어간다.**
그런데 `$target` 을 지정하는 24줄(15275~15300) 중 `tongueTwistRight` 는 **없다.**

`$target` 은 proc 스코프 변수라 **직전 반복의 값이 그대로 남는다.** `$as` 진행 순서가

```
... tongueBendUp , tongueBendDown , tongueTwistLeft , tongueTwistRight ...
                   └ $target = "CTRL_C_tongue_bendTwist_translateY"
                                     (양수, $target 안 건드림)
                                                       └ $target 이 위 값 그대로!
```

이므로 **`tongueTwistRight` 의 부호 반전 키가 `tongueBendUp/Down` 커브에 덮어써진다.**
올바른 타깃은 `tongueTwistLeft` 의 매핑(`tongue_bendTwist.translateX`)에 맞춰
`CTRL_C_tongue_bendTwist_translateX` 여야 한다.

- 영향: 혀 twist 를 쓰는 구간에서 **혀 bend 애니메이션이 오염**된다.
- 회피: FBX 에 `root_CTRL_expressions_tongueTwistRight` 가 있으면 Connect 전에 지우거나,
  세 파일에 아래 한 줄을 추가한다.
  ```mel
  if ($as[$i]=="tongueTwistRight") $target="CTRL_C_tongue_bendTwist_translateX";
  ```

### 3-6. `Connect Head Rotation` / `Translation` (참고)

```mel
root_HeadRoll/Pitch/Yaw            → FKHead_M.rotateX/Y/Z
root_HeadTranslationX/Y/Z          → FKHead_M.translateX/Y/Z   (× Main.height/160)
root_HeadTranslationZ 는 추가로 ×(-1)
```
- 이건 SDK 를 거치지 않고 **FKHead_M 에 직결**된다. 따라서 **Bake 대상이 아니다**(4장 참고).
- 위치 스케일이 `Main.height/160` 라는 매직 넘버로 캐릭터 크기에 맞춰진다.

---

## 4. `Bake to standard Face Controls` — 알고리즘

### 4-1. 전체 흐름

```
1) FaceControlSet 멤버를 정렬해 순회 (단, 이름이 CTRL_*_* 인 것은 skip = 패널 컨트롤 자신)
2) 각 컨트롤의 SDK 부모(SDK*)를 1~2단계 위로 찾음
     있으면  : SDK 로 들어가는 blendWeighted 를 대상으로
     없으면  : 컨트롤에서 나가는 blendWeighted(출력 bw)를 대상으로
3) 그 blendWeighted 에 물린 animCurve 들 중,
     "상류 드라이버가 bwCTRL_* / *Emotions* / *Phonemes* / *bwSmilePull*" 인 것만 골라
     새 blendWeighted(<bw>_NEW)에 순서대로 연결       ← MetaHuman 패널 기여분만 추출
4) <bw>_NEW.output → BAKER<bw>.translateX  (임시 transform)
5) bakeResults -simulation true -sampleBy 1 -t (playbackMin:playbackMax)  BAKER 전부
6) asMetaHumanAnimatorDeleteAnimation      ← 패널/머리 애니메이션 삭제 + 빌드포즈 복귀
   MetaHumanControlPanelVis = 0,  ctrlBox.limits = 0
7) delete -staticChannels  (변화 없는 BAKER 채널 제거)
8) BAKER 이름을 역파싱해 목적지 어트리뷰트를 만들고 copyKey/pasteKey
9) BAKER 그룹 삭제, "// N animationCurves baked." 출력
```

### 4-2. "MetaHuman 패널 기여분만" 을 고르는 필터

```mel
$tempString2 = `listConnections -s 1 -d 0 -scn 1 -type animCurve $bwOrig`;   // 이 bw 에 물린 SDK 커브들
for ($z...) {
    $secondaryDriven=0;
    $tempString3 = `listConnections -s 1 -d 0 -scn 1 -type blendWeighted $tempString2[$z]`;  // 커브의 상류
    for ($aa...) {
        if (!bwCTRL_* && !*Emotions* && !*Phonemes* && !*bwSmilePull*) $secondaryDriven=1;
        if (!$secondaryDriven) { connectAttr ($tempString2[$z]+".output") ($bwNew+".input["+$plugNr+"]"); $plugNr++; }
    }
}
```

- `animCurveUU` 의 `.input` 은 하나뿐이라 `$tempString3` 는 **0개 또는 1개**다.
- **`$tempString3` 가 0개이면 안쪽 루프가 아예 돌지 않아 그 커브는 조용히 제외된다.**
  → 드라이버 쪽에 `bwCTRL_*` 가 없는(= `asEnsureOutputBlendWeighted` 를 안 거친) SDK 는 **베이크에서 누락**된다.
- 반대로 **애니메이터가 AS 컨트롤에 직접 넣은 값/키는 의도적으로 제외**된다(그건 이미 컨트롤에 있으니까).

### 4-3. 베이크 범위 — **타임라인이 곧 범위다**

```mel
bakeResults -simulation true -t (`playbackOptions -q -min`+":"+`playbackOptions -q -max`)
    -sampleBy 1 -disableImplicitControl true -preserveOutsideKeys false
    -sparseAnimCurveBake false -bakeOnOverrideLayer false ... $bakers;
```

- **`playbackOptions min/max` 밖은 절대 베이크되지 않는다.** FBX 를 임포트해도 타임라인이 자동으로
  늘어나지 않은 상태에서 누르면 **앞뒤가 잘린다.** → 증상: "일부 구간만 맞고 나머지는 안 움직임".
- `-sampleBy 1` 이라 매 프레임 키. `-sparseAnimCurveBake false` 라 키를 솎지 않는다.
- **`-simulation true`** 이므로 프레임을 순서대로 재생하며 평가한다(느리지만 정확).

### 4-4. 목적지 어트리뷰트 이름 역파싱 (매우 취약)

```mel
$tempString[0]=`substitute ("BAKER"+$nameSpace+"bw") $bakers[$i] ""`;   // BAKERbwSDKctrlBrow_R_translateX -> SDKctrlBrow_R_translateX
$tempString[0]=`substitute "SDK" $tempString[0] ""`;                    // -> ctrlBrow_R_translateX
tokenize $tempString[0] "_" $tempString2;                               // [ctrlBrow, R, translateX]
$dest=$nameSpace+$tempString2[0]+"_"+$tempString2[1]+"."+$tempString2[2];
if (!`getAttr -settable $dest`) continue;                               // ← 조용히 포기
pasteKey $dest;
$num++;
```

- **`<컨트롤>_<사이드>_<어트리뷰트>` 3토큰을 가정**한다. 토큰이 4개 이상이면(컨트롤 이름에 `_` 가 더 있으면)
  `$dest` 가 엉뚱해지고 → `getAttr -settable` 실패 → **아무 메시지 없이 skip**.
- `substitute "SDK" ... ""` 는 **첫 번째 "SDK" 만** 지운다.
- **`getAttr -settable` 이 false 인 모든 경우가 조용히 버려진다.** 대표적으로:
  - 그 어트리뷰트가 **이미 다른 것에 connect** 되어 있음(컨스트레인트, 다른 SDK, 표현식)
  - **잠김(lock)**
  - **애님 레이어**에 들어가 있어 원본 플러그가 점유됨
  - 리퍼런스 엣지로 편집 불가
- 마지막에 찍히는 `// N animationCurves baked.` 의 **N 이 유일한 단서**다. 기대보다 작으면 여기서 샌 것이다.

### 4-5. 베이크의 부작용 (되돌리기 어려움)

| 코드 | 결과 |
|------|------|
| `asMetaHumanAnimatorDeleteAnimation` | `GRP_faceGUI` 하위 + **`FKHead_M`** 에 걸린 **`animCurveTU`** 를 전부 삭제하고 빌드포즈로 복귀. → **`Connect Head Rotation/Translation` 으로 붙인 머리 애니메이션도 같이 지워질 수 있다**(`root.Head*` 가 unitless 라 커브가 `animCurveTU` 인 경우. `doubleAngle` 이면 남는다). 머리는 베이크 대상도 아니므로 **머리 연결은 Bake 이후에** 하는 게 안전하다. |
| `setAttr MetaHumanControlPanelToggle.MetaHumanControlPanelVis 0` | 패널이 숨겨진다(정상). |
| `setAttr ctrlBox.limits 0` | AS 페이스 컨트롤의 **translate limit 이 전부 꺼진 채로 남는다.** 베이크 값이 설계 범위를 넘어가도 잘리지 않는다 — 의도된 동작이지만, 이후 수동 작업 시 컨트롤이 무한정 움직인다. |
| `delete -staticChannels` | 값이 **변하지 않는 채널은 커브째 삭제** → 그 컨트롤에는 키가 하나도 안 붙는다. 상수 오프셋이 필요한 컨트롤이라면 그 값이 유실된다. |

---

## 5. 왜 "UE 5.7 에서 뽑은 커브" 가 의도대로 안 붙는가 — 원인 체크리스트

가능성이 높은 순서.

### ① 이름 규약 불일치 (가장 흔함)

AS 는 **`root` 노드**와 **`root_CTRL_expressions_<name><L|R>` 커브 노드 이름**에 전적으로 의존한다.
UE 에서 내보낸 FBX 는 커브가 다른 노드/다른 이름으로 들어오기 쉽다.

```mel
// 진단 1: root 가 있는가, 리네임되지 않았는가
ls "root*";
// 진단 2: 기대하는 커브 노드가 실제로 있는가
size(`ls -type animCurve "root_CTRL_expressions_*"`);
// 진단 3: 실제로 어떤 이름으로 들어왔는지 (샘플 30개)
string $c[]=`ls -type animCurve "*CTRL_expressions*"`;  print `size($c)`; for($i=0;$i<30;$i++) print ($c[$i]+"\n");
// 진단 4: 네임스페이스로 들어왔는지
namespaceInfo -lon;
```

- 네임스페이스 있으면 → **네임스페이스 없이 다시 임포트**(또는 `namespace -mergeNamespaceWithRoot -rm`).
- 씬에 `root` 가 이미 있으면 → **빈 씬에 FBX 만 먼저 임포트**하고 리그를 레퍼런스로 붙이는 순서로.

### ② 매핑 테이블에 없는 커브 (설계상 버려짐)

**104개 × L/R 만** 처리한다. 코드 주석이 명시적으로 버린다고 적어 둔 것들:

```
UnKnown : eyeLowerLidDownL eyeLowerLidUpL eyeWidenL
Skip    : eyeParallelLookDirection eyePupilNarrowR eyeRelaxL eyeUpperLidUpL eyelashesDownINL
          headTiltLeftD headTurnDownD jawChinCompressL lookAtSwitch
Skip (AS 에 대응 없음)      : jawClenchL
Skip (대응을 못 찾음)       : mouthLipsPullDL mouthLipsPullUL mouthLipsTightenUL
                              tongueRoll tongueRollUp/Down/Left/Right
Skip (정적으로 보여 무시)   : mouthLipsStickyLPh1-3 neckSwallowPh1-5 neckThroatUp-Down
                              neckThroatInhale-Exhale neckDigastricUp-Down noseWrinkleUpperL
                              skullUnified teeth*
Skip (AS 컨트롤이 최신 MH 와 불일치): mouthLipsThickInwardDL tongueThick/Thin
Not found : mouthLipsPushUL / mouthLipsPushDL 의 반대 방향
```

→ **눈꺼풀 상하(`eyeLowerLid*`, `eyeUpperLidUp`), `eyeWiden`, 턱 clench, 목/삼킴, 치아, 혀 roll 은 아예 안 넘어온다.**
"눈이 덜 감긴다/눈꺼풀이 안 움직인다" 류 증상은 대부분 여기다.

```mel
// 진단 5: 값이 살아있는데 매핑에 없어서 버려진 커브 찾기
//        (Connect 실행 후 Script Editor 의 "AnimationCurve ... not found" warning 도 같이 볼 것)
string $all[]=`ls -type animCurve "root_CTRL_expressions_*"`;
for ($c in $all) { float $v[]=`keyframe -q -vc $c`; float $mx=0; for($x in $v) if (abs($x)>$mx) $mx=abs($x);
                   if ($mx>0.01) print ($c+"  max="+$mx+"\n"); }
```
이 목록과 부록 A 표를 대조하면 **무엇이 버려졌는지** 정확히 나온다.

### ③ 키가 조밀하지 않다 (UE 압축 커브)

3-4 의 손실이 그대로 드러난다. UE 에서 내보낼 때 **키 압축/최적화를 끄고 매 프레임 키**로 뽑으면
1번(0 구간 소실)·4번(선형 탄젠트) 오차가 크게 줄어든다.

### ④ 타임라인 범위

`Bake` 는 `playbackOptions min/max` 만 굽는다.

```mel
// 진단 6: 애니메이션 실제 범위 vs 타임라인
playbackOptions -q -min; playbackOptions -q -max;
findKeyframe -which first "root_CTRL_expressions_jawOpen";  findKeyframe -which last "root_CTRL_expressions_jawOpen";
```

### ⑤ 목적지가 settable 이 아니다 (조용한 skip)

애님 레이어를 쓰고 있거나, AS 컨트롤에 컨스트레인트/다른 연결이 걸려 있으면 **아무 말 없이 건너뛴다.**

```mel
// 진단 7: 베이크 직전에 FaceControlSet 중 settable 이 아닌 것 나열
string $m[]=`sets -q FaceControlSet`;
for ($o in $m) for ($a in {"translateX","translateY"})
    if (`attributeExists $a $o` && !`getAttr -settable ($o+"."+$a)`) print ($o+"."+$a+" NOT settable\n");
```
+ 베이크 후 출력되는 `// N animationCurves baked.` 의 N 을 반드시 확인.

### ⑥ 양방향 병합 충돌

up/down 이 동시에 0이 아닌 프레임이 있으면 음수가 이긴다(3-4 문제 2번).

```mel
// 진단 8: 양쪽이 동시에 살아있는 프레임이 있는지 (예: eyeLook 상하)
// 두 커브를 그래프 에디터에 함께 띄워 겹치는 구간이 있는지 보는 것이 가장 빠르다
```

### ⑦ `tongueTwistRight` 버그 (3-5)

### ⑧ 구조적 한계

MetaHuman 의 `board → raw` 는 다대다다. AS 는 raw 하나를 board 하나로 되돌리므로,
**여러 board 컨트롤이 합쳐져 만들어진 raw 값**은 원래 조합으로 복원되지 않는다.
`Connect` 결과를 패널에서 보면 값이 맞아 보여도, `Bake` 를 거쳐 AS 컨트롤로 내려가면
SDK 가중치(예: `brow_down → ctrlBrow.tx -0.9 / .ty -0.1`)를 통과하면서 **원본과 다른 포즈**가 될 수 있다.

---

## 6. 조용히 실패하는 지점 정리 (로그를 믿으면 안 되는 곳)

| 위치 | 조건 | 로그 |
|------|------|------|
| `Connect` 커브 없음 | `root_CTRL_expressions_*` 부재 | `warning` **있음** |
| `Connect` 컨트롤 없음 | `CTRL_*` 부재 | `warning` **있음** |
| `Connect` 연결 불가 | `getAttr -settable` false | `warning` **있음** |
| `Connect` 병합 타깃 없음 | 양수 커브 부재 | `warning` **있음** (단 음수 애니는 소실) |
| `Connect` 0 근처 키 삭제 | 항상 | **없음** ← |
| `Connect` 첫 키 미삭제 | 항상 | **없음** ← |
| `Connect` `tongueTwistRight` 오염 | 해당 커브 존재 시 | **없음** ← |
| `Bake` 상류 bw 없음 | SDK 커브가 bw 를 안 거침 | **없음** ← |
| `Bake` 타임라인 밖 | 항상 | **없음** ← |
| `Bake` 이름 역파싱 실패 | 토큰 4개 이상 | **없음** ← |
| `Bake` settable 아님 | 레이어/락/연결 | **없음** ← |
| `Bake` static 채널 삭제 | 값 불변 | **없음** ← |

→ **`// N animationCurves copied` (Connect) 와 `// N animationCurves baked` (Bake) 두 숫자를 기록해 두고
기대치와 비교하는 것이 유일한 실질적 검증 수단이다.**

---

## 7. 권장 작업 순서 (현재 툴을 그대로 쓸 경우)

1. **빈 씬**에 MetaHuman Animator/UE FBX 를 **네임스페이스 없이** 임포트 → `ls "root*"` 로 `root` 확인.
2. `ls -type animCurve "root_CTRL_expressions_*"` 개수 확인 (0이면 여기서 중단, 익스포트를 고쳐야 함).
3. **타임라인을 애니메이션 전 구간으로 맞춘다.**
4. AS 리그를 붙이고 `Add MetaHuman Control Panel` 이 되어 있는지 확인 (`FRM_faceGUI` 존재).
   AS FaceSetup 버전이 **6.055 이상**이어야 한다(미만이면 경고 대화상자가 뜬다).
5. **컨트롤을 하나 선택한 상태로** MetaHumanAnimator 창을 연다 → 네임스페이스가 창에 캡처된다.
   (창을 연 시점의 네임스페이스가 고정되므로, 리그를 바꾸면 창을 다시 열어야 한다.)
6. `Connect Face Animation` → Script Editor 의 warning 전부와 `// N animationCurves copied` 기록.
7. **여기서 먼저 육안 검수**한다. 이 단계가 틀리면 Bake 는 그 오차를 그대로 굳힌다.
8. 애님 레이어를 쓰고 있다면 **베이스 레이어로 정리**하고, AS 컨트롤에 걸린 컨스트레인트를 푼다.
9. `Bake to standard Face Controls` → `// N animationCurves baked` 기록.
10. **머리 연결(`Connect Head Rotation/Translation`)은 Bake 이후에** 한다(4-5 참고).
11. 베이크 후 `ctrlBox.limits` 가 0 이 되어 있으니, 필요하면 `setAttr ctrlBox.limits 1` 로 복구.

---

## 8. 더 정확하게 하려면 (직접 만들 경우의 설계 메모)

AS 경로가 근사인 이유가 3장·4장에 다 나와 있으므로, 자체 툴을 만든다면 다음이 개선점이다.

1. **매핑을 코드가 아니라 데이터(JSON)로.** 104개 하드코딩 대신 `raw control → (control, attr, scale, offset)`
   테이블을 파일로 두면 커버리지를 늘리고 캐릭터별로 교정할 수 있다.
   → 사내에 이미 같은 발상의 툴이 있다: `A00090_ConnectionBuilder` 의 `app/rules/<version>/*.json`.
2. **양방향은 잘라 붙이지 말고 "합성"한다.** `value = up - down` 을 **매 프레임 계산**해 새 커브를 만든다.
   0 근처 키를 지울 필요가 없어지고, 양쪽이 동시에 0이 아닐 때도 물리적으로 맞는 결과가 나온다.
   (`plusMinusAverage` 노드로 연결하거나, numpy 로 샘플링해 `setKeyframe`.)
3. **키를 지우지 않는다.** 0 을 0 으로 유지해야 원본이 보존된다. 탄젠트도 원본을 복사한다.
4. **역파싱 대신 명시적 목적지.** 이름 문자열을 쪼개 목적지를 유추하는 방식은 이름이 조금만 달라도 깨진다.
   테이블에 목적지를 직접 적는다.
5. **모든 skip 을 로그로.** 위 6장 표의 "없음" 항목을 전부 사유와 함께 출력한다.
6. **베이크 범위는 커브에서 구한다.** `findKeyframe -which first/last` 로 실제 범위를 잡고
   타임라인에 의존하지 않는다. (사내 공용 위젯 `Framework/qt/MOD_timeRange_qt_v01.py` 의
   *Get Sel Range* 와 같은 발상.)

---

## 부록 A. `Connect Face Animation` 전체 매핑표 (104개)

- `<S>` = `L` / `R`. 좌우 커브가 없고 접미사 없는 커브만 있으면 `CTRL_C_*` (센터)로 처리된다.
- **direct** = 커브를 그대로 연결. 키 가공 없음.
- **bidirectional +** = 양방향 축의 **양수 쪽**. 0 근처 키 제거 + 선형 탄젠트가 적용된다.
- **negative → merged** = 임시 Holder 로 받아 **-1 배 후 양수 커브에 `pasteKey -option merge`**.

| MetaHuman raw control (`root_CTRL_expressions_…`) | AS 패널 컨트롤 | 처리 |
|---|---|---|
| `browDown` | `CTRL_<S>_brow_down.translateY` | direct |
| `browLateral` | `CTRL_<S>_brow_lateral.translateY` | direct |
| `browRaiseIn` | `CTRL_<S>_brow_raiseIn.translateY` | direct |
| `browRaiseOuter` | `CTRL_<S>_brow_raiseOut.translateY` | direct |
| `earUp` | `CTRL_<S>_ear_up.translateY` | direct |
| `eyeBlink` | `CTRL_<S>_eye_blink.translateY` | direct |
| `eyeFaceScrunch` | `CTRL_<S>_eye_faceScrunch.translateY` | direct |
| `eyeCheekRaise` | `CTRL_<S>_eye_cheekRaise.translateY` | direct |
| `eyeLidPress` | `CTRL_<S>_eye_lidPress.translateY` | direct |
| `eyeLookUp` | `CTRL_<S>_eye.translateY` | bidirectional + |
| `eyeLookDown` | `CTRL_<S>_HolderEyeLookDown` → `CTRL_<S>_eye.translateY` | negative → merged |
| `eyeLookLeft` | `CTRL_<S>_eye.translateX` | bidirectional + |
| `eyeLookRight` | `CTRL_<S>_HolderEyeLookRight` → `CTRL_<S>_eye.translateX` | negative → merged |
| `eyeSquintInner` | `CTRL_<S>_eye_squintInner.translateY` | direct |
| `jawBack` | `CTRL_<S>_jaw_fwdBack.translateY` | bidirectional + |
| `jawFwd` | `CTRL_<S>_HolderJawForward` → `CTRL_C_jaw_fwdBack.translateY` | negative → merged |
| `jawChinRaiseD` | `CTRL_<S>_jaw_ChinRaiseD.translateY` | direct |
| `jawChinRaiseU` | `CTRL_<S>_jaw_ChinRaiseU.translateY` | direct |
| `jawLeft` | `CTRL_<S>_jaw.translateX` | bidirectional + |
| `jawRight` | `CTRL_<S>_HolderJawRight` → `CTRL_C_jaw.translateX` | negative → merged |
| `jawOpen` | `CTRL_<S>_jaw.translateY` | direct |
| `jawOpenExtreme` | `CTRL_<S>_jaw_openExtreme.translateY` | direct |
| `mouthCheekBlow` | `CTRL_<S>_mouth_suckBlow.translateY` | bidirectional + |
| `mouthCheekSuck` | `CTRL_<S>_HolderMouthSuck` → `CTRL_<S>_mouth_suckBlow.translateY` | negative → merged |
| `mouthCornerDepress` | `CTRL_<S>_mouth_cornerDepress.translateY` | bidirectional + |
| `mouthCornerPull` | `CTRL_<S>_mouth_cornerPull.translateY` | bidirectional + |
| `mouthDimple` | `CTRL_<S>_mouth_dimple.translateY` | direct |
| `mouthCornerUp` | `CTRL_<S>_mouth_corner.translateY` | bidirectional + |
| `mouthCornerDown` | `CTRL_<S>_HolderMouthCornerDown` → `CTRL_<S>_mouth_corner.translateY` | negative → merged |
| `mouthCornerWide` | `CTRL_<S>_mouth_corner.translateX` | bidirectional + |
| `mouthCornerNarrow` | `CTRL_<S>_HolderMouthCornerNarrow` → `CTRL_<S>_mouth_corner.translateX` | negative → merged |
| `mouthCornerSharpenU` | `CTRL_<S>_mouth_cornerSharpnessU.translateY` | bidirectional + |
| `mouthCornerRounderU` | `CTRL_<S>_HolderMouthCornerSharpnessU` → `…_cornerSharpnessU.translateY` | negative → merged |
| `mouthCornerSharpenD` | `CTRL_<S>_mouth_cornerSharpnessD.translateY` | bidirectional + |
| `mouthCornerRounderD` | `CTRL_<S>_HolderMouthCornerSharpnessD` → `…_cornerSharpnessD.translateY` | negative → merged |
| `mouthUp` | `CTRL_<S>_mouth.translateY` | bidirectional + |
| `mouthDown` | `CTRL_<S>_HolderMouthDown` → `CTRL_C_mouth.translateY` | negative → merged |
| `mouthLeft` | `CTRL_<S>_mouth.translateX` | bidirectional + |
| `mouthRight` | `CTRL_<S>_HolderMouthRight` → `CTRL_C_mouth.translateX` | negative → merged |
| `mouthFunnelU` | `CTRL_<S>_mouth_funnelU.translateY` | direct |
| `mouthFunnelD` | `CTRL_<S>_mouth_funnelD.translateY` | direct |
| `mouthLipsBlow` | `CTRL_<S>_mouth_lipsBlow.translateY` | direct |
| `mouthLipsPress` | `CTRL_<S>_mouth_lipsPressU.translateY` | direct |
| `mouthLipsPurseU` | `CTRL_<S>_mouth_purseU.translateY` | direct |
| `mouthLipsPurseD` | `CTRL_<S>_mouth_purseD.translateY` | direct |
| `mouthLipsPushU` | `CTRL_<S>_mouth_pushPullU.translateY` | direct |
| `mouthLipsPushD` | `CTRL_<S>_mouth_pushPullD.translateY` | direct |
| `mouthLipsThickU` | `CTRL_<S>_mouth_thicknessU.translateY` | bidirectional + |
| `mouthLipsThinU` | `CTRL_<S>_HolderMouthLipsThickU` → `…_thicknessU.translateY` | negative → merged |
| `mouthLipsThickD` | `CTRL_<S>_mouth_thicknessD.translateY` | bidirectional + |
| `mouthLipsThinD` | `CTRL_<S>_HolderMouthLipsThickD` → `…_thicknessD.translateY` | negative → merged |
| `mouthLipsTogetherU` | `CTRL_<S>_mouth_lipsTogetherU.translateY` | direct |
| `mouthLipsTogetherD` | `CTRL_<S>_mouth_lipsTogetherD.translateY` | direct |
| `mouthUpperLipTowardsTeeth` | `CTRL_<S>_mouth_lipsTowardsTeethU.translateY` | direct |
| `mouthLowerLipTowardsTeeth` | `CTRL_<S>_mouth_lipsTowardsTeethD.translateY` | direct |
| `mouthUpperLipBite` | `CTRL_<S>_mouth_lipBiteU.translateY` | direct |
| `mouthLowerLipBite` | `CTRL_<S>_mouth_lipBiteD.translateY` | direct |
| `mouthLowerLipDepress` | `CTRL_<S>_mouth_lowerLipDepress.translateY` | direct |
| `mouthUpperLipRollIn` | `CTRL_<S>_mouth_lipsRollU.translateY` | bidirectional + |
| `mouthUpperLipRollOut` | `CTRL_<S>_HolderMouthUpperLipRollOut` → `…_lipsRollU.translateY` | negative → merged |
| `mouthLowerLipRollIn` | `CTRL_<S>_mouth_lipsRollD.translateY` | bidirectional + |
| `mouthLowerLipRollOut` | `CTRL_<S>_HolderMouthLowerLipRollOut` → `…_lipsRollD.translateY` | negative → merged |
| `mouthUpperLipShiftLeft` | `CTRL_<S>_mouth_lipShiftU.translateY` | direct |
| `mouthUpperLipShiftRight` | `CTRL_<S>_HolderMouthUpperLipShiftRight` → `CTRL_C_mouth_lipShiftU.translateY` | negative → merged |
| `mouthLowerLipShiftLeft` | `CTRL_<S>_mouth_lipShiftD.translateY` | direct |
| `mouthLowerLipShiftRight` | `CTRL_<S>_HolderMouthLowerLipShiftRight` → `CTRL_C_mouth_lipShiftD.translateY` | negative → merged |
| `mouthPressU` | `CTRL_<S>_mouth_pressU.translateY` | direct |
| `mouthPressD` | `CTRL_<S>_mouth_pressD.translateY` | direct |
| `mouthSharpCornerPull` | `CTRL_<S>_mouth_sharpCornerPull.translateY` | direct |
| `mouthStickyUC` | `CTRL_<S>_mouth_stickyU.translateY` | direct |
| `mouthStickyDC` | `CTRL_<S>_mouth_stickyD.translateY` | direct |
| `mouthStickyUIN` | `CTRL_<S>_mouth_stickyInnerU.translateY` | direct |
| `mouthStickyDIN` | `CTRL_<S>_mouth_stickyInnerD.translateY` | direct |
| `mouthStickyUOUT` | `CTRL_<S>_mouth_stickyOuterU.translateY` | direct |
| `mouthStickyDOUT` | `CTRL_<S>_mouth_stickyOuterD.translateY` | direct |
| `mouthStretch` | `CTRL_<S>_mouth_stretch.translateY` | direct |
| `mouthStretchLipsClose` | `CTRL_<S>_mouth_stretchLipsClose.translateY` | direct |
| `mouthUpperLipRaise` | `CTRL_<S>_mouth_upperLipRaise.translateY` | direct |
| `mouthLipsTowardsU` | `CTRL_<S>_mouth_towardsU.translateY` | direct |
| `mouthLipsTowardsD` | `CTRL_<S>_mouth_towardsD.translateY` | direct |
| `neckMastoidContract` | `CTRL_<S>_neck_mastoidContract.translateY` | direct |
| `neckStretch` | `CTRL_<S>_neck_stretch.translateY` | direct |
| `noseNasolabialDeepen` | `CTRL_<S>_nose_nasolabialDeepen.translateY` | direct |
| `noseWrinkle` | `CTRL_<S>_nose.translateY` | direct |
| `noseNostrilDepress` | `CTRL_<S>_HolderNoseNostrilDepress` → `CTRL_<S>_nose.translateY` | negative → merged |
| `noseNostrilDilate` | `CTRL_<S>_nose.translateX` | bidirectional + |
| `noseNostrilCompress` | `CTRL_<S>_HolderNoseNostrilCompress` → `CTRL_<S>_nose.translateX` | negative → merged |
| `tongueUp` | `CTRL_<S>_tongue_move.translateY` | bidirectional + |
| `tongueDown` | `CTRL_<S>_HolderTongueDown` → `CTRL_C_tongue_move.translateY` | negative → merged |
| `tongueLeft` | `CTRL_<S>_tongue_move.translateX` | bidirectional + |
| `tongueRight` | `CTRL_<S>_HolderTongueRight` → `CTRL_C_tongue_move.translateX` | negative → merged |
| `tongueBendUp` | `CTRL_<S>_tongue_bendTwist.translateY` | bidirectional + |
| `tongueBendDown` | `CTRL_<S>_HolderTongueBendDown` → `CTRL_C_tongue_bendTwist.translateY` | negative → merged |
| `tongueTwistLeft` | `CTRL_<S>_tongue_bendTwist.translateX` | bidirectional + |
| `tongueTwistRight` | `CTRL_<S>_HolderTongueTwistRight` → **타깃 미지정 (버그, 3-5 참고)** | negative → merged |
| `tongueTipUp` | `CTRL_<S>_tongue_tipMove.translateY` | bidirectional + |
| `tongueTipDown` | `CTRL_<S>_HolderTongueTipDown` → `CTRL_C_tongue_tipMove.translateY` | negative → merged |
| `tongueTipLeft` | `CTRL_<S>_tongue_tipMove.translateX` | bidirectional + |
| `tongueTipRight` | `CTRL_<S>_HolderTongueTipRight` → `CTRL_C_tongue_tipMove.translateX` | negative → merged |
| `tongueIn` | `CTRL_<S>_tongue_inOut.translateY` | bidirectional + |
| `tongueOut` | `CTRL_<S>_HolderTongueOut` → `CTRL_C_tongue_inOut.translateY` | negative → merged |
| `tongueWide` | `CTRL_<S>_tongue_wideNarrow.translateY` | bidirectional + |
| `tongueNarrow` | `CTRL_<S>_HolderTongueNarrow` → `CTRL_C_tongue_wideNarrow.translateY` | negative → merged |
| `tonguePress` | `CTRL_<S>_tongue_press.translateY` | bidirectional + |

---

## 부록 B. 관련 문서

- `Add_ARKit_Curves_to_Skeleton_분석.md` — 언리얼 쪽 커브/스켈레톤 메타데이터 관점
- `SmartLayer_bake_algorithm_analysis.md` — 서드파티 베이크 알고리즘 역분석 사례
- `../A00090_ConnectionBuilder.md` — 규칙(JSON) 기반 어트리뷰트 결선 툴 (8장 1번 개선안의 기존 사례)
