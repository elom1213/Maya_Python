---
name: jun-jali-repo
description: JUN_JALI = VisemeNet(visemenet-inference) 포크 저장소 — 경로, origin(푸시 대상 main) / upstream, .venv 추론 환경, angela_JALI 리그 적용 예시
metadata:
  type: project
---

`C:\Users\USER\Desktop\JP\0030_maya_python_JUN\JUN_JALI` — 2026-10-19 포크. 목표: 같은 의미 · 다른 언어 음성 → JALI 리그 립싱크 (Maya → Unreal).

- **푸시 대상 = `origin` (`https://github.com/elom1213/JUN_JALI.git`) 의 `main`** — 사용자가 "앞으로 이 경로에 푸시" 라고 지정.
  푸시 자체는 여전히 그 턴에 요청이 있을 때만(전역 규칙 2장). `upstream` = `junhwanjang/visemenet-inference` (`c20ec78` 위에 작업).
- 추론: 저장소 안 `.venv`(Python 3.11.9 · `tensorflow-cpu` 2.15.1, `requirements.txt`) — `visemenet_frozen.pb` 가 원본 코드 수정 없이 돈다.
  입력은 **44.1kHz · 16bit int WAV** 필수(리샘플 없음, 48kHz/float 는 조용히 틀림). 출력 txt = 100fps × 22열(Jaw Lip + 비짐 20).
- 리그: `C:\Users\USER\Desktop\JP\0001_PJ_portfolio\0040_JULI\scenes\angela_JALI.ma`(Maya 2015, film 24fps) — `CNT_PHONEMES` /
  `CNT_COARTIC` / `CNT_JaLi.tx`(Jaw) `.ty`(Lip). VisemeNet 원본 매핑 이름이 그대로 맞는다. 적용 = `examples/maya_apply_visemenet.py`.
- 문서: `docs/0010_visemenet_feasibility.md`(진단 · M1~M7 계획) · `docs/0020_usage_example_maya.md`(사용법). 결과물 `out/` 은 gitignore.
- **2026-10-19 툴 3종**: `setup_env.bat`(더블클릭 설치 · 자가 검사) · `Run_VisemeNet_Converter.bat` + `tools/VisemeNet_Converter`
  (사전 검사 E01~E11, 실패면 변환 0, 결정적 모드 기본) · `vendor/Framework`(Maya_Python Framework 복사본, `tools/sync_framework.py` 로 갱신).
  마야 쪽은 Maya_Python `A00540_JaliLipSync` [[wip-a00540-jalilipsync]]. 문서 0050 = 설치 · 변환기 안내.
- **Python 3.14 PC (2026-10-20, Win10 보고)**: 새 Python 설치 관리자의 `py -3.11` 은 3.11 이 없어도 오류만 찍고 **종료 코드 0** →
  setup 은 후보를 실행해 출력(JUNPY 3 11 64)으로 판단. 없으면 **전용 Python 3.11.9** (python.org NuGet, SHA-256 `9283876d…`) 를 `.python\` 에
  .NET 으로 받아 푼다(`Lib\site-packages` 는 건너뜀 - 260자). bat 의 `call :say "... -> ..."` 처럼 메시지에 `>` 를 쓰면 리다이렉트된다.
- 남은 핵심 리스크: 영어 학습 모델이라 한국어 ㅓ · ㅡ, 일본어 う 품질 미검증. 라이선스: 원본 GPLv3/상용(UMass).

관련: [[mayapy-headless-verify]], [[posewrangler-plugin-fork-patch]]
