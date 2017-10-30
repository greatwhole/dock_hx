# -*- encoding: utf-8 -*-

def make_seo_link_alternate(url):
    if '//m.' in url:
        url = url.replace('//m.', '//')
    else:
        url = url.replace('//', '//m.')
    return url


def is_target_mobile(url):
    if '//m.' in url:
        return True
    return False