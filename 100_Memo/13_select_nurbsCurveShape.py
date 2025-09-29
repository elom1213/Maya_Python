def select_curve_shapes():
    """
    Select all curve shape nodes (nurbsCurve) in the scene.
    """
    curves = cmds.ls(type="nurbsCurve")  # find all curve shape nodes
    if curves:
        cmds.select(curves)
        return curves
    else:
        print("No curve shapes found.")
        return []


# Example usage:
selected_shapes = select_curve_shapes()