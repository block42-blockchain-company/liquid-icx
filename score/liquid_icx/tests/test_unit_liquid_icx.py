from ..liquid_icx import LiquidICX
from tbears.libs.scoretest.score_test_case import ScoreTestCase


class TestLiquidICX(ScoreTestCase):

    def setUp(self):
        super().setUp()
        self.score = self.get_score_instance(LiquidICX, self.test_account1)

    def test_hello(self):
        self.assertEqual(self.score.hello(), "Hello")
