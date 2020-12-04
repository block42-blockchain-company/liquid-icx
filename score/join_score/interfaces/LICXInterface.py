from iconservice import *


class LICXInterface(InterfaceScore):
    @interface
    def join(self) -> None:
        pass

    @interface
    def leave(self, _value: int = None) -> None:
        pass