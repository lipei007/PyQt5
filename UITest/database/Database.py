import pymysql
from dbutils.pooled_db import PooledDB


def mysql_connection(host, port, user, password, db):
    max_connections = 15  # 最大连接数
    pool = PooledDB(
        pymysql,
        max_connections,
        host=host,
        user=user,
        port=port,
        passwd=password,
        db=db,
        use_unicode=True)
    return pool


def escape_string(string):
    return pymysql.escape_string(string)


class DataBasePool:

    def __init__(self, host, port, user, password, db):
        self.pool = mysql_connection(host=host, port=port, user=user, password=password, db=db)

    def onError(self, sql, e):
        print(f'SQL: {sql} \n执行发生错误: ', e)

    def execute(self, sql):
        con = self.pool.connection()
        cur = con.cursor()
        try:
            cur.execute(sql)
            con.commit()
        except Exception as e:
            con.rollback()  # 事务回滚
            self.onError(sql=sql, e=e)
        finally:
            cur.close()
            con.close()

    def query(self, sql):
        con = self.pool.connection()
        cur = con.cursor(pymysql.cursors.SSDictCursor)

        results = []
        try:
            # 执行查询，返回查询条数
            cur.execute(sql)
            # 查询所有返回的数据, 数据量大大时候会出问题。使用游标SSDictCursor
            # results = cur.fetchall()

            while True:
                r = cur.fetchone()
                if not r:
                    break
                results.append(r)

        except Exception as e:
            self.onError(sql=sql, e=e)
        finally:
            cur.close()
            con.close()
        return results
