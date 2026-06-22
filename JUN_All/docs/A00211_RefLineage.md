---
title: A00211_RefLineage — 씬 reference → Lineage 내보내기
aliases: [A00211, RefLineage, Ref Lineage]
tags: [tool, maya, lineage, A00211_RefLineage]
updated: 2026-06-22
---

# A00211_RefLineage

현재 **Maya 씬의 reference 관계**(중첩 포함)를 읽어, **A00210_FileManager 의 Lineage 탭**에서
그대로 열리는 lineage JSON 으로 내보내는 **Maya 내 PySide** 툴이다. A00210 의 동반 툴이며,
A00210 에서 손으로 그리던 reference 관계를 **씬에서 자동으로** 뽑아낸다.

> [!info] 한 줄 요약
> "지금 열린 씬이 어떤 파일들을 reference 로 불러오는가"를 노드 그래프(JSON)로 만들어,
> A00210 Lineage 탭에서 **참조 대상 → 참조하는 파일** 점선 화살표로 본다.

---

## 1. 동작 원리

- **노드 = 파일 1개**(절대경로로 dedup). 현재 씬 자신도 루트 노드(depth 0)로 들어간다.
- **엣지 = reference 관계**. `cmds.referenceQuery` 로 각 reference 노드의 파일과 부모(자기를
  불러온 파일/씬)를 따라가며, A00210 의 **reference 엣지 규약**(`owner.references` 에 source id,
  화살표 **참조 대상(source) → 참조하는 파일(owner)**)으로 기록한다.
- **중첩 reference** 도 재귀로 따라가 깊이(depth)별로 자동 배치한다(계보 parents 가 아니라
  references 라 A00210 의 Auto Layout 에는 안 잡히므로 보기 좋은 초기 위치를 직접 준다).
- **포맷/설정 단일 소스**: A00210 의 `app/core/lineage.py`(`LineageGraph`) · `store.py` ·
  `prefs.py` 를 **그대로 재사용**한다. 따라서 JSON 포맷이 100% 동일하고, 출력 위치(`store_dir`)와
  키 기준(`project_root`)도 A00210 설정(`~/.jun_filemanager/prefs.json`)을 공유한다.
- **key**: `project_root` 기준 상대경로(POSIX). 루트 밖이거나 루트 미설정이면 `key=""`(노드는
  보이지만 record/썸네일 링크는 없음).

저장 경로: `<store_dir>/lineage/<name>.json` — A00210 의 Lineage 그래프와 같은 폴더.

---

## 2. 사용법

1. **설치**: `__dragDrop_A00211.py` 를 Maya 뷰포트로 드래그&드롭 → 셸프 버튼(`RefLineage`) 생성.
   (또는 `tools.A00211_RefLineage.run(True)` 직접 호출.)
2. reference 가 걸린 씬을 연 상태에서 셸프 버튼 실행 → 창이 뜨며 **자동 스캔**된다.
3. 필요하면 **Scan Scene References** 로 다시 스캔. 트리에서 씬 → 중첩 reference 구조를 확인한다.
4. **Graph name** 을 확인(기본값 = 씬 파일명)하고 **Export to Lineage JSON** 클릭.
5. A00210_FileManager 의 **Lineage 탭에서 Refresh** → 방금 만든 그래프가 노드로 나타난다.
   동기화하려면 A00210 의 **Push** 를 사용한다.

> [!tip] 명령으로 한 번에
> UI 없이 내보내려면:
> `from tools.A00211_RefLineage.app.core import ref_scanner as rs`
> `rs.export_scene_references(name="")`  → `(저장경로, 그래프)` 반환.

---

## 3. 메모

- **사전 조건**: A00210_FileManager 에서 **Store Repo(store_dir)** 가 설정돼 있어야 한다(미설정 시
  내보내기 경고). **Project root** 가 설정돼 있으면 노드 key 가 채워져 record/썸네일과 연결된다.
- 같은 이름의 그래프가 있으면 **덮어쓸지 확인**한다(수동으로 그린 그래프를 실수로 덮지 않도록).
- 같은 파일을 여러 번 reference 해도(복사본) **노드는 1개**로 합친다. 로드 안 된 reference 는
  트리/노드에 `unloaded` 로 표시한다.
- 이 툴은 **읽기 전용 스캔 + JSON 쓰기**만 한다. 씬을 수정하지 않는다.
