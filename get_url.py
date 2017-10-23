#encoding=utf-8
import json
import os
import random 
import threading
import time
import traceback
import urllib2
import requests
import logging

class get_url:
    def __init__(self,proxy_pool=None,session=None):
        if session==None:
            self.session=requests.Session()
        else:
            self.session=session
        self.proxy_pool=proxy_pool
        
    def get(self,url,timeout=5):
        for i in range(10):      #用不同的代理最多尝试10次，获取到数据则直接返回
            proxy=self.proxy_pool.get_proxy()    #从代理池中获取一个代理
            try:
                response=self.session.get(url, proxies=proxy,timeout=timeout)
            except Exception, e:  
                #traceback.print_exc()
                self.proxy_pool.add_wrong(proxy)
                logging.warning('invalid-proxy')
                continue
            try:
                return response.text
            except Exception,e:
                logging.warning('get-response-text-exception')
                traceback.print_exc()
        raise Exception('my_exception',url)

