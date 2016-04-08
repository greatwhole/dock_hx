
__author__ = 'greatwhole'


def to_str(x, charset='utf-8', errors='strict'):
    if x is None:
        return None
    if isinstance(x, str):
        return x
    try:
        return x.encode(charset, errors)
    except:
        # logger.error('TRACEBACK', traceback.format_exc())
        # logger.captureException()
        return None


def to_unicode(x, charset='utf-8', errors='strict'):
    if x is None:
        return None
    if isinstance(x, unicode):
        return x
    try:
        return x.decode(charset, errors)
    except:
        # logger.error('TRACEBACK', traceback.format_exc())
        # logger.captureException()
        return None