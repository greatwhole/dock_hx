# -*- coding: utf-8 -*-
'''
Created on 2016年2月26日
@author: greatwhole
'''
import yaml
import time

def load_config():
    pass


class Autoload():
    autoload_resources = {}

    @classmethod
    def create(cls, **kwargs):
        _hashkey =
        if _hashkey not in cls.autoload_resources:
            cls.autoload_resources[_hashkey] = cls(**kwargs)

        ret = cls.autoload_resources[_hashkey]
        ret.check_interval = kwargs['check_interval']

    @property
    def check_interval(self):
        return self.check_interval

    @check_interval.setter
    def check_interval(self, val):
        if val < self.check_interval:
            self.check_interval = val

    def get(self):
        checked_no = int(time.time()/self.check_interval)
        if checked_no > self._last_checked:
            self._last_checked = checked_no
            self.load()
        return self._data

    def load(self):
        data = None
        if self.location == 'local':
            with open('data/{}'.format(self.name), 'rb') as f:
                data = f.read()
        if self.name.endswith('.yaml') and data:
            data = yaml.load(data)
        self._data = data
        return data



if __name__ == '__main__':
    pass