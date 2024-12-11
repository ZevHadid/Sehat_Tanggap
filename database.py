from mysql.connector import pooling

dbconfig = {
    "host": "localhost",
    "user": "root",
    "password": "ZEVhs27*8*",
    "database": "manajemen_uks"
}

connection_pool = pooling.MySQLConnectionPool(
    pool_name="mypool",
    pool_size=20,
    **dbconfig
)

def get_db_connection():
    return connection_pool.get_connection()
