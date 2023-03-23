# -*- coding: utf-8 -*-
import re
import socket
import traceback
import requests
from github import Github, GithubException
from bs4 import BeautifulSoup
from .config import Config, public_mail_services, exclude_repository_rules, exclude_codes_rules
from math import floor, ceil
from .process import clone
from IPy import IP
from tld import get_tld
from .log import logger
from .sql import Sqluse,second_writer

regex_mail = r"([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)"
regex_host = r"@([a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)"
regex_pass = r"(pass|password|pwd)"
regex_title = r"<title>(.*)<\/title>"
regex_ip = r"^((([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))$"

# 增加单个页面的数量以减少请求的数量
# https://developer.github.com/v3/#pagination
# 每一页的数量（会影响到报告的效率）
per_page = 50

# TODO根据规则编号和页数预先计算的请求数
#
# pages * per_page * rules = requests
# 2 * 30 * 24 = 1440
#
# 默认扫描页数
default_pages = 4


class Engine(object):
    def __init__(self, token, type):
        """
        GitHub engine
        """
        self.token = token
        if type == "github":
            self.g = Github(login_or_token=token, per_page=per_page)
        self.rule_object = None
        self.rule_user = None
        self.code = ''
        # jquery/jquery
        self.full_name = ''
        self.sha = ''
        self.url = ''
        # src/attributes/classes.js
        self.path = ''

        self.result = None
        # 被排除掉的结果，为防止误报，将发送邮件人工核查
        self.exclude_result = None
        self.hash_list = None
        self.processed_count = None
        self.next_count = None

        self.second_result = {}


    def process_pages(self, pages_content, page, total):
        ## 将获取到到各类信息进行分类
        for index, content in enumerate(pages_content):
            current_i = page * per_page + index
            base_info = '[{k}] [{current}/{count}]'.format(k=self.rule_object.keyword, current=current_i, count=total)

            # 没有处理成功的，且遇到三个已处理的则跳过之后所有的
            if self.next_count == 0 and self.processed_count > 3:
                logger.info('{b} 遇到了 {pc} 已处理，跳过当前规则!'.format(b=base_info, pc=self.processed_count))
                return False
            # 获取扫描到到github url
            self.url = content.html_url
            print(self.url)
            # sha
            try:
                self.sha = content.sha
            except Exception as e:
                logger.warning('遇到了 {e}'.format(e=e))
                self.sha = ''
                self.url = ''

            if self.sha in self.hash_list:
                # pass already processed
                logger.info('{b} 已处理，跳过！ ({pc})'.format(b=base_info, pc=self.processed_count))
                self.processed_count += 1
                continue

            # path
            self.path = content.path

            # full name
            self.full_name = content.repository.full_name.strip()
            #if self._exclude_repository(self.full_name.lower(),self.path.lower()):
                # 传递排除存储库
                #logger.info('{b} 因路径而被排除，请跳过!'.format(b=base_info))
                #continue

            # code 包含对应页面的内容
            try:
                self.code = content.decoded_content.decode('utf-8')
                ## 对页面内容进行处理 去除图片 并保存其对应上下三行数据
                match_codes = self.codes()
                if len(match_codes) == 0:
                    logger.info('{b} 误报！未找到关键字！跳过！'.format(b=base_info))
                    continue
            except Exception as e:
                logger.warning('获取内容异常：{e} retrying...'.format(e=e))
                continue


            result = {
                'url': self.url,
                'match_codes': match_codes,
                'hash': self.sha,
                'code': self.code,
                'repository': self.full_name,
                'path': self.path,
            }
            if self._exclude_codes(match_codes):
                logger.info('{b} 代码可能没用，不要跳过，添加到列表中进行审核！'.format(b=base_info))
                self.exclude_result[current_i] = result
            else:
                self.result[current_i] = result

            # 独立进程下载代码
            #git_url = content.repository.html_url
            #clone(git_url, self.sha)
            logger.info('{b} 处理完成，下一个！'.format(b=base_info))
            self.next_count += 1

        return True

    def verify(self):
        try:
            ret = self.g.rate_limiting
            return True, 'TOKEN-PASSED: {r}'.format(r=ret)
        except GithubException as e:
            return False, 'TOKEN-FAILED: {r}'.format(r=e)

    def search(self, rule_object):
        ## 保存扫描规则
        self.rule_object = rule_object

        # 已经处理过的数量
        self.processed_count = 0
        # 处理成功的数量
        self.next_count = 0

        # max 5000 requests/H
        try:
            rate_limiting = self.g.rate_limiting
            rate_limiting_reset_time = self.g.rate_limiting_resettime
            logger.info('----------------------------')

            # RATE_LIMIT_REQUEST: rules * 1
            ext_query = ''
            if self.rule_object.extension is not None:
                for ext in self.rule_object.extension.split(','):
                    ext_query += '延期:{ext} '.format(ext=ext.strip().lower())
            keyword = '{keyword} {ext}'.format(keyword=self.rule_object.keyword, ext=ext_query)
            logger.info('Search keyword: {k}'.format(k=keyword))
            ## 调用github api 获取查询结果
            resource = self.g.search_code(keyword, sort="indexed", order="desc")
        except GithubException as e:
            msg = 'GitHub [search_code] exception(code: {c} msg: {m} {t}'.format(c=e.status, m=e.data, t=self.token)
            logger.critical(msg)
            return False, self.rule_object, msg

        logger.info('[{k}] 限速结果（剩余时间/总时间）：{rl}  限速复位时间： {rlr}'.format(k=self.rule_object.keyword, rl=rate_limiting, rlr=rate_limiting_reset_time))

        # RATE_LIMIT_REQUEST: rules * 1
        try:
            ## 获取第二页
            total = resource.totalCount
            logger.info('[{k}] 实际数量： {count}'.format(k=self.rule_object.keyword, count=total))
        except socket.timeout as e:
            return False, self.rule_object, e
        except GithubException as e:
            msg = 'GitHub [search_code] exception(code: {c} msg: {m} {t}'.format(c=e.status, m=e.data, t=self.token)
            logger.critical(msg)
            return False, self.rule_object, msg

        self.hash_list = Config().hash_list()

        default_pages = ceil(total/50)
        logger.info('[{k}] 预期的收购数量： {page}(Pages) * {per}(Per Page) = {total}(Total)'.format(k=self.rule_object.keyword,
                                                                                             page=default_pages,
                                                                                             per=per_page,
                                                                                             total=default_pages * per_page))
        if total < per_page:
            pages = 1
        else:
            pages = default_pages

        ## 此处开始循环将页面内容处理
        for page in range(pages):
            self.result = {}
            self.exclude_result = {}
            try:
                # RATE_LIMIT_REQUEST: pages * rules * 1
                pages_content = resource.get_page(page)
            except socket.timeout:
                logger.info('[{k}] [get_page] 超时，跳过以获取下一页！'.format(k=self.rule_object.keyword))
                continue
            except GithubException as e:
                msg = 'GitHub [get_page] exception(code: {c} msg: {m} {t}'.format(c=e.status, m=e.data, t=self.token)
                logger.critical(msg)
                return False, self.rule_object, msg

            logger.info('[{k}] 获取页面 {page} 的数据 {count}'.format(k=self.rule_object.keyword, page=page, count=len(pages_content)))
            ## 开始匹配
            if not self.process_pages(pages_content, page, total):
                # 若遇到处理过的，则跳过整个规则
                break
            ## 入库
            Sqluse(self.result, self.rule_object, 1, "", "").sqluse()
            # 每一页发送一份报告
            # Process(self.result, self.rule_object).process()
            # 暂时不发送可能存在的误报 TODO
            # Process(self.exclude_result, self.rule_object).process(True)

        logger.info('[{k}] 当前规则正在处理中，正常退出的过程！'.format(k=self.rule_object.keyword))
        return True, self.rule_object, len(self.result)

    ## 发包
    def http_https_get(self,m_url):
        try:
            m_headers = {
                'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:45.0) Gecko/20100101 Firefox/45.0'}
            requests.packages.urllib3.disable_warnings()
            m_res = requests.get(m_url, headers=m_headers, verify=False)
            m_res.encoding = 'utf-8'
            ## 响应码
            m_code = m_res.status_code
            return True, m_res.json()

        except Exception as e:
            return False, ""

    ## gitee 码云 获取信息摘取
    def gitee_process(self, n_textjson):
        try:
            n_projects = n_textjson["owner"]["html_url"]
            n_writer = n_textjson["owner"]["login"]
            for n_num in n_textjson["files"]:
                n_url = n_textjson["files"][n_num]["raw_url"]
                self.code = n_textjson["files"][n_num]["content"]
                continue
            ## 对页面内容进行处理 去除图片 并保存其对应上下三行数据
            match_codes = self.codes()
            if len(match_codes) == 0:
                logger.info('误报！未找到关键字！跳过！')
                return False, ""

            n_result = {
                'n_projects': n_projects,
                'n_writer': n_writer,
                'n_url': n_url,
                'n_value': match_codes
            }
            return True,n_result
        except Exception as e:
            logger.info('gitee ：gitee检索失败：{e}'.format(e=e))
            return False, ""


    ## gitee码云扫描
    def search_gitee(self,rule_object):
        ## 保存扫描规则
        self.rule_object = rule_object

        try:
            for num in range(1,500):
                n_url = "https://gitee.com/api/v5/search/gists?&q="+ self.rule_object.keyword +"&page="+ str(num) +"&per_page=20&order=desc"
                n_choose,n_textjsons = self.http_https_get(n_url)
                if len(n_textjsons) == 0:
                    return
                for n_textjson in n_textjsons:
                    n_choose, n_result = self.gitee_process(n_textjson)
                    if n_choose == False:
                        continue
                    Sqluse(n_result, self.rule_object, 1, "", "").gitte_sqladd()

        except Exception as e:
            logger.info('gitee ：gitee搜索失败：{e}'.format(e=e))


    ## 二次扫描起始位置
    def second_start(self,sql_writer, second_key, sql_task, sql_task_type):
        logger.info('-------->二次扫描开始<--------！')
        self.sql_task = sql_task
        self.sql_task_type = sql_task_type
        self.search_user(second_key, sql_writer)


    ## 开启二次匹配
    def search_user(self, second_key, second_user):
        n_code = second_key + "+ user:" + second_user
        try:
            resource = self.g.search_code(n_code, sort="indexed", order="desc")
        except GithubException as e:
            msg = 'GitHub [search_code] exception(code: {c} msg: {m} {t}'.format(c=e.status, m=e.data, t=self.token)
            logger.critical(msg)
            return False
        ## 获取第一页的内容
        try:
            # RATE_LIMIT_REQUEST: pages * rules * 1
            pages_content = resource.get_page(0)
        except socket.timeout:
            logger.info('[{k}] [get_page] 超时，跳过以获取下一页！'.format(k=second_key))
        except GithubException as e:
            msg = 'GitHub [get_page] exception(code: {c} msg: {m} {t}'.format(c=e.status, m=e.data, t=self.token)
            logger.critical(msg)
            return False
        ## 内容分类摘取
        self.seconde_process_pages(pages_content, second_key)
        ## 入库
        Sqluse(self.second_result, second_key, 2, self.sql_task, self.sql_task_type).sqluse()
        logger.info('当前正在处理中 二次遍历完成一次！')
        return True

    ##二次分类
    def seconde_process_pages(self, pages_content, second_key):
        num = 0
        next_resule = []
        ## 将获取到到各类信息进行分类
        for index, content in enumerate(pages_content):
            url = content.html_url
            path = content.path
            full_name = content.repository.full_name.strip()
            ## 清理重复项目
            if full_name in next_resule:
                continue
            next_resule.append(full_name)
            #if self._exclude_repository(full_name.lower(),path.lower()):
                # 传递排除存储库
            #   logger.info('因路径而被排除，请跳过!')
            #    continue
            # code 包含对应页面的内容
            try:
                code = content.decoded_content.decode('utf-8')
                ## 对页面内容进行处理 去除图片 并保存其对应上下三行数据
                match_codes = self._codesother("normal-match", code, second_key)
                if len(match_codes) == 0:
                    logger.info('误报！未找到关键字！跳过！')
                    continue
            except Exception as e:
                logger.warning('获取内容异常：{e} retrying...'.format(e=e))
                continue
            result = {
                'url': url,
                'match_codes': match_codes,
                'code': code,
                'repository': full_name,
                'path': path,
            }
            self.second_result[num] = result
            num = num + 1
        return True

    # 二段匹配关键字时使用
    def _codesother(self, rule_mode, code, keyword):
        # 去除图片的显示
        code = code.replace('<img', '')
        codes = code.splitlines()
        codes_len = len(codes)
        match_codes = []
        match_zerocode = []
        match_morestr = []
        n_len = 0
        ## 只匹配存在关键字的行
        if rule_mode == 'only-match':
            for n_code in codes:
                if keyword in n_code:
                        match_codes.append(n_code)
            return match_codes
        elif rule_mode == 'normal-match':
            # normal-match（匹配存在关键词的行及其上下1行）
            for idx, n_code in enumerate(codes):
                if keyword in n_code:
                    match_zerocode.append(n_code)
                    idxs = []
                    # prev lines
                    for i in range(-1, -0):
                        i_idx = idx + i
                        if i_idx in idxs:
                            continue
                        if i_idx < 0:
                            continue
                        if codes[i_idx].strip() == '':
                            continue
                        logger.debug('P:{x}/{l}: {c}'.format(x=i_idx, l=codes_len, c=codes[i_idx]))
                        idxs.append(i_idx)
                        match_codes.append(codes[i_idx])
                        n_len = n_len + len(codes[i_idx])
                    # current line
                    if idx not in idxs:
                        logger.debug('C:{x}/{l}: {c}'.format(x=idx, l=codes_len, c=codes[idx]))
                        match_codes.append(codes[idx])
                    # next lines
                    for i in range(1, 2):
                        i_idx = idx + i
                        if i_idx in idxs:
                            continue
                        if i_idx >= codes_len:
                            continue
                        if codes[i_idx].strip() == '':
                            continue
                        logger.debug('N:{x}/{l}: {c}'.format(x=i_idx, l=codes_len, c=codes[i_idx]))
                        idxs.append(i_idx)
                        match_codes.append(codes[i_idx])
                        n_len = n_len + len(codes[i_idx])
            return  match_zerocode

    def codes(self):
        # 去除图片的显示
        self.code = self.code.replace('<img', '')
        codes = self.code.splitlines()
        codes_len = len(codes)
        keywords = self._keywords()
        match_codes = []
        match_zerocode = []
        match_morestr = []
        n_len = 0
        if self.rule_object.mode == 'mail':
            return self._mail()
        elif self.rule_object.mode == 'only-match':
            # only match mode(只匹配存在关键词的行)
            for code in codes:
                for kw in keywords:
                    if kw in code:
                        match_codes.append(code)
            return match_codes
        elif self.rule_object.mode == 'normal-match':
            # normal-match（匹配存在关键词的行及其上下3行）
            for idx, code in enumerate(codes):
                for keyword in keywords:
                    if keyword in code:
                        match_zerocode.append(code)
                        idxs = []
                        # prev lines
                        for i in range(-3, -0):
                            i_idx = idx + i
                            if i_idx in idxs:
                                continue
                            if i_idx < 0:
                                continue
                            if codes[i_idx].strip() == '':
                                continue
                            logger.debug('P:{x}/{l}: {c}'.format(x=i_idx, l=codes_len, c=codes[i_idx]))
                            idxs.append(i_idx)
                            match_codes.append(codes[i_idx])
                            n_len = n_len + len(codes[i_idx])
                        # current line
                        if idx not in idxs:
                            logger.debug('C:{x}/{l}: {c}'.format(x=idx, l=codes_len, c=codes[idx]))
                            match_codes.append(codes[idx])
                        # next lines
                        for i in range(1, 4):
                            i_idx = idx + i
                            if i_idx in idxs:
                                continue
                            if i_idx >= codes_len:
                                continue
                            if codes[i_idx].strip() == '':
                                continue
                            logger.debug('N:{x}/{l}: {c}'.format(x=i_idx, l=codes_len, c=codes[i_idx]))
                            idxs.append(i_idx)
                            match_codes.append(codes[i_idx])
                            n_len = n_len + len(codes[i_idx])
            return match_codes
        else:
            # 匹配前20行
            return self.code.splitlines()[0:20]

    def _keywords(self):
        if '"' not in self.rule_object.keyword and ' ' in self.rule_object.keyword:
            return self.rule_object.keyword.split(' ')
        else:
            if '"' in self.rule_object.keyword:
                return [self.rule_object.keyword.replace('"', '')]
            else:
                return [self.rule_object.keyword]

    def _mail(self):
        logger.info('[{k}] mail rule'.format(k=self.rule_object.keyword))
        match_codes = []
        mails = []
        # 找到所有邮箱地址
        # TODO 此处可能存在邮箱账号密码是加密的情况，导致取不到邮箱地址
        mail_multi = re.findall(regex_mail, self.code)
        for mm in mail_multi:
            mail = mm.strip().lower()
            if mail in mails:
                logger.info('[SKIPPED] 邮件已处理完毕！')
                continue
            host = re.findall(regex_host, mail)
            host = host[0].strip()
            if host in public_mail_services:
                logger.info('[SKIPPED] 公共邮件服务！')
                continue
            mails.append(mail)

            # get mail host's title
            is_inner_ip = False
            if re.match(regex_ip, host) is None:
                try:
                    top_domain = get_tld(host, fix_protocol=True)
                except Exception as e:
                    logger.warning('get top domain exception {msg}'.format(msg=e))
                    top_domain = host
                if top_domain == host:
                    domain = 'http://www.{host}'.format(host=host)
                else:
                    domain = 'http://{host}'.format(host=host)
            else:
                if IP(host).iptype() == 'PRIVATE':
                    is_inner_ip = True
                domain = 'http://{host}'.format(host=host)
            title = '<Unknown>'
            if is_inner_ip is False:
                try:
                    response = requests.get(domain, timeout=4).content
                except Exception as e:
                    title = '<{msg}>'.format(msg=e)
                else:
                    try:
                        soup = BeautifulSoup(response, "html5lib")
                        if hasattr(soup.title, 'string'):
                            title = soup.title.string.strip()[0:150]
                    except Exception as e:
                        title = 'Exception'
                        traceback.print_exc()

            else:
                title = '<Inner IP>'

            match_codes.append("{mail} {domain} {title}".format(mail=mail, domain=domain, title=title))
            logger.info(' - {mail} {domain} {title}'.format(mail=mail, domain=domain, title=title))
        return match_codes

    def _exclude_repository(self, n_full_name, n_path):
        ret = False
        # 拼接完整的项目链接
        full_path = '{repository}/{path}'.format(repository=n_full_name, path=n_path)
        print(full_path)
        for err in exclude_repository_rules:
            if re.search(err, full_path) is not None:
                return True
        return ret

    @staticmethod
    def _exclude_codes(codes):
        ret = False
        for ecr in exclude_codes_rules:
            if re.search(ecr, '\n'.join(codes)) is not None:
                return True
        return ret