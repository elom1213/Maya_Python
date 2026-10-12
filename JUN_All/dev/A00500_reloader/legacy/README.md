# legacy — 옛 리로더 (보존용, 동작 보장 없음)

`dev/` 에 흩어져 있던 리로더 세대들을 A00500_reloader 로 정리하면서 **그대로** 옮겨 둔 것이다.
현행 코드는 `../app/core/reloader.py` 이고, 여기 파일들은 아무도 import 하지 않는다.

| 파일 | 원래 위치 | 무엇이었나 |
|------|-----------|------------|
| `reloader_mayaScript_v02.py` | `dev/reloader_mayaScript_v02.py` | 마야 스크립트 에디터에 붙여 넣어 쓰던 네 줄 — 이제 셸프 버튼(`__dragDrop_A00500.py`)이 대신한다 |
| `reloader_v01.py` | `dev/reloader.py` | v01 리로더 — 모듈 이름을 **목록에 손으로 적어** 리로드 |
| `reload_moduleList_v01.py` | `dev/reload_moduleList.py` | v01 의 모듈 목록 (옛 A00010~A00060 단일 파일 툴 기준) |
| `reloader_mayaScript_v01.py` | `dev/reloader_mayaScript_v01.py` | v01 용 붙여넣기 스크립트 |

v01 은 `from .reload_moduleList import *` 처럼 옛 파일 이름으로 상대 import 하므로 이 폴더에서는 돌지 않는다.
