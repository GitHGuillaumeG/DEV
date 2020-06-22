# Maya
import maya.cmds as cmds
from maya.api import OpenMaya as om


def get_cv_positions_from_curve(curve, space='world'):
    """
    Returns the positions of all the cvs of curve. Either in world space or in object space
    
    :param curve: (str) name of a nurbsCurve
    :param space: (str) either world or object
    
    :return: cvs positions 
    """

    curve_object = om.MGlobal.getSelectionListByName(curve).getDagPath(0)
    curve_fn = om.MFnNurbsCurve(curve_object)

    if not space == 'world':
        positions = curve_fn.cvPositions(space=om.MSpace.kObject)
    else:
        positions = curve_fn.cvPositions(space=om.MSpace.kWorld)

    return positions
