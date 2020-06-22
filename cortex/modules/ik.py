# Python libs
import collections

# Maya
import maya.cmds as cmds

# Cortex
from .base import Base
from ..rigobject.control import Control


class Ik(Base):

    def __init__(self, module_name, objects):
        super(Ik, self).__init__(module_name)

        # input attributes
        if isinstance(objects, str):
            self.objects = (objects,)
        elif isinstance(objects, collections.Iterable):
            self.objects = tuple(objects)
        else:
            self.objects = ('fk_0', )

        # output attributes
        self.guides = list()

    def start(self):
        """
        Creates the guides locators for the module. Retrieves matrix and hierarchy from stored data.

        """

        super(Ik, self).start()

        for object_name in self.objects:
            guide_object = cmds.spaceLocator(name='{0}_GUIDE'.format(object_name))[0]
            self.guides.append(guide_object)

            # Retrieve guide's position from stored data
            if object_name in self.start_data.keys():
                cmds.xform(guide_object, worldSpace=True, matrix=self.start_data[object_name]['matrix'])

        # Retrieve guide's parent from stored data
        for object_name in self.objects:
            if object_name in self.start_data.keys():
                cmds.parent('{0}_GUIDE'.format(object_name), self.start_data[object_name]['parent'])

    def build(self):
        super(Ik, self).build()

    def connect(self):
        super(Ik, self).connect()