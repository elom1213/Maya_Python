# AdvancedSkeleton — `No object matches name: lowerLipJoint10_R` 원인과 해결

- **대상**: AdvancedSkeleton **6.801** (`C:/Users/USER/Desktop/JP/0020_maya_plugin/0040_AdvancedSkeleton/AdvancedSkeleton.mel`)
- **발생 지점**: `Build AdvancedFace` 실행 중, `AdvancedSkeleton.mel` **line 34482**
- **에러 메시지**
  ```
  // Error: file: .../AdvancedSkeleton.mel line 34482: No object matches name: lowerLipJoint10_R
  ```
- **관찰**: 씬에는 `lowerfollicle10_R` 이 정상적으로 생성되어 있음

---

## 1. 요약 (TL;DR)

> **모델(입술 주변)의 좌우 비대칭** 때문입니다. AdvancedSkeleton 자체 버그가 아니라 AS 가 요구하는 전제 조건(모델 대칭) 위반이고,
> 하필 이 경로에는 방어 코드가 없어서 친절한 메시지 대신 raw 에러가 납니다.

1. AS 는 아랫입술 조인트를 만들 때 **오른쪽/왼쪽 각각 자기 쪽 build-curve 의 CV 수**만큼 만든다.
2. 그런데 "겹치는 마지막 lower 조인트를 지우는" 코드(line 34211)는 **왼쪽 개수**로 계산한 인덱스를 **좌우 양쪽에** 적용한다.
3. 좌우 CV 수가 다르면 오른쪽에서는 **엉뚱한 조인트(=10번)** 가 지워진다.
4. 이후 follicle 루프(line 34445~)는 **오른쪽 개수** 기준으로 돌면서 방금 잘못 지워진 `lowerLipJoint10_R` 을 조회 → **에러**.
5. `lowerfollicle10_R` 이 씬에 남아 있는 이유는 **follicle 생성(34467~34475)이 조인트 조회(34482)보다 먼저**이기 때문. 정상 동작이며 단서일 뿐 원인이 아니다.

**추정 수치**: `lowerLipMainBuildCurveLeft` = **11 CV**, `lowerLipMainBuildCurve`(오른쪽) = **12 CV 이상**
→ 즉 **오른쪽 아랫입술 엣지 루프의 정점이 왼쪽보다 최소 1개 더 잡혔다.**

> **좌우 CV 수가 어긋나는 원인은 2가지다.**
> - **(1) 모델 비대칭** → 3장
> - **(2) `FaceFitLipMain.selection` 에 저장된 엣지 루프가 중간에 끊겨 있음** → **6장** (mayapy 실측 포함)
>
> 둘 중 하나만 있어도 이 에러가 난다.

---

## 2. 코드 추적

### 2-1. 에러가 난 줄 (line 34477~34484)

```mel
//determine U value based on un-eveness of distribution of edge-rows in the models lips
//		v 6.5301 changed to sample surface instead, should be give follicles closer to the joints. e.g. raptor-lips
$pos=`xform -q -ws -t ($upperLower+"LipJoint"+$i+$side)`;      // ← line 34482, objExists 가드 없음
setAttr -type float3 tempClosestPointOnSurface.inPosition $pos[0] $pos[1] $pos[2];
$u=`getAttr tempClosestPointOnSurface.result.parameterU`;
```

`$upperLower="lower"`, `$i=10`, `$side="_R"` 인 순간 `lowerLipJoint10_R` 이 없어서 `xform -q` 가 실패한다.
같은 파일의 다른 곳(34551, 35663 등)에는 `objExists` 가드가 있는데 **이 줄에만 없다.**

### 2-2. 조인트 생성 — 좌우 각각 자기 개수 (line 34125~34196)

```mel
for ($b=1;$b>-2;$b=$b-2)            // b= 1 → _R (leftSuffix="")
  {                                 // b=-1 → _L (leftSuffix="Left")
  ...
  for ($upperLowerFactor=1;...)     // upper → lower
    {
    ...
    $mainNumCv=`getAttr ($upperLower+"LipMainBuildCurve"+$leftSuffix+".spans")`+1;   // line 34171

    //Create Joints
    for ($i=0;$i<$mainNumCv;$i++)                                                    // line 34174
      {
      select LipJoints_M;
      joint -n ($upperLower+"LipJoint"+$i+$side);
      ...
      }
    }
  }
```

- `lowerLipJoint*_R` 개수 = `lowerLipMainBuildCurve.spans + 1`
- `lowerLipJoint*_L` 개수 = `lowerLipMainBuildCurve**Left**.spans + 1`

**좌우 개수가 다를 수 있는 구조**다.

### 2-3. 문제의 삭제 — 루프 밖으로 새어 나온 `$mainNumCv` (line 34210~34212)

```mel
//remove first and last lower-joints, as they overlap upper-joints
select ("lowerLipJoint"+($mainNumCv-1)+"_R") ("lowerLipJoint"+($mainNumCv-1)+"_L");
delete ("lowerLipJoint"+($mainNumCv-1)+"_R") ("lowerLipJoint"+($mainNumCv-1)+"_L");
```

여기서 쓰이는 `$mainNumCv` 는 **바로 위 이중 루프의 마지막 반복에서 남은 값**,
즉 `b=-1`(Left) × `upperLower="lower"` → **`lowerLipMainBuildCurveLeft` 기준**이다.

이 값을 `_R` 에도 그대로 쓴다. → **좌우 개수가 다르면 오른쪽은 잘못된 인덱스를 지운다.**

### 2-4. follicle 루프 — 이번엔 오른쪽 개수 (line 34445~34462)

```mel
$mainNumCv=`getAttr ($upperLower+"LipMainBuildCurve.spans")`+1;   // line 34445 — Left 접미사 없음 = 오른쪽
...
for ($i=0;$i<$mainNumCv;$i++)
  {
  ...
  if ($upperLower=="lower" && $i==($mainNumCv-1))   // 지워진 마지막 lower 를 건너뛰려는 의도
    continue;
  ...
  $tempString[0]=`createNode follicle`;             // line 34467 — follicle 은 여기서 이미 생성됨
  ...
  $pos=`xform -q -ws -t ($upperLower+"LipJoint"+$i+$side)`;   // line 34482 — 여기서 터짐
```

건너뛰기 인덱스가 **오른쪽 개수 - 1** 인데, 실제로 지워진 건 **왼쪽 개수 - 1** 이라 어긋난다.

### 2-5. 숫자로 재현 (L = 11, R = 12 인 경우)

| 단계 | 오른쪽(`_R`) | 왼쪽(`_L`) |
|---|---|---|
| build curve CV 수 | **12** | **11** |
| 생성된 조인트 | `lowerLipJoint0_M`, `1_R` … `11_R` | `1_L` … `10_L` |
| line 34211 삭제 인덱스 (=`$mainNumCv_L - 1`) | **10** ← 잘못됨 | 10 ← 맞음 |
| 삭제 후 남은 조인트 | 1~9, **11** (10번 구멍) | 1~9 |
| follicle 루프 건너뛰기 인덱스 (=`$mainNumCv_R - 1`) | 11 | 11 |
| `$i=10` 도달 | `lowerfollicle10_R` 생성 → **`lowerLipJoint10_R` 없음 → 에러** | (여기 오기 전에 중단) |

관찰된 증상(`lowerfollicle10_R` 은 있는데 `lowerLipJoint10_R` 이 없다)과 **정확히 일치**한다.

> 반대로 왼쪽이 더 많았다면 line 34211 의 `select` 자체가 먼저 실패했을 것이다.
> line 34482 에서 `_R` 로 터졌다는 것은 **오른쪽 CV 수 > 왼쪽 CV 수** 라는 뜻이다.

### 2-6. 왜 그 전에 잡히지 않았나 (line 34342~34352)

바로 앞 RibbonCurve 루프에는 이런 코드가 있다.

```mel
if (!`objExists $joint`)//lower dont have 1st&last use upper
    $joint="upperLipJoint"+`getAttr upperLipMainBuildCurve.spans`+$jointSide;

if (!`objExists $joint`)
    error ("Joint: "+$joint+" not found.\nThis probably means the model is not symmetrical.\n..."
        +"https://www.youtube.com/watch?v=-V3Sk-COJU0&t=297s");
```

**AS 개발자가 이미 "조인트가 없다 = 모델이 비대칭이다"라고 진단해 둔 지점**이다.
다만 여기는 fallback(`upperLipJoint<n>_R`)이 있어서 조용히 통과해 버리고,
가드가 없는 line 34482 에서 뒤늦게 터지는 것이다.
→ **에러 문구는 다르지만 원인은 위 링크의 "모델 비대칭" 케이스와 동일하다.**

---

## 3. 근본 원인 — 왜 좌우 CV 수가 달라지나

### 3-1. 대칭 모드에서 왼쪽 피팅은 오른쪽의 **미러 복제**다 (line 31021~31041)

```mel
//duplicate Fitting to Left, if not using "nonSymmetrical"
if ($nonSymmetrical)
    asFaceShowBothSides;
else
    {
    ...
    duplicate -n ($tempString[$i]+"Left") $tempString[$i];
    setAttr ($tempString[$i]+"Left.sx") (-1*`getAttr ($tempString[$i]+".sx")`);   // X 미러
    ...
    }
```

즉 `lowerLipMainCurveLeft` 는 `lowerLipMainCurve` 를 `sx=-1` 로 뒤집은 **기하학적으로 완전한 미러**다.

### 3-2. 그 커브의 CV 를 "가장 가까운 정점"으로 스냅한다 (line 41095~41110)

```mel
//special case, slight asymmetry in Model easily cause mismatched num Right vs Left for Lip
if (`gmatch $curves[$i] "*Lip*"`)
    $tempString=`asFaceFitReSelect Lip Main`;
for ($y=0;$y<$numCv;$y++)
    {
    $pos=`xform -q -ws -t ($curves[$i]+".cv["+$y+"]")`;
    setAttr -type float3 closestSamplerFitSelection2.inPosition $pos[0] $pos[1] $pos[2];
    $vtxNr=`getAttr closestSamplerFitSelection2.result.closestVertexIndex`;
    $selection+=($geometry+".vtx["+$vtxNr+"] ");
    }
```

주석이 그대로 답이다 — **"slight asymmetry in Model easily cause mismatched num Right vs Left for Lip"**.

결과 문자열은 `select` → `ls -sl -fl` 로 **중복 제거**되므로:

- **(a) 토폴로지 자체가 비대칭** — 입술 루프의 정점 수가 좌우 다름 → 당연히 개수 차이
- **(b) 토폴로지는 같은데 정점 위치가 미세하게 비대칭** — 미러된 CV 2개가 **같은 정점**에 스냅 → 중복 제거되어 한 쪽만 1개 줄어듦

**(b) 만으로도 이 에러가 난다.** "겉보기엔 대칭인데 왜?" 의 답이 이것이다.

### 3-3. 추가로 의심할 것 — 모델이 월드 X=0 에 걸쳐 있는가

미러는 **X=0 기준**이다. 머리 지오메트리가 X 방향으로 조금이라도 이동해 있거나(freeze 안 됨),
그룹에 X 오프셋이 남아 있으면 왼쪽 미러 커브가 메시의 엉뚱한 곳에 떨어져서 같은 증상이 난다.

---

## 4. 씬에서 원인 확인하기

**에러 직후의 씬을 저장하지 말고 그대로 두고** 아래를 Script Editor(MEL)에 붙여 실행한다.
`LipConstruction` 그룹은 line 35372 에서야 삭제되므로 build-curve 들이 아직 씬에 남아 있다.

```mel
// 1) 좌우 build-curve CV 수 비교  — 두 값이 다르면 확진
print ("upper R : "+(`getAttr upperLipMainBuildCurve.spans`+1)+"\n");
print ("upper L : "+(`getAttr upperLipMainBuildCurveLeft.spans`+1)+"\n");
print ("lower R : "+(`getAttr lowerLipMainBuildCurve.spans`+1)+"\n");
print ("lower L : "+(`getAttr lowerLipMainBuildCurveLeft.spans`+1)+"\n");

// 2) 실제로 만들어진 lower 조인트 목록 (인덱스에 구멍이 있는지 확인)
print "--- lowerLipJoint _R ---\n";  print `ls -type joint "lowerLipJoint*_R"`;
print "--- lowerLipJoint _L ---\n";  print `ls -type joint "lowerLipJoint*_L"`;
```

**기대 결과** (이번 케이스): `lower R` = 12 이상, `lower L` = 11, 그리고 `lowerLipJoint*_R` 목록에서 **10번만 빠지고 11번은 존재**.

정점 단위로 어디가 비대칭인지 보려면 — **깨끗한 모델 씬(리깅 전)** 을 열고:

```
AdvancedSkeleton 창 → Preparation → Model → [Model Check]
```
→ 메시를 선택하고 `Check`. 비대칭 정점들이 **선택된 채로** 남는다 (허용 오차 0.001).
입 주변에 선택된 정점이 있으면 그게 범인이다.

> 참고: `Build AdvancedFace` 실행 중에는 AS 가 `asSkipModelSymmetryCheck` 노드를 만들어
> **이 대칭 검사를 일부러 건너뛴다**(line 30833). 그래서 빌드 시작 시점에 경고가 안 나왔던 것.
> 반드시 **수동으로** 따로 돌려야 한다.

---

## 5. 해결 방법

### 5-A. 근본 해결 (권장) — 모델을 대칭으로 만들고 재피팅

1. **리깅 전 깨끗한 모델 씬**을 연다. (실패한 빌드 씬은 버린다)
2. 메시가 **월드 X=0 에 걸쳐 있고 트랜스폼이 freeze** 되어 있는지 확인.
   - `Preparation → Model → [Model Clean]` (`asModelCleaner`) 을 먼저 돌리면 좋다.
3. `Preparation → Model → [Model Check]` 로 비대칭 정점을 확인.
4. 대칭화 — 가장 확실한 순서:
   - `Mesh > Mirror` 로 한쪽 반을 잘라내고 반대편을 미러 + merge (threshold 는 모델 스케일의 0.001 수준)
   - 입술만 손보고 싶다면 최소한 **위/아래 입술 엣지 루프 전 구간**을 대칭으로 맞춘다
     (입꼬리 ~ 입 중앙 사이 정점 수가 좌우 동일해야 하고, 위치도 미러 일치해야 함)
   - 대칭화 후 `Model Check` 를 다시 돌려 `// Model is symmetrical.` 이 출력되는지 확인
5. **Face Fit 을 다시 한다.** (특히 Lip 섹션 — Inner / Outer / Main 세 커브 모두)
   기존 피팅을 재사용하면 스냅 결과가 그대로일 수 있다.
6. `Build AdvancedFace` 재실행.

> 4번에서 "정점을 몇 개만 손으로 옮겨서" 맞추는 방법도 되지만, **미러 후 merge** 가 재발 위험이 가장 낮다.

### 5-B. 반쪽 해결 — `non symmetrical` 옵션

`Face → Preparation → [x] non symmetrical` 를 켜면 왼쪽 피팅을 미러 복제하지 않고 **직접 피팅**한다.
→ **모양(위치) 비대칭**은 해결된다.

**주의 2가지:**
- **개수 비대칭은 해결되지 않는다.** RibbonCurve/follicle 로직이 여전히 오른쪽 개수를 좌우 공통으로 쓰므로
  (line 34342, 34445), 좌우 입술 루프의 **정점 개수는 어차피 같아야 한다.**
- 이미 Lip 피팅을 끝낸 뒤에 이 옵션을 켜면 AS 가 막는다 (line 30818):
  ```
  Lip-Fitting was done before Non-Symmetrical was turned On.
  Delete the current lip-Fitting and re-do the Fitting for Non-Symmetrical model.
  ```
  → 켠 다음 **Lip 피팅을 지우고 처음부터 다시** 해야 한다.

### 5-C. 응급 패치 (MEL 직접 수정) — **비권장 / 임시**

모델을 지금 못 고치는데 일단 빌드는 통과시켜야 할 때만. **원본 백업 필수.**
`lowerLipJoint10_R` 이 빠진 자리를 **건너뛰게** 만드는 방식이라, 그 지점의 스티키 립 구동이 하나 빠진다.

**패치 ①** — `AdvancedSkeleton.mel` line 34462 (`continue;`) 바로 **다음 줄에** 삽입:

```mel
			if (!`objExists ($upperLower+"LipJoint"+$i+$side)`)//asymmetric-model guard
				continue;
```

**패치 ②** — 같은 파일 line 35143 (`continue;`) 바로 **다음 줄에도** 동일하게 삽입:

```mel
			if (!`objExists ($upperLower+"LipJoint"+$i+$side)`)//asymmetric-model guard
				continue;
```

(35145 의 `getAttr (...follicle....parameterU)` 와 35194 의 `connectAttr ... LipJoint$i$side.rx` 가
①에서 건너뛴 인덱스를 다시 참조하므로 두 곳 모두 필요하다.)

수정 후 Maya 에서 `rehash; source "AdvancedSkeleton.mel";` 로 다시 소스한다.

**남는 부작용 (반드시 인지할 것)**
- line 34342 RibbonCurve 루프는 없는 조인트를 `upperLipJoint<n>_R`(입꼬리) 로 **대체**한다.
  → 오른쪽 아랫입술 리본 커브에 **중복/왜곡된 포인트**가 생겨 입꼬리 근처 변형이 좌우 비대칭이 된다.
- 오른쪽 아랫입술 한 지점의 sticky-lip 구동(`lowerLipSR/MDL/Clamp/BC10_R`)이 통째로 빠진다.
- 즉 **"에러 없이 빌드되지만 리그 품질은 보장 안 됨"**. 프로덕션 리그에는 5-A 를 쓸 것.

---

## 6. 추가 진단 — `FaceFitLipMain` 에 저장된 엣지 루프가 **끊겨 있는** 경우

> 실사용 진단에서 **LipMain 에 저장된 엣지 루프가 온전한 루프가 아니라 도중에 끊겨 있는 것**이 확인되었다.
> 이것이 이 에러를 일으킬 수 있는지, 그리고 온전한 루프가 필수인지를 코드 + **mayapy 실측**으로 검증한 결과다.

### 6-0. 결론

| 질문 | 답 |
|---|---|
| 끊긴 엣지 루프가 이 에러를 일으키는가? | **그렇다.** 3장의 "모델 비대칭"과 **독립적인 별도 원인**이다. 모델이 완벽히 대칭이어도 루프가 끊겨 있으면 같은 에러가 날 수 있다. |
| 반드시 온전한(끊김 없는) 루프여야 하는가? | **그렇다.** AS 는 이를 전제로 하지만 **검사가 절반만 되어 있어서** 끊긴 루프가 Fit 단계를 조용히 통과한다. |
| 끊겨도 에러 없이 넘어갈 수 있는가? | 있다. 그 경우 **에러 대신 "입술 리그가 짧게 잘린 채" 빌드**된다 — 더 나쁜 결과다. |

### 6-1. 저장 위치

Face Fit 시 선택한 컴포넌트는 그대로 문자열로 박제된다 (`AdvancedSkeleton.mel:29340-29344`).

```mel
addAttr -ln selection -dt "string" ("FaceFit"+$section+$part+$leftSuffix);
$tempString[0]="";
for ($i=0;$i<size($sel);$i++)
    $tempString[0]=$tempString[0]+$sel[$i]+" ";
setAttr -type "string" ("FaceFit"+$section+$part+$leftSuffix+".selection") $tempString[0];
```

→ `FaceFitLipMain.selection`, `FaceFitLipOuter.selection`, `FaceFitLipInner.selection`
(비대칭 피팅이면 `...MainLeft.selection` 도)

### 6-2. Fit 단계 — 끊김 검사가 **한 방향만** 있다 (핵심)

`asCreateFaceFit` 은 `$startVtx`(입꼬리)에서 시작해 **두 방향**으로 루프를 걸어간다.
그런데 두 walk 의 막다른 길 처리 방식이 **다르다**.

**walk 1 — `$edges1` (line 29639-29678): 조용히 중단**

```mel
$tempString2=`ls -sl -fl`;
if ($tempString2[0]=="")
	break;                     // ← 에러도 경고도 없다. 그냥 커브가 짧게 끝난다
```

**walk 2 — `$edges2` (line 29941-29987): 에러**

```mel
$tempString2=`ls -sl -fl`;
if (!`size($tempString2)`)
	{
	delete ("FaceFit"+$section+$part+$leftSuffix) faceLoopCurve1;
	asFaceUpdateInfo 1;
	select $sel;
	error "Not a complete edgeloop";     // ← 이쪽만 막아준다
	}
```

즉 **`Not a complete edgeloop` 에러가 안 떴다는 것이 "루프가 온전하다"는 증거가 되지 못한다.**
끊긴 자리가 walk 1 쪽이면 Fit 은 성공한 것처럼 끝나고, 커브만 조용히 짧아진다.

### 6-3. Lip 은 **반대쪽 반을 먼저 지나간다**

```mel
string $startVtx=$maxXVtx;      // line 29429
string $endVtx=$minXVtx;        // line 29430
```

입술 walk 는 한쪽 입꼬리(maxX)에서 출발해 **입 전체 루프를 한 바퀴** 돈다.
그리고 커브에 포인트를 기록할 때 반대쪽 반은 건너뛴다 (line 29974):

```mel
else if ($section=="Lip" && $pos[0]>0.001 && size($lipStartVtxs)==0 && !`objExists asRunningFaceLipLeft`)
	;                          // x>0 (반대쪽 반) 은 커브에 넣지 않음
else
	{ $curveCmd+=" -p "+$pos[0]+" "+$pos[1]+" "+$pos[2]; ... }
```

**⇒ 끊긴 자리가 반대쪽 반에 있어도 내 쪽 커브가 망가진다.**
"오른쪽만 쓰니까 오른쪽만 온전하면 된다"는 통하지 않는다. **입 루프 전체가 온전해야 한다.**

### 6-4. Build 단계 — BFS 도 끊김에서 멈춘다 (**mayapy 실측**)

빌드 시 build-curve 는 스냅된 정점 집합(`$loopVtxs`) **안에서만 엣지로 확장하는 BFS** 로 만들어진다
(`AdvancedSkeleton.mel:34151-34166`).

```mel
select $tempString[0];                       // CV0 이 스냅된 정점에서 시작
for ($i=0;$i<size($loopVtxs);$i++)
	{
	$tempString=`ls -sl -fl`;
	if (size($tempString)==0)
		continue;                            // ← 더 갈 데가 없으면 그냥 넘어간다 (에러 없음)
	$completedVtxs=`stringArrayCatenate $completedVtxs $tempString`;
	$pos=`xform -q -ws -t $tempString`;
	$curveCmd+=" -p "+$pos[0]+" "+$pos[1]+" "+$pos[2];
	ConvertSelectionToEdges;
	ConvertSelectionToVertices;
	$tempString=`ls -sl -fl`;
	for ($y=0;$y<size($tempString);$y++)
		if (!`stringArrayCount $tempString[$y] $loopVtxs`)
			select -d $tempString[$y];       // ← 선택 집합 밖으로는 못 나간다
	select -d $completedVtxs;
	}
```

이 로직만 떼어내 Maya 2024 (`mayapy` + `maya.standalone`) 에서 정점 11개짜리 체인으로 돌린 결과:

| 케이스 | 선택된 정점 수 | 만들어진 커브 포인트 수 | `$mainNumCv` |
|---|---:|---:|---:|
| A. 온전한 체인 | 11 | 11 | **11** |
| B. index 5 에서 끊김 | 10 | **5** | **5** |
| C. index 8 에서 끊김 | 10 | **8** | **8** |

**확인된 사실 3가지**
1. 끊기면 **에러도 경고도 없이** 커브가 짧아진다.
2. 남는 CV 수 = **시작 정점 ~ 끊긴 지점까지의 거리**. 선택된 정점 수와 무관하다 (B: 10개 선택했는데 5개).
3. 끊긴 위치가 조금만 달라져도 결과 CV 수가 통째로 달라진다 (B=5 vs C=8).

→ 3번이 결정적이다. **좌/우가 서로 다른 지점에서 멈추면 2장의 개수 불일치가 그대로 재현된다.**

### 6-5. 끊김 위치에 따라 어떤 증상이 나오는가

| 좌/우 truncation | 결과 |
|---|---|
| 좌우가 **같은 지점**에서 끊김 | **에러 없이 빌드된다.** 대신 입술 조인트/컨트롤러가 입꼬리까지 못 가고 **중간에서 잘린 리그**가 나온다 |
| **오른쪽이 더 길게** 살아남음 (L 짧음) | `lowerLipJoint10_R` 없음 → **line 34482** ← **이번 케이스** |
| **왼쪽이 더 길게** 살아남음 (R 짧음) | 동일 문구가 **line 34211** 의 `select` 에서 발생 |

> `select` 와 `xform -q -ws -t` 는 없는 노드에 대해 **완전히 같은 메시지**(`No object matches name: ...`)를 낸다 (Maya 2024 확인).
> 따라서 **메시지 문구가 아니라 줄 번호(34211 vs 34482)로** 어느 쪽이 짧은지 구분해야 한다.

### 6-6. 그래서 온전한 엣지 루프는 **필수인가** → 예

1. AS 자신이 `error "Not a complete edgeloop"` 로 규정 (29963) — 다만 **두 방향 중 한 방향만** 검사
2. Fit walk 가 반대쪽 반을 먼저 지나므로 **끊김 위치가 어디든** 커브에 영향 (29429, 29974)
3. Build BFS 는 선택 집합 안에서 인접 엣지로만 확장 → **끊기면 정지** (34151-34166, 6-4 실측)
4. 이후 **조인트 생성 · 삭제 인덱스 · follicle · 리본 · 스티키립 · 스킨 웨이트**가 전부
   이 CV 수 하나(`$mainNumCv`)에 묶여 있다 (34171, 34211, 34445, 35117)

**끊긴 루프로 정상 리그가 나오는 경우는 없다.** 운이 좋으면 짧은 리그, 나쁘면 빌드 실패다.

### 6-7. 저장된 루프가 온전한지 검사하기

씬에 FaceFit 이 살아 있는 상태에서 Script Editor(**MEL**)에 붙여 실행한다.

```mel
// ---- 저장된 Lip 선택의 루프 무결성 검사 ----
global proc asCheckLoopIntegrity (string $faceFitNode)
{
string $ends[],$iso[],$neighbours[],$v,$m,$vtxs[];
int $c;
eval ("select "+`getAttr ($faceFitNode+".selection")`);
ConvertSelectionToVertices;
$vtxs=`ls -sl -fl`;
for ($v in $vtxs)
	{
	select $v;
	ConvertSelectionToEdges;
	ConvertSelectionToVertices;
	$neighbours=`ls -sl -fl`;
	$c=0;
	for ($m in $neighbours)
		if ($m!=$v && `stringArrayCount $m $vtxs`)
			$c++;
	if ($c==0) $iso[size($iso)]=$v;
	if ($c==1) $ends[size($ends)]=$v;
	}
print ($faceFitNode+" : total vtx="+size($vtxs)+"  openEnds="+size($ends)+"  isolated="+size($iso)+"\n");
select $ends $iso;
}

asCheckLoopIntegrity "FaceFitLipMain";
// asCheckLoopIntegrity "FaceFitLipOuter";
// asCheckLoopIntegrity "FaceFitLipInner";
// asCheckLoopIntegrity "FaceFitLipMainLeft";   // non-symmetrical 피팅을 썼다면
```

**판정** (Maya 2024 에서 닫힌 링 12정점으로 검증한 값)

| `openEnds` | 의미 |
|---:|---|
| **0** | **온전한 닫힌 루프 — 정상** |
| **2** | **한 군데 끊김** ← 이번 케이스 |
| **4 이상** | 여러 군데 끊김 |
| `isolated > 0` | 루프에서 완전히 떨어진 정점이 섞여 있음 |

실행 후 **끊긴 지점의 정점들이 선택된 채로 남는다.** 뷰포트에서 바로 어디가 끊겼는지 보인다.

> 이 검사는 "선택된 엣지"가 아니라 **메시 인접성**을 기준으로 센다.
> AS 의 build BFS(34151)가 정확히 같은 기준으로 걸어가므로, 엣지 기준 검사보다 실제 동작에 더 가깝다.

### 6-8. 해결 — 루프를 다시 잡는다

1. 위 검사로 끊긴 지점을 찾아 **뷰포트에서 확인**한다.
2. 메시의 해당 부분 토폴로지를 확인한다. 끊김은 보통 이런 데서 온다:
   - 입꼬리/인중 주변의 **폴(pole)·삼각형** 때문에 엣지 루프가 한 바퀴 이어지지 않음
   - `Select > Edge Loop` 이 중간에서 다른 줄로 튀어서, 사용자가 **수동으로 이어 붙이다 한 칸 빠뜨림**
   - 좌우 반을 따로 선택해 합치면서 **미드라인 정점 1개가 누락**
3. **입술 루프가 한 바퀴 완전히 도는지** 확인한다 — `Select > Edge Loop` 더블클릭 한 번으로
   입 전체가 끊김 없이 선택되어야 이상적이다. 안 되면 토폴로지를 고치는 편이 빠르다.
4. Lip 피팅(Inner / Outer / Main)을 **지우고 다시** 한다. `.selection` 은 피팅할 때만 갱신되므로
   커브만 옮겨서는 저장된 선택이 고쳐지지 않는다.
5. 다시 6-7 검사로 `openEnds=0` 확인 → 3장의 대칭 확인 → `Build AdvancedFace`.

---

## 7. 재발 방지 체크리스트

Face 빌드 전에 매번 확인:

- [ ] 메시가 **월드 X=0** 에 걸쳐 있고 트랜스폼 freeze / 히스토리 삭제됨 (`Model Clean`)
- [ ] `Model Check` 결과가 `// Model is symmetrical.`
- [ ] **입 엣지 루프가 한 바퀴 끊김 없이 이어짐** — 6-7 검사에서 `openEnds=0`
- [ ] 위/아래 **입술 엣지 루프의 좌우 정점 수가 동일**
- [ ] Lip Fit 커브(Inner/Outer/Main)가 좌우 대응 정점에 스냅되는지 육안 확인
- [ ] `non symmetrical` 옵션을 쓸 거면 **Lip 피팅 시작 전에** 켠다

> `Not a complete edgeloop` 에러가 안 났다고 안심하지 말 것 — 그 검사는 **두 방향 중 한 방향만** 본다 (6-2).

---

## 8. 참고

| 항목 | 위치 |
|---|---|
| 에러 발생 줄 | `AdvancedSkeleton.mel:34482` |
| 잘못된 인덱스로 조인트 삭제 | `AdvancedSkeleton.mel:34210-34212` |
| 조인트 생성 (좌우 별도 카운트) | `AdvancedSkeleton.mel:34171-34182` |
| follicle 루프 (오른쪽 카운트 사용) | `AdvancedSkeleton.mel:34445-34462` |
| AS 자체 "모델 비대칭" 에러 + 가이드 링크 | `AdvancedSkeleton.mel:34350-34352` |
| AS 자체 주석 "slight asymmetry ... mismatched num Right vs Left" | `AdvancedSkeleton.mel:41100` |
| 왼쪽 피팅 미러 복제 | `AdvancedSkeleton.mel:31021-31041` |
| 대칭 검사 본체 (`asModelChecker`) | `AdvancedSkeleton.mel:74223-74357` |
| 빌드 중 대칭 검사 스킵 | `AdvancedSkeleton.mel:30833-30835` |
| Fit 선택 저장 (`.selection`) | `AdvancedSkeleton.mel:29340-29344` |
| walk 1 — 끊김 시 **조용히 break** | `AdvancedSkeleton.mel:29666-29667` |
| walk 2 — 끊김 시 `Not a complete edgeloop` | `AdvancedSkeleton.mel:29958-29963` |
| Lip walk 시작/끝 정점 (반대쪽 반부터 통과) | `AdvancedSkeleton.mel:29429-29430`, `29974` |
| build-curve BFS (끊기면 조용히 절단) | `AdvancedSkeleton.mel:34151-34166` |

공식 영상:
- 비대칭 모델로 인한 lip joint 누락: <https://www.youtube.com/watch?v=-V3Sk-COJU0&t=297s>
- Model Check 사용법: <https://www.youtube.com/watch?v=mTB9Yh_sWKc&t=265s>
- non symmetrical 워크플로: <https://www.youtube.com/watch?v=kz4NaLGMtQg>
