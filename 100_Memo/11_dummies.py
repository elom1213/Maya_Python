
(((vector((floor((PlayerX / PixelWorldSize))), (floor((PlayerY / PixelWorldSize))), 0)) + 0.500000) * PixelWorldSize)
(vector(floor(playerX/pixelWorldSize), floor(playerY/pixelWorldSize) ,0) + 0.5 ) * pixelWorldSize

def create_joint_chain(objs, suffix="_jnt"):
    """
    Create a joint chain for the given objects.
    Each object's position will be used to place a joint.
    
    Parameters:
        objs (list): List of object names (transforms, locators, etc.)
        suffix (str): Suffix to add to each joint name
    
    Returns:
        list: Created joints in hierarchical order
    """
    joints = []
    cmds.select(clear=True)  # start clean
    
    for obj in objs:
        if not cmds.objExists(obj):
            cmds.warning(f"Object '{obj}' does not exist, skipping.")
            continue

        # Get world position of object
        pos = cmds.xform(obj, q=True, ws=True, t=True)
        
        # Create a joint at that position
        jnt = cmds.joint(name=f"{obj}{suffix}", position=pos)
        joints.append(jnt)
    
    # Orient the joint chain nicely
    if joints:
        cmds.joint(joints[0], edit=True, orientJoint="xyz", secondaryAxisOrient="yup", children=True, zeroScaleOrient=True)
    
    return joints

def vector_element_wise_multiply(v1, v2):
    return  [a * b for a, b in zip(v1, v2)]

    

    

Begin Object Class=/Script/KawaiiPhysicsEd.AnimGraphNode_KawaiiPhysics Name="AnimGraphNode_KawaiiPhysics_0" ExportPath="/Script/KawaiiPhysicsEd.AnimGraphNode_KawaiiPhysics'/Game/Avatar/Nif/Nif_HI_School/bp_02/Nif_HI_School_Skeleton_AnimBlueprint.Nif_HI_School_Skeleton_AnimBlueprint:KWI_cloth.AnimGraphNode_KawaiiPhysics_0'"
   Begin Object Class=/Script/AnimGraph.AnimGraphNodeBinding_Base Name="AnimGraphNodeBinding_Base_0" ExportPath="/Script/AnimGraph.AnimGraphNodeBinding_Base'/Game/Avatar/Nif/Nif_HI_School/bp_02/Nif_HI_School_Skeleton_AnimBlueprint.Nif_HI_School_Skeleton_AnimBlueprint:KWI_cloth.AnimGraphNode_KawaiiPhysics_0.AnimGraphNodeBinding_Base_0'"
   End Object
   Begin Object Name="AnimGraphNodeBinding_Base_0" ExportPath="/Script/AnimGraph.AnimGraphNodeBinding_Base'/Game/Avatar/Nif/Nif_HI_School/bp_02/Nif_HI_School_Skeleton_AnimBlueprint.Nif_HI_School_Skeleton_AnimBlueprint:KWI_cloth.AnimGraphNode_KawaiiPhysics_0.AnimGraphNodeBinding_Base_0'"
   End Object
   Node=(RootBone=(BoneName="Skirt_F_001"),AdditionalRootBones=((RootBone=(BoneName="Skirt_R_021")),(RootBone=(BoneName="Skirt_R_020")),(RootBone=(BoneName="Skirt_R_019")),(RootBone=(BoneName="Skirt_R_018")),(RootBone=(BoneName="Skirt_R_017")),(RootBone=(BoneName="Skirt_R_016")),(RootBone=(BoneName="Skirt_R_015")),(RootBone=(BoneName="Skirt_R_014")),(RootBone=(BoneName="Skirt_R_013")),(RootBone=(BoneName="Skirt_R_012")),(RootBone=(BoneName="Skirt_R_011")),(RootBone=(BoneName="Skirt_B_001")),(RootBone=(BoneName="Skirt_L_021")),(RootBone=(BoneName="Skirt_L_020")),(RootBone=(BoneName="Skirt_L_019")),(RootBone=(BoneName="Skirt_L_018")),(RootBone=(BoneName="Skirt_L_017")),(RootBone=(BoneName="Skirt_L_016")),(RootBone=(BoneName="Skirt_L_015")),(RootBone=(BoneName="Skirt_L_014")),(RootBone=(BoneName="Skirt_L_013")),(RootBone=(BoneName="Skirt_L_012")),(RootBone=(BoneName="Skirt_L_011"))),BoneForwardAxis=Y_Negative,DampingCurveData=(EditorCurveData=(Keys=((Value=0.600000),(Time=1.000000,Value=1.000000)))),StiffnessCurveData=(EditorCurveData=(Keys=((Value=1.000000),(Time=1.000000,Value=0.600000)))),CapsuleLimitsData=((Radius=6.316817,Length=10.846260,DrivingBone=(BoneName="UpperLeg_R"),OffsetLocation=(X=-0.011600,Y=-0.086223,Z=-0.000000),OffsetRotation=(Pitch=0.000000,Yaw=0.000000,Roll=90.000000),Location=(X=-6.679946,Y=1.965977,Z=62.656793),Rotation=(X=-0.005154,Y=-0.000000,Z=-0.000000,W=0.999987),SourceType=DataAsset,Guid=7A1B904142D76EA2EFDA5F9EA994E779),(Radius=6.316817,Length=10.846260,DrivingBone=(BoneName="UpperLeg_L"),OffsetLocation=(X=0.011600,Y=-0.086223,Z=-0.000000),OffsetRotation=(Pitch=0.000000,Yaw=0.000000,Roll=90.000000),Location=(X=6.679946,Y=1.965977,Z=62.656793),Rotation=(X=-0.005154,Y=0.000000,Z=0.000000,W=0.999987),SourceType=DataAsset,Guid=2DD7BE2B4ED661AC1FA63FA002B7918F),(Radius=6.316817,Length=10.846260,DrivingBone=(BoneName="UpperLeg_R"),OffsetLocation=(X=-0.008536,Y=-0.029341,Z=0.011029),OffsetRotation=(Pitch=0.000000,Yaw=-11.707306,Roll=75.000000),Location=(X=-6.373546,Y=0.921768,Z=68.356059),Rotation=(X=0.124761,Y=0.101045,Z=-0.013833,W=0.986931),SourceType=DataAsset,Guid=F1B5111C448CE23378D9CDB025691489),(Radius=6.316817,Length=10.846260,DrivingBone=(BoneName="UpperLeg_L"),OffsetLocation=(X=0.008536,Y=-0.029341,Z=0.011029),OffsetRotation=(Pitch=0.000000,Yaw=11.707306,Roll=75.000000),Location=(X=6.373546,Y=0.921768,Z=68.356059),Rotation=(X=0.124761,Y=-0.101045,Z=0.013833,W=0.986931),SourceType=DataAsset,Guid=AC1289E242981EC4C62ED39132D07183),(Radius=6.263916,Length=9.983810,DrivingBone=(BoneName="UpperLeg_R"),OffsetLocation=(X=-0.008712,Y=-0.022357,Z=-0.000000),OffsetRotation=(Pitch=0.000000,Yaw=-16.000000,Roll=90.000000),Location=(X=-6.391146,Y=2.031808,Z=69.043054),Rotation=(X=-0.005104,Y=0.139171,Z=-0.000717,W=0.990255),SourceType=DataAsset,Guid=8F4770AC44931DF24504F3A13DCF742B),(Radius=6.263916,Length=9.983810,DrivingBone=(BoneName="UpperLeg_L"),OffsetLocation=(X=0.008712,Y=-0.022357,Z=-0.000000),OffsetRotation=(Pitch=0.000000,Yaw=16.000000,Roll=90.000000),Location=(X=6.391146,Y=2.031808,Z=69.043054),Rotation=(X=-0.005104,Y=-0.139171,Z=0.000717,W=0.990255),SourceType=DataAsset,Guid=22F215EE4D2AF3EE9030F8979C359558)))
   bEnableDebugDrawBone=False
   bEnableDebugBoneLengthRate=False
   bEnableDebugDrawBoneConstraint=False
   ShowPinForProperties(0)=(PropertyName="ComponentPose",PropertyFriendlyName="Component Pose",PropertyTooltip=NSLOCTEXT("UObjectToolTips", "AnimNode_SkeletalControlBase:ComponentPose", "Input link"),CategoryName="Links",bShowPin=True)
   ShowPinForProperties(1)=(PropertyName="LODThreshold",PropertyFriendlyName="LOD Threshold",PropertyTooltip=NSLOCTEXT("UObjectToolTips", "AnimNode_SkeletalControlBase:LODThreshold", "* Max LOD that this node is allowed to run\n* For example if you have LODThreshold to be 2, it will run until LOD 2 (based on 0 index)\n* when the component LOD becomes 3, it will stop update/evaluate\n* currently transition would be issue and that has to be re-visited"),CategoryName="Performance",bCanToggleVisibility=True)
   ShowPinForProperties(2)=(PropertyName="AlphaInputType",PropertyFriendlyName="Alpha Input Type",CategoryName="Alpha")
   ShowPinForProperties(3)=(PropertyName="bAlphaBoolEnabled",PropertyFriendlyName="bEnabled",CategoryName="Alpha",bShowPin=True,bCanToggleVisibility=True)
   ShowPinForProperties(4)=(PropertyName="Alpha",PropertyFriendlyName="Alpha",PropertyTooltip=NSLOCTEXT("UObjectToolTips", "AnimNode_SkeletalControlBase:Alpha", "Current strength of the skeletal control"),CategoryName="Alpha",bShowPin=True,bCanToggleVisibility=True)
   ShowPinForProperties(5)=(PropertyName="AlphaScaleBias",PropertyFriendlyName="Alpha Scale Bias",CategoryName="Alpha")
   ShowPinForProperties(6)=(PropertyName="AlphaBoolBlend",PropertyFriendlyName="Blend Settings",CategoryName="Alpha")
   ShowPinForProperties(7)=(PropertyName="AlphaCurveName",PropertyFriendlyName="Alpha Curve Name",CategoryName="Alpha",bShowPin=True,bCanToggleVisibility=True)
   ShowPinForProperties(8)=(PropertyName="AlphaScaleBiasClamp",PropertyFriendlyName="Alpha Scale Bias Clamp",CategoryName="Alpha")
   ShowPinForProperties(9)=(PropertyName="RootBone",PropertyFriendlyName="Root Bone",PropertyTooltip="指定ボーンとそれ以下のボーンを制御対象に\nControl the specified bone and the bones below it",CategoryName="Bones")
   ShowPinForProperties(10)=(PropertyName="ExcludeBones",PropertyFriendlyName="Exclude Bones",PropertyTooltip="指定したボーンとそれ以下のボーンを制御対象から除去\nDo NOT control the specified bone and the bones below it",CategoryName="Bones")
   ShowPinForProperties(11)=(PropertyName="AdditionalRootBones",PropertyFriendlyName="Additional Root Bones",PropertyTooltip="指定ボーンとそれ以下のボーンを制御対象に(追加用)\nControl the specified bone and the bones below it (For Addition)",CategoryName="Bones")
   ShowPinForProperties(12)=(PropertyName="DummyBoneLength",PropertyFriendlyName="Dummy Bone Length",PropertyTooltip="0より大きい場合は、制御ボーンの末端にダミーボーンを追加。ダミーボーンを追加することで、末端のボーンの物理制御を改善\nAdd a dummy bone to the end bone if it\'s above 0. It affects end bone rotation.",CategoryName="Bones",bCanToggleVisibility=True)
   ShowPinForProperties(13)=(PropertyName="BoneForwardAxis",PropertyFriendlyName="Bone Forward Axis",PropertyTooltip="ボーンの前方。物理制御やダミーボーンの配置位置に影響\nBone forward direction. Affects the placement of physical controls and dummy bones",CategoryName="Bones",bCanToggleVisibility=True)
   ShowPinForProperties(14)=(PropertyName="PhysicsSettings",PropertyFriendlyName="Physics Settings",PropertyTooltip="物理制御の基本設定\nBasic physics settings",CategoryName="Physics Settings",bShowPin=True,bCanToggleVisibility=True)
   ShowPinForProperties(15)=(PropertyName="TargetFramerate",PropertyFriendlyName="Target Framerate",PropertyTooltip="ターゲットとなるフレームレート\nTarget Frame Rate",CategoryName="Physics Settings")
   ShowPinForProperties(16)=(PropertyName="OverrideTargetFramerate",PropertyFriendlyName="Override Target Framerate",CategoryName="Physics Settings")
   ShowPinForProperties(17)=(PropertyName="WarmUpFrames",PropertyFriendlyName="Warm Up Frames",PropertyTooltip="物理の空回し回数。物理処理が落ち着いてから開始・表示したい際に使用\nNumber of times physics has been idle. Used when you want to start/display after physics processing has settled down",CategoryName="Physics Settings",bCanToggleVisibility=True,bHasOverridePin=True)
   ShowPinForProperties(18)=(PropertyName="bUseWarmUpWhenResetDynamics",PropertyFriendlyName="Use Warm Up when Reset Dynamics",PropertyTooltip="ResetDynamics時に物理の空回しを行うフラグ\nFlags to use warmup physics when ResetDynamics",CategoryName="Physics Settings",bCanToggleVisibility=True,bHasOverridePin=True)
   ShowPinForProperties(19)=(PropertyName="bNeedWarmUp",PropertyFriendlyName="Need Warm Up",CategoryName="Physics Settings",bCanToggleVisibility=True)
   ShowPinForProperties(20)=(PropertyName="TeleportDistanceThreshold",PropertyFriendlyName="Teleport Distance Threshold",PropertyTooltip="1フレームにおけるSkeletalMeshComponentの移動量が設定値を超えた場合、その移動量を物理制御に反映しない\nIf the amount of movement of a SkeletalMeshComponent in one frame exceeds the set value, that amount of movement will not be reflected in the physics control.",CategoryName="Physics Settings",bCanToggleVisibility=True)
   ShowPinForProperties(21)=(PropertyName="TeleportRotationThreshold",PropertyFriendlyName="Teleport Rotation Threshold",PropertyTooltip="1フレームにおけるSkeletalMeshComponentの回転量が設定値を超えた場合、その回転量を物理制御に反映しない\nIf the rotation amount of SkeletalMeshComponent in one frame exceeds the set value, the rotation amount will not be reflected in the physics control.",CategoryName="Physics Settings",bCanToggleVisibility=True)
   ShowPinForProperties(22)=(PropertyName="PlanarConstraint",PropertyFriendlyName="Planar Constraint",PropertyTooltip="指定した軸に応じた平面上に各ボーンを固定\nFix the bone on the specified plane",CategoryName="Physics Settings",bCanToggleVisibility=True)
   ShowPinForProperties(23)=(PropertyName="bUpdatePhysicsSettingsInGame",PropertyFriendlyName="Update Physics Settings in Game",PropertyTooltip="各ボーンの物理パラメータを毎フレーム更新するフラグ。\n無効にするとパフォーマンスが僅かに改善するが、実行中に物理パラメータを変更することが不可能に\nFlag to update the physics parameters of each bone every frame.\nDisabling this will slightly improve performance, but it will make it impossible to change physics parameters during execution.",CategoryName="Physics Settings",bCanToggleVisibility=True,bIsMarkedForAdvancedDisplay=True)
   ShowPinForProperties(24)=(PropertyName="ResetBoneTransformWhenBoneNotFound",PropertyFriendlyName="Reset Bone Transform when Bone Not Found",PropertyTooltip="制御対象のボーンが見つからない場合にTransformをリセットするフラグ。基本的には無効を推奨\nFlag to reset Transform when the controlled bone is not found. It is generally recommended to disable this.",CategoryName="Physics Settings",bCanToggleVisibility=True,bIsMarkedForAdvancedDisplay=True)
   ShowPinForProperties(25)=(PropertyName="DampingCurveData",PropertyFriendlyName="Damping Rate by Bone Length Rate",PropertyTooltip="各ボーンに適用するPhysics Settings/ Damping パラメータを補正。\n「RootBoneから特定のボーンまでの長さ / RootBoneから末端のボーンまでの長さ」(0.0~1.0)の値におけるカーブの値を各パラメータに乗算\nCorrects the Physics Settings/Damping parameters applied to each bone.\nMultiplies each parameter by the curve value for \"Length from RootBone to specific bone / Length from RootBone to end bone\" (0.0~1.0).",CategoryName="Physics Settings",bCanToggleVisibility=True,bIsMarkedForAdvancedDisplay=True)
   ShowPinForProperties(26)=(PropertyName="StiffnessCurveData",PropertyFriendlyName="Stiffness Rate by Bone Length Rate",PropertyTooltip="各ボーンに適用するPhysics Settings/ Stiffness パラメータを補正。\n「RootBoneから特定のボーンまでの長さ / RootBoneから末端のボーンまでの長さ」(0.0~1.0)の値におけるカーブの値を各パラメータに乗算\nCorrects the Physics Settings/Stiffness parameters applied to each bone.\nMultiplies each parameter by the curve value for \"Length from RootBone to specific bone / Length from RootBone to end bone\" (0.0~1.0).",CategoryName="Physics Settings",bCanToggleVisibility=True,bIsMarkedForAdvancedDisplay=True)
   ShowPinForProperties(27)=(PropertyName="WorldDampingLocationCurveData",PropertyFriendlyName="World Damping Location Rate by Bone Length Rate",PropertyTooltip="各ボーンに適用するPhysics Settings/ WorldDampingLocation パラメータを補正。\n「RootBoneから特定のボーンまでの長さ / RootBoneから末端のボーンまでの長さ」(0.0~1.0)の値におけるカーブの値を各パラメータに乗算\nCorrects the Physics Settings/WorldDampingLocation parameters applied to each bone.\nMultiplies each parameter by the curve value for \"Length from RootBone to specific bone / Length from RootBone to end bone\" (0.0~1.0).",CategoryName="Physics Settings",bCanToggleVisibility=True,bIsMarkedForAdvancedDisplay=True)
   ShowPinForProperties(28)=(PropertyName="WorldDampingRotationCurveData",PropertyFriendlyName="World Damping Rotation Rate by Bone Length Rate",PropertyTooltip="各ボーンに適用するPhysics Settings/ WorldDampingRotation パラメータを補正。\n「RootBoneから特定のボーンまでの長さ / RootBoneから末端のボーンまでの長さ」(0.0~1.0)の値におけるカーブの値を各パラメータに乗算\nCorrects the Physics Settings/WorldDampingRotation parameters applied to each bone.\nMultiplies each parameter by the curve value for \"Length from RootBone to specific bone / Length from RootBone to end bone\" (0.0~1.0).",CategoryName="Physics Settings",bCanToggleVisibility=True,bIsMarkedForAdvancedDisplay=True)
   ShowPinForProperties(29)=(PropertyName="RadiusCurveData",PropertyFriendlyName="Radius Rate by Bone Length Rate",PropertyTooltip="各ボーンに適用するPhysics Settings/ CollisionRadius パラメータを補正。\n「RootBoneから特定のボーンまでの長さ / RootBoneから末端のボーンまでの長さ」(0.0~1.0)の値におけるカーブの値を各パラメータに乗算\nCorrects the Physics Settings/CollisionRadius parameters applied to each bone.\nMultiplies each parameter by the curve value for \"Length from RootBone to specific bone / Length from RootBone to end bone\" (0.0~1.0).",CategoryName="Physics Settings",bCanToggleVisibility=True,bIsMarkedForAdvancedDisplay=True)
   ShowPinForProperties(30)=(PropertyName="LimitAngleCurveData",PropertyFriendlyName="LimitAngle Rate by Bone Length Rate",PropertyTooltip="各ボーンに適用するPhysics Settings/ LimitAngle パラメータを補正。\n「RootBoneから特定のボーンまでの長さ / RootBoneから末端のボーンまでの長さ」(0.0~1.0)の値におけるカーブの値を各パラメータに乗算\nCorrects the Physics Settings/LimitAngle parameters applied to each bone.\nMultiplies each parameter by the curve value for \"Length from RootBone to specific bone / Length from RootBone to end bone\" (0.0~1.0).",CategoryName="Physics Settings",bCanToggleVisibility=True,bIsMarkedForAdvancedDisplay=True)
   ShowPinForProperties(31)=(PropertyName="SphericalLimits",PropertyFriendlyName="Spherical Limits",PropertyTooltip="コリジョン（球）\nSpherical Collision",CategoryName="Limits")
   ShowPinForProperties(32)=(PropertyName="CapsuleLimits",PropertyFriendlyName="Capsule Limits",PropertyTooltip="コリジョン（カプセル）\nCapsule Collision",CategoryName="Limits")
   ShowPinForProperties(33)=(PropertyName="BoxLimits",PropertyFriendlyName="Box Limits",PropertyTooltip="コリジョン（ボックス）\nBox Collision",CategoryName="Limits")
   ShowPinForProperties(34)=(PropertyName="PlanarLimits",PropertyFriendlyName="Planar Limits",PropertyTooltip="コリジョン（平面）\nPlanar Collision",CategoryName="Limits")
   ShowPinForProperties(35)=(PropertyName="LimitsDataAsset",PropertyFriendlyName="Limits Data Asset",PropertyTooltip="コリジョン設定（DataAsset版）。別AnimNode・ABPで設定を流用したい場合はこちらを推奨\nCollision settings (DataAsset version). This is recommended if you want to reuse the settings for another AnimNode or ABP.",CategoryName="Limits",bShowPin=True,bCanToggleVisibility=True)
   ShowPinForProperties(36)=(PropertyName="PhysicsAssetForLimits",PropertyFriendlyName="Physics Asset for Limits",PropertyTooltip="コリジョン設定（PhyiscsAsset版）。別AnimNode・ABPで設定を流用したい場合はこちらを推奨\nCollision settings (PhyiscsAsset版 version). This is recommended if you want to reuse the settings for another AnimNode or ABP.",CategoryName="Limits",bCanToggleVisibility=True)
   ShowPinForProperties(37)=(PropertyName="SphericalLimitsData",PropertyFriendlyName="Spherical Limits Data",PropertyTooltip="コリジョン設定（DataAsset版）における球コリジョンのプレビュー\nPreview of sphere collision in collision settings (DataAsset version)",CategoryName="Limits",bIsMarkedForAdvancedDisplay=True)
   ShowPinForProperties(38)=(PropertyName="CapsuleLimitsData",PropertyFriendlyName="Capsule Limits Data",PropertyTooltip="コリジョン設定（DataAsset版）におけるカプセルコリジョンのプレビュー\nPreview of capsule collision in collision settings (DataAsset version)",CategoryName="Limits",bIsMarkedForAdvancedDisplay=True)
   ShowPinForProperties(39)=(PropertyName="BoxLimitsData",PropertyFriendlyName="Box Limits Data",PropertyTooltip="コリジョン設定（DataAsset版）におけるボックスコリジョンのプレビュー\nPreview of box collision in collision settings (DataAsset version)",CategoryName="Limits",bIsMarkedForAdvancedDisplay=True)
   ShowPinForProperties(40)=(PropertyName="PlanarLimitsData",PropertyFriendlyName="Planar Limits Data",PropertyTooltip="コリジョン設定（DataAsset版）における平面コリジョンのプレビュー\nPreview of planar collision in collision settings (DataAsset version)",CategoryName="Limits",bIsMarkedForAdvancedDisplay=True)
   ShowPinForProperties(41)=(PropertyName="BoneConstraintGlobalComplianceType",PropertyFriendlyName="Bone Constraint Global Compliance Type",PropertyTooltip="Bone Constraintで用いる剛性タイプ\nStiffness type to use in Bone Constraint\nhttp://blog.mmacklin.com/2016/10/12/xpbd-slides-and-stiffness/",CategoryName="Bone Constraint (Experimental)",bCanToggleVisibility=True)
   ShowPinForProperties(42)=(PropertyName="BoneConstraintIterationCountBeforeCollision",PropertyFriendlyName="Bone Constraint Iteration Count Before Collision",PropertyTooltip="Bone Constraintの処理回数（コリジョン処理前）\nNumber of Bone Constraints processed before collision processing",CategoryName="Bone Constraint (Experimental)",bCanToggleVisibility=True)
   ShowPinForProperties(43)=(PropertyName="BoneConstraintIterationCountAfterCollision",PropertyFriendlyName="Bone Constraint Iteration Count After Collision",PropertyTooltip="Bone Constraintの処理回数（コリジョン処理後）\nNumber of Bone Constraints processed after collision processing",CategoryName="Bone Constraint (Experimental)",bCanToggleVisibility=True)
   ShowPinForProperties(44)=(PropertyName="bAutoAddChildDummyBoneConstraint",PropertyFriendlyName="Auto Add Child Dummy Bone Constraint",PropertyTooltip="末端ボーンをBoneConstraint処理の対象にした場合、自動的にダミーボーンも処理対象にするフラグ\nFlag to automatically processes dummy bones when the end bones are subject to BoneConstraint processing.",CategoryName="Bone Constraint (Experimental)",bCanToggleVisibility=True)
   ShowPinForProperties(45)=(PropertyName="BoneConstraints",PropertyFriendlyName="Bone Constraints",PropertyTooltip="BoneConstraint処理の対象となるボーンのペアを設定。スカートのように、ボーン間の距離を維持したい場合に使用\nSets the bone pair to be processed by BoneConstraint. Used when you want to maintain the distance between bones, such as a skirt.",CategoryName="Bone Constraint (Experimental)")
   ShowPinForProperties(46)=(PropertyName="BoneConstraintsDataAsset",PropertyFriendlyName="Bone Constraints Data Asset",PropertyTooltip="BoneConstraint処理の対象となるボーンのペアを設定 (DataAsset版）。別AnimNode・ABPで設定を流用したい場合はこちらを推奨\nSet the bone pairs to be processed by BoneConstraint (DataAsset version). If you want to reuse the settings for another AnimNode or another ABP, this is recommended.",CategoryName="Bone Constraint (Experimental)",bCanToggleVisibility=True)
   ShowPinForProperties(47)=(PropertyName="BoneConstraintsData",PropertyFriendlyName="Bone Constraints Data",PropertyTooltip="BoneConstraint処理の対象となるボーンのペアのプレビュー\nPreview of bone pairs that will be processed by BoneConstraint",CategoryName="Bone Constraint (Experimental)",bIsMarkedForAdvancedDisplay=True)
   ShowPinForProperties(48)=(PropertyName="Gravity",PropertyFriendlyName="External Force",PropertyTooltip="外力（重力など）\nExternal forces (gravity, etc.)",CategoryName="ExternalForce",bCanToggleVisibility=True)
   ShowPinForProperties(49)=(PropertyName="bEnableWind",PropertyFriendlyName="Enable Wind",CategoryName="ExternalForce",bCanToggleVisibility=True)
   ShowPinForProperties(50)=(PropertyName="WindScale",PropertyFriendlyName="Wind Scale",PropertyTooltip="WindDirectionalSourceによる風の影響度。ClothやSpeedTreeとの併用目的\nInfluence of wind by WindDirectionalSource. For use with Cloth and SpeedTree",CategoryName="ExternalForce",bCanToggleVisibility=True,bHasOverridePin=True)
   ShowPinForProperties(51)=(PropertyName="ExternalForces",PropertyFriendlyName="External Forces",PropertyTooltip="外力のプリセット。C++で独自のプリセットを追加可能(Instanced Struct)\nExternal force presets. You can add your own presets in C++.",CategoryName="ExternalForce")
   ShowPinForProperties(52)=(PropertyName="CustomExternalForces",PropertyFriendlyName="CustomExternalForces(EXPERIMENTAL)",PropertyTooltip="!!! VERY VERY EXPERIMENTAL !!!\n外力のプリセット。BP・C++で独自のプリセットを追加可能(Instanced Property)\n注意：AnimNodeをクリック or ABPをコンパイルしないと正常に動作しません\nExternal force presets. You can add your own presets in BP or C++\nNote: If you do not click on AnimNode or compile ABP, it will not work properly.",CategoryName="ExternalForce")
   ShowPinForProperties(53)=(PropertyName="bAllowWorldCollision",PropertyFriendlyName="Allow World Collision",PropertyTooltip="レベル上の各コリジョンとの判定を行うフラグ。有効にすると物理処理の負荷が大幅に上がります\nFlag for collision detection with each collision on the level. Enabling this will significantly increase the load of physics processing.",CategoryName="World Collision",bCanToggleVisibility=True)
   ShowPinForProperties(54)=(PropertyName="bOverrideCollisionParams",PropertyFriendlyName="Override Collision Params",CategoryName="World Collision",bCanToggleVisibility=True)
   ShowPinForProperties(55)=(PropertyName="CollisionChannelSettings",PropertyFriendlyName="Override SkelComp Collision Params",PropertyTooltip="SkeletalMeshComponentが持つコリジョン設定ではなく、独自のコリジョン設定をWorldCollisionで使用する際に設定\nUse custom collision settings in WorldCollision instead of the collision settings set in SkeletalMeshComponent.",CategoryName="World Collision",bCanToggleVisibility=True,bHasOverridePin=True)
   ShowPinForProperties(56)=(PropertyName="bIgnoreSelfComponent",PropertyFriendlyName="Ignore Self Component",PropertyTooltip="WorldCollisionにて、SkeletalMeshComponentが持つコリジョン(PhysicsAsset)を無視するフラグ\nIn WorldCollision, Flag to ignore collisions for SkeletalMeshComponent(PhysicsAsset) in WorldCollision",CategoryName="World Collision",bCanToggleVisibility=True,bHasOverridePin=True)
   ShowPinForProperties(57)=(PropertyName="IgnoreBones",PropertyFriendlyName="Ignore Bones",PropertyTooltip="WorldCollisionにて、SkeletalMeshComponentが持つコリジョン(PhysicsAsset)を無視する設定（骨）\nIn WorldCollision, set to ignore collision (PhysicsAsset) of SkeletalMeshComponent using bone",CategoryName="World Collision",bHasOverridePin=True)
   ShowPinForProperties(58)=(PropertyName="IgnoreBoneNamePrefix",PropertyFriendlyName="Ignore Bone Name Prefix",PropertyTooltip="WorldCollisionにて、SkeletalMeshComponentが持つコリジョン(PhysicsAsset)を無視する設定（骨名のプリフィックス）\nIn WorldCollision, set to ignore collision (PhysicsAsset) of SkeletalMeshComponent using bone name prefix",CategoryName="World Collision",bHasOverridePin=True)
   ShowPinForProperties(59)=(PropertyName="KawaiiPhysicsTag",PropertyFriendlyName="Kawaii Physics Tag",PropertyTooltip="ExternalForceなどで使用するフィルタリング用タグ\nTag for filtering of ExternalForce etc",CategoryName="Tag")
   ShowPinForProperties(60)=(PropertyName="ModifyBones",PropertyFriendlyName="Modify Bones",CategoryName="Bones")
   ShowPinForProperties(61)=(PropertyName="DeltaTime",PropertyFriendlyName="Delta Time",CategoryName="KawaiiPhysics")
   Binding="/Script/AnimGraph.AnimGraphNodeBinding_Base'AnimGraphNodeBinding_Base_0'"
   NodePosX=-416
   NodePosY=-2448
   ErrorType=3
   NodeGuid=6DFD9B6E406D1CECAC590596D98888A2
   CustomProperties Pin (PinId=309A372F46C8EAE704BDE091948861EE,PinName="ComponentPose",PinFriendlyName="Component Pose",PinToolTip="Component Pose\nComponent Space Pose Link Structure\n\nInput link",PinType.PinCategory="struct",PinType.PinSubCategory="",PinType.PinSubCategoryObject="/Script/CoreUObject.ScriptStruct'/Script/Engine.ComponentSpacePoseLink'",PinType.PinSubCategoryMemberReference=(),PinType.PinValueType=(),PinType.ContainerType=None,PinType.bIsReference=False,PinType.bIsConst=False,PinType.bIsWeakPointer=False,PinType.bIsUObjectWrapper=False,PinType.bSerializeAsSinglePrecisionFloat=False,DefaultValue="(LinkID=-1,SourceLinkID=-1)",AutogeneratedDefaultValue="(LinkID=-1,SourceLinkID=-1)",LinkedTo=(AnimGraphNode_LocalToComponentSpace_0 1E22EF1044B9F3F7F11C8FA489BD1CDF,),PersistentGuid=00000000000000000000000000000000,bHidden=False,bNotConnectable=False,bDefaultValueIsReadOnly=False,bDefaultValueIsIgnored=False,bAdvancedView=False,bOrphanedPin=False,)
   CustomProperties Pin (PinId=F5C48D134067A9F6E9A665AD34CF9958,PinName="bAlphaBoolEnabled",PinFriendlyName="bEnabled",PinToolTip="Enabled\nBoolean",PinType.PinCategory="bool",PinType.PinSubCategory="",PinType.PinSubCategoryObject=None,PinType.PinSubCategoryMemberReference=(),PinType.PinValueType=(),PinType.ContainerType=None,PinType.bIsReference=False,PinType.bIsConst=False,PinType.bIsWeakPointer=False,PinType.bIsUObjectWrapper=False,PinType.bSerializeAsSinglePrecisionFloat=False,DefaultValue="True",AutogeneratedDefaultValue="True",PersistentGuid=00000000000000000000000000000000,bHidden=True,bNotConnectable=False,bDefaultValueIsReadOnly=False,bDefaultValueIsIgnored=False,bAdvancedView=False,bOrphanedPin=False,)
   CustomProperties Pin (PinId=1B1A2ABB4B31DC140CA6BDBEFDC1AFB2,PinName="Alpha",PinFriendlyName="Alpha",PinToolTip="Alpha\nFloat (single-precision)\n\nCurrent strength of the skeletal control",PinType.PinCategory="real",PinType.PinSubCategory="float",PinType.PinSubCategoryObject=None,PinType.PinSubCategoryMemberReference=(),PinType.PinValueType=(),PinType.ContainerType=None,PinType.bIsReference=False,PinType.bIsConst=False,PinType.bIsWeakPointer=False,PinType.bIsUObjectWrapper=False,PinType.bSerializeAsSinglePrecisionFloat=False,DefaultValue="1.000000",AutogeneratedDefaultValue="1.000000",PersistentGuid=00000000000000000000000000000000,bHidden=False,bNotConnectable=False,bDefaultValueIsReadOnly=False,bDefaultValueIsIgnored=False,bAdvancedView=False,bOrphanedPin=False,)
   CustomProperties Pin (PinId=74EABA934AAF52C3ACBA7ABEEB31A71A,PinName="AlphaCurveName",PinFriendlyName="Alpha Curve Name",PinToolTip="Alpha Curve Name\nName",PinType.PinCategory="name",PinType.PinSubCategory="",PinType.PinSubCategoryObject=None,PinType.PinSubCategoryMemberReference=(),PinType.PinValueType=(),PinType.ContainerType=None,PinType.bIsReference=False,PinType.bIsConst=False,PinType.bIsWeakPointer=False,PinType.bIsUObjectWrapper=False,PinType.bSerializeAsSinglePrecisionFloat=False,DefaultValue="None",AutogeneratedDefaultValue="None",PersistentGuid=00000000000000000000000000000000,bHidden=True,bNotConnectable=False,bDefaultValueIsReadOnly=False,bDefaultValueIsIgnored=False,bAdvancedView=False,bOrphanedPin=False,)
   CustomProperties Pin (PinId=19B8FD2846BA0EC5243BC3A754E7509B,PinName="PhysicsSettings",PinFriendlyName="Physics Settings",PinToolTip="Physics Settings\nKawaii Physics Settings Structure\n\n物理制御の基本設定\nBasic physics settings",PinType.PinCategory="struct",PinType.PinSubCategory="",PinType.PinSubCategoryObject="/Script/CoreUObject.ScriptStruct'/Script/KawaiiPhysics.KawaiiPhysicsSettings'",PinType.PinSubCategoryMemberReference=(),PinType.PinValueType=(),PinType.ContainerType=None,PinType.bIsReference=False,PinType.bIsConst=False,PinType.bIsWeakPointer=False,PinType.bIsUObjectWrapper=False,PinType.bSerializeAsSinglePrecisionFloat=False,DefaultValue="(Damping=0.100000,Stiffness=0.050000,WorldDampingLocation=0.800000,WorldDampingRotation=0.800000,Radius=3.000000,LimitAngle=0.000000)",AutogeneratedDefaultValue="(Damping=0.100000,Stiffness=0.050000,WorldDampingLocation=0.800000,WorldDampingRotation=0.800000,Radius=3.000000,LimitAngle=0.000000)",LinkedTo=(K2Node_MakeStruct_0 CE85FC964F48D5D7DFF12D9D02B29788,),PersistentGuid=00000000000000000000000000000000,bHidden=False,bNotConnectable=False,bDefaultValueIsReadOnly=False,bDefaultValueIsIgnored=False,bAdvancedView=False,bOrphanedPin=False,)
   CustomProperties Pin (PinId=53D2BE5244F3BDBCE285B0BD1CBB18FD,PinName="LimitsDataAsset",PinFriendlyName="Limits Data Asset",PinToolTip="Limits Data Asset\nKawaii Physics Limits Data Asset Object Reference\n\nコリジョン設定（DataAsset版）。別AnimNode・ABPで設定を流用したい場合はこちらを推奨\nCollision settings (DataAsset version). This is recommended if you want to reuse the settings for another AnimNode or ABP.",PinType.PinCategory="object",PinType.PinSubCategory="",PinType.PinSubCategoryObject="/Script/CoreUObject.Class'/Script/KawaiiPhysics.KawaiiPhysicsLimitsDataAsset'",PinType.PinSubCategoryMemberReference=(),PinType.PinValueType=(),PinType.ContainerType=None,PinType.bIsReference=False,PinType.bIsConst=False,PinType.bIsWeakPointer=False,PinType.bIsUObjectWrapper=True,PinType.bSerializeAsSinglePrecisionFloat=False,AutogeneratedDefaultValue="None",LinkedTo=(K2Node_VariableGet_0 4D0AA5824FC39BD7EBAAECABE7CC8B60,),PersistentGuid=00000000000000000000000000000000,bHidden=False,bNotConnectable=False,bDefaultValueIsReadOnly=False,bDefaultValueIsIgnored=False,bAdvancedView=False,bOrphanedPin=False,)
   CustomProperties Pin (PinId=CF753C134B71F9E80DF68B96E1E30589,PinName="Pose",Direction="EGPD_Output",PinType.PinCategory="struct",PinType.PinSubCategory="",PinType.PinSubCategoryObject="/Script/CoreUObject.ScriptStruct'/Script/Engine.ComponentSpacePoseLink'",PinType.PinSubCategoryMemberReference=(),PinType.PinValueType=(),PinType.ContainerType=None,PinType.bIsReference=False,PinType.bIsConst=False,PinType.bIsWeakPointer=False,PinType.bIsUObjectWrapper=False,PinType.bSerializeAsSinglePrecisionFloat=False,LinkedTo=(AnimGraphNode_KawaiiPhysics_10 CC3100A44E0751D57387BB913AD53AD8,),PersistentGuid=00000000000000000000000000000000,bHidden=False,bNotConnectable=False,bDefaultValueIsReadOnly=False,bDefaultValueIsIgnored=False,bAdvancedView=False,bOrphanedPin=False,)
End Object


import maya.cmds as cmds

#    Create a window with two option menu groups.
#
window = cmds.window( title='Example 1' )
cmds.columnLayout()

#    Create a couple of option menu groups.
#
colors = cmds.optionMenuGrp(label='Colors')
cmds.menuItem( label='Red' )
cmds.menuItem( label='Green' )
cmds.optionMenuGrp( l='Position' )
cmds.menuItem( label='Left' )
cmds.menuItem( label='Center' )
cmds.menuItem( label='Right' )

#    Now add an additional item to the first option menu.
#
cmds.menuItem(parent=(colors +'|OptionMenu'), label='Blue' )
cmds.showWindow( window )

#    Create another window with an option menu group.
#
window = cmds.window( title='Example 2' )
cmds.columnLayout()
cmds.optionMenuGrp( label='Size', extraLabel='cm', columnWidth=[(1,80), (2, 120)], columnAttach=(1,"left",20))
cmds.menuItem( label='10' )
cmds.menuItem( label='100' )
cmds.menuItem( label='1000' )
cmds.showWindow( window )


import maya.cmds as cmds


def on_option_changed(selected_label):

    print(selected_label)


name_omg = "main"

cmds.optionMenuGrp(
    name_omg,
    label="Select",
    changeCommand=on_option_changed
)

cmds.menuItem(label='10')
cmds.menuItem(label='100')
cmds.menuItem(label='1000')



def on_option_changed(textfield_name, selected_label):

    cmds.textField(
        textfield_name,
        e=True,
        text=selected_label
    )
    
changeCommand=partial(on_option_changed, name_tfg)

JUN_All/
  ├─tools/ 
  │  ├─A0010_base.py
  │  ├─A0020_humanikTool.py
  │  └─A0030_moveSkinWeightTool.py
  ├─ui/ 
  │  ├─colorThem.py
  │  ├─optionMenuGrp.py
  │  └─radioColleciton.py