# Wind Tool V03
#
# V03 는 A00390_WindTool_V02 를 그대로 복제해 시작한다(Sine / Chain Wave /
# Chain Wave Lite 세 탭 동일). 바뀐 것은 **위상 시계(windPhaseTime)를 만드는 방식**과
# 그 위에 얹은 **Playback 탭**뿐이다.
#
# 03.00  재생 속도 - windPhaseTime 표현식을 걷어낸다.
#        V02 는 드라이버마다 expression 을 하나씩 붙이고 그 안에서 매 프레임
#        `getAttr -time` 을 시작 프레임부터 현재 프레임까지 반복 호출했다. 이것이
#        재생 비용의 99.8% 였다(30체인 58.7ms -> 표현식만 지우면 0.10ms).
#
#        상수 속도 : 노드 3개로 대체. 상수의 적분은 곱셈 한 번이라 **결과 회전값이
#                    V02 와 완전히 같다**(실측 0.000e+00).
#        키 걸린 속도 : `keyframe -q` 로 키 데이터를 직접 읽어 구간 적분하는
#                    **씬에 하나뿐인** 통합 표현식. 키를 고치면 즉시 반영되는 라이브다.
#                    (표현식은 내용보다 개수가 비용이다 - 30개 5.84ms vs 1개 1.38ms)
#
#        실측(중앙값, Parallel EM, 체인당 조인트 5):
#            20체인  41.28ms(24fps)  ->  0.29ms(3480fps)   144x
#            50체인 104.64ms(10fps)  ->  0.61ms(1640fps)   172x
#           200체인 429.85ms( 2fps)  ->  2.13ms( 470fps)   202x
#        재생 구간에 따라 느려지던 것도 사라졌다(50체인 f280-300: 324.7ms -> 0.62ms).
#
#        Playback 탭 신규 - Rebuild Phase / Bake Phase (V02-exact) /
#                    Solo Selected · Unmute All · Mute All.
#        windMute - 체인을 rest 자세로 세우고 평가를 멈춘다(nodeState=Blocking).
#                    `windEnvelope=0` 은 값에 0을 곱할 뿐 평가를 막지 못한다(실측
#                    62.97ms -> 63.18ms). 둘은 전혀 다른 일이다.
# 03.01  로그창을 공용 위젯 `JUN_mod_log_qt_v01` 로 교체 (Expand / Clear / Copy)
# 03.03  창 높이 자동 맞춤 - 탭(중첩 포함)을 바꿀 때마다 창 높이를 지금 보이는 페이지에 맞춘다.
#        스크롤 없이 다 보이고 짧은 페이지로 가면 줄어든다. 페이지가 화면보다 길면 화면 높이에서 멈춤.
#        공용 Framework/qt/MOD_tabFit_qt_v01 (A00275 v01.38 과 같은 방식)

# 03.04  Flow 탭 - 블렌더 애드온 Waves Gen 식 바람(기울기 + 두 축 진행파 + 불규칙 · 돌풍 + 끝 따라가기)을 마야 노드망으로.
#        프리셋 Slow Flow / Breeze / Fast Flutter (옵션 2개) + flowMix (라이브 · 키 가능), 위상 엔진 flowPhaseEngine
#        (speed · Mix · timeScale 키를 Simpson 으로 정확 적분). 블렌더 기준 데이터와 12/12 일치. 계획 docs/plans/A00390_WindTool_wavesgen_port_plan.md

# 03.05  Chain Wave Lite 에 Flutter - Flow 탭(Waves Gen)의 Flutter 를 이식: 노드마다 로컬 회전에 **누적되는** 파동 항
#        (windFlutter 도/뼈, 뼈 12개 기준 + windFlutterStiffness). Lite 의 사인(같은 위상)을 재사용, 노드당 4개.
#        기본 0 = 예전 Lite 와 완전히 같은 회전. 빌드 옵션으로 끄면 어트리뷰트 · 노드도 없다.

# 03.06  Chain Wave Lite 에 Tip Follow - Flow 탭(Waves Gen)의 끝 따라가기를 이식: 체인 끝 너머 Tip 로케이터(*_liteTip, 루트의 부모 아래)를
#        노드들이 쫓는다(Tip 을 움직이면 체인이 따라온다 = 2차 애니). Flow 와 **같은 함수**(flow_manager.make_tip / tip_follow_quat /
#        follow_gain 으로 떼어 냄 - Flow 결과 불변, 회귀 56/56). Lite 회전을 쿼터니언으로 받아 slerp(q_lite, q_aim, w_k) -> rotate,
#        드라이버 windTipFollow [0, 0.99] 라이브 · 키, 실효 envelope = windEnvelope / (1 - 0.7 follow). 0 이면 예전 Lite 와 같다(위치 3e-14).
#        Lite 는 끝 노드도 돌린다 - 끝 노드 진행축 = 마지막 뼈 방향. 세 rotate 채널이 모두 연결된다. 빌드 옵션 기본 꺼짐(노드당 약 +19).
#        시험 tests/test_lite_tip_follow.py 24/24.

VERSION = "03.06"
LAST_UPDATE = "2026-11-06"
