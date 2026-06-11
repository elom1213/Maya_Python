# -*- coding: utf-8 -*-
"""
slerp ramp 핵심 로직.

A00150_remapVal/sample_01.py (Chris Lesage, 2019) 의 add_attr / build_slerp_ramp 를
동작 변경 없이 이식했다. 하단의 하드코딩 실행부(원본 라인 121-125)는 제거하고,
대신 UI 에서 이름(문자열)으로 호출할 수 있는 run_build() 래퍼를 추가했다.

원문: http://rigmarolestudio.com/maya_remapValue_slerp
"""

import pymel.core as pm


def add_attr(node, pDataType, pParamName, pMin=None, pMax=None, pDefault=0.0):
    """
    adds an attribute that shows up in the channel box
    returns the newly created attribute
    """
    if node.hasAttr(pParamName):
        return node.attr(pParamName)
    else:
        node.addAttr(pParamName, at=pDataType, keyable=True, dv=pDefault)
        newAttr = node.attr(pParamName)
        if pMin != None:
            newAttr.setMin(pMin)
        if pMax != None:
            newAttr.setMax(pMax)
        pm.setAttr(newAttr, e=True, channelBox=True)
        pm.setAttr(newAttr, e=True, keyable=True)
        return newAttr


def build_slerp_ramp(prefix, controlObj, oColl, twistAttrs=['rotateX']):
    """
    Take a collection of objects and interpolate them along a curve.
    It uses a master remapValue that drives multiple remapValues
    to simulate the effect of a multi-out curve node.
    References to "twist", because it was originally written for twisting ribbon IK
    But it can interpolate any custom attributes you wish
    """
    # The master twist profile curve.
    masterName = '{}_master_ribbon_lerp_MAP'.format(prefix)
    masterRemap = pm.createNode('remapValue', n=masterName)
    # set the range to the count of twist objects.
    masterRemap.inputMax.set(len(oColl))
    # set to smooth interpolation.
    masterRemap.value[0].value_Interp.set(2)

    pStartName = '{}_start'.format(prefix)
    pEndName = '{}_end'.format(prefix)
    twistStartName = '{}_start_position'.format(prefix)
    twistEndName = '{}_end_position'.format(prefix)
    twistTypeName = '{}_interpolation'.format(prefix)

    pStart = add_attr(controlObj, 'double', pStartName, pDefault=0.0)
    pEnd = add_attr(controlObj, 'double', pEndName, pDefault=0.0)
    twistStart = add_attr(controlObj, 'double', twistStartName, pMin=0.0, pMax=1.0, pDefault=0.0)
    twistEnd = add_attr(controlObj, 'double', twistEndName, pMin=0.0, pMax=1.0, pDefault=1.0)
    # twistType interpolation 0: none 1: linear 2: smooth 3: spline
    twistType = add_attr(controlObj, 'long', twistTypeName, pMin=0, pMax=2, pDefault=2)
    twistStart.connect(masterRemap.value[0].value_Position)
    twistEnd.connect(masterRemap.value[1].value_Position)
    twistType.connect(masterRemap.value[0].value_Interp)

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
        twistProfile.inputMax.set(len(oColl))
        twistProfile.inputValue.set(i)
        masterRemap.value[0].value_Position.connect(twistProfile.value[0].value_Position)
        masterRemap.value[0].value_FloatValue.connect(twistProfile.value[0].value_FloatValue)
        masterRemap.value[0].value_Interp.connect(twistProfile.value[0].value_Interp)

        masterRemap.value[1].value_Position.connect(twistProfile.value[1].value_Position)
        masterRemap.value[1].value_FloatValue.connect(twistProfile.value[1].value_FloatValue)
        masterRemap.value[1].value_Interp.connect(twistProfile.value[1].value_Interp)

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
            twistAdd.output2D.output2Dx.connect(twistNode.attr(twistAttr))


def run_build(prefix, controller_name, joint_names, twist_attrs):
    """이름(문자열)으로 받은 입력을 PyNode 로 변환해 build_slerp_ramp 를 실행한다.

    UI 는 pymel 을 직접 다루지 않고 이 함수만 호출한다.
    Returns: 생성된 master remapValue 노드명.
    """
    control = pm.PyNode(controller_name)
    coll = [pm.PyNode(n) for n in joint_names]
    build_slerp_ramp(prefix, control, coll, twistAttrs=list(twist_attrs))
    return '{}_master_ribbon_lerp_MAP'.format(prefix)
