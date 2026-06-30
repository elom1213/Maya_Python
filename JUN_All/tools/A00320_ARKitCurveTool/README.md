# A00320_ARKitCurveTool

UE 5.5 — Content Browser 에서 **Skeleton 우클릭 → "Add ARKit Curves to Skeleton"** 기능을
**B-2(하이브리드) 방식**으로 구현한 코드 모음.

> 원본 분석/설계 문서:
> `../../docs/study/Add_ARKit_Curves_to_Skeleton_분석.md`
> `../../docs/study/Add_ARKit_Curves_B안_구현가이드.md`

⚠️ 이 폴더의 파일들은 **참고/이식용 원본**입니다.
실제 적용은 `C:\MANUSetup` 프로젝트에 **사용자가 직접 복사·빌드**하셔야 합니다.
(이 도구는 MANUSetup 경로를 건드리지 않습니다.)

---

## 파일 구성

| 파일 | 이식 위치(권장) | 역할 |
|------|----------------|------|
| `MANUSkeletonCurveLibrary.h` | `MANUProject/Source/MANU/Utilities/` | C++ 래퍼 헤더 — `AddCurveMetaData` 를 BP/Python 에 노출 |
| `MANUSkeletonCurveLibrary.cpp` | `MANUProject/Source/MANU/Utilities/` | 래퍼 구현 (ARKit 52개 이름 자체 포함) |
| `add_arkit_curves.py` | `MANUProject/Content/Python/` | 선택 스켈레톤에 커브 일괄 추가하는 실행 스크립트 |
| `init_unreal.py` | `MANUProject/Content/Python/` | 우클릭 메뉴 자동 등록 (에디터 시작 시 실행) |

> **왜 C++가 필요한가**: UE 5.5에서 `USkeleton::AddCurveMetaData()` 는 Python/BP 에
> 기본 노출되지 않습니다. 그래서 "얇은 C++ 래퍼 1개"가 최소 비용의 핵심입니다.
> 나머지(메뉴/순회/결과표시)는 전부 Python 으로 처리합니다.

---

## 설치 순서

1. **Python 플러그인 활성화**
   - `Edit > Plugins` → `Python Editor Script Plugin` 체크 → 에디터 재시작
   - (또는 `.uproject` 의 `Plugins` 에 `{"Name": "PythonScriptPlugin", "Enabled": true}` 추가)

2. **C++ 래퍼 이식 + 빌드**
   - `MANUSkeletonCurveLibrary.h/.cpp` 를 `Source/MANU/Utilities/` 에 복사
   - 프로젝트 빌드 (Visual Studio 또는 에디터 Live Coding)
   - 빌드 후 Python 에서 확인: `dir(unreal.MANUSkeletonCurveLibrary)`

3. **Python 스크립트 이식**
   - `add_arkit_curves.py`, `init_unreal.py` 를 `Content/Python/` 에 복사
   - 에디터 재시작 → `init_unreal.py` 가 우클릭 메뉴 자동 등록

4. **실행**
   - Content Browser 에서 Skeleton 우클릭 → **MANU Tools > Add ARKit Curves to Skeleton**
   - 또는 Output Log Python 창에서:
     ```python
     import add_arkit_curves; add_arkit_curves.add_arkit_curves_to_selected()
     ```

---

## 검증 체크리스트

- [ ] `dir(unreal.MANUSkeletonCurveLibrary)` 에 `add_arkit_curves_to_skeleton` 표시
- [ ] Skeleton 우클릭 메뉴에 항목 노출
- [ ] 실행 후 Skeleton 더블클릭 → Anim Curve 패널에 52개 표시
- [ ] 재실행 시 "추가된 커브: 0개" (중복 추가 안 됨 = idempotent)

---

## 대안 / 변형

- **52개 이름을 프로젝트 기존 데이터와 공유하려면**: `MANUSkeletonCurveLibrary.cpp` 의
  자체 리스트 대신 `FARKitBlendShapeHelper::GetARKitBlendShapeNames()` 호출로 교체.
  단, `MANU.Build.cs` 에 `"MANUAnimation"` 의존성 추가 필요. (.cpp 상단 주석 참고)
- **순수 Python(B-1) 만으로**: 커브 추가 단계가 UE API 한계로 막힘 → 비권장.
- **C++ 풀모듈(A안)**: 기존 MANUEditor 의 ContentBrowser 익스텐더 방식.
  우클릭 위치 자유도가 높지만 코드량이 많음.

---

## Maya 사용자를 위한 대응 메모

| Maya | Unreal |
|------|--------|
| `cmds.ls(selection=True)` | `unreal.EditorUtilityLibrary.get_selected_assets()` |
| marking menu / `popupMenu` | `init_unreal.py` + `unreal.ToolMenus` |
| `cmds.confirmDialog` | `unreal.EditorDialog.show_message` |
| Python 단독으로 대부분 처리 | 핵심 API 일부는 C++ 노출 래퍼 필요 |
