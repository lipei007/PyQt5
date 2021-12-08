import json

from UITest import utils


def import_step(step):
    keys = []
    values = []
    for k, v in step.items():
        if v is not None:
            keys.append(k)
            values.append(v)

    utils.DataSource.insert_key_values_to_table('t_task_flow_step', keys, values)


def import_flow(flow):
    flow['steps'] = None

    keys = []
    values = []
    for k, v in flow.items():
        if v is not None:
            keys.append(k)
            values.append(v)

    utils.DataSource.insert_key_values_to_table('t_task_flow', keys, values)


def import_task(task):
    flows = task['flows']
    main_flow_id = task['main_flow_id']
    task['flows'] = None
    task['main_flow_id'] = None
    task['id'] = None

    keys = []
    values = []
    for k, v in task.items():
        if v is not None:
            keys.append(k)
            values.append(v)

    utils.DataSource.insert_key_values_to_table('t_task', keys, values)

    # 查询最后一个插入的任务ID
    sql = 'select max(id) as id from t_task;'
    rests = utils.DataSource.query_sql(sql)
    if len(rests) == 0:
        return
    tid = rests[0]['id']
    if flows is None:
        return

    # 查询最后插入流程ID
    sql = 'select max(id) as id from t_task_flow;'
    rests = utils.DataSource.query_sql(sql)
    fid_start = 1
    if len(rests) > 0:
        fid_start = rests[0]['id']

    old_new_fid_maps = {}
    tmp_arr = []

    for flow in flows:
        # 更新流程所属任务ID
        flow['task_id'] = tid

        # 新流程ID
        fid_start = fid_start + 1
        # 旧流程ID
        old_fid = flow['id']
        flow['id'] = fid_start
        # 设置新旧流程ID映射
        old_new_fid_maps[old_fid] = fid_start

        # 更新流程步骤所属流程ID
        steps = flow['steps']
        if steps is not None:
            for step in steps:
                step['flow_id'] = fid_start
                tmp_arr.append(step)

        # 执行插入
        import_flow(flow)

        # 更新主流程
        if main_flow_id != 0 and old_fid == main_flow_id:
            sql = f'update t_task set main_flow_id={fid_start} where id={tid};'
            utils.DataSource.execute_sql(sql)

    # 更新流程执行步骤
    for step in tmp_arr:
        turn_id = step['turn_flow_id']
        if turn_id is None:
            turn_id = 0

        new_fid = old_new_fid_maps.get(turn_id)
        if new_fid is not None:
            step['turn_flow_id'] = new_fid
        else:
            step['turn_flow_id'] = 0

        step['id'] = None
        import_step(step)


def import_str(js_str):
    print(f'导入数据\n{js_str}')
    arr = json.loads(js_str)
    if not isinstance(arr, list):
        return
    for task in arr:
        import_task(task)
