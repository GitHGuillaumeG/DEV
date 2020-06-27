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
    num_cvs = curve_fn.numCVs
    data = dict()

    for cv_index in range(num_cvs):
        if not space == 'world':
            position = curve_fn.cvPosition(cv_index)
        else:
            position = curve_fn.cvPosition(cv_index, space=om.MSpace.kWorld)
        data[cv_index] = position[0], position[1], position[2]

    return data
