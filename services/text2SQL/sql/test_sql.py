import unittest
from sql import SQLBase


class TestSqlBase(unittest.TestCase):
    def setUp(self) -> None:
        self.cli = SQLBase("127.0.0.1", "mysql")

    def test_connect_without_verify(self):
        result = self.cli.connect()
        self.assertTrue(result)

    def test_connect_with_verify(self):
        result = self.cli.connect(verify=True)
        self.assertFalse(result)

    def tearDown(self):
        print("测试用例{}执行结束...".format(self))