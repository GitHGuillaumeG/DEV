import logging

import pymel.core as pm

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class Fk(object):

    def __init__(self):

        # Input attributes
        self._name = None
        self._input_data = None

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):

        if isinstance(value, basestring):
            self._name = value

    @property
    def input_data(self):
        return self._input_data

    @input_data.setter
    def input_data(self, value):
        if not isinstance(value, dict):
            log.error('invalid input data.')
            return
        self._input_data = value

    def build(self):

        self.build_dag()

    def build_dag(self):

        null = pm.createNode('transform', n='{0}_NULL'.format(self.name))
        con = pm.createNode('transform', n='{0}_CON'.format(self.name))
