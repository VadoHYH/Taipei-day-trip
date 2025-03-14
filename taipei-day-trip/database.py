import pymysql

# 建立 MySQL 連線
def get_db_connection():
    return pymysql.connect(
        host="ip-172-31-42-179",
        user="root",
        password="ec2wehelpmysql",
        database="taipei_trip",
        cursorclass=pymysql.cursors.DictCursor
    )


