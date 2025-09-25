
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

    