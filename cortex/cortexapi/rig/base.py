from maya.api import OpenMaya as om


class Base(object):
    """
    Base class for rigging function sets that act on a node.    
    """
    def __init__(self, node):

        self._node = str(node)
        self._m_object = om.MGlobal.getSelectionListByName(self._node).getDependNode(0)
        self._m_handle = om.MObjectHandle(self._m_object)

    def __str__(self):
        """
        Returns the node name as string representation. If the name has changed, it will be
        retrieved from the stored MObject.
        Returns:
            str: String representation of the node name
        """
        # Try to get the MObject of node and return it if it passed
        try:
            om.MSelectionList().add(self._node)
        except RuntimeError:
            # If it didn't pass, check if the node is valid (not deleted), raise an error if not valid.
            if not self._m_handle.isValid():
                raise ValueError('The MObject is not valid anymore.')
            # If the node is valid, its name has changed, retrieve the node name from the MObject
            if self._m_object.hasFn(om.MFn.kDagNode):
                self._node = om.MFnDagNode(self._m_object).partialPathName()
            else:
                self._node = om.MFnDependencyNode(self._m_object).name()
        return self._node

    @property
    def m_object(self):
        """
        Returns node as an MObject
        Returns: (om.MObject) node's MObject
        """

        if not self._m_handle.isValid():
            raise ValueError('The MObject is not valid anymore.')
        return self._m_object


    @property
    def m_dag_node(self):
        """
        Returns node as an MDagNode
        Returns: (om.MDagNode) node's MDagNode
        """

        if not self._m_handle.isValid():
            raise ValueError('The MObject is not valid anymore.')
        if not self._m_object.hasFn(om.MFn.kDagNode):
            raise ValueError('The MObject is not a dag node.')
        return om.MFnDagNode(self._m_object)

    @property
    def m_dagpath(self):
        """
        Returns node as an MDagPath
        Returns: (om.MDagPath) node's MDagPath
        """

        return self.m_dag_node.getPath()

    def get_world_matrix(self):
        """
        Get the world matrix of node
        Returns: (om.MMatrix) world matrix
        """
        '''
        world_matrix_plug = self.m_dagpath.findPlug('worldMatrix', False).elementByLogicalIndex(0)
        world_matrix_attr = world_matrix_plug.asMObject()
        matrix_data = om.MFnMatrixData(world_matrix_attr).matrix()
        
        return matrix_data
        '''
        pass


