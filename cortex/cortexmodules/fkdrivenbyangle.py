
import pymel.core as pm
from maya.api import OpenMaya as om

import logging
import collections

from EXTERNAL.DEV_reel.ggilbaud import transforms
from ..cortexmodules import rotationreader

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class FkDrivenByAngle(object):
    """
    This module creates an FK control driven by the difference between a target and a reference node rotation axis.
    It's purpose is to automate the control behaviour based on an angle.

    Typical use would be a collar, where we want the collar control to move/compensate/rotate based on the
    rotation/orientation of the neck. 
    A shirt-end control that would need to react to the legs.
    A shirt sleeve that needs to react to elbow rotation or wrist rotation.
    Some rigid armor plates that would need to slide along an underlying geometry based on some motion...
    
    The module will create an animation curve between the extracted axis and the driver node (aka setDrivenKey).
    Riggers can manipulate those animation curves to tweak the automated behaviour of the control. 
    
    Attributes:
    Input
        name: (str) construction name with no suffix (used to name nodes created by this module)
        target: (str) read the value of this node
        reference: (str) compare target's value with this node
        maintain_offset: (bool) True to set eventual rotation offset between target and reference as the default value
        axis_data:(dict) dict = {(str)axis to read :(str|tuple|list) axis to drive}

    Output
        buffer: (PyNode) buffer/NULL top transform of the setup


    Example:
    from rig_zone.usr.ggilbaud.modules import fkdrivenbyangle
    fk_driven = fkdrivenbyangle.FkDrivenByAngle()

    fk_driven.name       = 'l_collarFront'
    fk_driven.target     = 'c_neck_0_JNT'
    fk_driven.reference  = 'c_chest_0_JNT'
    fk_driven.axis_data  = {'x':'tx', 'y':('ty', 'ry'), 'z':['tz','rz']}
                         -> rotation x difference between target and reference will drive translateX of the FK control
                         -> rotation y difference between target and reference will drive translateY and rotateY
                         of the FK control
                         -> rotation z difference between target and reference will drive translateZ and rotateZ
                         of the FK control

    fk_driven.build()

    print fk_driven.__dict__
    # Result: {'_target': 'c_neck_0_JNT',
               '_reference': 'c_chest_0_JNT',
               '_name': 'l_collarFront',
               '_maintain_offset': True,
               '_axis_data': {'y': ('ty', 'ry'), 'x': 'tx', 'z': ['tz', 'rz']},
               'buffer': nt.Transform(u'l_collarFront_NULL'),
               '_output_data': nt.Transform(u'l_collarFront_DATA')}
    """

    def __init__(self):
        # Input attributes
        self._name = None
        self._target = None
        self._reference = None
        self._maintain_offset = None
        self._axis_data = None

        # Output attributes
        self._buffer = None
        self._driver = None
        self._output_data = None

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
    def maintain_offset(self):
        return self._maintain_offset

    @maintain_offset.setter
    def maintain_offset(self, value):
        self._maintain_offset = value

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
    def buffer(self):
        return self._buffer

    @property
    def driver(self):
        return self._driver

    @driver.setter
    def driver(self, value):
        self._driver = value

    def build(self):
        """
        Module builder.
        
        Returns: success
        """

        if not self.target:
            log.error('target property is not set or object don\'t exists. Abort.')
            return
        if not self.reference:
            log.error('reference property is not set or object don\'t exists. Abort.')
            return
        if not self.axis_data:
            log.error('axis_data property not set. Abort.')
            return

        # Build dag
        if not pm.objExists('{0}_DRV'.format(self.name)):
            self.build_dag()
        else:
            self.driver = pm.PyNode('{0}_DRV'.format(self.name))
            self._buffer = pm.PyNode('{0}_NULL'.format(self.name))

        # Build RotationReader
        rot_reader_output_data, rot_reader_maya_data = self.build_rotation_reader()

        # Connect RotationReader to dag
        self.connect_rotation_reader_to_driver_dag(rot_reader_output_data, rot_reader_maya_data)

        return log.info('{0} built succesfully!'.format(self.__class__.__name__))

    def build_dag(self):
        """
        Creates module's dag nodes and hierarchy.
        
        Returns:(PyNode Transform or None) buffer/NULL top group
        """

        self._buffer = pm.createNode('transform', n='{0}_NULL'.format(self.name), skipSelect=True)
        self.driver = pm.createNode('transform', n='{0}_DRV'.format(self.name), skipSelect=True)
        con = pm.circle(n='{0}_CON'.format(self.name), constructionHistory=False)[0]
        jnt = pm.joint(n='{0}_JNT'.format(self.name))
        jnt.setParent(con)
        con.setParent(self.driver)
        self.driver.setParent(self._buffer)

        return self._buffer

    def build_rotation_reader(self):
        """
        Creates a RotationReader module from this instance input attributes to extract axis rotation value differences
        between target and reference nodes. If target and reference matrix are not identical it will ensure
        the offset is maintain through the RotationReader.
        
        Returns: (RotationReader instance) output attributes
        """

        # Check for an offset between target and reference
        target_local_matrix = transforms.get_matrix_offset(self.reference, self.target)
        if target_local_matrix == om.MMatrix.kIdentity:
            self.maintain_offset = False
        else:
            self.maintain_offset = True

        # Build rotation reader module
        rot_reader = rotationreader.RotationReader()
        rot_reader.name = self.name
        rot_reader.target = self.target
        rot_reader.reference = self.reference
        rot_reader.axis = [key for key in self.axis_data.keys() if self.axis_data.get(key)]
        rot_reader.maintain_offset = self.maintain_offset

        rot_reader.build()

        return rot_reader.output_data, rot_reader.maya_data

    def connect_rotation_reader_to_driver_dag(self, rot_reader_output_data, rot_reader_maya_data):
        """
        Connects the output of a RotationReader to the driver node's axis to drive via an anim curve (setDriven Key).
        Args:
            rot_reader_output_data: (RotationReader instance) output data dictionary
            rot_reader_maya_data: (RotationReader instance) RotationReader maya metadata node
        """

        # Store driver dag to the RotationReader maya metadata node
        rot_reader_maya_data.drive.unlock()
        self.driver.message >> rot_reader_maya_data.drive
        rot_reader_maya_data.drive.lock()

        # Connect rotation reader output to driver dag node
        for driver_axis in self.axis_data.iterkeys():
            driven_plug = list()
            if self.axis_data.get(driver_axis):
                driver_plug = '{0}.outputRotate{1}'.format(rot_reader_output_data['extracted_{0}'.format(driver_axis)],
                                                           driver_axis.upper())

                if isinstance(self.axis_data.get(driver_axis), basestring):
                    driven_plug.append('{0}.{1}'.format(self.driver, self.axis_data.get(driver_axis)))

                elif isinstance(self.axis_data.get(driver_axis), collections.Iterable):
                    driven_plug.extend(['{0}.{1}'.format(self.driver, val) for val in self.axis_data.get(driver_axis)])

            if driven_plug:
                for driven in driven_plug:
                    for driver_val, val in zip((-90, 0, 90), (-1, 0, 1)):
                        pm.setDrivenKeyframe(driven,
                                             currentDriver=driver_plug,
                                             driverValue=driver_val,
                                             value=val,
                                             inTangentType='spline',
                                             outTangentType='spline',
                                             )

                    anim_curve = pm.PyNode(driven).inputs()[0]
                    anim_curve.setInTangentType(1, 'linear')
                    anim_curve.setOutTangentType(1, 'linear')
                    anim_curve.setPreInfinityType('linear')
                    anim_curve.setPostInfinityType('linear')
                    pm.rename(anim_curve, '{0}_drive{1}_ANC'.format(self.driver.rpartition('_')[0],
                                                                    driven.rpartition('.')[2].upper()
                                                                    ))
                    # log.info('{0}.rotate{1} drives {2}'.format(self.target, driver_axis.upper(), driven))

    def add_driver_connections(self, driver, axis_data):
        """
        Use this function to add one or more axis connections to an existing FkDrivenByAngle setup using the same target
        and reference nodes.
        
        :param driver: (str) name of the driver node you want to add connections to
        :param axis_data: (dict) dict = {(str)axis to read :(str|tuple|list) axis to drive}
        
        Examples:
        You have already built a FkDrivenByAngle setup to extract the rotateY axis value of a target and a reference
        node and drive the translateX and translateY axis of the FkDrivenByAngle driver node.
        Later on you realize that you would also need to extract the rotateZ value and drive rotateX with it.
        
        Instead of building a whole neu FkDrivenByAngle setup to extract the rotateZ value, you can call this function
        to add it to the already existing setup. This makes sure you only use the strict minimum number of nodes needed,
        improving the performance and making the file lighter, faster to open.
        
        from rig_zone.usr_ggilbaud.modules import fkdrivenbyangle
        fk_driven = fkdrivenbyangle.FkDrivenByAngle()
        fk_driven.add_driver_connections('l_wrist_DRV', {'z':'rx'})
        """

        if not pm.objExists(driver):
            log.error('Wrong argument. {0} node doesn\'t exists. Abort.'.format(driver))
            return

        self.axis_data = axis_data
        if not self.axis_data:
            return
        driver_axis = [key for key in self.axis_data.keys()]

        driver = pm.PyNode(driver)
        maya_data = driver.outputs(type='network')[0] if not None else None
        if not maya_data:
            log.error('{0} is not a driver node. Abort.'.format(driver))
            return

        rot_reader = rotationreader.RotationReader.add_axis(maya_data, driver_axis)
        self.connect_rotation_reader_to_driver_dag(rot_reader.output_data, rot_reader.maya_data)

        for key, val in axis_data.iteritems():
            log.info('{0} successfully added connections from {1} {2} axis'
                     ' to {3} {4} axis!'.format(self.__class__.__name__,
                                                rot_reader.__class__.__name__,
                                                key,
                                                driver,
                                                val))




