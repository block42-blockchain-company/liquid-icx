from ..liquid_icx import LiquidICX
from iconservice import *
from tbears.libs.scoretest.score_test_case import ScoreTestCase


#
# Basic Unit tests for LiquidICX.
#
class TestLiquidICX(ScoreTestCase):
    MIN_VALUE_TO_GET_REWARDS = 10 * 10**18

    def setUp(self):
        super().setUp()
        self.score = self.get_score_instance(LiquidICX, self.test_account1)

    def test_name(self):
        self.assertEqual(self.score.name(), "LiquidICX")

    def test_symbol(self):
        self.assertEqual(self.score.symbol(), "LICX")

    def test_decimals(self):
        self.assertEqual(self.score.decimals(), 18)

    def test_totalSupply(self):
        self.assertEqual(self.score.totalSupply(), 0)

    def test_join(self):
        """
        Assert transferable & locked
        Join
        Assert transferable & locked
        Put one term in advance
        Assert t & l
        Put another term forward
        Assert t & l
        """

        self.assertEqual(self.score.balanceOf(self.test_account1), 0)

        self.set_msg(self.test_account1, self.MIN_VALUE_TO_GET_REWARDS)
        self.score.join()
        #self.assertEqual(self.score.balanceOf(self.test_account1), min_value_to_get_rewards)

    def test_join_fail(self):
        self.set_msg(self.test_account1, self.MIN_VALUE_TO_GET_REWARDS - 1)
        self.assertRaises(IconScoreException, self.score.join)
