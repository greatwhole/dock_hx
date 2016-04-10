# -*- coding: utf-8 -*-
"""
Created on '16/4/10'
@author: 'greatwhole'

试图抽象地解决 redis 和 sql 之间的联动
其中 sql 部分使用 sqlalchemy 包装
"""
ttl = 60*10


class ReSqlBase(object):
    def __init__(self, r_name, r_ins, sql, expire=ttl):
        """
        :param r_name:
        :param r_ins:  redis 实例
        :param sql: sql 表
        :param expire:

        redis key 的设计：
                table_name:<ReSql_type>:<kwargs>

        """
        self.r_name = r_name
        self.r_ins = r_ins
        self.sql = sql
        self.expire = expire

    def get(self):
        exist_flag = self.check_exist()
        if not exist_flag:
            self.sync_s2r()
            # if self.sql:
            #     self.write_val = self.get_from_sql()     #从其他途径获取
            #     self.sync_s2r()
            # else:
            #     logger.debug(u'数据不存在')
            #     return None
        # 统一再取一次（逻辑更加清晰，特别是对rhash，但是会多一次对redis的连接，以后再优化）
        res = self.get_from_redis()
        return res

    def check_exist(self):
        return self.r_ins.exists(self.r_name)

    def get_from_redis(self):
        raise NotImplementedError

    def get_from_sql(self):
        raise NotImplementedError

    def sync_r2s(self):
        """redis 内容 同步到 sql"""
        raise NotImplementedError

    def sync_s2r(self):
        """sql 内容 同步到 redis"""
        raise NotImplementedError


class ReSqlHash(ReSqlBase):
    def __init__(self, r_name, r_ins, fields='__all__', **kwargs):
        """
        :param r_name:
        :param r_ins:
        :param fields: (all, <list>) 从hash中取 全部/部分 字段，如果是部分，则需要传递list
        :param kwargs:
            # fields: <list>
        :return:
        """
        super(ReSqlHash, self).__init__(r_name=r_name, r_ins=r_ins, **kwargs)
        self.r_method = 'hash'

        if fields == '__all__':
            self.fields = fields
        else:
            if isinstance(fields, basestring):
                self.fields = [fields]
            elif isinstance(fields, (tuple, set, list)):
                self.fields = fields
            else:
                raise TypeError

    def check_exist(self):
        """检查字段fileds 是否都存在"""
        flag = self.r_ins.exists(self.r_name)
        if not flag:
            return flag

        for key in self.fields:
            if not self.r_ins.hexists(self.r_name, key):
                flag = False
                break
        return flag

    def get_from_redis(self):
        if self.fields == 'all':
            return self.r_ins.hgetall(self.r_name)
        # elif isinstance(self.fields, basestring):
        #     return self.r_ins.hget(self.r_name, self.fields)
        else:
            return self.r_ins.hmget(self.r_name, *self.fields)

    def sync_s2r(self):
        self.r_ins.hmset(self.r_name, self.write_val)
        if self.expire is not None:
            self.r_ins.expire(self.r_name, time=self.expire)

    def sync_r2s(self):
        """redis 内容 同步到 sql"""
        raise NotImplementedError