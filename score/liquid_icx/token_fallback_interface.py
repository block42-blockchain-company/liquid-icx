from iconservice import *
from .irc_2_interface import IRC2TokenStandard

# An interface of tokenFallback.
# Receiving SCORE that has implemented this interface can handle
# the receiving or further routine.
class TokenFallbackInterface(IRC2TokenStandard):
    @interface
    def tokenFallback(self, _from: Address, _value: int, _data: bytes):
        pass
