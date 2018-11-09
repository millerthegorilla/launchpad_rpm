import logging

class FuncThread(threading.Thread):
    def __init__(self, target, *args):
        self._target = target
        self._args = args
        threading.Thread.__init__(self)

    def run(self):
        self._target(*self._args)


def log(self, msg='', level='info',
        exception=None, std_out=False, to_disk=False):
    log_level = {
        'debug'     : logging.debug,
        'info'      : logging.info,
        'warning'   : logging.warning,
        'error'     : logging.error,
        'critical'  : logging.critical
    }.get(level, logging.debug('unable to log - check syntax'))
    if exception is not None:
        raise type(exception)(msg)
    if std_out is not False:
        log_level(msg)


def gen_dict_extract(key, var):
    if hasattr(var,'iteritems'):
        for k, v in var.iteritems():
            if k == key:
                yield v
            if isinstance(v, dict):
                for result in gen_dict_extract(key, v):
                    yield result
            elif isinstance(v, list):
                for d in v:
                    for result in gen_dict_extract(key, d):
                        yield result
