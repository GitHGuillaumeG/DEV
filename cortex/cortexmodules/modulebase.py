"""
Abstract class for all modules.
"""

# from ..cortexcore import asset
# import maya.cmds as cmds


class ModuleBase(object):

    def __init__(self, name):
        # super(ModuleBase, self).__init__()
        self.name = ModuleAttribute(name)

        self.environment = None

    def __setattr__(self, key, value):
        """
        x.__setattr__('name', value) <==> x.name = value
        Args:
            key (str): attribute name
            value (object): attribute value
        """
        super(ModuleBase, self).__setattr__(key, value)
        if isinstance(value, ModuleAttribute):
            # Store the module instance on the attribute.
            value._module = self

    def serialize(self):

        module_attributes = dict()
        for key, value in self.__dict__.iteritems():
            if isinstance(value, ModuleAttribute):
                module_attributes[key] = value

        return module_attributes

    def deserialize(self):

        print 'deserialize'


class ModuleAttribute(object):
    def __init__(self, *args):

        self._value = args[0] if len(args) == 1 else None
        self._module = None

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, val):

        self._value = val

    @property
    def module(self):
        """
        Returns the module the attribute belongs to.
        Returns:
            cortex module: module instance
        """
        return self._module

    @property
    def module_name(self):
        """
        Returns the name of the module the attribute belongs to.
        Returns:
            str: module name
        """
        return None if self._module is None else self._module.name
