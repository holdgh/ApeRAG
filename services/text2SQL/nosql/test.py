from services.text2SQL.nosql.mongo_query import Mongo

if __name__ == "__main__":
    r = Mongo(host='localhost', port='27017', db='test', collection='user', pwd='')
    print(r.connect())
    q = r.text_to_query("查询名字为 John Doe 或者年龄小于 18 的用户：")
    print(q)
