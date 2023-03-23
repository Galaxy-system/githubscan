# -*- coding: utf-8 -*-
import pymysql
import datetime
import re
import time
import base64
import html

from .log import logger
from .sqlconfig import sql_configread

"""
数据库：
Data_False  误报
Data_True   确认
Data_Waitie 待处理

n_task  n_task_type n_system  n_keyword   n_writer    n_project   n_url   n_value     n_time  n_type      n_remarks
任务      类型        平台类型    关键字      作者         项目        网址     内容         时间    二次扫描认证    备注 
"""

Data_Wait = "Data_Wait"
Data_True = "Data_True"
Data_False = "Data_False"
n_config = "n_config"

class Sqluse(object):
    def __init__(self, content, rule_object, n_num, sql_task, sql_task_type):
        self.content = content
        self.rule_object = rule_object
        self.n_num = n_num
        self.sql_task = sql_task
        self.sql_task_type = sql_task_type

    def sqluse(self):
        logger.info('Process count: {count}'.format(count=len(self.content)))
        if len(self.content) == 0:
            logger.info('none content for send mysql')
            return True
        connection = sql_try()
        if self.n_num == 1:
            self._sqladd(connection)
            connection.close()
            return True
        if self.n_num == 2:
            self._second_sqladdr(connection)
            connection.close()
            return True

    ## 关键字扫描
    def _sqladd(self,connection):
        ## 获取时间
        n_time = time.strftime("%Y-%m-%d", time.localtime())
        num = 0
        cursor = connection.cursor()
        n_keyword = self.rule_object.keyword
        n_task = self.rule_object.types
        n_task_type = self.rule_object.corp

        for i, v in self.content.items():
            n_project = v['repository']
            n_writer = n_project.split('/')[0]
            n_url = v['url']
            n_system = "Github"
            n_remarks = ""

            ## 判断项目是否在数据库存在重复
            num = self._num_sql(n_project,n_keyword,n_writer,cursor)
            ## 如果存在则跳出循环
            if num == True:
                logger.info('项目：{value} 重复'.format(value=n_project))
                return True

            if len(v['match_codes']) > 0:
                n_value = ''
                for c in v['match_codes']:
                    c = html.escape(c)
                    n_value += c + "<br>"

            ##base64加密处理
            n_values = base64.b64encode(n_value.encode('utf-8'))
            n_values = str(n_values, 'utf-8')

            sql = "INSERT INTO " + Data_Wait + " (n_task, n_task_type, n_system, n_keyword,n_writer,n_project,n_url,n_value,n_time,n_type,n_remarks) VALUES " \
                  + "( \"" + n_task + "\",\"" + n_task_type + "\",\"" + n_system + "\",\"" + n_keyword + "\",\"" + n_writer + "\",\"" + n_project + "\",\"" + n_url + "\",\"" + n_values + "\",\"" + n_time + "\",\"" + "first" + "\",\"" + n_remarks + "\" )"

            try:
                # 执行sql语句
                cursor.execute(sql)
                connection.commit()
                time.sleep(0.1)
            except pymysql.Error as e:
                logger.info('mysql 数据写入失败：{e}'.format(e=e))
        return True

    ## 关键字扫描
    def gitte_sqladd(self):
        connection = sql_try()
        ## 获取时间
        n_time = time.strftime("%Y-%m-%d", time.localtime())
        num = 0
        cursor = connection.cursor()
        n_keyword = self.rule_object.keyword
        n_task = self.rule_object.types
        n_task_type = self.rule_object.corp

        n_project = self.content["n_projects"]
        n_writer = self.content["n_writer"]
        n_url = self.content["n_url"]
        n_system = "Gitee"
        n_remarks = ""

        ## 判断项目是否在数据库存在重复
        num = self._num_sql(n_project,n_keyword,n_writer,cursor)
        ## 如果存在则跳出循环
        if num==True:
            logger.info('项目：{value} 重复'.format(value=n_project))
            return True

        if len(self.content["n_value"]) > 0:
            n_value = ''
            for c in self.content["n_value"]:
                c = html.escape(c)
                n_value += c + "<br>"

        if len(n_value) >= 5000:
            n_value = "数据过大，请手工查看"

        ##base64加密处理
        n_values = base64.b64encode(n_value.encode('utf-8'))
        n_values = str(n_values, 'utf-8')

        sql = "INSERT INTO " + Data_Wait + " (n_task, n_task_type, n_system, n_keyword,n_writer,n_project,n_url,n_value,n_time,n_type,n_remarks) VALUES " \
              + "( \"" + n_task + "\",\"" + n_task_type + "\",\"" + n_system + "\",\"" + n_keyword + "\",\"" + n_writer + "\",\"" + n_project + "\",\"" + n_url + "\",\"" + n_values + "\",\"" + n_time + "\",\"" + "first" + "\",\"" + n_remarks + "\" )"

        try:
            # 执行sql语句
            cursor.execute(sql)
            connection.commit()
            time.sleep(0.1)
            connection.close()
        except pymysql.Error as e:
            logger.info('mysql 数据写入失败：{e}'.format(e=e))
            connection.close()

        return True

    ## 二次扫描添加
    def _second_sqladdr(self, connection):
        ## 获取时间
        n_time = time.strftime("%Y-%m-%d", time.localtime())
        cursor = connection.cursor()

        n_keyword = self.rule_object

        for i, v in self.content.items():
            n_project = v['repository']
            n_writer = n_project.split('/')[0]
            n_url = v['url']
            n_remarks = ""
            n_system = "Github"

            ## 判断项目是否在数据库存在重复
            num = self._num_sql(n_project,n_keyword,n_writer,cursor)
            ## 如果存在则跳出循环
            if num == True:
                logger.info('项目：{value} 重复'.format(value=n_project))
                return True

            if len(v['match_codes']) > 0:
                n_value = ''
                for c in v['match_codes']:
                    c = html.escape(c)
                    n_value += c + "<br>"

            if len(n_value) >= 5000:
                n_value = "数据过大，请手工查看"

            ##base64加密处理
            n_values = base64.b64encode(n_value.encode('utf-8'))
            n_values = str(n_values, 'utf-8')

            sql = "INSERT INTO " + Data_Wait + " (n_task, n_task_type, n_system, n_keyword,n_writer,n_project,n_url,n_value,n_time,n_type,n_remarks) VALUES " \
                  + "( \"" +  self.sql_task + "\",\"" + self.sql_task_type + "\",\"" + n_system + "\",\"" +n_keyword + "\",\"" + n_writer + "\",\"" + n_project + "\",\"" + n_url + "\",\"" + n_values + "\",\"" + n_time + "\",\"" + "second" + "\",\"" + n_remarks + "\" )"

            try:
                # 执行sql语句
                cursor.execute(sql)
                connection.commit()
                time.sleep(0.1)
            except pymysql.Error as e:
                logger.info('mysql 数据写入失败2：{e}'.format(e=e))
        return True

    ## 判断数据库存储内容个数
    def _num_sql(self, n_project,n_keyword,n_writer, cursor):
        ## 获取时间
        n_time = time.strftime("%Y-%m-%d", time.localtime())

        try:

            sql = "select count(*) from " + Data_Wait + " where n_project = %s and n_writer = %s and n_keyword = %s"
            cursor.execute(sql, (n_project,n_writer,n_keyword))
            sql_num = cursor.fetchall()
            if int(sql_num[0][0]) >= 1:
                return True

            sql = "select count(*) from " + Data_True + " where n_project = %s and n_writer = %s and n_keyword = %s"
            cursor.execute(sql, (n_project,n_writer,n_keyword))
            sql_num = cursor.fetchall()
            if int(sql_num[0][0]) >= 1:
                return True

            sql = "select count(*) from " + Data_False + " where n_project = %s and n_writer = %s and n_keyword = %s"
            cursor.execute(sql, (n_project,n_writer,n_keyword))
            sql_num = cursor.fetchall()
            if int(sql_num[0][0]) >= 1:
                return True


        except pymysql.Error as e:
            logger.info('mysql 查询个数失败：{e}'.format(e=e))

        return False


###################################################===查询===#################################################
## 去重查任务
def sql_taskshow(n_need):
    connection = sql_try()
    cursor = connection.cursor()
    sql = "select distinct n_task from " + n_need
    try:
        cursor.execute(sql)
        sql_configs = cursor.fetchall()
    except pymysql.Error as e:
        print('mysql 查询配置信息：{e}'.format(e=e))
        connection.close()
    connection.close()
    return sql_configs

## 查询各个数据库信息
def sql_config(n_need):
    connection = sql_try()
    cursor = connection.cursor()
    sql = "select * from " + n_need
    try:
        cursor.execute(sql)
        sql_configs = cursor.fetchall()
    except pymysql.Error as e:
        print('mysql 查询配置信息：{e}'.format(e=e))
        connection.close()
    connection.close()
    return sql_configs

## 查询指定任务的信息并解码base64
def sql_taskmessage(n_table, n_task):
    list_back = []
    connection = sql_try()
    cursor = connection.cursor()
    try:
        sql = "select * from " + n_table + " where n_task =%s"
        cursor.execute(sql, (n_task))
        sql_messages = cursor.fetchall()
        for i in range(len(sql_messages)):
            n_value = str(sql_messages[i][7])
            missing_padding = 4 - len(n_value) % 4
            if missing_padding:
                n_value += '=' * missing_padding
            msql_basedecode = str(base64.b64decode(n_value))
            list_back.append([sql_messages[i][0],sql_messages[i][1],sql_messages[i][2],sql_messages[i][3],sql_messages[i][4],sql_messages[i][5],sql_messages[i][6],msql_basedecode,sql_messages[i][8],sql_messages[i][9],sql_messages[i][10]])
    except pymysql.Error as e:
        print('mysql 查询数据库信息：{e}'.format(e=e))
        connection.close()
    connection.close()
    return list_back

## 查询存在
def sql_SearchTaskAll(n_table, n_task, n_codeurl):
    connection = sql_try()
    cursor = connection.cursor()
    try:
        sql = "select * from " + n_table + " where n_task =%s and n_url=%s"
        cursor.execute(sql, (n_task,n_codeurl))
        sql_messages = cursor.fetchall()
    except pymysql.Error as e:
        print('mysql 查询数据库信息：{e}'.format(e=e))
        connection.close()
    connection.close()
    return sql_messages

## 二次循环作者查询
def second_writer(n_task,n_task_type):
    connection = sql_try()
    cursor = connection.cursor()
    sql = "select distinct n_writer from " + Data_Wait + " where n_task = \"" + n_task + "\" and n_task_type = \"" + n_task_type + "\" and n_system=\"Github\"  and n_type = \"first\" and  n_writer not in (select distinct n_writer from " + Data_Wait + " where n_type = \"second\")"
    try:
        cursor.execute(sql)
        sql_writers = cursor.fetchall()
        connection.close()
    except pymysql.Error as e:
        logger.info('mysql 查询个数失败：{e}'.format(e=e))
        connection.close()
    if len(sql_writers) == 0:
        return  False
    return sql_writers

## 读取配置信息
def read_config():
    connection = sql_try()
    sql = "select * from " + n_config + " where n_choose = %s"
    cursor = connection.cursor()
    try:
        cursor.execute(sql,("open"))
        sql_config = cursor.fetchall()
    except pymysql.Error as e:
        logger.info('mysql ：读取扫描信息失败{e}'.format(e=e))
        exit(0)
    return  sql_config

## 读取tocken信息
def read_tocken():
    connection = sql_try()
    sql = "select * from n_githubtocken where n_value = \"可用\" "
    cursor = connection.cursor()
    try:
        cursor.execute(sql)
        sql_tocken = cursor.fetchall()
    except pymysql.Error as e:
        logger.info('mysql ：读取扫描信息失败{e}'.format(e=e))
        exit(0)
    return  sql_tocken
###################################################===添加/删除/修改===#################################################
## 处理将等待处理的任务移到误报
def Opcode_ChooseMove(n_table, n_taskalls, n_message):
    for n_taskall in n_taskalls:
        n_task = n_taskall[0]
        n_task_type = n_taskall[1]
        n_system = n_taskall[2]
        n_keyword = n_taskall[3]
        n_writer = n_taskall[4]
        n_project = n_taskall[5]
        n_url = n_taskall[6]
        n_value = n_taskall[7]
        n_time = n_taskall[8]
        n_type = n_taskall[9]
        if len(n_message) != 0:
            n_remarks = n_message
        else:
            n_remarks = n_taskall[10]

        try:
            sql = "INSERT INTO " + n_table + " (n_task,n_task_type,n_system,n_keyword,n_writer,n_project,n_url,n_value,n_time,n_type,n_remarks) VALUES ( %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s )"
            connection = sql_try()
            cursor = connection.cursor()
            # 执行sql语句
            cursor.execute(sql,(n_task, n_task_type, n_system, n_keyword, n_writer, n_project, n_url, n_value, n_time, n_type, n_remarks))
            connection.commit()
        except pymysql.Error as e:
            connection.close()
            logger.info('mysql ：处理移动数据库失败：{e}'.format(e=e))
            return False
        connection.close()
        return True

## 添加备注信息
def Opcode_AddMessage(n_table, n_task,n_url, n_message):
    try:
        sql = "UPDATE " + n_table +" SET n_remarks =%s WHERE n_url =%s and n_task =%s"
        connection = sql_try()
        cursor = connection.cursor()
        # 执行sql语句
        cursor.execute(sql, (n_message, n_url, n_task))
        connection.commit()
    except pymysql.Error as e:
        connection.close()
        logger.info('mysql ：处理移动数据库失败：{e}'.format(e=e))
        return False
    connection.close()
    return True

## 删除原表数据
def Opcode_ChooseDelete(n_table, n_task, n_codeurl):
    try:
        connection = sql_try()
        cursor = connection.cursor()
        sql = "DELETE FROM " + n_table + " where n_task =%s and n_url=%s"

        cursor.execute(sql, (n_task, n_codeurl))
        connection.commit()
    except pymysql.Error as e:
        connection.close()
        logger.info('mysql ：删除原始数据失败：{e}'.format(e=e))
        return False
    connection.close()
    return True

## tocken判断是否可用
def Check_Tocken(n_back, tockens):
    try:
        connection = sql_try()
        cursor = connection.cursor()
        if n_back == True:
            n_back_html = "恭喜你！tocken验证成功"
            sql = "UPDATE n_githubtocken SET n_value =%s WHERE n_tocken =%s"
            # 执行sql语句
            cursor.execute(sql,("可用",tockens))
        else:
            n_back_html = "错误！tocken不可用"
            sql = "DELETE FROM n_githubtocken WHERE n_tocken = %s"
            # 执行sql语句
            cursor.execute(sql,(tockens))
        connection.commit()
    except pymysql.Error as e:
        connection.close()
        logger.info('mysql ：tocken操作失败：{e}'.format(e=e))
    connection.close()
    return n_back_html

##tocken添加
def Add_Tocken(n_tocken):
    try:
        sql = "INSERT INTO n_githubtocken (n_tocken, n_value) VALUES ( %s,%s)"
        connection = sql.sql_try()
        cursor = connection.cursor()
        # 执行sql语句
        cursor.execute(sql, (n_tocken, "待验证"))
        connection.commit()
    except pymysql.Error as e:
        connection.close()
        logger.info('mysql ：tocken添加失败：{e}'.format(e=e))
        return "异常！添加失败！"
    connection.close()
    return "恭喜你！添加成功"

## 关键字搜索开关修改
def Change_Keywords(n_choose,n_task,n_keywords):
    try:
        sql = "UPDATE " + n_config + " SET n_choose =%s WHERE n_keyword=%s and n_task=%s"
        connection = sql_try()
        cursor = connection.cursor()
        # 执行sql语句
        cursor.execute(sql, (n_choose, n_keywords, n_task))
        connection.commit()
    except pymysql.Error as e:
        connection.close()
        logger.info('mysql ：关键字搜索开关失败：{e}'.format(e=e))
        return "错误！修改失败"
    connection.close()
    return "恭喜你！修改成功！"

## 删除关键字
def Delect_Config(n_task,n_task_type):
    try:
        sql = "DELETE FROM " + n_config + " WHERE n_task = %s and n_task_type = %s"
        connection = sql_try()
        cursor = connection.cursor()
        # 执行sql语句
        cursor.execute(sql, (n_task,n_task_type))
        connection.commit()

        sql = "DELETE FROM " + Data_False + " WHERE n_task = %s and n_task_type = %s"
        connection = sql_try()
        cursor = connection.cursor()
        # 执行sql语句
        cursor.execute(sql, (n_task, n_task_type))
        connection.commit()

        sql = "DELETE FROM " + Data_True + " WHERE n_task = %s and n_task_type = %s"
        connection = sql_try()
        cursor = connection.cursor()
        # 执行sql语句
        cursor.execute(sql, (n_task, n_task_type))
        connection.commit()

        sql = "DELETE FROM " + Data_Wait + " WHERE n_task = %s and n_task_type = %s"
        connection = sql_try()
        cursor = connection.cursor()
        # 执行sql语句
        cursor.execute(sql, (n_task, n_task_type))
        connection.commit()
    except pymysql.Error as e:
        connection.close()
        logger.info('mysql ：关键字删除失败：{e}'.format(e=e))
        return "错误！删除失败！"
    connection.close()
    return "恭喜你！删除成功！"

## 添加扫描关键字
def Add_Config(n_task, n_task_type, n_keyword, n_mode, n_extension, n_secondkeyword, n_choose):
    try:
        sql = "INSERT INTO n_config (n_task, n_task_type, n_keyword, n_mode, n_extension, n_secondkeyword, n_choose) VALUES ( %s,%s,%s,%s,%s,%s,%s )"
        connection = sql_try()
        cursor = connection.cursor()
        # 执行sql语句
        cursor.execute(sql, (n_task, n_task_type, n_keyword, n_mode, n_extension, n_secondkeyword, n_choose))
        connection.commit()
    except pymysql.Error as e:
        connection.close()
        logger.info('mysql ：关键字添加失败：{e}'.format(e=e))
        return "错误！添加失败"
    connection.close()
    return "恭喜你！添加成功！"

## 修改密码
def Change_Passwd(n_username, n_newpassword, n_oldpassword):
    try:
        sql = "select * from n_login where login_user = %s and login_passwd = %s"
        connection = sql_try()
        cursor = connection.cursor()
        cursor.execute(sql, (n_username, n_oldpassword))
        sql_login = cursor.fetchall()
        if len(sql_login) == 0:
            return "错误！请检查用户名密码！"

        sql = "UPDATE n_login SET login_passwd =%s WHERE login_user = %s"
        cursor.execute(sql, (n_newpassword, n_username))
        connection.commit()
    except pymysql.Error as e:
        connection.close()
        logger.info('mysql ：修改密码失败：{e}'.format(e=e))
        return "错误！修改失败"
    connection.close()
    return  "恭喜！修改成功～！"

## 登陆检测用户名密码
def Check_User(n_username, n_password):
    try:
        sql = "select * from n_login where login_user=%s and login_passwd=%s"
        connection = sql_try()
        cursor = connection.cursor()
        cursor.execute(sql, (n_username, n_password))
        sql_login = cursor.fetchall()
        if len(sql_login) == 0:
            return "错误！账号密码错误","/"
    except pymysql.Error as e:
        connection.close()
        logger.info('mysql ：登陆校验失败：{e}'.format(e=e))
        return "错误！数据库出错","/"
    connection.close()
    return "恭喜你！登陆成功～！","/OpenCodeSearch/index"

###################################################===功能===#################################################
## 测试mysql是否成功连接 表是否创建成功
def sql_try():
    try:
        username, password, host, port, db = sql_configread()
        connection = pymysql.connect(host,username,password,db,port,charset='utf8')
        logger.info('mysql 连接成功')
    except pymysql.Error as e:
        logger.info('mysql 连接失败：{e}'.format(e=e))
        exit(0)
    return connection

