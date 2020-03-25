from ..liquid_icx import LiquidIcx
from tbears.libs.scoretest.score_test_case import ScoreTestCase


class TestLiquidIcx(ScoreTestCase):

    def setUp(self):
        super().setUp()
        self.score = self.get_score_instance(LiquidIcx, self.test_account1)

    def test_hello(self):
        self.assertEqual(self.score.hello(), "Hello")
