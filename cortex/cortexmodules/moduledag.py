"""
Abstract class for modules that build dag nodes.
"""

import maya.cmds as cmds
from ..cortexmodules import modulebase


class ModuleDag(modulebase.ModuleBase):

    def __init__(self, name):
        super(ModuleDag, self).__init__(name)

        self._structure = None

        # Output attributes
        self.module_group = modulebase.ModuleAttribute()
        self.no_inherit_group = modulebase.ModuleAttribute()
        self.parent = modulebase.ModuleAttribute()

    def build(self):

        module_group = cmds.createNode('transform', n='{0}_module'.format(self.name.value), skipSelect=True)
        no_inherit_group = cmds.createNode('transform', n='{0}_noInherit'.format(self.name.value), skipSelect=True)
        self.module_group.value = module_group
        self.no_inherit_group.value = no_inherit_group

    def deserialize(self):
        pass