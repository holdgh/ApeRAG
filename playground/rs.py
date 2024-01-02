# -*- coding: utf-8 -*-

from redisearch import TextField
from redisearch.client import Client, Query

client = Client('idx')
try:
    client.drop_index()
except:
    pass



client.create_index([TextField('txt')])

# Add a document
client.add_document('docCn1',
                    txt='Release v1.0.2 Redis支持主从同步。数据可以从主服务器向任意数量的从服务器上同步从服务器可以是关联其他从服务器的主服务器。这使得Redis可执行单层树复制。从盘可以有意无意的对数据进行写操作。由于完全实现了发布/订阅机制，使得从数据库在任何地方同步树时，可订阅一个频道并接收主服务器完整的消息发布记录。同步对读取操作的可扩展性和数据冗余很有帮助。[8]',
                    language="chinese")
print(client.search(Query('任意 同步').language("chinese").summarize().highlight()))
