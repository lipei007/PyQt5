import json
import utils.DataSource


def query_flow_steps(fid):
    """
    查询流程步骤
    :param fid: 流程ID
    :return: 步骤集合
    """
    sql = f'select * from t_task_flow_step where flow_id={fid};'
    rests = utils.DataSource.query_sql(sql)
    tmp_arr = []
    for step in rests:
        step['create_time'] = None
        tmp_arr.append(step)
    return tmp_arr


def query_task_flow(tid):
    """
    查询任务流程
    :param tid: 任务ID
    :return: 任务流程
    """
    sql = f'select * from t_task_flow where task_id={tid};'
    rests = utils.DataSource.query_sql(sql)

    tmp_arr = []
    for flow in rests:
        fid = flow['id']
        steps = query_flow_steps(fid)
        flow['steps'] = steps
        flow['create_time'] = None
        tmp_arr.append(flow)

    return tmp_arr


def query_task(tid):
    """
    查询任务
    :param tid: 任务ID
    :return: 任务Json
    """
    sql = f"select * from t_task where id={tid};"
    rests = utils.DataSource.query_sql(sql)
    if len(rests) > 0:

        task = rests[0]
        flow_arr = query_task_flow(tid)
        task['flows'] = flow_arr
        task['create_time'] = None
        task['modify_time'] = None
        return [task]

    return None


def query_all_task():
    """
    查询所有任务
    :return: 任务数组
    """
    sql = f"select * from t_task;"
    rests = utils.DataSource.query_sql(sql)
    tmp_arr = []
    for task in rests:
        tid = task['id']
        flow_arr = query_task_flow(tid)
        task['flows'] = flow_arr
        task['create_time'] = None
        task['modify_time'] = None
        tmp_arr.append(task)
    return tmp_arr


def dump_2_json(obj):
    """
    转JSON字符串
    :param obj: 数组/字典
    :return: json字符串
    """
    if obj is None:
        return None

    json_str = json.dumps(obj)
    return json_str
