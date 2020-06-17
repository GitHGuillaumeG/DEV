import logging
import collections

from EXTERNAL.DEV_reel.ggilbaud import transforms

import pymel.core as pm

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

VALID_AXIS = ('x', 'y', 'z')


class RotationReader(object):
    """
    This module builds a dg node network to extract an axis rotation value between a target and a reference node using
    quaternions.
    
    Attributes:
    Inputs
    name: (str) construction name with no suffix (used to name nodes created by this module)
    target: (str) read the value of this node
    reference: (str) compare target's value with this node
    axis: (str|tuple|list) rotation axis to read
    maintain_offset: (bool) True to set an initial rotation offset between target and reference as the default value
    
    Outputs
    data_node: (dict) dict={matrix_info=PyNode DecomposeMatrix or None,
                            extracted_x=PyNode QuatToEuler or None,
                            extracted_y=PyNode QuatToEuler or None,
                            extracted_z=PyNode QuatToEuler or None}
    maya_node: (PyNode Network) metadata of the module  

    Example:
    Extract the rotateX value difference between the wrist joint and the elbow joint.
    >>
    from rig_zone.usr.ggilbaud.modules import rotationreader
    rot_reader = rotationreader.RotationReader()
    
    rot_reader.name = 'l_wrist'
    rot_reader.target = 'l_wrist_0_JNT'
    rot_reader.reference = 'l_elbow_0_JNT'
    rot_reader.axis = 'x'       
    # rot_reader.axis = ('y','z') -> axis can be passed as a tuple
    # rot_reader.axis = ['x', 'z'] -> axis can be passed as a list
    rot_reader.build()
    
    # Result:
    The quatToEuler node at the end of the dg network created holds the rotateX axis difference between l_wrist_0_JNT
    and l_elbow_0_JNT.
    
    >>
    print rot_reader.maya_data
    # Result: Prints out the name of the rotation reader meatadata node
    
    >>
    print rot_reader.__dict__
    # Result: {' _target': 'l_wrist_0_JNT',
               '_reference': 'l_elbow_0_JNT',
               '_name': 'l_wrist',
               '_axis': ['x'],
               '_maintain_offset': False,
               '_output_data': {'matrix_info':nt.DecomposeMatrix(u'l_wrist_localSpaceInfo_DMAT')
                                'extracted_x':nt.QuatToEuler(u'l_wrist_extractRotX_QTE'),
                                'extracted_y':None,
                                'extracted_z':None)}
               '_maya_data': nt.Network(u'l_wrist_DATA_NTE')
               }
    """

    def __init__(self):
        # Input attributes
        self._name = None
        self._target = None
        self._reference = None
        self._axis = None
        self._maintain_offset = False

        # Output attributes
        self._output_data = dict(matrix_info=None, extracted_x=None, extracted_y=None, extracted_z=None)
        self._maya_data = None

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
    def axis(self):
        return self._axis

    @axis.setter
    def axis(self, value):
        is_valid = self.get_valid_axis(value)
        if not is_valid:
            log.warning('No valid axis found. Default to None.')
            self._axis = None
        else:
            self._axis = is_valid

    @property
    def maintain_offset(self):
        return self._maintain_offset

    @maintain_offset.setter
    def maintain_offset(self, value):
        self._maintain_offset = value

    @property
    def output_data(self):
        return self._output_data

    @output_data.setter
    def output_data(self, value):
        self._output_data = value

    @property
    def maya_data(self):
        return self._maya_data

    @maya_data.setter
    def maya_data(self, value):
        self._maya_data = value

    def build(self):
        """
        Module builder.
        """

        self.get_local_space()
        self.extract_value()
        self.to_maya_data_node()

        log.info('{0} built succesfully!'.format(self.__class__.__name__))

    def get_local_space(self):
        """
        Creates dg nodes to get the matrix of target in the space of reference.
        If maintain_offset is True, the calculation will preserve the eventual axis offset between the two nodes and 
        consider this offset as the zero default state.
        """

        if not self.target:
            log.error('target property is nto set. Abort.')
            return
        if not self.reference:
            log.error('reference property is nto set. Abort.')
            return

        if not self.output_data['matrix_info']:
            local_space = pm.createNode('multMatrix', n='{0}_toLocal_MMAT'.format(self.name), skipSelect=True)
            local_space_info = pm.createNode('decomposeMatrix',
                                             n='{0}_localSpaceInfo_DMAT'.format(self.name),
                                             skipSelect=True
                                             )
            self.output_data['matrix_info'] = local_space_info

            start_index = 0
            if self.maintain_offset:
                offset = transforms.get_matrix_offset(self.reference, self.target)
                local_space.matrixIn[0].set(offset, type='matrix')
                start_index = 1

            target = pm.PyNode(self.target)
            reference = pm.PyNode(self.reference)
            target.worldMatrix[0] >> local_space.matrixIn[start_index]
            reference.worldInverseMatrix[0] >> local_space.matrixIn[start_index + 1]
            local_space.matrixSum >> local_space_info.inputMatrix

    def extract_value(self):
        """
        Extracts axis euler rotation value between target and reference from the output quaternion of matrix_info.
        """

        if not self.output_data['matrix_info']:
            log.error('matrix_info class attribute not set. Abort.')
            return
        if not self.axis:
            log.error('axis class attribute not set. Abort.')
            return

        for axis in self.axis:
            if axis == 'x' and not self.output_data['extracted_x'] or axis == 'y' and not self.output_data['extracted_y']\
             or axis == 'z' and not self.output_data['extracted_z']:
                quat_to_euler = pm.createNode('quatToEuler',
                                              n='{0}_extractRot{1}_QTE'.format(self.name, axis.upper()),
                                              skipSelect=True)

                src_plug = ('outputQuat.outputQuat{0}'.format(axis.upper()), 'outputQuat.outputQuatW')
                dest_plug = ('inputQuat.inputQuat{0}'.format(axis.upper()), 'inputQuat.inputQuatW')
                for src, dest in zip(src_plug, dest_plug):
                    pm.PyNode('{0}.{1}'.format(self.output_data['matrix_info'], src)) >>\
                     pm.PyNode('{0}.{1}'.format(quat_to_euler, dest))

                # Prevent flipping at 90 degrees by setting the extracted axis to be the last in the chain of
                # rotate order
                if axis == 'x':
                    quat_to_euler.inputRotateOrder.set(0)
                    self._output_data['extracted_x'] = quat_to_euler
                elif axis == 'y':
                    quat_to_euler.inputRotateOrder.set(1)
                    self._output_data['extracted_y'] = quat_to_euler
                else:
                    quat_to_euler.inputRotateOrder.set(2)
                    self._output_data['extracted_z'] = quat_to_euler

    @staticmethod
    def get_valid_axis(axis):
        """
        Checks and returns axis if it is valid. To be valid, axis should be either a string, a tuple or a list
        made of : 'x','y','z'.

        Example :
        from rig_zone.usr.ggilbaud.modules.rotationreader import RotationReader as rotReader
        rotReader().get_valid_axis('x')                -> return ['x']
        rotReader().get_valid_axis(('x', 'y'))         -> return ['x','y']
        rotReader().get_valid_axis(['x', 'y'])         -> return ['x','y']
        rotReader().get_valid_axis(['x', 'w', 'q'])    -> return ['x']

        :param axis: (str|tuple|list) axis to check

        :return: (list) valid axis
        """

        axis_to_check = list()
        if isinstance(axis, basestring):
            axis_to_check.append(axis)
        elif isinstance(axis, collections.Iterable):
            axis_to_check.extend(axis)
        else:
            log.error('axis argument should be a tuple, a list or a string made of "x", "y", "z"')
            return

        valid_axis = list()
        for axis in axis_to_check:
            if axis not in VALID_AXIS:
                log.warning('{0} is not a valid axis, it will be ignored. See help for details.'.format(axis))
            else:
                valid_axis.append(axis)
        return valid_axis if valid_axis else None

    def to_maya_data_node(self):
        """
        Creates and sets a maya metadata object to keep track of relevant nodes created by this module.
        It is used to retrieve data from the maya scene and add new output connections to an existing RotationReader
        setup instead of creating a new one. This will prevent the creation of nodes that are already there
        and instead re-use the existing ones. 

        :return: (PyNode Network) metadata node  
        """

        if not pm.objExists('{0}_rotReader_DATA'.format(self.name)):
            self.maya_data = pm.createNode('network', n='{0}_rotReader_DATA'.format(self.name), skipSelect=True)
            pm.addAttr(self.maya_data, longName='constructor_name', dataType='string')
            pm.addAttr(self.maya_data, longName='matrix_info', attributeType='message')
            pm.addAttr(self.maya_data, longName='extracted_x', attributeType='message')
            pm.addAttr(self.maya_data, longName='extracted_y', attributeType='message')
            pm.addAttr(self.maya_data, longName='extracted_z', attributeType='message')
            pm.addAttr(self.maya_data, longName='drive', attributeType='message')

        else:
            self.maya_data = pm.PyNode('{0}_rotReader_DATA'.format(self.name))

        self.maya_data.constructor_name.unlock()
        self.maya_data.constructor_name.set(self.name)
        self.maya_data.constructor_name.lock()

        if self.output_data['matrix_info']:
            self.maya_data.matrix_info.unlock()
            self.output_data['matrix_info'].message >> self.maya_data.matrix_info
            self.maya_data.matrix_info.lock()

        if self.output_data['extracted_x']:
            self.maya_data.extracted_x.unlock()
            self.output_data['extracted_x'].message >> self.maya_data.extracted_x
            self.maya_data.extracted_x.lock()

        if self.output_data['extracted_y']:
            self.maya_data.extracted_y.unlock()
            self.output_data['extracted_y'].message >> self.maya_data.extracted_y
            self.maya_data.extracted_y.lock()

        if self.output_data['extracted_z']:
            self.maya_data.extracted_z.unlock()
            self.output_data['extracted_z'].message >> self.maya_data.extracted_z
            self.maya_data.extracted_z.lock()

        return self.maya_data

    @classmethod
    def add_axis(cls, maya_data, axis):
        """
        Use this function to add one or more axis output to an existing RotationReader setup.
        
        :param maya_data: (str) name of a RotationReader metadata Maya node for which you'd like to output an axis
        :param axis: (str|tuple|list) axis to add
        
        Example:
        You have already built a RotationReader to extract the rotateY axis value of a target and a reference node.
        Later on you realize that you would also need to extract the rotateZ value.
        Instead of building a whole neu RotationReader setup to extract the rotateZ value, you can call this function
        to add it to the already existing setup. That way you'll use only the strict minimum number of nodes that you
        need,improving the performance of the rig and making the file size smaller.
        
        The parameter maya_data is a metadata dg network node that lives in your maya scene and should be named like
        this : nameOfYourModule_rotReader_DATA
        
        >>
        from rig_zone.usr_ggilbaud.modules import rotationreader
        rot_reader = rotationreader.RotationReader()
        
        rot_reader.add_axis('l_wrist_rotReader_DATA', 'z')
        
        :return: new RotationReader instance
        """

        if not pm.objExists(maya_data):
            log.error('{0} metadata node doesn\'t exists. Abort.')
            return
        maya_data_node = pm.PyNode(maya_data)

        constructor_name_from_maya = maya_data_node.constructor_name.get()
        matrix_info_from_maya = maya_data_node.matrix_info.get()
        if axis == 'x' and maya_data_node.extracted_x.get()\
                or axis == 'y' and maya_data_node.extracted_y.get()\
                or axis == 'z' and maya_data_node.extracted_z.get():
            return
        else:
            extracted_x_from_maya = maya_data_node.extracted_x.get()
            extracted_y_from_maya = maya_data_node.extracted_y.get()
            extracted_z_from_maya = maya_data_node.extracted_z.get()
            axis = axis

        rot_reader = cls()
        rot_reader.name = constructor_name_from_maya
        rot_reader.axis = axis
        rot_reader.output_data['matrix_info'] = matrix_info_from_maya
        rot_reader.output_data['extracted_x'] = extracted_x_from_maya
        rot_reader.output_data['extracted_y'] = extracted_y_from_maya
        rot_reader.output_data['extracted_z'] = extracted_z_from_maya

        rot_reader.extract_value()
        rot_reader.to_maya_data_node()

        log.info('axis {0} added succesfully to {1}!'.format(axis, cls.__name__))

        return rot_reader
