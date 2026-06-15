# -*- coding: utf-8 -*-
"""
slerp ramp 핵심 로직.

A00150_remapVal/sample_01.py (Chris Lesage, 2019) 의 add_attr / build_slerp_ramp 를
동작 변경 없이 이식했다. 하단의 하드코딩 실행부(원본 라인 121-125)는 제거하고,
대신 UI 에서 이름(문자열)으로 호출할 수 있는 run_build() 래퍼를 추가했다.

원문: http://rigmarolestudio.com/maya_remapValue_slerp
"""

import pymel.core as pm


# remapValue value_Interp 매핑(1:linear 2:smooth 3:spline)에 맞춘 enum 정의.
# enum 내부 값을 그대로 value_Interp 에 연결하므로 변환 노드가 필요 없다.
INTERP_ENUM_NAME = "Linear=1:Smooth=2:Spline=3"


def add_attr(node, pDataType, pParamName, pMin=None, pMax=None, pDefault=0.0, enumName=None):
    """
    adds an attribute that shows up in the channel box
    returns the newly created attribute

    enumName 이 주어지면 enum 어트리뷰트로 만든다(min/max 는 의미가 없어 건너뛴다).
    """
    if node.hasAttr(pParamName):
        return node.attr(pParamName)
    else:
        if enumName is not None:
            node.addAttr(pParamName, at=pDataType, keyable=True, dv=pDefault, enumName=enumName)
        else:
            node.addAttr(pParamName, at=pDataType, keyable=True, dv=pDefault)
        newAttr = node.attr(pParamName)
        if enumName is None:
            if pMin != None:
                newAttr.setMin(pMin)
            if pMax != None:
                newAttr.setMax(pMax)
        pm.setAttr(newAttr, e=True, channelBox=True)
        pm.setAttr(newAttr, e=True, keyable=True)
        return newAttr


def build_slerp_ramp(prefix, controlObj, oColl, twistAttrs=['rotateX'],
                     outputMin=0.0, outputMax=1.0, interpolation=1):
    """
    Take a collection of objects and interpolate them along a curve.
    It uses a master remapValue that drives multiple remapValues
    to simulate the effect of a multi-out curve node.
    References to "twist", because it was originally written for twisting ribbon IK
    But it can interpolate any custom attributes you wish

    master 의 outputMin/outputMax 도 컨트롤러 제어 attr(`{prefix}_output_min` 등)로
    노출되어 master 를 driven 하고, master 가 다시 모든 자식 remapValue 의
    outputMin/outputMax 를 driven 한다(진폭을 한 곳에서 조절).
    """
    # The master twist profile curve.
    masterName = '{}_master_ribbon_lerp_MAP'.format(prefix)
    masterRemap = pm.createNode('remapValue', n=masterName)
    # 마스터 input 범위는 항상 0 .. (오브젝트 수 - 1). max(...,1) 은 N<=1 의 0 division 방지.
    masterRemap.inputMax.set(max(len(oColl) - 1, 1))
    # set to linear interpolation.
    masterRemap.value[0].value_Interp.set(1) # 0:none 1:linear 2:smooth 3:spline

    pStartName = '{}_start'.format(prefix)
    pEndName = '{}_end'.format(prefix)
    twistStartName = '{}_start_position'.format(prefix)
    twistEndName = '{}_end_position'.format(prefix)
    twistTypeName = '{}_interpolation'.format(prefix)

    pStart = add_attr(controlObj, 'double', pStartName, pDefault=0.0)
    pEnd = add_attr(controlObj, 'double', pEndName, pDefault=0.0)
    twistStart = add_attr(controlObj, 'double', twistStartName, pMin=0.0, pMax=1.0, pDefault=0.0)
    twistEnd = add_attr(controlObj, 'double', twistEndName, pMin=0.0, pMax=1.0, pDefault=1.0)
    # twistType interpolation enum(Linear=1 / Smooth=2 / Spline=3). 기본 Linear.
    # enum 값 1/2/3 이 그대로 value_Interp 로 연결된다(아래 connect).
    twistType = add_attr(controlObj, 'enum', twistTypeName,
                         pDefault=interpolation, enumName=INTERP_ENUM_NAME)
    twistStart.connect(masterRemap.value[0].value_Position)
    twistEnd.connect(masterRemap.value[1].value_Position)
    twistType.connect(masterRemap.value[0].value_Interp)
    twistType.connect(masterRemap.value[1].value_Interp)

    # output range 제어 attr 2개 — 컨트롤러에 노출하고 master 의 outputMin/Max 를 driven.
    outMinAttr = add_attr(controlObj, 'double', '{}_output_min'.format(prefix), pDefault=outputMin)
    outMaxAttr = add_attr(controlObj, 'double', '{}_output_max'.format(prefix), pDefault=outputMax)
    outMinAttr.connect(masterRemap.outputMin)
    outMaxAttr.connect(masterRemap.outputMax)

    for i, twistNode in enumerate(oColl):
        # add a start and end twist parameter to the follicles.
        twistMLT = pm.createNode('multiplyDivide', n='{}_lerp_{}_MLT'.format(prefix, i+1))
        twistAdd = pm.createNode('plusMinusAverage', n='{}_lerp_{}_ADD'.format(prefix, i+1))
        pStart.connect(twistMLT.input1X)
        pEnd.connect(twistMLT.input1Y)

        twistProfileName = '{}_lerp_profile_{}_MAP'.format(prefix, i+1)
        twistProfile = pm.createNode('remapValue', n=twistProfileName)
        # add a reverse node for the end twist, to add up to 1.0 of the first curve.
        # This simple technique would fail if you wanted to have different
        # interpolations for Start and End twist. However, I don't. If I run both Start
        # and End the same amount, then the whole interpolation should add up to 1.0
        reverseProfileName = '{}_lerp_{}_REVERSE'.format(prefix, i+1)
        reverseProfile = pm.createNode('reverse', n=reverseProfileName)

        # connect masterRemap remapValue curve to the other remapValue nodes.
        # Then you can drive them all with one, faking a multi-out curve.
        twistProfile.inputValue.set(i)

        masterRemap.inputMax.connect(twistProfile.inputMax)
        masterRemap.inputMin.connect(twistProfile.inputMin)

        masterRemap.value[0].value_Position.connect(twistProfile.value[0].value_Position)
        masterRemap.value[0].value_FloatValue.connect(twistProfile.value[0].value_FloatValue)
        masterRemap.value[0].value_Interp.connect(twistProfile.value[0].value_Interp)

        masterRemap.value[1].value_Position.connect(twistProfile.value[1].value_Position)
        masterRemap.value[1].value_FloatValue.connect(twistProfile.value[1].value_FloatValue)
        masterRemap.value[1].value_Interp.connect(twistProfile.value[1].value_Interp)

        # master 의 outputMin/Max 로 각 자식의 진폭을 driven (한 곳에서 일괄 조절).
        masterRemap.outputMin.connect(twistProfile.outputMin)
        masterRemap.outputMax.connect(twistProfile.outputMax)

        # connect the profile remapValue to the multiplyDivide nodes
        twistProfile.outValue.connect(twistMLT.input2Y)
        twistProfile.outValue.connect(reverseProfile.input.inputX)
        #TODO: If you wanted to get rid of the Reverse nodes,
        # you could hook up the remapValues in reverse.
        # So the last remapValue would be the first one for the input2X
        # However, that only works if the curves are horizontally symmetrical:
        # Ease-in-ease-out or linear. Ease-in-linear-out wouldn't work.
        reverseProfile.output.outputX.connect(twistMLT.input2X)

        twistMLT.outputX.connect(twistAdd.input2D[0].input2Dx)
        twistMLT.outputY.connect(twistAdd.input2D[1].input2Dx)
        for twistAttr in twistAttrs:
            twistOffset = pm.createNode('plusMinusAverage', n='{}_lerp_{}_OFFSET_{}'.format(prefix, i+1, twistAttr))
            twistAdd.output2D.output2Dx.connect(twistOffset.input2D[0].input2Dx)

            attrInit = pm.getAttr("{}.{}".format(twistNode,twistAttr))
            twistOffset.input2D[1].input2Dx.set(attrInit)
            twistOffset.output2D.output2Dx.connect(twistNode.attr(twistAttr))


def run_build(prefix, controller_name, joint_names, twist_attrs,
              output_min=0.0, output_max=1.0, interpolation=1):
    """이름(문자열)으로 받은 입력을 PyNode 로 변환해 build_slerp_ramp 를 실행한다.

    UI 는 pymel 을 직접 다루지 않고 이 함수만 호출한다.
    output_min/output_max 는 컨트롤러 output 제어 attr 의 기본값이 된다.
    interpolation 은 interpolation enum 의 기본값(1:Linear 2:Smooth 3:Spline).
    Returns: 생성된 master remapValue 노드명.
    """
    control = pm.PyNode(controller_name)
    coll = [pm.PyNode(n) for n in joint_names]
    build_slerp_ramp(prefix, control, coll, twistAttrs=list(twist_attrs),
                     outputMin=output_min, outputMax=output_max,
                     interpolation=interpolation)
    return '{}_master_ribbon_lerp_MAP'.format(prefix)


def build_sine_wave(prefix, controlObj, oColl, driverAttr, objAttrs=['translateY'],
                    inputMin=0.0, inputMax=0.0, outputMin=0.0, outputMax=1.0):
    """위상이 어긋난 사인 웨이브를 오브젝트 컬렉션에 전파한다.

    build_slerp_ramp 와 별개인 두 번째 빌드 모드. 오브젝트마다
        plusMinusAverage(위상 offset) -> animCurveUU(0..N-1 선형, Pre/Post Infinity Constant)
        -> remapValue(봉우리 커브) -> object.attr
    체인을 만든다. 컨트롤러에 공통 driver attr 하나(driverAttr)를 추가해 모든
    plusMinusAverage.input1D[0] 에 연결, 전체 위상을 한 값으로 민다.
    각 plusMinusAverage 의 input1D[1] 은 인덱스 i(0,1,2,...) 만큼 위상이 어긋난다.

    remapValue 의 4개 range(input min/max, output min/max)와 봉우리 커브는 master
    remapValue(`{prefix}_wave_master_MAP`) 가 들고 모든 자식 waveMap 을 driven 한다.
    컨트롤러 제어 어트리뷰트(`{prefix}_input_min` 등)는 master 를 driven 하므로
    컨트롤러 -> master -> 자식 체인으로 빌드 후 라이브 조절이 가능하다(ref_01 구조).
    inputMin/outputMin/outputMax 는 그 제어 어트리뷰트의 기본값이다.
    inputMax 는 항상 오브젝트 개수-1(span)로 고정한다(인자 inputMax 는 무시).
    이렇게 하면 master 의 input 범위가 0 .. (오브젝트 수 - 1) 로 animCurve 출력과 정렬된다.
    """
    n = len(oColl)
    # span = 입력/커브 범위. N==1 일 때 0 division / 동일 키 생성을 막는다.
    span = max(n - 1, 1)
    # inputMax 는 항상 오브젝트 수-1 로 고정(UI In Max 입력은 무시). master input 범위 = 0..span.
    in_max_default = span

    # 컨트롤러에 공통 driver attr(위상 시작값) 추가. 이미 있으면 재사용.
    driver = add_attr(controlObj, 'double', driverAttr, pDefault=0.0)

    # remapValue range 제어 attr 4개 — 컨트롤러에 노출하고 master remapValue 에 connect.
    inMinAttr = add_attr(controlObj, 'double', '{}_input_min'.format(prefix), pDefault=inputMin)
    inMaxAttr = add_attr(controlObj, 'double', '{}_input_max'.format(prefix), pDefault=in_max_default)
    outMinAttr = add_attr(controlObj, 'double', '{}_output_min'.format(prefix), pDefault=outputMin)
    outMaxAttr = add_attr(controlObj, 'double', '{}_output_max'.format(prefix), pDefault=outputMax)

    # master remapValue: 컨트롤러 range attr 와 봉우리 커브를 들고, 모든 자식
    # waveMap 의 range/커브를 driven(ref_01 의 fake multi-out curve 구조).
    masterName = '{}_wave_master_MAP'.format(prefix)
    masterMap = pm.createNode('remapValue', n=masterName)
    inMinAttr.connect(masterMap.inputMin)
    inMaxAttr.connect(masterMap.inputMax)
    outMinAttr.connect(masterMap.outputMin)
    outMaxAttr.connect(masterMap.outputMax)
    # 봉우리(사인 반주기) 커브 spline 을 master 한 곳에만 set.
    peak = [(0.0, 0.0), (0.5, 1.0), (1.0, 0.0)]
    for idx, (pos, val) in enumerate(peak):
        masterMap.value[idx].value_Position.set(pos)
        masterMap.value[idx].value_FloatValue.set(val)
        masterMap.value[idx].value_Interp.set(3)  # 0:none 1:linear 2:smooth 3:spline

    for i, obj in enumerate(oColl):
        # (1) plusMinusAverage : driver + i (오브젝트별 위상 offset)
        waveAdd = pm.createNode('plusMinusAverage', n='{}_wave_{}_ADD'.format(prefix, i + 1))
        waveAdd.operation.set(1)  # sum
        driver.connect(waveAdd.input1D[0])
        waveAdd.input1D[1].set(i)

        # (2) animCurveUU : (0,0)..(span,span) 선형, Pre/Post Infinity = Constant
        waveCurve = pm.createNode('animCurveUU', n='{}_wave_curve_{}'.format(prefix, i + 1))
        pm.setKeyframe(waveCurve, float=0.0, value=0.0)
        pm.setKeyframe(waveCurve, float=float(span), value=float(span))
        pm.keyTangent(waveCurve, edit=True, itt='linear', ott='linear')
        pm.setInfinity(waveCurve, pri='constant', poi='constant')
        waveAdd.output1D.connect(waveCurve.input)

        # (3) remapValue : input 0..span, 봉우리 커브는 master 가 driven
        waveMap = pm.createNode('remapValue', n='{}_wave_{}_MAP'.format(prefix, i + 1))
        # 4개 range 를 master 경유로 connect (master <- 컨트롤러 attr <- 사용자).
        masterMap.inputMin.connect(waveMap.inputMin)
        masterMap.inputMax.connect(waveMap.inputMax)
        masterMap.outputMin.connect(waveMap.outputMin)
        masterMap.outputMax.connect(waveMap.outputMax)
        # 봉우리 커브(value[0~2])도 master 에서 connect — 커브 모양을 한 곳에서 편집.
        for idx in range(len(peak)):
            masterMap.value[idx].value_Position.connect(waveMap.value[idx].value_Position)
            masterMap.value[idx].value_FloatValue.connect(waveMap.value[idx].value_FloatValue)
            masterMap.value[idx].value_Interp.connect(waveMap.value[idx].value_Interp)
        # inputValue 는 각 노드 고유(animCurve 출력)이므로 master 와 연결하지 않는다.
        waveCurve.output.connect(waveMap.inputValue)

        # remapValue 출력을 선택된 모든 오브젝트 어트리뷰트에 연결.
        for attr in objAttrs:
            waveMap.outValue.connect(obj.attr(attr))


def run_build_wave(prefix, controller_name, joint_names, driver_attr, obj_attrs,
                   input_min=0.0, input_max=0.0, output_min=0.0, output_max=1.0):
    """이름(문자열) 입력을 PyNode 로 변환해 build_sine_wave 를 실행한다.

    UI 는 pymel 을 직접 다루지 않고 이 함수만 호출한다.
    Returns: 컨트롤러에 추가된 driver attr 의 전체 경로(예: 'ctl.wave').
    """
    control = pm.PyNode(controller_name)
    coll = [pm.PyNode(n) for n in joint_names]
    build_sine_wave(prefix, control, coll, driver_attr, objAttrs=list(obj_attrs),
                    inputMin=input_min, inputMax=input_max,
                    outputMin=output_min, outputMax=output_max)
    return '{}.{}'.format(controller_name, driver_attr)
