import unittest
from services.text2SQL.nosql.redis_query import Redis
from services.text2SQL.nosql.clickhouse_query import Clickhouse
from services.text2SQL.nosql.mongo_query import Mongo


class TestRedis(unittest.TestCase):
    def setUp(self) -> None:
        self.cli = Redis("127.0.0.1")

    def test_connect_without_verify(self):
        result = self.cli.connect()
        self.assertTrue(result)

    def test_connect_with_verify(self):
        result = self.cli.connect(verify=True)
        self.assertFalse(result)

    def tearDown(self):
        print("测试用例{}执行结束...".format(self))


class TestClickHouse(unittest.TestCase):
    def setUp(self) -> None:
        self.cli = Clickhouse("127.0.0.1", pwd="4gtfgprc")

    def test_connect_without_verify(self):
        result = self.cli.connect()
        self.assertTrue(result)

    def test_connect_with_verify(self):
        self.cli = Clickhouse("127.0.0.1")
        result = self.cli.connect(verify=True)
        self.assertFalse(result)

    def tearDown(self):
        print("测试用例{}执行结束...".format(self))


class TestMongo(unittest.TestCase):
    def setUp(self) -> None:
        self.cli = Mongo("127.0.0.1")

    def test_connect_without_verify(self):
        result = self.cli.connect()
        self.assertTrue(result)

    def test_connect_with_verify(self):
        result = self.cli.connect(verify=True)
        self.assertFalse(result)

    def tearDown(self):
        print("测试用例{}执行结束...".format(self))
