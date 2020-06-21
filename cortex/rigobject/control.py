# Python libs
import collections
import os
import json

# Maya
import maya.cmds as cmds
from maya.api import OpenMaya as om

# Cortex
from ..api import component
from ..api import environment


class Control(object):

    def __init__(self, node):

        self.node = node
        self.buffer = None
        self._shape = dict()

    @classmethod
    def create(cls, name):

        ctl = cmds.createNode('transform', n=name)
        node = cls(ctl)

        return node

    @property
    def shape(self):
        if not self._shape:
            self.get_shape_data()

        return self._shape

    @shape.setter
    def shape(self, value):

        if value:
            self._shape = value
        else:
            self._shape = DEFAULT_SHAPE
        self.set_shape_data()

    def add_buffer(self):

        self.buffer = cmds.createNode('transform', n=self.node.replace('_CTL', '_BUF'))
        cmds.xform(self.buffer, worldSpace=True, matrix=cmds.xform(self.node, q=True, matrix=True))

        ctl_parent = cmds.listRelatives(self.node, parent=True)
        if ctl_parent:
            cmds.parent(self.buffer, ctl_parent)

        cmds.parent(self.node, self.buffer)

    def add_joint(self):

        jnt = cmds.createNode('joint', n=self.node.replace('_CTL', '_JNT'))
        cmds.xform(jnt, worldSpace=True, matrix=cmds.xform(self.node, q=True, matrix=True))

        cmds.parent(jnt, self.node)

        return jnt

    def get_shape(self):
        """
        Returns a list of non-intermediate nurbsCurves shapes directly below node.
        
        Returns: (list of str) curves name
        """

        shapes = list()
        node_dag = om.MGlobal.getSelectionListByName(self.node).getDagPath(0)
        node_fn = om.MFnDagNode()

        for i in range(node_dag.numberOfShapesDirectlyBelow()):
            shape_dag = node_dag.extendToShape(i)
            if not shape_dag.hasFn(om.MFn.kNurbsCurve):
                continue
            node_fn.setObject(shape_dag)
            if node_fn.isIntermediateObject:
                continue
            shapes.append(shape_dag.partialPathName())

        return shapes

    def get_shape_data(self):
        """
        Gets NURBS curve shape(s) data from node

        """
        curve_shape = self.get_shape()
        if not isinstance(curve_shape, collections.Iterable):
            curve_shape = (curve_shape, )

        for i, curve in enumerate(curve_shape):
            curve_path = om.MGlobal.getSelectionListByName(curve).getDagPath(0)
            curve_fn = om.MFnNurbsCurve(curve_path)

            self._shape['shape{0}'.format(i)]['degree'] = curve_fn.degree
            self._shape['shape{0}'.format(i)]['point'] = component.get_cv_positions_from_curve(curve)
            self._shape['shape{0}'.format(i)]['knot'] = list(curve_fn.knots())
            self._shape['shape{0}'.format(i)]['periodic'] = True if curve_fn.form == curve_fn.kPeriodic else False

    def set_shape_data(self):
        """
        Replaces/Sets node's nurbsCurves shapes with instance's shape data

        """

        # Delete current curve's shapes below node
        current_shapes = self.get_shape()
        if current_shapes:
            cmds.delete(current_shapes)

        for i, shape_name in enumerate(self._shape):
            # Create a nurbsCurve parented under node
            curve = cmds.createNode('nurbsCurve',
                                    skipSelect=True,
                                    parent=self.node,
                                    n='{0}Shape{1}'.format(self.node, i))

            # Create a temp curve with instance data
            degree = self.shape[shape_name]['degree']
            point = self.shape[shape_name]['point']
            knot = self.shape[shape_name]['knot']
            periodic = self.shape[shape_name]['periodic']

            temp_curve = cmds.curve(degree=degree,
                                    point=[tuple(point[comp])[:3] for comp in sorted(point.keys())],
                                    knot=knot,
                                    periodic=periodic,
                                    n='temp_transform')

            # Connect temp curve local to nurbsCurve create attribute. Eval and delete temp curve
            cmds.connectAttr('{0}.local'.format(temp_curve), '{0}.create'.format(curve))
            cmds.dgeval('{0}.local'.format(curve))
            cmds.delete(temp_curve)

    def set_shape_from_library(self, value):
        """
        Sets the control shape from a json shape file in the controlshape's library

        Args:
            value (str): name of a controlshape file in the library

        """

        shape_library = environment.Environment.controlShape_library
        shape_file = os.path.join(shape_library, '{0}.json'.format(value))

        if not os.path.isfile(shape_file):
            print('library file {0} does not exists'.format(value))
            return

        shape_data = json.loads(shape_file, indent=2)

        self.shape = shape_data


# Default control shape (circle)
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

