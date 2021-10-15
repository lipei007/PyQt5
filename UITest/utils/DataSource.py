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


# 将数据表插入数据库
def insert_to_table(rows, table, maps):
    for row in rows:
        insert_row(row, table, maps)


# 插入数据
def insert_row(row, table, maps):
    cols = len(row)

    keys = []
    values = []

    for j in range(0, cols):
        value = row[j]
        key = maps.get(j, None)
        if key is not None:
            keys.append(key)

            if value is None:
                value = ""
            value = escape_string(value.strip())
            values.append(f'\'{value}\'')

    if len(keys) > 0:
        sql = f'insert into {table} ({",".join(keys)}) values ({",".join(values)});'
        mysql_pool.execute(sql=sql)


def execute_sql(sql):
    mysql_pool.execute(sql=sql)


def query_sql(sql):
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
