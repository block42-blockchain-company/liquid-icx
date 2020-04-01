from ..fake_system_contract import FakeSystemContract
from tbears.libs.scoretest.score_test_case import ScoreTestCase


class TestFakeSystemContract(ScoreTestCase):

    def setUp(self):
        super().setUp()
        self.score = self.get_score_instance(FakeSystemContract, self.test_account1)

    def test_hello(self):
        self.assertEqual(self.score.hello(), "Hello")
