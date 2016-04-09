# -*- coding: utf-8 -*-
"""
Created on '16/4/7'
@author: 'greatwhole'
"""

from redis import Redis
from dock_hx.common.singleton import singleton, params_singleton


@params_singleton
class RedisStore(Redis):

    @classmethod
    def create(cls, config, **kwargs):
        """
            reids = {'host': 127.0.0.1, 'port': 6369, 'db': 0}
            redis = {'url': redis//127.0.0.1:6379/0
        """
        if 'url' in config:
            return cls.from_url(config['url'], **kwargs)
        else:
            return cls(**config, **kwargs)
