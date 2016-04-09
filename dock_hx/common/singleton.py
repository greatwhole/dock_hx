# -*- coding: utf-8 -*-
"""
Created on '16/4/9'
@author: 'greatwhole'
"""
import functools


class SingletonMetaclass(type):
    _instance = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instance:
            cls._instances[cls] = super(SingletonMetaclass, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


# todo
def param_singelton(cls, *args, **kwargs):
    instance = {}

    def deco(cls):
        @functools.wraps
        def _singleton(*args, **kwargs):
            if cls not in instance:
                instance[cls] = {}
            uuid = '.'.join(args, kwargs.items())
            if uuid not in instance[cls]:
                instance[cls][uuid] = cls(*args, **kwargs)
            return instance[cls][uuid]
        return _singleton
    return deco