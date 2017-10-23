#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
The MIT License (MIT)

Copyright (c) 2015-2016 7sDream

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

import getpass
import importlib
import json
import time
try:
    from urllib import urlencode
except ImportError:
    from urllib.parse import urlencode
import requests
import functools
import re
import os
import sys
from requests import Session
from requests.packages.urllib3.util import Retry

Zhihu_URL = 'https://www.zhihu.com'
Login_URL = Zhihu_URL + '/login/email'
Captcha_URL = Zhihu_URL + '/captcha.gif'
Default_Header = {'X-Requested-With': 'XMLHttpRequest',
                  'Referer': 'http://www.zhihu.com',
                  'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; '
                                'rv:39.0) Gecko/20100101 Firefox/39.0',
                  'Host': 'www.zhihu.com'}


class ZhihuClient:

    """知乎客户端类，内部维护了自己专用的网络会话，可用cookies或账号密码登录."""

    def __init__(self, cookies=None):
        """创建客户端类实例.
        :param str cookies: 见 :meth:`.login_with_cookies` 中 ``cookies`` 参数
        :return: 知乎客户端对象
        :rtype: ZhihuClient
        """
        self._session = requests.Session()
        self._session.headers.update(Default_Header)
        self.proxies = None
        if cookies is not None:
            assert isinstance(cookies, str)
            self.login_with_cookies(cookies)

    # ===== login staff =====

    @staticmethod
    def _get_captcha_url():
        params = {
            'r': str(int(time.time() * 1000)),
            'type': 'login',
        }
        return Captcha_URL + '?' + urlencode(params)

    def get_captcha(self):
        """获取验证码数据。
        :return: 验证码图片数据。
        :rtype: bytes
        """
        self._session.get(Zhihu_URL)
        r = self._session.get(self._get_captcha_url())
        return r.content

    def login(self, email, password, captcha=None):
        """登陆知乎.
        :param str email: 邮箱
        :param str password: 密码
        :param str captcha: 验证码, 默认为None，表示不提交验证码
        :return:
            ======== ======== ============== ====================
            元素序号 元素类型 意义           说明
            ======== ======== ============== ====================
            0        int      是否成功       0为成功，1为失败
            1        str      失败原因       登录成功则为空字符串
            2        str       cookies字符串 登录失败则为空字符串
            ======== ======== ============== ====================
        :rtype: (int, str, str)
        """
        data = {'email': email, 'password': password,
                'remember_me': 'true'}
        if captcha is not None:
            data['captcha'] = captcha
        r = self._session.post(Login_URL, data=data)
        j = r.json()
        code = int(j['r'])
        message = j['msg']
        cookies_str = json.dumps(self._session.cookies.get_dict()) \
            if code == 0 else ''
        return code, message, cookies_str

    def login_with_cookies(self, cookies):
        """使用cookies文件或字符串登录知乎
        :param str cookies:
            ============== ===========================
            参数形式       作用
            ============== ===========================
            文件名         将文件内容作为cookies字符串
            cookies 字符串  直接提供cookies字符串
            ============== ===========================
        :return: 无
        :rtype: None
        """
        if os.path.isfile(cookies):
            with open(cookies) as f:
                cookies = f.read()
        cookies_dict = json.loads(cookies)
        self._session.cookies.update(cookies_dict)
        # return self.session()

    def login_in_terminal(self, need_captcha=False, use_getpass=True):
        """不使用cookies，在终端中根据提示登陆知乎
        :param bool need_captcha: 是否要求输入验证码，如果登录失败请设为 True
        :param bool use_getpass: 是否使用安全模式输入密码，默认为 True，
            如果在某些 Windows IDE 中无法正常输入密码，请把此参数设置为 False 试试
        :return: 如果成功返回cookies字符串
        :rtype: str
        """
        print('====== zhihu login =====')

        email = raw_input('email: ')
        if use_getpass:
            password = getpass.getpass('password: ')
        else:
            password = input("password: ")

        if need_captcha:
            captcha_data = self.get_captcha()
            with open('captcha.gif', 'wb') as f:
                f.write(captcha_data)

            print('please check captcha.gif for captcha')
            captcha = raw_input('captcha: ')
            os.remove('captcha.gif')
        else:
            captcha = None

        print('====== logging.... =====')

        code, msg, cookies = self.login(email, password, captcha)

        if code == 0:
            print('login successfully')
        else:
            print(msg)

        return email, cookies

    def create_cookies(self, need_captcha=False, use_getpass=True):
        """在终端中执行登录流程，将 cookies 存放在文件中以便后续使用
        :param bool need_captcha: 登录过程中是否使用验证码， 默认为 False
        :param bool use_getpass: 是否使用安全模式输入密码，默认为 True，
            如果在某些 Windows IDE 中无法正常输入密码，请把此参数设置为 False 试试
        :return:
        """
        email, cookies_str = self.login_in_terminal(need_captcha, use_getpass)
        if cookies_str:
            with open('cookies/'+email+'.json', 'w') as f:
                f.write(cookies_str)
            print('cookies file created.')
        else:
            print('can\'t create cookies.')


if __name__ == '__main__':
    if sys.version_info[0] == 3:
        try:
            raw_input = input
        except NameError:
            pass
    zh = ZhihuClient(cookies=None)
    zh.create_cookies(need_captcha=True, use_getpass=True)
