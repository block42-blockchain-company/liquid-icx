from iconservice import *
from ..scorelib.consts import *


class Utils:
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

    @staticmethod
    def calcBPS(part: int, base: int) -> int:
        """
        Calculating Basis Point
        :param part:
        :param base:
        :return:
        """
        return int((part * 10000) / base)
