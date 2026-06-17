---
title: 작업 일지 (WORKLOG)
aliases: [WORKLOG, 작업일지, devlog]
tags: [worklog, maya-python]
updated: 2026-06-17
---

# 작업 일지 (WORKLOG)

git 커밋 기록을 근거로 하루 작업을 요약한다. 최신 날짜가 위.

> [!info] 보기
> Obsidian 에서 `JUN_All/docs` 를 vault(또는 폴더)로 열면 속성/태그/링크가 동작한다.
> 굵게/링크가 별표째 보이면 소스 모드이므로 `Ctrl+E` 로 읽기/라이브 프리뷰 전환.

---

## 2026-06-17 (오늘)

> [!summary] 윈도우 최상단 정책 개선 + 신규 툴 2종(A00200·Release Builder) + Mirror Key Behavior
- **Framework/qt**: 모든 Qt 툴 창을 **마야 메인 윈도우에 parent** — 뷰포트 위에는 떠 있되 다른 툴
  창과는 정상 Z-order(밑에 있는 창을 클릭하면 위로 올라옴). `Qt.WindowStaysOnTopHint`(항상 최상단)
  폐기. 공용 헬퍼 `Framework/qt/maya_window.py` 의 `maya_main_window()` 추가, A00110+12개 Qt 툴 및
  A00008 템플릿에 일괄 적용(A00200 은 기존부터 동일 패턴) (`d2b5ad4`) #Framework
- **dev/release_builder_QT**: 릴리스 패키징용 **PySide Release Builder QT** 신규 (`7640a92`) #dev
- **A00200_CSV_tool**: **ARKit 페이셜 CSV import** 신규 툴 + 드래그&드롭 설치(`__dragDrop_A00200`)
  (`3d9ec1e`) #A00200_CSV_tool
- **A00110_animTool**: Mirror Key 탭에 **Behavior 모드**(기본 ON) 추가 — 반대쪽 컨트롤러의 고유
  forward/up 축 방향을 보존하며 미러. 소스의 **로컬 채널 값(translate/rotate)을 타겟에 그대로
  복사**한다(반사·행렬 연산 없음, 반사축 무관). Maya `mirror joints` 의 Behavior 세팅으로 만든
  좌우 축 반전 리그용. 체크박스로 기존 월드 반사(orientation)와 선택, 구간/현재프레임 둘 다 적용.
- **A00110_animTool**: Behavior 가 ON 이면 반사축이 무의미하므로 **Mirror Axis 라디오 비활성**.
- **A00110_animTool**: Mirror 실행(Mirror Selected·Mirror Current Frame)이 **씬 선택과 무관하게
  Source/Target 리스트의 오브젝트만** 대상으로 처리(선택 → `Resolve Pairs`/`Select Source` 로
  리스트 채우기 → 실행으로 단계 분리). (v01.08~01.09) #A00110_animTool

## 2026-06-16

> [!summary] 신규 병합 툴 2종 + Qt 인프라 정리 + JointTool Aim 재설계
- **A00145_RigConnect**: MEL ConnectionTool V04.02 + A00140 병합(4탭 PySide) 신규 툴, 사용법 [A00145 가이드](A00145_RigConnect.md) (`5592490`, `d1750df`) #A00145_RigConnect
- **A00060_jointTool_V02**: MEL JointTool V05.03 + A00060 병합(4탭) 신규 툴, 사용법 [A00060 V02 가이드](A00060_jointTool_V02.md) (`ec42af1`, `bbb78bd`) #A00060_jointTool_V02
- **A00060_jointTool_V02**: Aim 탭 재설계 — Aim axis 드롭박스(X/Y/Z) + twist-only IK식 정렬(joint 월드 위치 보존·constraint/cycle 제거·레퍼런스 안전, v01.01) (`4c67ac8`) #A00060_jointTool_V02
- **Framework/qt**: 모든 Qt 툴을 `Framework.qt.qt` 래퍼 경유로 일원화 (`f3c8d58`) #Framework
- **deps**: 외부 의존성 관리 중앙화 (`a13792c`)
- **A00110_animTool**: Smart bake 옵션(native `bakeResults -smart`, v01.07) + 비교 문서 (`859299d`, `c0d7db8`) #A00110_animTool
- **dragDrop**: 드롭 설치 파일명 고유화로 셸프 버튼 충돌 해결 (`30f0f09`)
- **A00190_FKIK_General_Tool**: 레거시 FK/IK 툴 PySide 리팩터 (`cab90a6`) #A00190_FKIK

## 2026-06-15

> [!summary] animTool/abSymMesh PySide 강화 + bake 성능
- **A00110_animTool**: Copy Key 탭(v01.03)·Mirror Key 탭(v01.04) 추가 + 문서화 (`f6139ac`, `147fa7f`, `be41423`, `8917cbf`) #A00110_animTool
- **A00180_abSymMesh**: Python/OpenMaya 재구현(속도)·app/ 레이아웃 + PySide UI·동작 문서 (`f01ced1`, `f6f5053`, `4719e56`) #A00180_abSymMesh
- **A00170_driverTool**: RemapVal + SphericalEye 를 탭 툴로 병합 (`96acac4`) #A00170_driverTool
- **A00150_remapVal**: 보간을 enum(Linear/Smooth/Spline)으로 (`2cb49aa`) #A00150_remapVal
- **A00120_FKIK**: per-frame 루프 대신 native `bakeResults` 로 bake (`b83c591`) #A00120_FKIK
- **A00080_KWI_creator**: 결합 파일 출력(base+setting+LD) (`61c459e`) #A00080_KWI_creator
- **dev/reload**: per-tool `reload_for_tool` 추가 + 전 Qt 런처 전환 (`1660c63`)
- **Framework/styles**: 체크박스·라디오 인디케이터 전 테마 가시성 수정 (`acf285e`, `730f8b4`) #Framework

---
