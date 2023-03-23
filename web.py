# -*- coding: utf-8 -*-
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, render_template, url_for, request, redirect
from github import Github, GithubException
import datetime
import pymysql
import base64
import time
import html
from githubscan import sql
from githubscan import github
from githubscan.sqlconfig import sql_configread

######################## 配置信息公用 ########################
n_year  = datetime.datetime.now().year
n_month  = datetime.datetime.now().month
n_day  = datetime.datetime.now().day

n_time = str(n_year) + '.' + str(n_month) + '.' + str(n_day)
n_table = 'n_' + str(datetime.datetime.now().year)

## 数据库
stable_config = "n_config"
stable_wait = "Data_Wait"
stable_true = "Data_True"
stable_false = "Data_False"
stable_tocken = "n_githubtocken"
stable_login = "n_login"

## 扫描时间设置
scan_week = "1"
scan_hour = "14"
scan_minute = "00"
n_scheduler = None

app = Flask(__name__)

######################## 登陆页面Login ########################
## 登陆初始化界面
@app.route('/')
def index():
    return render_template('Login.html')

## 验证账号密码
@app.route('/admin/login', methods=['POST'])
def login():
    n_username = request.form['logname']
    n_password= request.form['logpass']
    n_back_html, n_bach_url = sql.Check_User(n_username, n_password)
    return render_template('back.html', n_back=n_back_html, n_backurl=n_bach_url)

## 修改密码界面
@app.route('/admin/change')
def admin_change():
    n_keyword = sql.sql_taskshow("n_config")
    return render_template('changepass.html', n_keyword=n_keyword)

## 修改密码
@app.route('/admin/changepassword', methods=['POST'] )
def admin_changepassword():
    n_username = request.form['username']
    n_oldpassword = request.form['oldpassword']
    n_newpassword = request.form['newpassword']
    n_back_html = sql.Change_Passwd(n_username, n_newpassword, n_oldpassword)
    return render_template('back.html', n_back=n_back_html, n_backurl="/admin/change")

######################## 代码库搜索初始页面OpenCode_index ########################
## 初始页面
@app.route('/OpenCodeSearch/index')
def OpenCode_index():
    ## 获取所有的项目
    n_config = sql.sql_taskshow(stable_config)
    return render_template('OpenCode_index.html', n_task=n_config)

######################## 展示任务OpenCode_Task ########################
## 展示界面
@app.route('/OpenCodeSearch/TaskShow')
def OpenCode_TaskShow():
    ## 获取所有的项目
    n_config = sql.sql_taskshow(stable_config)
    n_configall = sql.sql_config(stable_config)
    return render_template('OpenCode_Task.html', n_task=n_config, n_taskall=n_configall)

## 打开开关
@app.route('/OpenCodeSearch/taskonoff', methods=['POST'])
def OpenCode_TaskOnOff():
    n_task = request.form['task']
    n_keywords = request.form['keywords']
    n_change = request.form['change']

    n_back_html = sql.Change_Keywords(n_change, n_task, n_keywords)
    return render_template('back.html', n_back=n_back_html, n_backurl="/OpenCodeSearch/TaskShow")

## 删除任务+所有
@app.route('/OpenCodeSearch/deletetask', methods=['POST'])
def OpenCode_DeleteTask():
    n_task = request.form['task']
    n_task_type = request.form['task_type']
    n_back_html = sql.Delect_Config(n_task,n_task_type)
    return render_template('back.html', n_back=n_back_html, n_backurl="/OpenCodeSearch/TaskShow")

######################## 添加任务OpenCode_Add ########################
## 展示界面
@app.route('/OpenCodeSearch/TaskAddShow')
def OpenCode_TaskAddShow():
    ## 获取所有的项目
    n_config = sql.sql_taskshow(stable_config)
    return render_template('OpenCode_Add.html', n_task=n_config)

## 添加任务
@app.route('/OpenCodeSearch/TaskAdd', methods=['POST'])
def OpenCode_TaskAdd():
    n_task = request.form['task']
    n_task_type = request.form['task_type']
    n_keyword = request.form['keywords']
    n_mode = request.form['mode']
    n_extension = request.form['extension']
    n_secondkeyword = request.form['secondkeywords']
    n_choose = request.form['choose']

    if len(n_task)==0 or len(n_task_type)==0 or len(n_keyword)==0 or len(n_secondkeyword)==0 or len(n_choose)==0 or len(n_mode)==0:
        return render_template('back.html', n_back="参数错误！请重新输入～～！", n_backurl="/OpenCodeSearch/TaskAddShow")

    n_back_html = sql.Add_Config(n_task, n_task_type, n_keyword, n_mode, n_extension, n_secondkeyword, n_choose)

    return render_template('back.html', n_back=n_back_html, n_backurl="/OpenCodeSearch/TaskAddShow")


######################## 等待处理OpenCode_Wait ########################
## 展示界面
@app.route('/OpenCodeSearch/ShowWait/<n_task>', methods=['GET'])
def OpenCode_Wait(n_task):
    ## 获取所有的项目
    n_config = sql.sql_taskshow(stable_config)
    ## 查询待处理的内容
    n_data_waie = sql.sql_taskmessage(stable_wait,n_task)
    return render_template('OpenCode_Wait.html', n_task=n_config, n_value = n_data_waie)

## 丢入误报/确认泄漏数据库
@app.route('/OpenCodeSearch/changewait', methods=['POST'])
def OpenCode_WaitPutFalse():
    n_choose = False
    n_task = request.form['task']
    n_codeurl = request.form['codeurl']
    n_handle = request.form['handle']
    n_message = request.form['message']
    ## 读取数据
    n_TaskAll = sql.sql_SearchTaskAll(stable_wait, n_task, n_codeurl)

    if len(n_TaskAll) != 0:
        ## 写入数据
        if n_handle == "choosefalse":
            n_choose = sql.Opcode_ChooseMove(stable_false, n_TaskAll, n_message)
        elif n_handle == "choosetrue":
            n_choose = sql.Opcode_ChooseMove(stable_true, n_TaskAll, n_message)
        if n_choose == True:
            ## 删除原表数据
            n_choose = sql.Opcode_ChooseDelete(stable_wait, n_task, n_codeurl)
            if n_choose == True:
                return render_template('back.html', n_back="处理成功", n_backurl="/OpenCodeSearch/ShowWait/" + n_task)

    return render_template('back.html', n_back="处理失败，异常操作", n_backurl="/OpenCodeSearch/ShowWait/" + n_task)

######################## 确认OpenCode_True ########################
@app.route('/OpenCodeSearch/ShowTrue/<n_task>', methods=['GET'])
def OpenCode_True(n_task):
    ## 获取所有的项目
    n_config = sql.sql_taskshow(stable_config)
    ## 查询待处理的内容
    n_data_waie = sql.sql_taskmessage(stable_true,n_task)
    return render_template('OpenCode_True.html', n_task=n_config, n_value = n_data_waie)

## 丢入误报/确认泄漏数据库
@app.route('/OpenCodeSearch/changetrue', methods=['POST'])
def OpenCode_TruePut():
    n_task = request.form['task']
    n_codeurl = request.form['codeurl']
    n_handle = request.form['handle']
    n_message = request.form['message']

    if n_handle == "choosefalse":
        ## 读取数据
        n_TaskAll = sql.sql_SearchTaskAll(stable_true, n_task, n_codeurl)
        if len(n_TaskAll) != 0:
            n_choose = sql.Opcode_ChooseMove(stable_false, n_TaskAll, n_message)
            if n_choose == True:
                ## 删除原表数据
                n_choose = sql.Opcode_ChooseDelete(stable_true, n_task, n_codeurl)
                if n_choose == True:
                    return render_template('back.html', n_back="处理成功", n_backurl="/OpenCodeSearch/ShowTrue/" + n_task)
    elif n_handle == "addmessgae":
        if len(n_message) !=0:
            n_choose = sql.Opcode_AddMessage(stable_true, n_task, n_codeurl, n_message)
            if n_choose == True:
                return render_template('back.html', n_back="处理成功", n_backurl="/OpenCodeSearch/ShowTrue/" + n_task)

    return render_template('back.html', n_back="处理失败，异常操作", n_backurl="/OpenCodeSearch/ShowTrue/" + n_task)

######################## 误报处理OpenCode_False ########################
@app.route('/OpenCodeSearch/ShowFalse/<n_task>', methods=['GET'])
def OpenCode_False(n_task):
    ## 获取所有的项目
    n_config = sql.sql_taskshow(stable_config)
    ## 查询待处理的内容
    n_data_waie = sql.sql_taskmessage(stable_false,n_task)
    return render_template('OpenCode_False.html', n_task=n_config, n_value = n_data_waie)

## 丢入误报/确认泄漏数据库
@app.route('/OpenCodeSearch/changefalse', methods=['POST'])
def OpenCode_FalsePut():
    n_task = request.form['task']
    n_codeurl = request.form['codeurl']
    n_handle = request.form['handle']
    n_message = request.form['message']

    if n_handle == "choosetrue":
        ## 读取数据
        n_TaskAll = sql.sql_SearchTaskAll(stable_false, n_task, n_codeurl)
        if len(n_TaskAll) != 0:
            n_choose = sql.Opcode_ChooseMove(stable_true, n_TaskAll, n_message)
            if n_choose == True:
                ## 删除原表数据
                n_choose = sql.Opcode_ChooseDelete(stable_false, n_task, n_codeurl)
                if n_choose == True:
                    return render_template('back.html', n_back="处理成功", n_backurl="/OpenCodeSearch/ShowFalse/" + n_task)
    elif n_handle == "addmessgae":
        if len(n_message) !=0:
            n_choose = sql.Opcode_AddMessage(stable_false, n_task, n_codeurl, n_message)
            if n_choose == True:
                return render_template('back.html', n_back="处理成功", n_backurl="/OpenCodeSearch/ShowFalse/" + n_task)

    return render_template('back.html', n_back="处理失败，异常操作", n_backurl="/OpenCodeSearch/ShowFalse/" + n_task)

######################## 展示任务OpenCode_Setting ########################
## 展示界面
@app.route('/OpenCodeSearch/SystemSet')
def OpenCode_SystemSet():
    n_week = ""
    if scan_week == "0":
        n_week = "星期一"
    elif scan_week == "1":
        n_week = "星期二"
    elif scan_week == "2":
        n_week = "星期三"
    elif scan_week == "3":
        n_week = "星期四"
    elif scan_week == "4":
        n_week = "星期五"
    elif scan_week == "5":
        n_week = "星期六"
    elif scan_week == "6":
        n_week = "星期天"
    n_read = "当前设定扫描时间为每周的" + n_week + "，" + scan_hour + ":" + scan_minute + "执行扫描任务"

    ## 获取当前时间
    n_time = time.strftime("%b-%d-%Y %H:%M:%S", time.localtime())

    ## 获取所有的项目
    n_config = sql.sql_config(stable_config)
    n_tocken = sql.sql_config(stable_tocken)

    return render_template('OpenCode_Setting.html', n_task=n_config, n_tocken =n_tocken, n_read=n_read, n_time=n_time)

## 添加tocken
@app.route('/system/add_tocken', methods=['POST'])
def add_tocken():
    n_tocken = request.form['n_tocken']

    if n_tocken == "":
        return render_template('back.html', n_back ="不能为空", n_backurl="/OpenCodeSearch/SystemSet")

    n_back_html = sql.Add_Tocken(n_tocken)

    return render_template('back.html', n_back = n_back_html, n_backurl="/OpenCodeSearch/SystemSet")


## 添加时间
@app.route('/system/add_time', methods=['POST'])
def add_time():
    global scan_week
    global scan_hour
    global scan_minute
    global n_scheduler
    scan_week = request.form['exec_everyweek_day']
    n_hour = request.form['exec_everyweek_time']
    scan_week = html.escape(scan_week)
    n_hour = html.escape(n_hour)

    n_time = n_hour.split(':')
    scan_hour = n_time[0]
    scan_minute = n_time[1]

    try:
        n_scheduler.shutdown(wait=False)
        n_scheduler = BackgroundScheduler()
        n_scheduler.add_job(github, 'cron', month='1-12', day_of_week=scan_week, hour=scan_hour, minute=scan_minute,id="githubscan")
        # 启动调度任务
        n_scheduler.start()
    except Exception as e:
        return render_template('back.html', n_back="设置时间失败！", n_backurl="/OpenCodeSearch/SystemSet")

    return render_template('back.html', n_back ="恭喜你！时间设置成功", n_backurl="/OpenCodeSearch/SystemSet")

## tocken认证接口
def verify(tockens):
    g = Github(login_or_token=tockens, per_page=50)
    try:
        ret = g.rate_limiting
        return True
    except GithubException as e:
        return False

## tocken验证
@app.route('/tocken/<tockens>', methods=['GET'])
def check_tocken(tockens):
    n_back = verify(tockens)
    n_back_html = sql.Check_Tocken(n_back, tockens)

######################## 其他 ########################
## 404页面
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404
## 500页面
@app.errorhandler(500)
def page_error(e):
    return render_template('500.html'), 500
######################## 入口位置 ########################
##设置启动
def job_start():
    global n_scheduler
    try:
        # 创建后台执行的 schedulers
        n_scheduler = BackgroundScheduler()
        # 添加调度任务
        # 在每年 1-12 月份中的每个星期一 00:00, 01:00, 02:00 和 03:00 执行任务
        n_scheduler.add_job(github, 'cron', month='1-12', day_of_week=scan_week, hour=scan_hour, minute=scan_minute,id="githubscan")
        # 启动调度任务
        n_scheduler.start()
    except Exception as e:
        print("任务启动失败")
        exit(0)


if __name__ == '__main__':
    #job_start()
    #github()
    ##,use_reloader=False
    app.run(host='0.0.0.0',port=5000,debug=True)
