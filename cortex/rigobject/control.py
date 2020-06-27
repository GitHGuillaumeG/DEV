# Python libs
import collections
import os
import json
import logging

# Maya
import maya.cmds as cmds
from maya.api import OpenMaya as om

# Cortex
from ..api import component
from ..api import environment

# Logger
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class Control(object):
    """
    Function set for rig controls.
    This class allows you to create, modify and query rig controls.

    To create a control, you should use the create() classmethod
    head_ctl = Control.create('C_head_CTL')

    To query or modify a control from the maya scene, instantiate the class with its name
    spine_ctl = Control('C_Spine_0_CTL')

    you can then modify its shape or color :
    spine_ctl.set_shape_from_library('square')
    spine_ctl.color = 'yellow'

    or query and store its shape(s) data :
    spine_ctlShape = ctl.shape
    spine_ctlColor = ctl.color

    and copy it to another control :
    head_ctl.shape = spine_ctlShape
    head_ctl.color = spine_ctlColor
    """

    def __init__(self, name):

        # input attributes
        if not cmds.objExists(name):
            log.error('the object {0} does not exist. Control instance not initialized correctly.'.format(name))
            return
        self.name = name

        # output attributes
        self.buffer = None
        self.joint = None
        self._shape = dict()
        self._color = dict()

    @classmethod
    def create(cls, name):
        """
        Creates a control (a transform). Instantiate the class with that control name as argument.

        :param name: (str) name of the control

        :return: Control() class instance set to control
        """

        ctl = cmds.createNode('transform', n=name, skipSelect=True)
        node = cls(ctl)
        node.shape = None

        return node

    @property
    def shape(self):
        """
        Gets the control nurbsCurve shape(s) data (points, degree, knots, periodic)
        :return: (dict) the shape data
        """

        if not self._shape:
            self.get_shape_data()

        return self._shape

    @shape.setter
    def shape(self, value):
        """
        Sets the control nurbsCurve shape(s) data (points, degree, knots, periodic).
        :param value: (dict) dictionary containing attributes to (re)create a nurbsCurve
        """

        if value:
            if not isinstance(value, dict):
                log.error('You must set a shape with a dictionary containing the proper data to set the control shape.'
                          'Check Control.get_shape_data() or Control.shape property for more info.')
                return
            self._shape = value
        else:
            self._shape = DEFAULT_SHAPE
        self.set_shape_data()

    @property
    def color(self):
        """
        Gets the drawing override color of the nurbsCurves shapes of the control.
        This will return the color name of the shape from the controlShapes color library.

        Control's shape colors are identified by name. E.g. 'yellow', 'lightRed', 'darkBlue'... and are associated
        with some values. E.g. 'yellow': [1.0, 1.0, 0.0]

        :return: (dict) shape name:color name
        """
        if not self._color:
            shapes = self.get_shape()
            colors = dict()
            color_lib = environment.CONTROLSHAPES_COLOR
            with open(color_lib, 'r') as handle:
                color_lib = json.load(handle)

            for shape in shapes:
                if not cmds.getAttr('{0}.overrideEnabled'.format(shape)):
                    colors[shape] = 'no override'
                    continue
                if not cmds.getAttr('{0}.overrideRGBColors'.format(shape)):
                    color = cmds.getAttr('{0}.overrideColor'.format(shape))
                else:
                    color = cmds.getAttr('{0}.overrideColorRGB'.format(shape))[0]
                    color = [float('%.3f'%c) for c in color]

                for key, val in color_lib.items():
                    if color == val:
                        colors[shape] = key
            self._color = colors

        return self._color

    @color.setter
    def color(self, value):
        """
        Sets the drawing override color of the control nurbsCurves shape(s) based on a value.
        Value can be a string or a dictionary.
        If it's a string, it must match one of the color name in the controlShapes color library.
        If it's a dictionary, the keys should be the shapes of the control and the values must match one of the color
        name in the controlShapes color library.

        :param value: (str|dict) color name|shape name:color name

        """

        if not isinstance(value, str) or isinstance(value, dict):
            log.error('You mush specify a color name from the controlshapes color library. Abort.')
            return
        color_lib = environment.CONTROLSHAPES_COLOR
        with open(color_lib, 'r') as handle:
            color_lib = json.load(handle)

        if isinstance(value, str):
            if value not in color_lib.keys():
                log.error('The color you specified : {0} does not exist in the controlshapes'
                          ' color library. Abort.'.format(value))
                return

            color = color_lib[value]
            for shape in self.get_shape():
                cmds.setAttr('{0}.overrideEnabled'.format(shape), True)
                if isinstance(color, collections.Iterable):
                    cmds.setAttr('{0}.overrideRGBColors'.format(shape), True)
                    cmds.setAttr('{0}.overrideColorRGB'.format(shape), color[0], color[1], color[2])
                else:
                    cmds.setAttr('{0}.overrideRGBColors'.format(shape), False)
                    cmds.setAttr('{0}.overrideColor'.format(shape), color)
                self._color[shape] = value
        else:
            for shape, color_name in value:
                if color_name not in color_lib.keys():
                    log.error('The color you specified : {0} for shape {1} does not exist in the controlshapes'
                              ' color library. Abort.'.format(color_name, shape))
                    return

                color = color_lib[color_name]
                if cmds.objExists(shape) and cmds.listRelatives(shape, parent=True) == self.name:
                    cmds.setAttr('{0}.overrideEnabled'.format(shape), True)
                    if isinstance(color, collections.Iterable):
                        cmds.setAttr('{0}.overrideRGBColors'.format(shape), True)
                        cmds.setAttr('{0}.overrideColorRGB'.format(shape), color[0], color[1], color[2])
                    else:
                        cmds.setAttr('{0}.overrideRGBColors'.format(shape), True)
                        cmds.setAttr('{0}.overrideColor'.format(shape), color)
                    self._color[shape] = color_name
                else:
                    log.warning('shape : {0} does not exists or is not a child of control : {1}'.format(shape, self.name))
                    continue

    def add_buffer(self):
        """
        Inserts a buffer transform above the control.

        :return: (str) buffer name
        """

        if not self.buffer:
            self.buffer = cmds.createNode('transform', n=self.name.replace('_CTL', '_BUF'), skipSelect=True)
            cmds.xform(self.buffer, worldSpace=True, matrix=cmds.xform(self.name, q=True, worldSpace=True, matrix=True))

            ctl_parent = cmds.listRelatives(self.name, parent=True)
            if ctl_parent:
                cmds.parent(self.buffer, ctl_parent[0])

            cmds.parent(self.name, self.buffer)
        else:
            log.warning('control : {0} has already a buffer associated with it : {1}'.format(self.name, self.buffer))

        return self.buffer

    def add_joint(self):
        """
        Adds a joint directly below the control.

        :return: (str) joint's name
        """
        if not self.joint:
            self.joint = cmds.createNode('joint', n=self.name.replace('_CTL', '_JNT'), skipSelect=True)
            cmds.xform(self.joint, worldSpace=True, matrix=cmds.xform(self.name, q=True, worldSpace=True, matrix=True))
            cmds.parent(self.joint, self.name)

            for attr in ('tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'jointOrientX', 'jointOrientY', 'jointOrientZ'):
                cmds.setAttr('{0}.{1}'.format(self.joint, attr), 0.0)
        else:
            log.warning('control : {0} has already a joint associated with it : {1}'.format(self.name, self.joint))

        return self.joint

    def get_shape(self):
        """
        Returns a list of non-intermediate nurbsCurves shapes parented directly below the control.
        
        Returns: (list of str) curves shape name
        """

        shapes = list()
        node_dag = om.MGlobal.getSelectionListByName(self.name).getDagPath(0)
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
        Gets the control nurbsCurves shapes data (points, degree, knot and periodic attributes)
        """

        curve_shape = self.get_shape()
        if not isinstance(curve_shape, collections.Iterable):
            curve_shape = (curve_shape, )

        self._shape = dict()
        for i, curve in enumerate(curve_shape):
            self._shape['shape{0}'.format(i)] = dict(degree=1, point=None, knot=None, periodic=True)
            curve_path = om.MGlobal.getSelectionListByName(curve).getDagPath(0)
            curve_fn = om.MFnNurbsCurve(curve_path)

            self._shape['shape{0}'.format(i)]['degree'] = curve_fn.degree
            self._shape['shape{0}'.format(i)]['point'] = component.get_cv_positions_from_curve(curve)
            self._shape['shape{0}'.format(i)]['knot'] = list(curve_fn.knots())
            self._shape['shape{0}'.format(i)]['periodic'] = True if curve_fn.form == curve_fn.kPeriodic else False

    def set_shape_data(self):
        """
        Sets/replaces the control nurbsCurves shapes with the instance shape data (self._shape)
        """

        # Delete current curve's shapes below node
        current_shapes = self.get_shape()
        if current_shapes:
            cmds.delete(current_shapes)

        for i, shape_name in enumerate(self._shape):
            # Create a nurbsCurve parented under node
            curve = cmds.createNode('nurbsCurve',
                                    skipSelect=True,
                                    parent=self.name,
                                    n='{0}Shape{1}'.format(self.name, i))

            # Create a temp curve with instance data
            degree = self.shape[shape_name]['degree']
            knot = self.shape[shape_name]['knot']
            periodic = self.shape[shape_name]['periodic']
            curve_points = list()
            for key in sorted(self.shape[shape_name]['point']):
                curve_points.append(self.shape[shape_name]['point'][key])

            temp_curve = cmds.curve(degree=degree,
                                    point=curve_points,
                                    knot=knot,
                                    periodic=periodic,
                                    n='temp_transform')

            # Connect temp curve local to nurbsCurve create attribute. Eval and delete temp curve
            cmds.connectAttr('{0}.local'.format(temp_curve), '{0}.create'.format(curve))
            cmds.dgeval('{0}.local'.format(curve))
            cmds.delete(temp_curve)

    def set_shape_from_library(self, value):
        """
        Sets the control nurbsCurves shape from a json file in the controlShape's library

        Args:
            value (str): name of a controlShape file in the controlShape's library
        """

        shape_library = environment.CONTROLSHAPES_LIBRARY
        shape_file = os.path.join(shape_library, '{0}.json'.format(value))

        if not os.path.isfile(shape_file):
            log.error('controlShape library file {0} does not exists'.format(value))
            return

        with open(shape_file, 'r') as handle:
            shape_data = json.load(handle)
        self.shape = shape_data

    def store_shape_to_library(self, name):
        """
        Stores the control nurbsCurves shape as a json file in the controlShape's library
        """

        shape_library = environment.CONTROLSHAPES_LIBRARY
        shape_file = os.path.join(shape_library, '{0}.json'.format(name))

        data = json.dumps(self.shape, indent=2)
        with open(shape_file, 'w+') as handle:
            handle.write(data)


# Default control shape (circle)
DEFAULT_SHAPE = {"shape0": {
    "periodic": True,
    "knot": [-2.0, -1.0, 0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
    "degree": 3,
    "point": {
        "0": [0.783611624891225, 4.798237340988468e-17, -0.7836116248912238],
        "1": [-1.2643170607829326e-16, 6.785732323110913e-17, -1.108194187554388],
        "2": [-0.7836116248912243, 4.798237340988471e-17, -0.7836116248912243],
        "3": [-1.108194187554388, 1.966335461618786e-32, -3.21126950723723e-16],
        "4": [-0.7836116248912245, -4.7982373409884694e-17, 0.783611624891224],
        "5": [-3.3392053635905195e-16, -6.785732323110915e-17, 1.1081941875543881],
        "6": [0.7836116248912238, -4.798237340988472e-17, 0.7836116248912244],
        "7": [1.108194187554388, -3.644630067904792e-32, 5.952132599280585e-16],
        "8": [0.783611624891225, 4.798237340988468e-17, -0.7836116248912238],
        "9": [-1.2643170607829326e-16, 6.785732323110913e-17, -1.108194187554388],
        "10": [-0.7836116248912243, 4.798237340988471e-17, -0.7836116248912243],
        }
    }
}

