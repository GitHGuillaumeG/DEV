import collections

from maya.api import OpenMaya as om
import components as components_api

TOL = 10e-6


class Points(collections.defaultdict):

    @staticmethod
    def _get_default():
        return om.MPoint()

    @classmethod
    def deserialize(cls, data):
        """
        Returns points from the serialized data.
        Args:
            data (list): list of key, value tuples
                key: component data
                value: point as tuple of 3 values
        Returns:
            Points: component points
        """
        return cls({components_api.Component.deserialize(k): om.MPoint(v) for k, v in data})

    @classmethod
    def from_curve_cvs(cls, curve, world=False, internal=False, components=None, hidden=False):
        """
        Returns the CV positions of a nurbsCurve.
        Args:
            curve (str): nurbsCurve
            world (bool): world or object space
            internal (bool): internal or UI units
            components (components_api.Components): component selection
            hidden (bool): True returns hidden (overlapping) cvs
        Returns:
            Points: positions of the nurbsCurve CVs
        """
        if components is None:
            components = components_api.Components.from_curve_cvs(curve, hidden=hidden)
        curve_fn = om.MFnNurbsCurve()
        curve_fn.setObject(om.MGlobal.getSelectionListByName(curve).getDagPath(0))

        point_a = curve_fn.cvPositions(om.MSpace.kWorld if world else om.MSpace.kObject)
        coeff = 1.0 if internal else om.MDistance.internalToUI(1.0)
        if abs(coeff - 1.0) > TOL:
            return cls({comp: point_a[comp.weight_index] * coeff for comp in components})

        return cls({comp: om.MPoint(point_a[comp.weight_index]) for comp in components})

    def __init__(self, *args, **kwargs):
        """
        Initialize the points dictionary with default MPoint(0, 0, 0).
        Args:
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments.
        """
        super(Points, self).__init__(self._get_default, *args, **kwargs)
        self._hash_table = None
        self._hash_center = None
        self._hash_step = None

    def serialize(self):
        """
        Returns serialized data for the points.
        Returns:
            list: list of key, value tuples
                key: component data
                value: point as tuple of 3 values
        """
        return [(key.serialize(), tuple(self[key])[:-1]) for key in self]

