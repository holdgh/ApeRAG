from services.text2SQL.base import *

if __name__ == '__main__':
    pg = SQLBase(user="postgres", pw="", database_name="postgres",islocal=True,dialect="postgresql")
    response = pg.query("How old is Steven?")
    print(response)
