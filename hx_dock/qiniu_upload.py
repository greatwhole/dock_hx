# -*- coding: utf-8 -*-
from qiniu import Auth, put_file, etag

# https://developer.qiniu.com/kodo/sdk/1242/python


# TODO 单例 decorate
class QiniuUpload(object):
    def __init__(self, ak, sk, bucket_name, expire):
        self.ak = ak
        self.sk = sk
        self.q = Auth(ak, sk)
        self.bucket_name = bucket_name
        self.expire = expire

    def upload(self, src, dest, check=True):
        token = self.q.upload_token(self.bucket_name, dest, self.expire)
        ret, info = put_file(token, dest, src)

        if check:
            assert ret['key'] == dest, "ret['key'] <{}> unmatch dest <{}>".format(ret['key'], dest)
            assert ret['hash'] == etag(src), "ret['hash']  <{}> unmatch etag(src), <{}>".format(ret['hash'], etag(src))
        return True
