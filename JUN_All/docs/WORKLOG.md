---
title: 작업 일지 (WORKLOG)
aliases: [WORKLOG, 작업일지, devlog]
tags: [worklog, maya-python]
updated: 2026-06-16
---

# 작업 일지 (WORKLOG)

git 커밋 기록을 근거로 하루 작업을 요약한다. 최신 날짜가 위.

> [!info] 보기
> Obsidian 에서 `JUN_All/docs` 를 vault(또는 폴더)로 열면 속성/태그/링크가 동작한다.
> 굵게/링크가 별표째 보이면 소스 모드이므로 `Ctrl+E` 로 읽기/라이브 프리뷰 전환.

---

## 2026-06-16 (오늘)

> [!summary] 신규 병합 툴 2종 + Qt 인프라 정리
- **A00145_RigConnect**: MEL ConnectionTool V04.02 + A00140 병합(4탭 PySide) 신규 툴, 사용법 [A00145 가이드](A00145_RigConnect.md) (`5592490`, `d1750df`) #A00145_RigConnect
- **A00060_jointTool_V02**: MEL JointTool V05.03 + A00060 병합(4탭) 신규 툴, 사용법 [A00060 V02 가이드](A00060_jointTool_V02.md) (`ec42af1`, `bbb78bd`) #A00060_jointTool_V02
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
