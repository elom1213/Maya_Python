# Wind Tool V02
#
# V02 는 A00390_WindTool 을 그대로 복제해 시작한다(Sine / Chain Wave 탭 동일).
# 02.00  Chain Wave Lite - 커브·ikHandle·프록시 없이 각도만으로 파형을 만든다.
#                          진폭의 뜻이 "CV 를 미는 거리" 에서 **뼈가 흔들리는 각도(도)** 로 바뀐다.
# 02.01  windEnvelope [0,1] - Node 출력이 만드는 드라이버 전부에 영향력 어트리뷰트.
#                          0 = 노드가 아무 영향도 주지 않음, 0.5 = 절반, 1 = 완전 적용.
# 02.02  Chain Wave Lite 에 Rotate Axis (object) - 각 노드의 오브젝트 축 하나로만 회전.
#                          켜면 Sway Axis(월드)는 UI 에서 비활성 + 계산에서도 제외.
#        Place driver at chain root - Node 출력 드라이버 로케이터를 체인 최상단 위치에
#                          만든다(기본 ON). Sine / Chain Wave / Chain Wave Lite 세 탭 전부.
# 02.03  Chain Wave Lite 디버그 커브 - 체인이 어떻게 흔들리는지 보여 주는 커브(기본 ON).
#                          Chain Wave 탭의 커브와 같은 방식이지만 체인이 커브를 구동한다.
# 02.04  아웃라이너 그룹 분리 - Chain Wave Lite 가 드라이버 로케이터는 `_liteDriverGrp`,
#                          디버그 커브는 `_liteCurveGrp` 로 나눠 담는다(예전엔 번갈아 쌓였다).
#        드라이버가 루트를 따라간다 - Node 출력에서 드라이버 로케이터가 루트 본/컨트롤러의
#                          **월드 위치**를 계속 따라간다(위치만, 회전 제외). constraint 없이
#                          multMatrix + decomposeMatrix 직결. 세 탭 전부.

VERSION = "02.04"
LAST_UPDATE = "2026-08-21"
