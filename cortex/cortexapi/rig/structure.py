import os

from maya.api import OpenMaya as om

from ..rig import base


def get_structure_data_from_maya_scene():
    """
    Get the structure data from a Maya scene into a dictionary.
    Examples :
    structure = {'Root_C':{
                        'parent':'',
                        'matrix': [om.MMatrix],
                        'nodes':['Root_C_0'],
                        },
                'Spine_C':{
                        'parent':'Root_C_0',
                        'matrix': [om.MMatrix, om.MMatrix, om.MMatrix, om.MMatrix],
                        'nodes':['Spine_C_0', 'Spine_C_1', 'Spine_C_2', 'Spine_C_3'],
                        },
    }
    Returns: structure dictionary
    """
    structure = {}
    # Iterate through the Dag
    iter_dag = om.MItDag()
    while not iter_dag.isDone():
        item = iter_dag.currentItem()
        # Only consider nodes of type kJoint
        if item.hasFn(om.MFn.kJoint):
            node = base.Base(om.MFnDagNode(item).partialPathName())
            dag_node = node.m_dag_node

            # Add the node's module name to the structure dictionary if not present already
            module_id = dag_node.name().partition('_')[0]
            split_temp = dag_node.name().partition('_')[2]
            module_side = split_temp.partition('_')[0]
            module_name = '{0}_{1}'.format(module_id, module_side)

            if module_name not in structure:
                structure[module_name] = {'nodes': [], 'matrix': [], 'parent': ''}
            structure[module_name]['nodes'].append(dag_node.name().rpartition('_')[0])

            # Add the node's worldMatrix information to the module's dictionary
            world_matrix = node.m_dagpath.inclusiveMatrix()
            structure[module_name]['matrix'].append(tuple(world_matrix))

            # Add parent module information
            parent_m_object = dag_node.parent(0)
            parent_dag_node = om.MFnDagNode(parent_m_object)
            parent_module_name = parent_dag_node.name().partition('_')[0]
            if parent_module_name != module_name.partition('_')[0]:
                structure[module_name]['parent'] = parent_dag_node.name()

        iter_dag.next()
    return structure

