# -*- coding: utf-8 -*-
import os
import time
import json
import traceback
import configparser
from .log import logger
from .sql import read_config,read_tocken

home_path = os.path.join(os.path.expandvars(os.path.expanduser("~")), ".gsil")
code_path = os.path.join(home_path, 'codes')
project_directory = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
config_path = os.path.join(project_directory, 'config.gsil')
rules_path = os.path.join(project_directory, 'rules.gsil')



def get(level1=None, level2=None):
    """
    Get config value
    :param level1:
    :param level2:
    :return: string
    """
    if level1 is None and level2 is None:
        return
    config = configparser.ConfigParser()

    config.read(config_path)
    value = None
    try:
        value = config.get(level1, level2)
    except Exception as e:
        print(level1, level2)
        traceback.print_exc()
        print("GSIL/config.gsil file configure failed.\nError: {0}".format(e))
    return value

## 数据库读取tocken
def tcoken_get():
    m_tockens = []
    n_tockens = read_tocken()
    for n_tocken in n_tockens:
        m_tockens.append(n_tocken[0])
    return  m_tockens
# GitHub tokens

tokens = tcoken_get()
if len(tokens) == 0:
    exit(0)

exclude_repository_rules = [
    #
    # 添加此规则要确保一定不会出现误报
    # 由于repository_path全部转为小写了，所以规则也全部小写
    #
    # GitHub博客
    r'(github.io)|(github.com)$',
    # Android客户端项目
    r'(app/src/main)',
    # 爬虫
    r'(crawler)|(spider)|(scrapy)|(爬虫)',
    # 文档
    # doc可能存在误报
    r'((开发文档)|(api))',
    # 软件作者
    r'(jquery)|(contact)|(readme)|(authors)',
    # 软件配置
    r'(surge)|(adblock)|(hosts)|(\.pac)|(ads)|(blacklist)|(package\.json)|(podspec\.json)|(tracking_servers)',
    # 无用东西
    r'(linux_command_set)|(domains)|(sdk)|(linux)|(\.html)|(\.apk)|(domain-list)|(easylist)|(urls)|(easylist)|(http_analytic)|(filtersregistry)|(PhyWall\.java)',
]

exclude_codes_rules = [
    # 超链接
    r'(href)',
    # 框架
    r'(iframe\ src)',
    # 邮件schema
    r'(mailto:)',
    # Markdown
    r'(\]\()',
    r'(npm\.taobao\.org)',
    r'(HOST-SUFFIX)|(DOMAIN-SUFFIX)',
]

public_mail_services = [
    'msg.com',
    '126.com',
    '139.com',
    '163.com',
    'qq.com',
    'vip.qq.com',
    'gmail.com',
    'sina.com.cn',
    'sina.com',
    'aliyun.com',
    'sohu.com',
    'yeah.net',
    'msn.com',
    'mail.com',
    'outlook.com',
    'live.com',
    'foxmail.com',
    'mai.com',
    'example.com',
    'example.org',
    'yourdomain.com',
    'domain.com',
    'company.com',
    'otherdomain.com',
    'mydomain.com',
    'host.com',
    'yourhost.com',
    'domain.tld',
    'foo.bar',
    'bar.com',
    'dom.ain',
    'localhost.com',
    'xxxxx.com',
    'xxxx.com',
    'xxx.com',
    'xx.com',
    'email.com'
]

# Rules Structure Design
#
# 'rule keywords': {
#     'mode': '' // RuleMode: normal-match(default)/only-match/full-match/mail
#     'extension': '' // search extension: (default)/txt/md/java/python/etc...
# }
#
'''
try:
    with open(rules_path) as f:
        rules_dict = json.load(f)
except Exception as e:
    logger.critical('please config GSIL/rules.gsil!')
    logger.critical(traceback.format_exc())
'''

class Rule(object):
    def __init__(self, types=None, corp=None, keyword=None, mode='normal-match', extension=None, secondkeyword=None, choose=1):
        self.types = types          ## 一级标签
        self.corp = corp            ## 二级标签
        self.keyword = keyword      ## 关键字
        self.mode = mode            ## 模式
        self.extension = extension  ## 匹配类型
        self.secondkeyword = secondkeyword ## 二次匹配关键字
        self.choose = choose        ##判断是否扫描，1为扫描 0为不扫描

## 数据库读取配置信息
def get_rules():
    rules_objects = []
    extension = None
    sql_backs = read_config()
    for sql_back in sql_backs:
        first_type = sql_back[0]
        second_corp = sql_back[1]
        keyword = sql_back[2]
        mode = sql_back[3]
        choose = sql_back[6]
        if len(sql_back[5]) >0 :
            secondkeyword = sql_back[5]
        if sql_back[4] != "":
            extension = sql_back[4]
        r = Rule(first_type, second_corp, keyword, mode, extension, secondkeyword, choose)
        rules_objects.append(r)
    return  rules_objects

class Config(object):
    def __init__(self):
        self.project_directory = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
        if os.path.isdir(home_path) is not True:
            os.makedirs(home_path)
        self.hash_path = os.path.join(home_path, 'hash')
        if os.path.isfile(self.hash_path) is not True:
            open(self.hash_path, 'a').close()
        self.data_path = os.path.join(home_path, 'data')
        if os.path.isdir(self.data_path) is not True:
            os.makedirs(self.data_path)
        self.run_data = os.path.join(home_path, 'run')
        self.run_data_daily = os.path.join(home_path, 'run-{date}'.format(date=time.strftime('%y-%m-%d')))

    def hash_list(self):
        """
        Get all hash list
        :return: list
        """
        with open(self.hash_path) as f:
            return f.read().splitlines()

    def add_hash(self, sha):
        """
        Append hash to file
        :param sha:
        :return: True
        """
        with open(self.hash_path, 'a') as f:
            f.write('\r\n{line}'.format(line=sha))
        return True

    @staticmethod
    def copy(source, destination):
        """
        Copy file
        :param source:
        :param destination:
        :return:
        """
        if os.path.isfile(destination) is not True:
            logger.info('Not set configuration, setting....')
            with open(source) as f:
                content = f.readlines()
            with open(destination, 'w+') as f:
                f.writelines(content)
            logger.info('Config file set success({source})'.format(source=source))
        else:
            return


class Conf(object):
    def __init__(self, base_config_file):
        self.base_config_file = base_config_file

    def get(self, extend_config_file):
        config = configparser.ConfigParser()
        config.read(self.base_config_file)
        base_dict = config._sections
        config = configparser.ConfigParser()
        config.read(extend_config_file)
        target_dict = config._sections

        for b_key, b_value in base_dict.items():
            for t_key, t_value in target_dict.items():
                if b_key == t_key:
                    b_ports = b_value['ports'].split(',')
                    t_ports = t_value['ports'].split(',')
                    for t_port in t_ports:
                        if t_port not in b_ports:
                            b_ports.append(t_port)
                    base_dict[b_key]['ports'] = ','.join(b_ports)
        return base_dict


c_default = {
    'job_success': 0,
    'job_failed': 0,
    'found_count': 0,
    'list': []
}


def daily_run_data(data=None):
    run_data_path = Config().run_data_daily
    if data is None:
        if os.path.isfile(run_data_path):
            with open(run_data_path) as f:
                c = f.readline()
            c = json.loads(c)
            if c == '':
                c = c_default
        else:
            c = c_default
        return c
    else:
        with open(run_data_path, 'w') as f:
            d = json.dumps(data)
            f.writelines(d)
