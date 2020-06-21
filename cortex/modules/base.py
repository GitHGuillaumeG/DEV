# Python lib
import json
import os

# Maya
import maya.cmds as cmds

# Cortex
from ..api import environment


class Base(object):
    """
    Abstract base class of all the modules.
    
    All modules are set by input instance attributes when they are initialized. Most of the modules will also store
    instance output attributes which are usually set during the creation_step of the modules.
    
    Examples:
        # Initialize an fk leg module
        leg_mod = fk.FK('leg', objects = ('thigh','knee','ankle'))
        
        # Runs the start creation_step of the leg module and get its start_data 
        leg_mod.start()
        print(leg_mod.start_data)
        # Result : #
    
    Every module can implement creation_step functions (start, build and connect) which are used to create a module
    from zero to a fully built and connected module.
    
    start creation_step : can be seen as the "guide" step. Where you will position objects in space to define pivot
    points and set a hierarchy.
    
    build creation step : takes the objects from the start creation_step as inputs and builds a set of instructions,
    controls, joints, special rig functionality...
    
    connect creation step : handles the connection of the module with other modules, space switching... Deformer modules
    such as skinCluster could also use the connect step to load weights.
    
    
    Modules are built in a specific order which is the responsibility of the rigger. For example, when loading skin
    weights on a deformerSkin module, you should make sure that the joints used for the skinCLuster have been built
    already.
    
    The abstract base class implements serialization and deserialization of data, which is used to save and load data 
    per module and per module_step. This makes it possible to rebuild just a specific module (even just a specific
    module step) if needed, rather than having to rebuild a whole rig, as long as eventual dependencies are taken
    care of.
    
    """

    def __init__(self, name):

        # input attributes
        self.name = name

        # output attributes
        self.start_data = dict()
        self.build_data = dict()
        self.connect_data = dict()

    def start(self):
        pass

    def build(self):
        pass

    def connect(self):
        pass

    def serialize(self, module_step=None, data=None):
        """
        Saves/Writes a module's data on disk.

        module_step should be set to start, build or connect. 

        :param module_step: (str) the module step (start, build, connect) 
        :param data: (dict) the data to write on disk

        :return: (str, dict) module step, data
        """

        if not module_step or not data:
            return None

        data = json.dumps(data, indent=2)

        module_path = os.path.join(environment.Environment.data_path, self.name)
        if not os.path.isdir(module_path):
            os.mkdir(module_path)

        module_step = os.path.join(module_path, '{0}.json'.format(module_step))

        with open(module_step, 'w+') as handle:
            handle.write(data)

        return module_step, data

    def serialize_start_data(self, guides):
        """
        Gets the start guides data in a dictionary (matrix, hierarchy) and calls serialise function to save that data
        on disk.
        
        :param guides: (iterable) objects to serialize
        :return (dict) {'guide0':
                            {'matrix':[],
                             'hierarchy': ''
                             },
                        'guide1':
                            {'matrix':[],
                             'hierarchy': ''
                             },
                        ...
                        }
        """

        for guide in guides:
            mat = cmds.xform(guide, q=True, worldSpqce=True, matrix=True)
            parent = cmds.listRelatives(guide, parent=True)[0]
            self.start_data[guide]['matrix'] = mat
            self.start_data[guide]['hierarchy'] = parent

        self.serialize(module_step='start', data=self.start_data)

        return self.start_data

    def serialize_build_data(self):
        pass

    def serialize_connect_data(self):
        pass

    def deserialize(self, module_name, attribute=None):
        """
        Returns the data from a module_name and a module attribute.
        
        :param module_name: (str) name of a module 
        :param attribute: (str) name of a module attribute  
        
        :return: 
        """
        if not attribute:
            return None

        data_path = environment.Environment.data_path
        print (data_path, type(data_path))
        module_path = os.path.join(data_path, module_name)
        if not os.path.isdir(module_path):
            return None

        attribute_path = os.path.join(module_path, '{0}.json'.format(attribute))
        if not os.path.isfile(attribute_path):
            return None

        return json.load(attribute_path)




