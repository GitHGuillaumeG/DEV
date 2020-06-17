import pymel.core as pm
import maya.cmds as cmds

from ..rig import base
from ..rig import controlshape


class Control(base.Base):

    def __init__(self, node):
        super(Control, self).__init__(node)

        # Input attributes
        self._name = None
        self._buffer = None
        self._shape = None
        self._py_node = None

        # Output attributes

    @classmethod
    def create(cls, name, node_type='transform', shape=None, control_buffer=False):

        # Create control and buffer
        ctl = pm.createNode(node_type, skipSelect=True)
        if name:
            pm.rename(ctl, name)

        if control_buffer:
            buf = pm.createNode('transform', skipSelect=True)
            ctl.setParent(buf)
            if name:
                pm.rename(buf, '{0}_NULL'.format(ctl.rpartition('_')[0]))

        if node_type == 'joint':
            ctl.drawStyle.set(2)

        # Create shape
        ctl_shape = controlshape.ControlShape(ctl)
        ctl_shape.data = shape

        node = cls(ctl)
        node.name = ctl.name()
        if control_buffer:
            node.buffer = buf.name()
        node.shape = ctl_shape

        return node

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        if isinstance(value, basestring):
            self._name = value

    @property
    def buffer(self):
        return self._buffer

    @buffer.setter
    def buffer(self, value):
        self._buffer = value

    @property
    def shape(self):
        return self._shape

    @shape.setter
    def shape(self, value):
        self._shape = value

    @property
    def py_node(self):
        if not self._py_node:
            self._py_node = pm.PyNode(self)

        return self._py_node

    def add_joint(self):
        """
        Creates a joint parented immediately under the control.
        Returns:

        """
        jnt = pm.joint(n=self.name.replace('_CTL', '_JNT'))
        jnt.setMatrix(self.py_node.getMatrix(worldSpace=True))
        jnt.setParent(self.py_node)

