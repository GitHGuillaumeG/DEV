
from ..cortexcore import asset
from ..cortexmodules import moduledag
from ..cortexmodules import master
from ..cortexmodules import spine
import maya.cmds as cmds


class MyBiped(asset.Asset):

    def __init__(self):
        super(MyBiped, self).__init__()

        # Modules are built in the order you add them, you're responsible of the building order. Any module that is
        # connected to another one should be added after the module he is dependent of.
        # e.g. we set an arm module attach point to be the last joint of a clavicle module so that the arm follows the
        # clavicle. We must make sure that the clavicle module is added before the arm module so that the last joint of
        # the clavicle module will exist in the scene and the arm module will be able to attach to it.

        # Add the master module
        master_mod = master.Master('Master')
        self.add_module(master_mod)

        # Add the spine module
        spine_mod = spine.Spine('Spine')
        spine_mod.parent = master_mod.rig_modules
        self.add_module(spine_mod)

        # Add the neck module
        neck_mod = moduledag.ModuleDag('Neck')
        self.add_module(neck_mod)

        # Add the head module

        # Add L/R modules
        # clavicle
        # arm
        # hand
        # thumb
        # index
        # middle
        # ring
        # pinky
        # groin
        # leg
        # foot

    def build(self):
        super(MyBiped, self).build()



