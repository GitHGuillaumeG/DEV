
from ..cortexmodules import master
import maya.cmds as cmds

import collections
import logging

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class Asset(object):

    def __init__(self):
        self.environment = None

        self._modules = collections.OrderedDict()

    @property
    def modules(self):
        """
        Returns all modules of the asset as a dictionary -> module.name : module instance
        """

        return self._modules

    def get_module(self, name):
        """
        Returns the instance of a module from its name or None if the module doesn't exist on the asset.
        Args:
            name (str): name of a module

        Returns:
            module instance
        """

        for key, value in self._modules.iteritems():
            if key == name:
                return value
        return None

    def has_module(self, name):
        """
        Returns True if the module name exist on asset.
        Returns (bool): True if module name exists
        """

        if self.get_module(name):
            return True
        return False

    def add_module(self, mod):
        """
        Adds a new module to the asset.
        Args:
            mod (class instance): a cortexmodule instance
        """

        # todo check that the module name doesn't exist already
        # todo check that mod is indeed a cortexmodule
        self._modules[mod.name.value] = mod

    def remove_module(self, mod):
        """
        Removes/deletes a module from the asset.
        Args:
            mod (str|cortexmodule instance): name or instance of a cortexmodule 
        """

        to_delete = None
        if isinstance(mod, str):
            to_delete = mod
        if hasattr(mod, 'name'):
            to_delete = mod.name.value

        search_mod = self.get_module(to_delete)
        if search_mod:
            self._modules.pop(to_delete)
        else:
            log.warning('No module named {0} found on the asset, could not delete it.'.format(mod))

    def build(self):
        """
        Builds every modules stored in the asset and parent them in the hierarchy.
        Returns:

        """
        cmds.file(new=True, force=True)

        for mod_name, mod_instance in self.modules.iteritems():
            log.info('Start building module : {0}'.format(mod_name))
            # Build each module
            mod_instance.build()

            # Parent module in the hierarchy
            if hasattr(mod_instance, 'parent'):
                parent = mod_instance.parent.value
                if parent and cmds.objExists(parent):
                    cmds.parent(mod_instance.module_group.value, parent)

                # If no parent has been set and a Master module exist, parent the current module under the Rig_modules
                # group of Master module
                if not parent:
                    for mod in self.modules.itervalues():
                        if isinstance(mod, master.Master):
                            cmds.parent(mod_instance.module_group.value, mod.rig_modules.value)
                            break

            # Parent module no inherit group in the hierarchy
            if hasattr(mod_instance, 'no_inherit_group'):
                for mod in self.modules.itervalues():
                    if isinstance(mod, master.Master):
                        cmds.parent(mod_instance.no_inherit_group.value, mod.rig_no_inherit.value)
                        break

            log.info('Done building module : {0}'.format(mod_name))

    def serialize(self):
        """
        Gets the serialized data of every module in a dictionary. 
        
        Returns (dict): {module.name : {ModuleAttribute : value, ModuleAttribute : value, ...},
                         module.name : {ModuleAttribute : value, ModuleAttribute : value, ...},
                         ...}

        """
        data = collections.OrderedDict()
        for mod_name, mod_instance in self.modules.iteritems():
            data[mod_name] = mod_instance.serialize()
        return data

    def deserialize(self):
        pass


