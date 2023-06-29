import unittest
from redis_query import Redis
from clickhouse_query import Clickhouse
from mongo_query import Mongo


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
