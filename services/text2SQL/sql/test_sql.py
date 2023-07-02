import unittest
from mysql import Mysql


class TestMysql(unittest.TestCase):
    def setUp(self) -> None:
        self.cli = Mysql(host="127.0.0.1", db_type="mysql", db="mydb", pwd="ml8hdhhr", user="root")

    def test_connect_without_verify(self):
        result = self.cli.connect()
        self.assertTrue(result)

    def test_connect_with_verify(self):
        result = self.cli.connect(verify=True)
        self.assertFalse(result)

    def tearDown(self):
        print("测试用例{}执行结束...".format(self))