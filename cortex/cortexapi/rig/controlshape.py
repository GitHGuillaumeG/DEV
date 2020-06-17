import logging

from maya.api import OpenMaya as om
import maya.cmds as cmds

from ..rig import base
from ..data import points
from ..environment import path

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class ControlShape(base.Base):
    """
    This class gets and sets data needed to calculate and create a NURBS curve from/to a node.

    Attributes:
        node (str): node name
    """

    DEFAULT_SHAPE = None

    def __init__(self, node):
        super(ControlShape, self).__init__(node)
        self._data = {}

    @property
    def data(self):
        """
        Gets node's shapes data
        Returns:
            _data (dict): controlshape data dictionary
        """
        if not self._data:
            self.from_node()
        return self._data

    @data.setter
    def data(self, value):
        """
        Creates/Replaces nodes's shape
        Args:
            value (dict): controlshape data dictionary 
        """
        if value:
            self._data = value
        else:
            self._data = DEFAULT_SHAPE
        self.to_node()

    def get_curves_below_node(self):
        """
        Returns a list of non-intermediate NURBS curves directly below the transform.
        Returns:
            list: list of curves (str)
        """
        shapes = list()
        node_dag = self.m_dagpath
        node_fn = om.MFnDagNode()

        for i in xrange(node_dag.numberOfShapesDirectlyBelow()):
            shape_dag = om.MDagPath(node_dag).extendToShape(i)
            if not shape_dag.hasFn(om.MFn.kNurbsCurve):
                continue
            node_fn.setObject(shape_dag)
            if node_fn.isIntermediateObject:
                continue
            shapes.append(shape_dag.partialPathName())
        return shapes

    def from_library(self, value):
        """
        Sets  ControlShape from a file in the controlshape's library
        
        Args:
            value (str): name of a controlshape file in the library
        
        Examples:
            from cortex.cortexapi.rig import controlshape
            shape = controlshape.ControlShape('C_pelvis_0_CTL')
            shape.from_library('cube')
        
        """

        shape_data = path.Path().get_controlshape_data_from_file(value)
        if not shape_data:
            return
        self.data = shape_data

    def from_node(self):
        """
        Gets NURBS curve shape(s) data from node

        """
        curve_shape = self.get_curves_below_node()
        if not isinstance(curve_shape, list):
            curve_shape = [curve_shape]

        for i, curve in enumerate(curve_shape):
            curve_fn = om.MFnNurbsCurve()
            curve_fn.setObject(om.MGlobal.getSelectionListByName(curve).getDagPath(0))

            shape = self._data['shape{0}'.format(i)] = {}
            shape['degree'] = curve_fn.degree
            shape['point'] = points.Points.from_curve_cvs(curve, hidden=True, internal=True).serialize()
            shape['knot'] = list(curve_fn.knots())
            shape['periodic'] = True if curve_fn.form == curve_fn.kPeriodic else False

    def to_node(self):
        """
        Replace node's NURBS curves shapes with _data

        """
        # Delete current curve shapes below node
        current_shapes = self.get_curves_below_node()
        for shape in current_shapes:
            cmds.delete(shape)

        for i, shape in enumerate(self.data):
            # Create a nurbsCurve parented under node
            curve = cmds.createNode('nurbsCurve',
                                    skipSelect=True,
                                    parent=self._node,
                                    n='{0}Shape{1}'.format(self._node, i)
                                    )

            # Extract data and create a curve
            shape_data = self.data.get(shape, [])
            degree = shape_data.get('degree')
            point = points.Points.deserialize(shape_data.get('point'))
            knot = shape_data.get('knot')
            periodic = shape_data.get('periodic')

            temp_node = cmds.curve(degree=degree,
                                   point=[tuple(point[comp])[:3] for comp in sorted(point.keys())],
                                   knot=knot,
                                   periodic=periodic,
                                   n='temp_transform')

            # Connect curve local to nurbsCurve create, eval, delete curve
            cmds.connectAttr('{0}.local'.format(temp_node), '{0}.create'.format(curve))
            cmds.dgeval('{0}.local'.format(curve))
            cmds.delete(temp_node)

    def translate(self, values, world=False):
        """
        Translates all curves Cvs with the given values
        Args:
            values (tuple): triplets of translate values 
            world (bool): True to translate in world space
        """
        curves = self.get_curves_below_node()
        if curves:
            cmds.move(values[0], values[1], values[2],
                      ['{0}.cv[*]'.format(curve) for curve in curves],
                      relative=True,
                      objectSpace=not world,
                      worldSpace=world)

    def rotate(self, values, world=False):
        """
        Rotates all curves Cvs with the given values
        Args:
            values (tuple): triplets of rotate values 
            world (bool): True to rotate in world space
        """
        curves = self.get_curves_below_node()
        if curves:
            cmds.rotate(values[0], values[1], values[2],
                        ['{0}.cv[*]'.format(curve) for curve in curves],
                        relative=True,
                        objectSpace=not world,
                        worldSpace=world)

    def scale(self, values, world=False):
        """
        Scale all curves cvs with the given values
        Args:
            values (tuple): triplets of scale values 
            world (bool): True to scale in world space
        """
        curves = self.get_curves_below_node()
        if curves:
            cmds.scale(values[0], values[1], values[2],
                       ['{0}.cv[*]'.format(curve) for curve in curves],
                       relative=True,
                       objectSpace=not world,
                       worldSpace=world)

    def is_valid(self):
        """
        A valid curve should have at least one span.
        Returns:
            bool: True if the curve is valid
        """
        return True if len(self.point) > self.degree else False

    def deserialize(self, data):
        """
        Applies the serialized data to the function set
        Args:
            data (dict): serialized data 

        Returns:
        """
        pass

    def serialize(self):
        """
        Returns serialized data for the function set
        Returns: 
            dict: serialized data
        """
        pass

# Default shape is a circle
DEFAULT_SHAPE = {"shape0": {
    "periodic": True,
    "knot": [-2.0, -1.0, 0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
    "degree": 3,
    "point": [
        [[8, "cv[8]", [8]], [0.783611624891225, 4.798237340988468e-17, -0.7836116248912238]],
        [[4, "cv[4]", [4]], [-0.7836116248912245, -4.7982373409884694e-17, 0.783611624891224]],
        [[5, "cv[5]", [5]], [-3.3392053635905195e-16, -6.785732323110915e-17, 1.1081941875543881]],
        [[10, "cv[10]", [10]], [-0.7836116248912243, 4.798237340988471e-17, -0.7836116248912243]],
        [[1, "cv[1]", [1]], [-1.2643170607829326e-16, 6.785732323110913e-17, -1.108194187554388]],
        [[6, "cv[6]", [6]], [0.7836116248912238, -4.798237340988472e-17, 0.7836116248912244]],
        [[7, "cv[7]", [7]], [1.108194187554388, -3.644630067904792e-32, 5.952132599280585e-16]],
        [[2, "cv[2]", [2]], [-0.7836116248912243, 4.798237340988471e-17, -0.7836116248912243]],
        [[9, "cv[9]", [9]], [-1.2643170607829326e-16, 6.785732323110913e-17, -1.108194187554388]],
        [[3, "cv[3]", [3]], [-1.108194187554388, 1.966335461618786e-32, -3.21126950723723e-16]],
        [[0, "cv[0]", [0]], [0.783611624891225, 4.798237340988468e-17, -0.7836116248912238]]
        ]
    }
}
