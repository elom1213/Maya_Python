# -*- coding: utf-8 -*-
"""
spherical eye drive 핵심 로직.

눈동자 맨 앞(Z+)에서 중심까지 Z축 일렬로 배치된 조인트들을 컨트롤러 attr 하나(driver)로
구면 dilation 시킨다. rest(driver=0)에서 모든 조인트 scale=1, translateZ=조인트 초기값을
유지하고, driver 가 밀면 위도(offset)별 sin/cos 로 변형한다.

    scaleX/Y_i   = 1       + driver * R * sin(offset_i)
    translateZ_i = Zinit_i + driver * R * cos(offset_i)
    (translateX / translateY 는 구동하지 않음)

offset_i 는 리스트 순서로 앞 0° -> 중심 90° 등분배되며 고정이므로 sin/cos 는 빌드 시
파이썬 상수로 박는다. driver / radius(R) 는 컨트롤러 attr 로 노출되어 빌드 후 라이브 조절.
"""

import math
import pymel.core as pm


def add_attr(node, pDataType, pParamName, pMin=None, pMax=None, pDefault=0.0):
    """채널박스에 보이는 keyable 어트리뷰트 추가(이미 있으면 재사용). 새 attr 반환."""
    if node.hasAttr(pParamName):
        return node.attr(pParamName)

    node.addAttr(pParamName, at=pDataType, keyable=True, dv=pDefault)
    newAttr = node.attr(pParamName)
    if pMin is not None:
        newAttr.setMin(pMin)
    if pMax is not None:
        newAttr.setMax(pMax)
    pm.setAttr(newAttr, e=True, channelBox=True)
    pm.setAttr(newAttr, e=True, keyable=True)
    return newAttr


def build_spherical_drive(prefix, controlObj, oColl, driverAttr='dilate', radius=1.0):
    """Z축 일렬 조인트들을 컨트롤러 driver 하나로 구면 dilation 구동한다.

    oColl 은 앞(Z+) -> 중심 순서의 조인트 리스트여야 한다.
    driverAttr / {prefix}_radius 를 컨트롤러에 추가하고, 공통 multiplyDivide(driver*R)
    하나 + 조인트당 multiplyDivide/addDoubleLinear 로 scale/translateZ 를 구동한다.
    """
    driver = add_attr(controlObj, 'double', driverAttr, pDefault=0.0)
    rAttr = add_attr(controlObj, 'double', '{}_radius'.format(prefix), pDefault=radius)

    span = max(len(oColl) - 1, 1)

    # driver * R 은 모든 조인트 공통 -> 한 번만 만든다.
    dR = pm.createNode('multiplyDivide', n='{}_dR_MLT'.format(prefix))
    driver.connect(dR.input1X)
    rAttr.connect(dR.input2X)                    # dR.outputX = driver * R

    for i, jnt in enumerate(oColl):
        offset = 90.0 * (i / span)               # 앞 0° -> 중심 90°
        sinC = math.sin(math.radians(offset))
        cosC = math.cos(math.radians(offset))
        zinit = jnt.translateZ.get()             # 빌드 시 조인트 로컬 translateZ

        # dR*sin -> outputX, dR*cos -> outputY (한 노드 두 채널)
        mlt = pm.createNode('multiplyDivide', n='{}_eye_{}_MLT'.format(prefix, i + 1))
        dR.outputX.connect(mlt.input1X)
        mlt.input2X.set(sinC)                    # outputX = dR * sin
        dR.outputX.connect(mlt.input1Y)
        mlt.input2Y.set(cosC)                    # outputY = dR * cos

        # scaleX/Y = 1 + dR*sin
        sAdd = pm.createNode('addDoubleLinear', n='{}_eye_{}_sADD'.format(prefix, i + 1))
        mlt.outputX.connect(sAdd.input1)
        sAdd.input2.set(1.0)
        sAdd.output.connect(jnt.scaleX)
        sAdd.output.connect(jnt.scaleY)

        # translateZ = Zinit + dR*cos
        zAdd = pm.createNode('addDoubleLinear', n='{}_eye_{}_zADD'.format(prefix, i + 1))
        mlt.outputY.connect(zAdd.input1)
        zAdd.input2.set(zinit)
        zAdd.output.connect(jnt.translateZ)
        # translateX / translateY 는 연결하지 않는다(고정).


def run_build(prefix, controller_name, joint_names, driver_attr='dilate', radius=1.0):
    """이름(문자열) 입력을 PyNode 로 변환해 build_spherical_drive 를 실행한다.

    UI 는 pymel 을 직접 다루지 않고 이 함수만 호출한다.
    joint_names 는 앞(Z+) -> 중심 순서여야 한다.
    Returns: 컨트롤러에 추가된 driver attr 의 전체 경로(예: 'ctl.dilate').
    """
    control = pm.PyNode(controller_name)
    coll = [pm.PyNode(n) for n in joint_names]
    build_spherical_drive(prefix, control, coll, driverAttr=driver_attr, radius=radius)
    return '{}.{}'.format(controller_name, driver_attr)


# scale 체인이 R^2 - dist^2 의 제곱근을 못 구하는(=R 이 rest 거리보다 작거나 pole) 임계값.
_RHO_EPS = 1e-9


def build_spherical_drive_nodes(prefix, controlObj, oColl, driverAttr='dilate', radius=1.0):
    """dilate(-90~90) 하나로 모든 조인트를 center(+) 또는 front(-) 조인트로 수렴 + 구 표면에 맞춘다.

    translate (양방향): dilate>0 이면 center(oColl[-1]) 로, dilate<0 이면 front(oColl[0]) 로 수렴.
        t_c = clamp(dilate,  0, 90)/90        # center 방향 0..1
        t_f = clamp(dilate,-90,  0)/(-90)     # front 방향 0..1
        translate_i = init_i + t_c*(center - init_i) + t_f*(front - init_i)
    두 항 중 항상 하나만 0 이 아니므로 합으로 양방향이 된다. 모든 조인트를 구동한다(각 끝 조인트는
    한 방향의 앵커이자 반대 방향의 이동 대상).

    scale: 각 조인트에 바인드된 커브(단면 링)가 반지름 R(=radius) 구의 표면에 항상 놓이도록
    scaleX/Y 를 구동한다. center 와의 현재 거리 ζ 에 대해 구 단면 반경 ρ(ζ)=√(R²−ζ²) 이므로
        scaleX/Y_i = √(R² − ζ_i(t)²) / √(R² − ζ_i,rest²)   # rest 단면 대비 비율(rest=1)
    distanceBetween(center 기준)이 방향과 무관하게 현재 거리를 읽으므로 center/front 양방향 모두
    구 표면을 따른다(front 극점에서 scale 0). sqrt 는 multiplyDivide(power)로 구현(Maya 2023 호환).

    center 까지 rest 거리가 R 이상(√음수)이거나 ρ_rest≈0(front pole 등)인 조인트는 scale 만 skip
    (translate 는 유지). oColl 은 앞(Z+) -> 중심 순서여야 한다(>= 2개).
    Returns: scale 을 구동하지 못한 조인트 이름 리스트.
    """
    if len(oColl) < 2:
        raise ValueError('Need at least 2 joints (front .. center) to converge.')

    R = float(radius)
    Rsq = R * R
    skipped = []                                   # scale 미구동 조인트

    # dilate 양방향: +면 center, -면 front 로 수렴. -90..90 클램프(끝에서 완전 수렴, 초과 overshoot 방지).
    driver = add_attr(controlObj, 'double', driverAttr, pMin=-90.0, pMax=90.0, pDefault=0.0)

    # t_c = clamp(dilate, 0, 90)/90  (center 방향 0..1)
    tcClp = pm.createNode('clamp', n='{}_tc_CLP'.format(prefix))
    driver.connect(tcClp.inputR)
    tcClp.minR.set(0.0)
    tcClp.maxR.set(90.0)
    tcMlt = pm.createNode('multiplyDivide', n='{}_tc_MLT'.format(prefix))
    tcClp.outputR.connect(tcMlt.input1X)
    tcMlt.input2X.set(1.0 / 90.0)                 # outputX = t_c

    # t_f = clamp(dilate, -90, 0) * (-1/90)  (front 방향 0..1)
    tfClp = pm.createNode('clamp', n='{}_tf_CLP'.format(prefix))
    driver.connect(tfClp.inputR)
    tfClp.minR.set(-90.0)
    tfClp.maxR.set(0.0)
    tfMlt = pm.createNode('multiplyDivide', n='{}_tf_MLT'.format(prefix))
    tfClp.outputR.connect(tfMlt.input1X)
    tfMlt.input2X.set(-1.0 / 90.0)                # outputX = t_f

    fx, fy, fz = oColl[0].translate.get()          # front(joint1) 수렴 타겟
    cx, cy, cz = oColl[-1].translate.get()         # center(jointN) 수렴 타겟

    for i, jnt in enumerate(oColl):                # 전 조인트 구동(각 끝은 반대 방향 앵커)
        ix, iy, iz = jnt.translate.get()           # 빌드 시 로컬 translate(원위치)
        cdx, cdy, cdz = cx - ix, cy - iy, cz - iz  # center 수렴 벡터(상수)
        fdx, fdy, fdz = fx - ix, fy - iy, fz - iz  # front 수렴 벡터(상수)

        # --- translate: init + t_c*(center-init) + t_f*(front-init) ---
        cMlt = pm.createNode('multiplyDivide', n='{}_conv_{}_cMLT'.format(prefix, i + 1))
        tcMlt.outputX.connect(cMlt.input1X)
        tcMlt.outputX.connect(cMlt.input1Y)
        tcMlt.outputX.connect(cMlt.input1Z)
        cMlt.input2X.set(cdx)
        cMlt.input2Y.set(cdy)
        cMlt.input2Z.set(cdz)

        fMlt = pm.createNode('multiplyDivide', n='{}_conv_{}_fMLT'.format(prefix, i + 1))
        tfMlt.outputX.connect(fMlt.input1X)
        tfMlt.outputX.connect(fMlt.input1Y)
        tfMlt.outputX.connect(fMlt.input1Z)
        fMlt.input2X.set(fdx)
        fMlt.input2Y.set(fdy)
        fMlt.input2Z.set(fdz)

        pma = pm.createNode('plusMinusAverage', n='{}_conv_{}_PMA'.format(prefix, i + 1))
        pma.operation.set(1)                       # sum
        cMlt.output.connect(pma.input3D[0])
        fMlt.output.connect(pma.input3D[1])
        pma.input3D[2].input3Dx.set(ix)
        pma.input3D[2].input3Dy.set(iy)
        pma.input3D[2].input3Dz.set(iz)
        pma.output3D.connect(jnt.translate)

        # --- scale: 커브를 구 표면에 맞춤 (scaleX/Y = ρ(현재 center거리) / ρ(rest거리)) ---
        dist_rest_sq = cdx * cdx + cdy * cdy + cdz * cdz  # center 까지 rest 거리^2 = ζ_rest^2
        rho_rest_sq = Rsq - dist_rest_sq            # rest 단면 반경^2
        if rho_rest_sq <= _RHO_EPS:
            # center 까지 거리 >= R(구 밖) 또는 pole(ρ_rest≈0, ÷0) -> scale 만 skip, translate 는 유지.
            skipped.append(jnt.name())
            continue
        rho_rest = math.sqrt(rho_rest_sq)

        # distanceBetween: center 로부터 조인트의 현재 거리 ζ(t) (translate 출력 사용).
        dst = pm.createNode('distanceBetween', n='{}_sc_{}_DST'.format(prefix, i + 1))
        pma.output3D.connect(dst.point1)
        dst.point2.set([cx, cy, cz])

        # ζ(t)^2
        dsq = pm.createNode('multiplyDivide', n='{}_sc_{}_dsq_MLT'.format(prefix, i + 1))
        dsq.operation.set(3)                        # power
        dst.distance.connect(dsq.input1X)
        dsq.input2X.set(2.0)

        # R^2 - ζ(t)^2
        sub = pm.createNode('plusMinusAverage', n='{}_sc_{}_sub_PMA'.format(prefix, i + 1))
        sub.operation.set(2)                        # subtract
        sub.input1D[0].set(Rsq)
        dsq.outputX.connect(sub.input1D[1])

        # √(R^2 - ζ(t)^2) = ρ(t)
        sqrt = pm.createNode('multiplyDivide', n='{}_sc_{}_sqrt_MLT'.format(prefix, i + 1))
        sqrt.operation.set(3)                       # power
        sub.output1D.connect(sqrt.input1X)
        sqrt.input2X.set(0.5)

        # scale = ρ(t) / ρ_rest -> scaleX, scaleY
        scl = pm.createNode('multiplyDivide', n='{}_sc_{}_scl_MLT'.format(prefix, i + 1))
        scl.operation.set(2)                        # divide
        sqrt.outputX.connect(scl.input1X)
        scl.input2X.set(rho_rest)
        scl.outputX.connect(jnt.scaleX)
        scl.outputX.connect(jnt.scaleY)

    return skipped


def run_build_nodes(prefix, controller_name, joint_names, driver_attr='dilate', radius=1.0):
    """이름(문자열) 입력을 PyNode 로 변환해 build_spherical_drive_nodes 를 실행한다.

    UI 는 pymel 을 직접 다루지 않고 이 함수만 호출한다.
    joint_names 는 앞(Z+) -> 중심 순서여야 한다(첫=front 타겟, 마지막=center 타겟).
    Returns: (driver attr 전체 경로, scale 미구동 조인트 이름 리스트).
    """
    control = pm.PyNode(controller_name)
    coll = [pm.PyNode(n) for n in joint_names]
    skipped = build_spherical_drive_nodes(
        prefix, control, coll, driverAttr=driver_attr, radius=radius)
    return '{}.{}'.format(controller_name, driver_attr), skipped
