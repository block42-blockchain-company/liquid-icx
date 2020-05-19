from ..liquid_icx import LiquidICX
from iconservice import *
from tbears.libs.scoretest.score_test_case import ScoreTestCase

#
# Basic Unit tests for LiquidICX.
#
class TestLiquidICX(ScoreTestCase):

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

    #def test_tranfser(self):
        # self.assertEqual(self.score.Transfer(self.test_account2, 100), )
        # self.assertEqual(self.score.Transfer(self.test_account2, 100), )
