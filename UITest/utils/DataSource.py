from database.Database import DataBasePool, escape_string

# 数据库连接池
mysql_pool = DataBasePool(host='localhost', port=3306, user='root', password='abc123456', db='load_emu')


# 查询表的所有字段
def query_all_columns(table):
    arr = mysql_pool.query(f'select COLUMN_NAME from information_schema.COLUMNS where table_name = \'{table}\';')

    columns = []
    for dic in arr:
        name = dic['COLUMN_NAME']
        columns.append(name)
    return columns


def execute_sql(sql):
    print(sql)
    mysql_pool.execute(sql=sql)


def query_sql(sql):
    print(sql)
    return mysql_pool.query(sql)


def escape(string):
    return escape_string(string)


def insert_key_values_to_table(table, keys, values, failure_callback=None):
    if keys is None or values is None or table is None:
        return

    if len(keys) == 0:
        return

    if len(keys) != len(values):
        return

    values_str = ""
    for v in values:
        if isinstance(v, str):
            vl = escape_string(v)
            values_str = values_str + f"\'{vl}\',"
        else:
            values_str = values_str + f"{v},"

    values_str = values_str[0: len(values_str) - 1]

    sql = f'insert into {table} ({",".join(keys)}) values ({values_str});'
    print(sql)
    mysql_pool.execute(sql=sql)
