
from ..cortexmodules import modulebase
from ..cortexapi.rig import control
import maya.cmds as cmds


class Master(modulebase.ModuleBase):

    def __init__(self, name):
        super(Master, self).__init__(name)

        # output attributes
        self.master_group = modulebase.ModuleAttribute()
        self.rig_modules = modulebase.ModuleAttribute()
        self.rig_no_inherit = modulebase.ModuleAttribute()
        self.geo_group = modulebase.ModuleAttribute()

    def build(self):

        master_group = cmds.createNode('transform', n='Master', skipSelect=True)
        rig_group = cmds.createNode('transform', n='Rig', skipSelect=True)
        geo_group = cmds.createNode('transform', n='Geometry', skipSelect=True)
        cmds.parent(rig_group, master_group)
        cmds.parent(geo_group, master_group)

        placer_con = control.Control.create('placer_CON')
        placer_con.shape.from_library('master')
        placer_offset_con = control.Control.create('placerOffset_CON')
        placer_offset_con.shape.from_library('placer')
        root_con = control.Control.create('root_CON')
        root_con.shape.from_library('circle')

        cmds.parent(root_con, placer_offset_con)
        cmds.parent(placer_offset_con, placer_con)
        cmds.parent(placer_con, rig_group)

        rig_modules = cmds.createNode('transform', n='Rig_modules', skipSelect=True)
        rig_no_inherit = cmds.createNode('transform', n='Rig_no_inherit', skipSelect=True)

        cmds.parent(rig_modules, root_con)
        cmds.parent(rig_no_inherit, rig_group)
        cmds.setAttr('{0}.inheritsTransform'.format(rig_no_inherit), 0)

        # Set output attributes
        self.master_group.value = master_group
        self.rig_modules.value = rig_modules
        self.rig_no_inherit.value = rig_no_inherit
        self.geo_group.value = geo_group

