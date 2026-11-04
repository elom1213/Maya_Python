---
name: wip-a00220-save-cache
description: A00220 Save Cache(SSD 캐시 저장 → HDD 지연 복사) 계획 — 실측상 로컬 HDD 는 마야 저장 이득 없음(OS 쓰기 캐시), NAS 실측 게이트 대기
metadata:
  type: project
---

2026-11-04 계획서 `JUN_All/docs/plans/A00220_BackupTool_save_cache_plan.md`. **구현 전** — 1단계 실측 게이트(사용자 실제 씬 · NAS) 대기.

실측(이 PC: C: WD SN850X NVMe, D: Seagate ST4000DM004 SATA HDD):
- python 쓰기 fsync 없이 300MB = HDD 0.07s(SSD 와 같음), 1500MB = HDD 1.7s. fsync 하면 HDD ~148MB/s.
- **마야 저장(mayapy 2024) 426MB .mb 4~6s · 904MB .ma 4s대 — SSD 와 HDD 같다.** 저장 시간은 직렬화(CPU), 마야는 fsync 안 함 → OS 캐시가 흡수.
- 시험 장면 함정: polyPlane 은 히스토리째 저장돼 0MB — `delete(ch=True)` 해야 메쉬 데이터가 들어간다.

**Why:** 사용자는 "HDD 저장이 느리니 SSD 에 먼저" 를 전제로 기획했지만 로컬 HDD 에선 전제가 실측으로 성립하지 않았다.
**How to apply:** 진행 요청이 오면 먼저 NAS(`\172.30.1.93\...`) · 실제 씬 저장 시간을 재고(팀 NAS 에 쓰기 전 허락), 차이가 있을 때만 계획서 2단계부터. A00220 은 standalone 이라 마야 쪽 훅이 반드시 필요.
