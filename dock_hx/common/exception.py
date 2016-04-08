# -*- coding: utf-8 -*-
from werkzeug.exceptions import HTTPException

__all__ = [
    'AppBaseException',
    'ParameterError',
    'IntegrityException'
]

class AppBaseException(HTTPException):
    def __init__(self, code, description='', response=None, extra_info=None):
        self.code = code
        self.description = description
        self.response = response
        self.extra_info = extra_info


class ParameterError(AppBaseException):
    pass


class IntegrityException(HTTPException):
    code = 400
    description = 'Request Data Is Not Integrity'

    def __init__(self, **kwargs):
        super(IntegrityException, self).__init__(kwargs)