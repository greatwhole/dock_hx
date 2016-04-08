# -*- coding: utf-8 -*-
'''
Created on '16/3/21'
@author: 'greatwhole'
'''


class ReadOnlyDict(dict):
    __readonly = False

    def readonly(self, readonly=True):
        self.__readonly = bool(readonly)

    def __setitem__(self, key, value):
        if self.__readonly:
            raise TypeError, "this is read only dict"
        return dict.__setitem__(self, key, value)

    def __delitem__(self, key):
        if self.__readonly:
            raise TypeError, "this is read only dict"
        return dict.__delitem__(self, key)
