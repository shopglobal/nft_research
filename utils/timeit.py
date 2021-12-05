"""Module to create the timeit decorator."""

from functools import wraps
from time import time
import collections
import numpy as np
import pandas as pd


def timeit(f):
    """
    decorator to time function
    :param f:
    :return:
    """

    @wraps(f)
    def wrap(*args, **kwargs):
        if len(args) >= 1:
            logger = getattr(args[0], 'logger', None)
        else:
            logger = None

        before_str = 'Running '

        if len(args) > 0 and hasmethod(args[0], f.__name__):
            before_str += f'{type(args[0]).__name__}.'
        before_str += f'{f.__name__}('

        if len(args) >= 1 and args[1:]:
            before_str += ', '.join('%s=%s' % (k, type_or_value(v)) for k, v in kwargs.items())

        before_str += ')...'

        if logger is not None:
            logger.info(before_str)
        else:
            print(before_str)

        ts = time()
        result = f(*args, **kwargs)
        te = time()

        seconds = te - ts
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        after_str = '%s took %dh%02dm%02ds.' % (f.__name__, h, m, s)

        if hasmethod(args[0], f.__name__):
            after_str = ('%s.' % type(args[0]).__name__) + after_str

        if logger is not None:
            logger.info(after_str)
        else:
            print(after_str)

        return result

    return wrap


def type_or_value(x):
    supported_value = [str, int, float, list, dict, bool, pd.Timestamp]
    if type(x) in supported_value:
        if type(x) != list:
            if type(x) == str:
                return "'%s'" % x
            else:
                return x
        else:
            return x[:(np.minimum(len(x), 10))]
    else:
        return type(x).__name__


def hasmethod(obj, method_name):
    return hasattr(obj, method_name) and callable(getattr(obj, method_name))


def callable(obj):
    return isinstance(obj, collections.Callable)
