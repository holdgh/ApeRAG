import redis


def add_testdata_to_redis():
    r = redis.Redis(host="localhost", port=6379, db=2)
    pipe = r.pipeline()

    pipe.set("foo", "string")
    pipe.set("size", 25)
    pipe.lpush("fruits", "apple", "banana", "orange")
    pipe.sadd("hobbies", "reading", "swimming", "coding")
    pipe.hmset("person1", {"name": "Alice", "age": 30, "city": "New York"})
    pipe.hmset("person2", {"name": "Bob", "age": 35, "city": "London"})
    pipe.hmset("person3", {"name": "Charlie", "age": 40, "city": "Paris"})

    pipe.execute()


if __name__ == "__main__":
    add_testdata_to_redis()
