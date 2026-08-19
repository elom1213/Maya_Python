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

VERSION = "02.02"
LAST_UPDATE = "2026-08-19"
