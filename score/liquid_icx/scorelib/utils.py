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

    @staticmethod
    def calcValueProportionalToBasisPoint(value: int, basis_point: int) -> int:
        """
        Calculating a value proportional to the Basis point
        :param value:
        :param basis_point:
        :return:
        """
        return int((value * basis_point) / 10000)

    @staticmethod
    def isPrep(db: IconScoreDatabase, address: Address) -> bool:
        """
        Checks if the given address is either a sub or main prep.
        The prep_array is updated only once per term.
        :param db: score-database
        :param address: address to check
        :return: True, if address is prep
        """
        sys_score = IconScoreBase.create_interface_score(SYSTEM_SCORE, InterfaceSystemScore)
        iiss_info = sys_score.getIISSInfo()
        prep_array: ArrayDB = ArrayDB("prep_array", db, value_type=Address)
        preps_updated = VarDB("preps_updated", db, value_type=int)  # stores height, last time when the preps got updated

        if preps_updated.get() < iiss_info["nextPRepTerm"] - TERM_LENGTH or not len(prep_array):
            # remove all previous preps
            while prep_array:
                prep_array.pop()
            # query main/sub preps and append them to prep_array
            prep_list: list = sys_score.getMainPReps()["preps"]
            prep_list.extend(sys_score.getSubPReps()["preps"])
            for prep in prep_list:
                prep_array.put(prep["address"])

            preps_updated.set(iiss_info["blockHeight"])

        return address in prep_array
