import logging

from ..cortexmodules import fkdrivenbyangle
from ..cortexmodules import rotationreader

import pymel.core as pm

log = logging.getLogger(__name__)
log.setLevel(logging.WARNING)


class CorrectiveJoint(object):
    """
    This module is meant to be used to fix bad looking deformations (volume loss...). It serves the same purpose
    as corrective blendshapes, but instead of using blendshapes it's using corrective joints to deform a mesh 
    via skinCluster weights.

    The module will create a setup of joints that are connected to the angle difference between a target and a reference
    node. A rigger can then decide how much translation, rotation or scale the joints will move based on that angle.
    By adding skinCluster weights to those joints, the painted area of the mesh will deform according to the settings
    made by the rigger.
    
    Attributes:
    Input
        name: (str) construction name with no suffix (used to name nodes created by this module)
        target: (str) read the rotation value of this node
        reference: (str) compare target's rotation value with this node
        axis_data:(dict) dict = {(str) corrective joint name: {(str)axis to read :(str|tuple|list) axis to drive}}
        twist_axis: (str) target's twist axis
    Output
        buffer: (PyNode) buffer/NULL top transform of the setup

    Example:
    Create a corrective joint module to fix bad looking deformation for the wrist. We'll need 4 corrective joints, one 
    to fix the rotated up deformation of the wrist, one to fix the rotated down deformation of the wrist, one to fix
    the rotated left deformation of the wrist and one to fix the rotated right deformation of the wrist. We'll call
    those joints North, South, East and West.
    
    >>
    from rig_zone.usr.ggilbaud.modules import correctivejoint
    corrective_module = correctivejoint.CorrectiveJoint()

    corrective_module.name = 'l_wristVolume'
    corrective_module.target = 'l_wrist_0_JNT'
    corrective_module.reference = 'l_elbow_0_JNT'
    corrective_module.axis_data = {'North':{'z':('tx', 'ty')},
                                   'South':{'z':('tx', 'ty')},
                                   'East':{'y':('tx', 'tz')},
                                   'West':{'y':('tx', 'tz')}
                                  }
    corrective_module.twist_axis = 'x'
    corrective_module.build()

    # Result :
    4 corrective joints are created, initially positioned and oriented at the target location (l_wrist_0_JNT).
    
    North : 'l_wristVolumeNorth_JNT' has translateX and translateY attributes driven by customizable animation curves
    that reads as input the rotateZ angle difference between l_wrist_0_JNT and l_elbow_0_JNT.
     
    South : 'l_wristVolumeSouth_JNT' with translateX and translateY attributes driven by customizable animation curves
    that reads as input the rotateZ angle difference between l_wrist_0_JNT and l_elbow_0_JNT.
    
    East : 'l_wristVolumeEast_JNT' with translateX and translateZ attributes driven by customizable animation curves
    that reads as input the rotateY angle difference between l_wrist_0_JNT and l_elbow_0_JNT
    
    West : 'l_wristVolumeWest_JNT' with translateX and translateZ attributes driven by customizable animation curves
    that reads as input the rotateY angle difference between l_wrist_0_JNT and l_elbow_0_JNT
    
    """

    def __init__(self):

        # Input Attributes
        self._name = None
        self._target = None
        self._reference = None
        self._axis_data = None
        self._twist_axis = None

        # Output attributes

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    @property
    def target(self):
        return self._target

    @target.setter
    def target(self, value):
        if not pm.objExists(value):
            log.error('{0} node don\'t exist. target default to None'.format(value))
            self._target = None
        else:
            self._target = value

    @property
    def reference(self):
        return self._reference

    @reference.setter
    def reference(self, value):
        if not pm.objExists(value):
            log.error('{0} node don\'t exist. reference default to None'.format(value))
            self._reference = None
        else:
            self._reference = value

    @property
    def axis_data(self):
        return self._axis_data

    @axis_data.setter
    def axis_data(self, value):
        if not isinstance(value, dict):
            log.error('axis_data is not a dictionary. Default to None.')
            self._axis_data = None
        else:
            self._axis_data = value

    @property
    def twist_axis(self):
        return self._twist_axis

    @twist_axis.setter
    def twist_axis(self, value):
        self._twist_axis = value

    def build(self):
        """
        Builds the module.
        """

        # Build the module dag hierarchy
        mod = pm.createNode('transform', n='{0}_module'.format(self.name), skipSelect=True)
        mod_inherit = pm.createNode('transform', n='{0}Inherit_TSF'.format(self.name), skipSelect=True)
        mod_data = pm.createNode('transform', n='{0}_DATA'.format(self.name))
        mod_inherit.setMatrix(pm.PyNode(self.target).getMatrix(worldSpace=True))
        mod_inherit.setParent(mod)
        mod_data.setParent(mod)

        # Build a rotation reader module to output angles between target and reference nodes
        rot_reader = rotationreader.RotationReader()
        rot_reader.name = self.name
        rot_reader.target = self.target
        rot_reader.reference = self.reference
        axis = list()
        for data in self.axis_data.itervalues():
            for key in data.iterkeys():
                if key not in axis:
                    axis.append(key)
        rot_reader.axis = axis
        rot_reader.build()

        # Build controls and joints driven by the rotation reader angle output
        fk_driven = fkdrivenbyangle.FkDrivenByAngle()
        fk_driven.target = self.target
        fk_driven.reference = self.reference

        for identifier, axis_data in self.axis_data.iteritems():
            fk_driven.name = '{0}{1}'.format(self.name, identifier)
            fk_driven.axis_data = axis_data
            fk_driven.build_dag()
            fk_driven.connect_rotation_reader_to_driver_dag(rot_reader.output_data, rot_reader.maya_data)
            fk_driven.buffer.setMatrix(mod_inherit.getMatrix(worldSpace=True))
            fk_driven.buffer.setParent(mod_inherit)
    
        # Attach the module in the hierarchy
        target_ws_info = pm.createNode('decomposeMatrix', n='{0}WorldSpace_DMAT'.format(mod.rpartition('_')[0]))
        pm.PyNode(self.target).worldMatrix[0] >> target_ws_info.inputMatrix
        target_ws_info.outputTranslateX >> mod_inherit.translateX
        target_ws_info.outputTranslateY >> mod_inherit.translateY
        target_ws_info.outputTranslateZ >> mod_inherit.translateZ

        # Make the setup follow target's twist axis of rotation
        if not self._twist_axis:
            log.info('twist_axis not provided. The setup will not follow target twist rotation.')
        else:
            rot_reader.axis = self._twist_axis
            rot_reader.extract_value()
            twist_output = rot_reader.data_node['extracted_{0}'.format(self._twist_axis)]

            pm.PyNode('{0}.outputRotate{1}'.format(twist_output, self._twist_axis.upper())) >> \
                pm.PyNode('{0}.rotate{1}'.format(mod_inherit, self._twist_axis.upper()))

        # Builds end
        log.info('{0} built succesfully!'.format(self.__class__.__name__))

    def delete_module(self):
        """
        Deletes dag and dg nodes built by the module.
        
        :return:
        """
        pass
