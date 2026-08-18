---
name: wip-a00510-bone-viewport
description: "JUN_UE A00510 본 표시 툴 - PersonaOptions CDO 로 draw mode, BoneDrawSize 는 C++ 아니면 불가"
metadata: 
  node_type: memory
  type: project
  originSessionId: 559dfd30-01bc-4110-8708-a1499b043ca1
  modified: 2026-08-14T03:40:33.834Z
---

`JUN_UE` 의 A00510_bone_viewport (v01.00, 2026-08-14). 스켈레탈 메시 뷰포트에서
`눈 아이콘 > Bones > All Hierarchy` 를 타고 들어가던 것을 메뉴 클릭 한 번으로.

**되는 것**: `unreal.find_object(None, "/Script/UnrealEd.Default__PersonaOptions")` 로 CDO 를 잡고
`DefaultBoneDrawSelection`(0=None … **5=All Hierarchy**), `bShowBoneColors` 를 읽고 쓴다.

**안 되는 것 — Bone Draw Size**: `FAnimationViewportClient::BoneDrawSize` 는 `UPROPERTY` 도
`UFUNCTION` 도 아닌 **평범한 C++ 멤버**다. 리플렉션이 없으니 파이썬에서 접근할 방법이 아예 없다.
(에디터를 열 때마다 1.0 으로 리셋되는 이유이기도 하다.) C++ 에디터 모듈이면
`IPersonaViewport::GetViewportClient()` → `SetBoneDrawSize()` 로 가능 — 둘 다 Public 헤더.

**함정 3개**
- `unreal.PersonaOptions` 클래스는 **생성되지 않는다**. CDO 를 경로로 직접 찾아야 한다
- 그렇게 얻은 오브젝트는 프로퍼티 이름이 snake_case 가 아니라 **C++ 이름 그대로** (`DefaultBoneDrawSelection`)
- 파이썬에 `SaveConfig()` 가 없어 **세션 한정**. 뷰포트 메뉴에서 Persona 옵션을 아무거나 한 번
  건드리면 엔진이 오브젝트 전체를 저장하면서 우리 값도 같이 기록된다
- 이미 열려 있는 뷰포트는 `BonesToDraw` 캐시 때문에 즉시 안 바뀐다 →
  Skeleton Tree 에서 본을 한 번 클릭하면 갱신 (`UpdateBonesToDraw()` 가 도는 순간: 에디터 열 때 /
  메시 교체 / 본 선택 변경)

관련: [[jun-ue-plugin-repo]], [[unreal-python-tool-verify]]
