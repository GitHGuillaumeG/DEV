
from ..cortexmodules import moduledag
from ..cortexmodules import modulebase


class Spine(moduledag.ModuleDag):

    def __init__(self, name):
        super(Spine, self).__init__(name)

    def build(self):
        super(Spine, self).build()

    def build_structure(self, version=None):
        pass

    def get_structure_from_file(self):
        pass

    def get_structure_from_scene(self):
        pass
