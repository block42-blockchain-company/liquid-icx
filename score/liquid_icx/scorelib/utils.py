from iconservice import *
from ..interfaces.system_score_interface import *
from ..scorelib.consts import *


class Utils:
    @staticmethod
    def system_score_interface():
        return IconScoreBase.create_interface_score(SYSTEM_SCORE, InterfaceSystemScore)

    @staticmethod
    def remove_from_array(array: ArrayDB, el) -> None:
        temp = []
        # find that element and remove it
        while array:
            current = array.pop()
            if current == el:
                break
            else:
                temp.append(current)
        # append temp back to arrayDB
        while temp:
            array.put(temp.pop())
