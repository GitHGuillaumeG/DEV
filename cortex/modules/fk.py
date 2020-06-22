# Python lib
import collections

# Maya
import maya.cmds as cmds

# Cortex
from .base import Base
from ..rigobject.control import Control


class Fk(Base):

    def __init__(self, module_name, objects):
        super(Fk, self).__init__(module_name)

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

        super(Fk, self).start()

        for object_name in self.objects:
            guide_object = cmds.spaceLocator(name='{0}_GUIDE'.format(object_name))[0]
            self.guides.append(guide_object)

            # Retrieve guide's position from stored data
            if guide_object in self.start_data.keys():
                cmds.xform(guide_object, worldSpace=True, matrix=self.start_data[guide_object]['matrix'])

        # Retrieve guide's parent from stored data
        for guide_object in self.guides:
            if guide_object in self.start_data.keys():
                parent = self.start_data[guide_object]['hierarchy']
                if not parent == 'world':
                    cmds.parent(guide_object, parent)

    def build(self):
        """
        
        :return: 
        """
        super(Fk, self).build()

        if not self.guides:
            print('no start objects found,  abort.')
            return

        for guide in self.guides:
            ctl = Control.create(guide.replace('_GUIDE', '_CTL'))
            ctl.set_shape_from_library('square')
            ctl.add_buffer()
            ctl.add_joint()

    def connect(self):
        super(Fk, self).connect()


def run(name, objects):

    fk_mod = Fk(name, objects)

    # Creates guides and retrieves matrix and parent information from the stored module data (if data exists)
    fk_mod.start()

    # Store guides matrix and parent information as module data
    fk_mod.serialize_start_data(fk_mod.guides)

    # Builds
    fk_mod.build()



