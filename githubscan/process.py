# -*- coding: utf-8 -*-
import os
import time
import shutil
import subprocess
from jinja2 import utils
from .config import Config, get, daily_run_data, code_path
from .log import logger


class Process(object):
    def __init__(self, content, rule_object):
        """
        Process content
        :param content:
        :param rule_object:
        """
        self.content = content
        self.rule_object = rule_object

    def process(self, maybe_mistake=False):
        logger.info('Process count: {count}'.format(count=len(self.content)))
        ret_mail = self._send_mail(maybe_mistake)
        if ret_mail:
            for i, v in self.content.items():
                Config().add_hash(v['hash'])
                logger.debug('{hash} add success!'.format(hash=v['hash']))
            logger.debug('send mail success!')
        return ret_mail

    ## 写入mysql 数据库中
    def _send_mysql(self):
        if len(self.content) == 0:
            logger.info('none content for send mail')
            return True
        return True
    def _send_mail(self, maybe_mistake=False):
        """
        Send mail
        :return: boolean
        """
        if len(self.content) == 0:
            logger.info('none content for send mail')
            return True
        if maybe_mistake:
            title = '〔GSIL〕MB_MT '
        else:
            title = '〔GSIL〕'
        subject = '{title}[{types}] [{rule_name}] {count}'.format(title=title, types=self.rule_object.types, rule_name=self.rule_object.corp, count=len(self.content))
        to = get('mail', 'to')
        cc = get('mail', 'cc')
        html = '<h3>Rule: {rule_regex} Count: {count} Datetime: {datetime}</h3>'.format(rule_regex=self.rule_object.keyword, datetime=time.strftime("%Y-%m-%d %H:%M:%S"), count=len(self.content))
        for i, v in self.content.items():
            html += '<h3>({i})<a href="{url}">{hash}</a> {repository}/{path}</h3>'.format(i=i, url=v['url'], hash=v['hash'][:6], repository=v['repository'], path=v['path'])
            if len(v['match_codes']) > 0:
                code = ''
                for c in v['match_codes']:
                    code += '{c}<br>'.format(c=utils.escape(c))
                html += '<code>{code}</code><hr>'.format(code=code)
            self._save_file(v['hash'], v['code'])
        html += '</table></body>'
        return html

    @staticmethod
    def _save_file(sha, data):
        """
        Save content to file
        :param sha:
        :param data:
        :return:
        """
        with open(os.path.join(Config().data_path, sha), 'w+', encoding='utf-8') as f:
            f.writelines(data)
        return True


def clone(git_url, dist_dir):
    # 下载会非常占用磁盘
    if get('github', 'clone').strip().lower() == 'false':
        return
    path = os.path.join(code_path, dist_dir)
    if os.path.isdir(path):
        shutil.rmtree(path)
    param = ['/usr/bin/git', 'clone', git_url, path]
    print(' '.join(param))
    assert subprocess.Popen(param, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
