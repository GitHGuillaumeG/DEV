# Python lib
import collections

# Maya
import maya.cmds as cmds

# Cortex
from .base import Base


class FkTest(Base):

    def __init__(self, module_name, guides_name):
        super(FkTest, self).__init__(module_name)

        # input attributes
        self.module_name = module_name

        if isinstance(guides_name, str):
            self.guides_name = (guides_name,)
        elif isinstance(guides_name, collections.Iterable):
            self.guides_name = tuple(guides_name)
        else:
            self.guides_name = 'C_error'

        # stored attributes
        self.guides_data = self.deserialize(self.name, 'guides') if not None else dict()

        # output attributes
        self.output = None

    def start(self):
        """
        Creates the guides locators for the module. Retrieves matrix and parent from stored data.
         
        :return: 
        """
        super(FkTest, self).start()

        for guide_name in self.guides_name:
            guide_object = cmds.spaceLocator(name='{0}_GUIDE'.format(guide_name))

            # Retrieve guide's position from stored data
            if guide_name in self.guides_data.keys():
                cmds.xform(guide_object, worldSpace=True, matrix=self.guides_data[guide_name]['matrix'])

        # Retrieve guide's parent from stored data
        for guide_name in self.guides_name:
            if guide_name in self.guides_data.keys():
                cmds.parent('{0}_GUIDE'.format(guide_name), self.guides_data[guide_name]['parent'])

    def build(self):
        """
        
        :return: 
        """
        pass

