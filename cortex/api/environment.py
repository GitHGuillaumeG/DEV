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
    cortex = None
    controlShape_library = None

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

        # Asset/shot
        environment = os.path.normpath(os.path.join('E:/PROD', show, division, asset_type, asset_name))
        if not os.path.isdir(environment):
            print 'falied to set environment'

        Environment.current = environment
        Environment.data_path = os.path.normpath(os.path.join(environment, 'rig/DATA'))

        # Cortex
        Environment.cortex = os.path.normpath('E:/DEV/cortex')
        Environment.controlShape_library = os.path.normpath(os.path.join(Environment.cortex,
                                                                         'cortexlibrary/controlshapes'))

    def set_shot(self):
        pass
