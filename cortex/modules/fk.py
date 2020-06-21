# Python lib
import collections

# Maya
import maya.cmds as cmds

# Cortex
from .base import Base
from ..rigobject.control import Control


class FkTest(Base):

    def __init__(self, module_name, objects):
        super(FkTest, self).__init__(module_name)

        # input attributes
        if isinstance(objects, str):
            self.objects = (objects,)
        elif isinstance(objects, collections.Iterable):
            self.objects = tuple(objects)
        else:
            self.objects = ('fk_0', )

        # stored attributes
        self.guides_data = self.deserialize(self.name, 'guides') if not None else dict()

        # output attributes
        self.guides = None
        self.output = None

    def start(self):
        """
        Creates the guides locators for the module. Retrieves matrix and parent from stored data.
         
        :return: 
        """
        super(FkTest, self).start()

        for object_name in self.objects:
            guide_object = cmds.spaceLocator(name='{0}_GUIDE'.format(object_name))
            self.guides.append(guide_object)

            # Retrieve guide's position from stored data
            if object_name in self.guides_data.keys():
                cmds.xform(guide_object, worldSpace=True, matrix=self.guides_data[object_name]['matrix'])

        # Retrieve guide's parent from stored data
        for object_name in self.objects:
            if object_name in self.guides_data.keys():
                cmds.parent('{0}_GUIDE'.format(object_name), self.guides_data[object_name]['parent'])

    def build(self):
        """
        
        :return: 
        """
        if not self.guides:
            print('no start objects found,  abort.')
            return

        for guide in self.guides:
            ctl = Control.create(guide.replace('_GUIDE', '_CTL'))
            ctl.set_shape_from_library('square')
            ctl.add_buffer()
            ctl.add_joint()


def run(name, guides_name):

    fk_mod = FkTest(name, guides_name)

    # Creates guides and retrieves matrix and parent information from the stored module data (if data exists)
    fk_mod.start()

    # Store guides matrix and parent information as module data
    fk_mod.serialize_start_data(fk_mod.guides)

    # Builds
    fk_mod.build()



