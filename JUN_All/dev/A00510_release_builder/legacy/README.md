# legacy — 옛 릴리즈 빌더 (보존용, 동작 보장 없음)

| 파일 | 원래 위치 | 무엇이었나 |
|------|-----------|------------|
| `build_release.py` | `dev/build_release.py` (2026-05-10) | `TOOL_PATH` 를 손으로 고쳐 가며 툴 하나 + Framework 를 `G:/D_link_dir/...` 고정 경로로 복사하던 스크립트. 2026-09 에 Qt 창 `A00510_release_builder` 로 대체됐다. 경로가 이 PC 에 없으니 돌지 않는다 |

현행 코드는 `../app/core/release_builder.py` 이고 복사 규칙(툴 하나 + Framework, `dev` 제외)은 그대로 이어받았다.
