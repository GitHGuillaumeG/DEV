import os
import json
import logging

from ..rig import structure

CONTROLSHAPE_DIR = 'E:/DEV/cortex/cortexlibrary/controlshapes/'
ASSET_MODULES_DIR = 'rigging/data/modules/'

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class Path(str):

    def __init__(self):
        super(Path, self).__init__()
        self._path = None

    @property
    def path(self):
        return self._path

    @path.setter
    def path(self, value):

        # check for a valid path
        if not os.path.exists(value):
            log.warning('{0} path does not exists on disk.'.format(value))
        self._path = os.path.normpath(value).replace(os.sep, '/')

    def to_json(self, data):
        """
        Exports data to json file path
        Args:
            data (dict): dictionary of data
        """

        data = json.dumps(data, indent=2)
        with open(self.path, 'w+') as handle:
            handle.write(data)

    def from_json(self):
        """
        Imports data from json file path    
        Args:
            path (str): path to file 
    
        Returns:
            data (dict): data from file
        """

        with open(self.path, 'r') as handle:
            return json.load(handle)

    def get_controlshape_data_from_file(self, value):
        """
        Returns the data contained in a control shape file path in the library on disk.
        Args:
            value: (str) name of a control shape file

        Returns: (dict) control shape's data
        """
        self.path = '{0}{1}.json'.format(CONTROLSHAPE_DIR, value)

        if not os.path.isfile(self.path):
            log.error('{0} is not a valid file in the library ({1})'.format(value, CONTROLSHAPE_DIR))
        data = self.from_json()
        return data

    def serialize_structure_to_asset_modules(self, path_to_asset):

        mm = structure.get_structure_data_from_maya_scene()

        for mod in mm.iterkeys():
            self.path = os.path.join(path_to_asset, ASSET_MODULES_DIR)
            current_modules = os.listdir(self.path)

            mod_dir = os.path.join(self.path, mod)
            if mod not in current_modules:
                os.mkdir(mod_dir)

            self.path = os.path.join(mod_dir, 'structure.json')
            if not os.path.exists(self.path):

                self.to_json(mm[mod])




