import maya.cmds as cmds
import json
import os

DATA_PATH = "E:\PROD\AUTORIG_PROD_TEMPLATE\assets\characters\template_biped\RIG\WORK\DATA"


class Base(object):

    def __init__(self, name):
        self.input = None
        self.output = None
        self.name = name

    def start(self):
        pass

    def build(self):
        pass

    def connect(self):
        pass

    def serialize(self, module_name, module_attribute, data):

        if not module_attribute:
            return None

        data = json.dumps(data, indent=2)

        module_path = os.path.join(DATA_PATH, module_name)
        if not os.path.isdir(module_path):
            os.mkdir(module_path)

        module_attribute = os.path.join(module_path, '{0}.json'.format(module_attribute))

        with open(module_attribute, 'w+') as handle:
            handle.write(data)

    def deserialize(self, module_name, attribute=None):
        """
        Returns the data from a module_name and a module attribute.
        
        :param module_name: (str) name of a module 
        :param attribute: (str) name of a module attribute  
        
        :return: 
        """
        if not attribute:
            return None

        module_path = os.path.join(DATA_PATH, module_name)
        if not os.path.isdir(module_path):
            return None

        attribute_path = os.path.join(module_path, '{0}.json'.format(attribute))
        if not os.path.isfile(attribute_path):
            return None

        return json.load(attribute_path)




