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

VERSION = "03.00"
LAST_UPDATE = "2026-08-24"
