#encoding=utf-8
import requests
import re
import threading
import traceback
import time
import urllib2
import logging

class proxy_pool:
    def __init__(self,timeout=5):
        self.timeout=timeout
        user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5)'  
        self.headers = {'User-Agent': user_agent}  
        self.proxy_list=[]     #存储proxy列表(代理列表)
        self.proxy_times={}    #存储proxy被使用的总次数及代理出错的次数
        self.stop=False        #是否要停止add_proxy_thread线程的标志
        self.index=0           #当前要获取的代理的在代理列表中的下标 
        self.mutex=threading.Lock()    #多线程互斥锁，使对proxy_list的操作不致混乱
        self.add_proxy_thread=threading.Thread(target=self.add_proxies)    #爬取代理网站，获取代理的线程
        self.add_proxy_thread.daemon=True        #设置该线程为daemon，即主程序退出后，该线程也退出
        self.add_proxy_thread.start()
        logging.info('add proxy start done')
        #self.add_proxy_thread.join()
        
    def get_size(self):
        return len(self.proxy_list)
        
    def get_proxies(self):
        return self.proxy_list
    
    def str2proxy(self,s):              #将字符串转换为代理字典
        return {'http':s,'https':s}
        
    def proxy2str(self,proxy):          #将代理转换成字符串，以在proxy_times字典中作为键使用
        return proxy['http']
        
    def add_times(self,proxy):          #增加某代理的使用总次数记录
        try:
            self.proxy_times[self.proxy2str(proxy)]['times']+=1
        except Exception,e:
            pass
            
    def add_wrong(self,proxy):          #增加某代理的代理出错次数记录
        try:
            self.proxy_times[self.proxy2str(proxy)]['wrong']+=1
        except Exception,e:
            pass
    
    def get_proxy(self):              #从代理列表中获取一个代理
        self.mutex.acquire()          #获取互斥锁
        try:    
            if self.proxy_list:
                self.index%=len(self.proxy_list)
                p=self.proxy_list[self.index]
                self.index+=1
                self.add_times(p)
                logging.debug(str(self.index))
                return p
            logging.warning('None-proxy')       #代理列表为空则返回None
            return None
        except Exception,e:
            pass 
        finally:
            self.mutex.release()      #释放互斥锁
        
    def remove(self,proxy):           #从代理列表中移除一个代理
        if proxy==None:
            return
        try:
            self.mutex.acquire()
            self.proxy_list.remove(proxy)
        except Exception,e:
            pass
        finally:
            self.mutex.release()

    def remove_wrong(self):           #移除不可用的或经常出错的代理
        try:
            for p in self.proxy_list:
                t=self.proxy_times[self.proxy2str(p)]
                if t['times']<=10:    #使用总次数小于10时，先不移除
                    continue
                if t['wrong']/float(t['times'])>0.5:    #出错率大于50%，则移除
                    self.remove(p)
                logging.debug('remove success')
        except Exception,e:
            traceback.print_exc()
            logging.debug('remove wrong error occured.')
            
    def test_proxy(self,ip,port):     #测试爬取到的一个代理是否可用
        sess = requests.session() 
        sess.headers.update(self.headers)
        proxy = {'http': ip+ ':' + port, 'https': ip + ':' + port}
        url = "http://ip.chinaz.com/getip.aspx"  #用来测试IP是否可用的url  
        try:
            response = sess.get(url, proxies=proxy, timeout=self.timeout)  
            if proxy not in self.proxy_list:
                self.mutex.acquire()
                self.proxy_list.append(proxy)
                self.mutex.release()
            s=self.proxy2str(proxy)
            if s not in self.proxy_times:
                self.proxy_times[s]={}
                self.proxy_times[s]['times']=0
                self.proxy_times[s]['wrong']=0
        except Exception, e:  
            pass
                
    def add_page_proxies(self,page_num):        #解析代理网站的一个页面，获取页面中的代理
        session = requests.session()
        session.headers.update(self.headers)
        try:
            page_response=session.get("http://www.ip181.com/daili/"+str(page_num)+".html",timeout=self.timeout)
        except Exception,e:
            logging.warning('can not get ip181 page '+str(page_num))
            return 
        #用正则表达式解析页面，获取代理列表
        pros=re.findall(r'<tr[^>]+?>\s+<td>([^<]+?)</td>\s+<td>(\d+)</td>\s+<td>[^<]+?</td>\s+<td>HTTP,HTTPS</td>.+?</tr>',page_response.text,re.S)
        #以多线程测试解析到的代理
        threads=[]
        for pro in pros:  
            new_test_thread=threading.Thread(target=self.test_proxy,args=(pro[0],pro[1]))
            threads.append(new_test_thread)
        for thr in threads:
            thr.start()
        for thr in threads:
            thr.join()
        
    def add_proxies(self):            #从代理网站获取代理
        sleep_seconds=5
        while True:
            for itera in range(360):
                if self.stop==True:
                    exit(0)
                if (itera*sleep_seconds)%(5*60)==0:
                    self.add_page_proxies(1)
                if (itera*sleep_seconds)%(10)==0:
                    self.remove_wrong()
                if (itera*sleep_seconds)%(20)==0:
                    self.add_page_proxies(itera/4+1)                
                    logging.debug('proxies num: '+str(len(self.proxy_list)))
                time.sleep(sleep_seconds)

