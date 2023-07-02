from sqlalchemy import create_engine, MetaData, Table, String, Column, Integer, insert


def add_test_data_to_mysql(pwd):
    engine = create_engine("mysql+pymysql://root:{}@127.0.0.1:3306/mydb".format(pwd))
    metadata_obj = MetaData()

    table_name = "student"
    student = Table(
        table_name,
        metadata_obj,
        Column("id", Integer, primary_key=True),
        Column("name", String(16)),
        Column("grade", Integer),
        Column("class", Integer, nullable=False),
    )
    metadata_obj.create_all(engine)

    rows = [
        {"id": 1, "name": "lucy", "grade": 85, "class": 1},
        {"id": 2, "name": "ross", "grade": 78, "class": 1},
        {"id": 3, "name": "tom", "grade": 82, "class": 1},
        {"id": 4, "name": "jerry", "grade": 95, "class": 1},
        {"id": 5, "name": "angel", "grade": 75, "class": 1},
        {"id": 6, "name": "david", "grade": 63, "class": 1},
        {"id": 7, "name": "joy", "grade": 89, "class": 2},
        {"id": 8, "name": "bin", "grade": 85, "class": 2},
        {"id": 9, "name": "james", "grade": 92, "class": 2},
        {"id": 10, "name": "sam", "grade": 79, "class": 2},
        {"id": 11, "name": "lili", "grade": 80, "class": 2},
    ]
    for row in rows:
        stmt = insert(student).values(**row)
        with engine.connect() as connection:
            _ = connection.execute(stmt)
            connection.commit()

    table_name = "city_stats"
    city_stats_table = Table(
        table_name,
        metadata_obj,
        Column("city_name", String(16), primary_key=True),
        Column("population", Integer),
        Column("country", String(16), nullable=False),
    )
    metadata_obj.create_all(engine)

    rows = [
        {"city_name": "Toronto", "population": 2731571, "country": "Canada"},
        {"city_name": "Tokyo", "population": 13929286, "country": "Japan"},
        {"city_name": "Berlin", "population": 600000, "country": "Germany"},
    ]
    for row in rows:
        stmt = insert(city_stats_table).values(**row)
        with engine.connect() as connection:
            _ = connection.execute(stmt)
            connection.commit()


if __name__ == "__main__":
    add_test_data_to_mysql("")
