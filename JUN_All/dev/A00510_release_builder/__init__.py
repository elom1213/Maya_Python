# -*- coding: utf-8 -*-
# A00510_release_builder - dev tool package. run() 만 밖으로 낸다.
#
# launch 는 import 시점에 AppUserModelID 를 지정하므로(터미널 실행용) 패키지 import 만으로
# 그 부작용이 나지 않게 run() 안에서 늦게 import 한다. 셸프 버튼은 run() 을 부른다.


def run():
    from .launch import run as _run
    return _run()
