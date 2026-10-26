---
name: wip-stt-converter
description: "JUN_JALI STT Converter(음성 → 대본 변환기) — 2026-10-23 계획서만(docs/0130), 코드 전. 한·일·영 wav → MFA 용 .lab, faster-whisper large-v3-turbo 1차 · Qwen3-ASR 2차. 대상 PC 두 종(RTX 5070 / Ryzen 9 3900X + RTX A2000 12GB + 32GB) + Windows 10 지원이 사용자 지정 조건"
metadata:
  node_type: memory
  type: project
  originSessionId: 40661a54-d8da-4b4c-af07-5f9083aed21b
  modified: 2026-10-23T06:53:57.010Z
---

**2026-10-23 — 계획 단계.** 계획서 `JUN_JALI/docs/0130_stt_converter_plan.md`(README 표 등록, 로컬 커밋 — 푸시 안 함).
자리: VisemeNet Converter `Correct` 모드의 **입력 대본**(지금은 `JUN_JALI_Voice/0060_Vivian_voice/src_*/*.txt` 를 사람이 받아씀)을 자동으로 만드는 앞 단계.
A00560 JaliBatch 계획의 P4(wav 폴더에서 변환까지) 가 이 툴의 `cli.py` 를 부른다.

- **사용자 지정 조건 (4개, 모두 2026-10-23)**: ① 한국어 · 일본어 · 영어, 잡음 없는 wav 여러 개 → 그 언어 텍스트, **로컬**(딥러닝 OK)
  ② **기준 사양 PC: Ryzen 9 3900X · RTX A2000 12 GB · RAM 32 GB 이상**에서도 동작 ③ **Windows 10** 에서도 동작.
  ④ **PC 에 Python 3.14 만 설치돼 있어도 동작** → D14: `setup_stt.bat` 이 PC Python 에 의존하지 않고 `setup_env.bat` 과 같은 `:probe`/`:download_python` 으로 전용 3.11.9 를 `.python\` 에 받아(이미 있으면 공유) `.venv_stt` 를 만든다. 3.14 네이티브는 `--use-system-python` 보조 경로만(PySide6 ≥ 6.11 이 3.14 지원, PyTorch 는 2.15 부터 CUDA 12.x 휠 중단).
  → 성능 기준은 A2000(Ampere sm_86, 5070 의 1/4 ~ 1/3) 으로, FlashAttention · vLLM 같은 의존성은 안 쓴다.
- 권장 결정: `JUN_JALI/tools/STT_Converter` + `setup_stt.bat`(별도 `.venv_stt`, Python 3.11) + `Run_STT_Converter.bat`;
  1차 엔진 faster-whisper `large-v3-turbo`(= `mobiuslabsgmbh/faster-whisper-large-v3-turbo`), 2차 Qwen3-ASR-1.7B(Apache 2.0, 2026-01, ko·ja·en);
  출력 `<이름>.lab` 기본(`.txt` 는 VisemeNet 결과와 겹쳐 E34) + `.stt.json`; 기존 대본은 Skip 기본; 언어는 사람이 강제(D4); 오류 E40~/W20~.
- 정규화가 핵심: 숫자 → 수사(`1등` → 일등, num2words ko/ja/en + 한국어 단위명사 규칙표), 영문 약어 사용자 사전, 일본어 공백은 **남긴다**(제거는 VisemeNet Converter v01.04 가 함).
- 조사 결과: 한국어는 Qwen3-ASR(Kspon CER 9.6 vs Whisper-v3 13.8) · BuzzASR/korean(Whisper-v3 미세조정, CT2 변환으로 1차 엔진에 끼울 수 있음);
  일본어 kotoba-whisper 는 Reazon 도메인 밖에선 v3 가 더 정확; NVIDIA Parakeet/Canary 는 ko·ja 없음; SenseVoice 는 속도용.
- **Blackwell 함정**: CTranslate2 4.6.2 가 sm120 INT8 비활성, 4.7.0 에서 패딩 수정 — 5070 에서 `int8_float16` 실측 전엔 float16 기본. PyTorch 는 cu128 휠(sm_120 · sm_86 둘 다 포함).
- M0 실측 9항목(개발 PC 7 + 기준 PC 1 + 3.14 모사 1) 을 코드 전에 — 아직 안 함. Q1~Q8 답 없으면 권장안.

관련: [[jun-jali-repo]], [[wip-a00560-jalibatch]], [[wip-a00540-jalilipsync]]
