from iconservice import *


class NotAFunctionError(Exception):
    pass


def whenNotPaused(func):
    if not isfunction(func):
        raise NotAFunctionError

    @wraps(func)
    def __wrapper(self, *args, **kwargs):
        if self._is_paused.get():
            revert("LiquidICX: Function only callable when score is not paused.")

        return func(self, *args, **kwargs)
    return __wrapper


def whenPaused(func):
    if not isfunction(func):
        raise NotAFunctionError

    @wraps(func)
    def __wrapper(self, *args, **kwargs):
        if not self._is_paused.get():
            revert("LiquidICX: Function only callable when score is paused.")

        return func(self, *args, **kwargs)
    return __wrapper
