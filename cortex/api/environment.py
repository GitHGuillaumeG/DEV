# Python libs
import os


class Environment(object):
    """
    Environment class is used to set a user in a specific asset or shot centric work context.
    
    e.g. :
    'E:/PROD/project_test/rig/character/bob'
    'E:/PROD/project_test/sequence010/shot020/animation'
    
    Class attributes allow the user to retrieve and write data to specific locations on disk based on the current
    context.
    """

    current = None
    data_path = None
    cortex_path = None
    controlShape_library_path = None

    def __init__(self):

        pass

    def set_asset(self, show, division, asset_type, asset_name):
        """
        Sets a work environment
        
        :param show: (str) name of the show
        :param division: (str) name of the division. Either asset, shot
        :param asset_type: (str) the type of asset. Either character, prop, vehicle
        :param asset_name: (str) name of the asset
        
        :return: (str) the path of the environment 
        """

        # Current Asset environment
        environment = os.path.join('E:/PROD', show, division, asset_type, asset_name).replace(os.sep, '/')
        if not os.path.isdir(environment):
            print 'falied to set environment'

        Environment.current = environment

        # Data path
        data_path = os.path.join(environment, 'rig/DATA')
        Environment.data_path = os.path.normpath(data_path)

        # Cortex
        Environment.cortex_path = os.path.normpath('E:/DEV/cortex')

        control_shape_library = os.path.join(Environment.cortex_path, 'cortexlibrary/controlshapes')
        Environment.controlShape_library_path = os.path.normpath(control_shape_library)

    def set_shot(self):
        pass
