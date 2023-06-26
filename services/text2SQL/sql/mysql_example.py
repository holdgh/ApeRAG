from services.text2SQL.base import *

if __name__ == '__main__':
    pg = SQLBase(user="root", pw="kd7xvd8d", host="127.0.0.1", database_name="test", islocal=True,
                 dialect="mysql")
    response = pg.query("How old is Steven?")
    print(response)
