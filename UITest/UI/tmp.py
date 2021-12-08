

keys = ['a', 'b', 'c']
values = ['A', 'B', 3]

if __name__ == '__main__':
    tmp_arr = []
    for v in values:
        if v is str:
            tmp_arr.append(f'\'{v}\'')
        else:
            tmp_arr.append(v)

    values_str = ""
    for vl in tmp_arr:
        print(vl)
        print(f'\'{vl}\'')
        if isinstance(vl, str):
            values_str = values_str + f"\'{vl}\',"
        else:
            values_str = values_str + f'{vl},'

    values_str = values_str[0: len(values_str) - 1]

    sql = f'insert into tmp_tb ({",".join(keys)}) values ({values_str}));'
    print(sql)