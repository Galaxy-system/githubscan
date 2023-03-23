# -*- coding: utf-8 -*-
import time
import random
import traceback
from .engine import Engine
from .log import logger
from .config import Config, get_rules, tokens, daily_run_data
from .sql import second_writer,sql_config

running_data = []

stable_config = "n_config"
gitrr_access_token = "9337f0b8c2b63a218a2998ee11b951d9"

# keywrod扫描
def search(idx, rule):
    """
    class instance can't pickle in apply_async
    :param idx:
    :param rule:
    :return:
    """
    token = random.choice(tokens)
    try:
        return Engine(token=token, type="github").search(rule)
    except Exception as e:
        traceback.print_exc()
        return False, None, traceback.format_exc()

## gitee码云扫描
def search_gitee(idx, rule):
    try:
        return Engine(token=gitrr_access_token, type="gitee").search_gitee(rule)
    except Exception as e:
        traceback.print_exc()
        return False, None, traceback.format_exc()

## 二次扫描
def second_search(sql_writer,second_key,sql_task,sql_task_type):
    token = random.choice(tokens)
    try:
        return Engine(token=token, type="github").second_start(sql_writer,second_key,sql_task,sql_task_type)
    except Exception as e:
        traceback.print_exc()
        return False, None, traceback.format_exc()

# store search result
def store_result(result):
    """
    store running result
    :param result:
    :return:
    """
    r_ret, r_rule, r_msg = result
    if r_ret:
        r_datetime = time.strftime("%Y-%m-%d %H:%M:%S")
        # 不需要的类型过滤掉
        if r_rule.corp.lower() in ['vulbox']:
            return
        with open(Config().run_data, 'a') as f:
            rule = '[{t}][{c}][{k}]'.format(t=r_rule.types, c=r_rule.corp, k=r_rule.keyword)
            f.write('{datetime} {ret} {rule} {msg}\r\n'.format(datetime=r_datetime, ret=r_ret, rule=rule, msg=r_msg))
        # store list
        running_data.append([r_datetime, r_ret, rule, r_msg])


# start
def start():
    ## 获取规则列表
    rules = get_rules()
    if len(rules) == 0:
        logger.critical('get rules failed, rule types not found!')
        exit(0)
    logger.info('rules length: {rl}'.format(rl=len(rules)))
    ## 多线程
    #pool = multiprocessing.Pool()

    for idx, rule_object in enumerate(rules):
        if ',' not in rule_object.keyword:
            n_first_keyword = rule_object.keyword
            logger.info('>>>>>>>>>>>>> {n} > {r} >>>>>>'.format(n=rule_object.corp, r=n_first_keyword))
            rule_object.keyword = n_first_keyword
            search(idx, rule_object)
            search_gitee(idx, rule_object)
        else:
            n_first_keywords = rule_object.keyword.split(',')
            for n_first_keyword in n_first_keywords:
                logger.info('>>>>>>>>>>>>> {n} > {r} >>>>>>'.format(n=rule_object.corp, r=n_first_keyword))
                rule_object.keyword = n_first_keyword
                search(idx,rule_object)
                search_gitee(idx, rule_object)
                time.sleep(60)
        time.sleep(60)

        #pool.apply_async(search, args=(idx, rule_object), callback=store_result)
    #pool.close()
    #pool.join()

    ## 开启基于作者二次扫描
    ## 获取所有任务
    n_tasks = sql_config(stable_config)
    for n_task in n_tasks:
        ## 获取任务的存在泄漏的对应作者
        sql_writers = second_writer(n_task[0],n_task[1])

        if sql_writers == False:
            continue

        ## 二次扫描关键字内容进行分割
        if ',' in n_task[5]:
            second_keys = n_task[5].split(',')
        else:
            second_keys = n_task[5]
        ## 遍历作者
        for sql_writer in sql_writers:
            ## 遍历二次扫描关键字
            for second_key in second_keys:
                second_search(sql_writer[0], second_key, n_task[0],n_task[1])
                time.sleep(180)



# generate report file
def generate_report(data):
    for rd in data:
        datetime, ret, rule, msg = rd
        html = '<li> {datetime} {ret} {rule} {msg}</li>'.format(datetime=datetime, ret=ret, rule=rule, msg=msg)
        run_data = daily_run_data()
        run_data['list'].append(html)
        if ret:
            run_data['found_count'] += msg
            run_data['job_success'] += 1
        else:
            run_data['job_failed'] += 1
        daily_run_data(run_data)


def github():
        logger.info('启动监视器github信息泄漏')
        # start
        start()
        # start generate report file
        #generate_report(running_data)


if __name__ == '__main__':
    github()
