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

        # stored module_step attributes
        self.start_data = dict()
        self.build_data = dict()
        self.connect_data = dict()

    def start(self):

        data = self.deserialize(self.name, step='start')
        if data:
            self.start_data = data

    def build(self):

        self.build_data = self.deserialize(self.name, step='build') if not None else dict()

    def connect(self):

        self.connect_data = self.deserialize(self.name, step='connect') if not None else dict()

    def serialize(self, module_attribute=None, module_step=None, data=None):
        """
        Saves/Writes a module's module_step data on disk.
        
        :param module_attribute: (str) name of a module attribute to serialize
        :param module_step: (str) either start, build or connect 
        :param data: (dict) the data to write on disk

        :return: (str, str, dict) module_attribute, module_step, data
        """

        if not module_attribute or not module_step or not data:
            return None

        data = json.dumps(data, indent=2)

        module_data_path = os.path.join(environment.Environment.data_path, self.name)
        if not os.path.isdir(module_data_path):
            os.mkdir(module_data_path)

        module_step = os.path.join(module_data_path, module_step)
        if not os.path.isdir(module_data_path):
            os.mkdir(module_data_path)

        module_attribute_file = os.path.join(module_step, '{0}.json'.format(module_attribute))

        with open(module_attribute_file, 'w+') as handle:
            handle.write(data)

        return module_step, module_attribute, data

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
            self.start_data[guide] = dict(matrix=list(), hierarchy='')

            mat = cmds.xform(guide, q=True, worldSpace=True, matrix=True)
            self.start_data[guide]['matrix'] = mat

            parent = cmds.listRelatives(guide, parent=True)
            if parent:
                self.start_data[str(guide)]['hierarchy'] = parent[0]
            else:
                self.start_data[str(guide)]['hierarchy'] = 'world'

        self.serialize(module_step='start', data=self.start_data)

        return self.start_data

    def serialize_build_data(self):
        pass

    def serialize_connect_data(self):
        pass

    def deserialize(self, module_name, step=None):
        """
        Returns the data from a module_name and a module attribute.
        
        :param module_name: (str) name of a module 
        :param step: (str) name of a module step
        
        :return: 
        """
        print(module_name, step)
        if not step:
            return None

        print 'been here'
        data_path = environment.Environment.data_path
        print (data_path, type(data_path))
        module_path = os.path.join(data_path, module_name)
        if not os.path.isdir(module_path):
            return None

        print 'been there'
        step_path = os.path.join(module_path, '{0}.json'.format(step))
        if not os.path.isfile(step_path):
            return None

        print 'all the way'
        with open(step_path, 'r') as handle:
            return json.load(handle)




