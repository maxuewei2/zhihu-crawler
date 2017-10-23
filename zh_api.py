#encoding=utf-8
from zhihu_client import ZhihuClient
import json
import os
import random 
import threading
import time
import traceback
import Queue
import proxy_pool
import get_url
import logging

class ZhihuAPI:
    """
        获取用户的信息：
            先获取用户的profile，从中得到topic、question、followee、follower的数量。
            然后分别获取topic、question、followee、follower信息。
                由于要获取的内容可能极多(如一个用户可能关注了几万个问题)，故而无法一次全部获取，所以需分多次获取。
                如，若要获取用户关注的所有问题，先从profile中得知，该用户共关注了10000个问题，
                每次获取时，指定offset和limit，获取从offset开始的limit个。直至全部获取到。
    """
    def __init__(self,cookie_file_name,proxy_pool,get_batch_size,sleep_seconds_between_batch):
        self.client = ZhihuClient(cookie_file_name)
        self.session=self.client._session
        self.proxy_pool=proxy_pool
        self.get_url=get_url.get_url(self.proxy_pool,self.session)
        self.get_batch_size=get_batch_size
        self.sleep_seconds_between_batch=sleep_seconds_between_batch
        
    def load_json(self,url,url_type):    #给定url及要获取的信息类型，返回得到的json对象
        for i in range(10):              #尝试10次
            try:
                j=json.loads(self.get_url.get(url))
                if 'data' not in j and url_type!='profile':     #如果返回对象的格式错误
                    continue
                return j
            except Exception,e:
                logging.error('url-load-json-error')
        logging.error('can-not-get-%s' %url_type)
        return None
        #raise Exception('my_exception')
        
    def get_user_profile(self,user_id):               #获取用户的profile，即个人信息
        pro_url='https://www.zhihu.com/api/v4/members/'+user_id+'?include=locations,employments,gender,educations,business,voteup_count,thanked_Count,follower_count,following_count,cover_url,following_topic_count,following_question_count,following_favlists_count,following_columns_count,avatar_hue,answer_count,articles_count,pins_count,question_count,columns_count,commercial_question_count,favorite_count,favorited_count,logs_count,marked_answers_count,marked_answers_text,message_thread_token,account_status,is_active,is_bind_phone,is_force_renamed,is_bind_sina,is_privacy_protected,sina_weibo_url,sina_weibo_name,show_sina_weibo,is_blocking,is_blocked,is_following,is_followed,mutual_followees_count,vote_to_count,vote_from_count,thank_to_count,thank_from_count,thanked_count,description,hosted_live_count,participated_live_count,allow_message,industry_category,org_name,org_homepage,badge[?(type=best_answerer)].topics'
        return self.load_json(pro_url,'profile')
        
    def get_user_topics(self,user_id,offset,limit,gqueue):         #获取用户关注的topic(话题)
        topics_url='https://www.zhihu.com/api/v4/members/'+user_id+'/following-topic-contributions?include=data[*].topic.introduction&offset='+str(offset)+'&limit='+str(limit)
        j=self.load_json(topics_url,'topic')
        gqueue.put((offset,j)) #将获取到的json对象和offset值放在一起，组成元组，放入队列gqueue中
        
    def get_user_questions(self,user_id,offset,limit,gqueue):          #获取用户关注的topic(话题)
        questions_url='https://www.zhihu.com/api/v4/members/'+user_id+'/following-questions?include=data[*].created,answer_count,follower_count,author&offset='+str(offset)+'&limit='+str(limit)
        j=self.load_json(questions_url,'question')
        gqueue.put((offset,j))
    
    def get_user_followers(self,user_id,offset,limit,gqueue):#获取用户关注的follwers (the ones that follow this user)
        followers_url='https://www.zhihu.com/api/v4/members/'+user_id+'/followers?include=data[*].answer_count,articles_count,gender,follower_count,is_followed,is_following,badge[?(type=best_answerer)].topics&offset='+str(offset)+'&limit='+str(limit)
        j=self.load_json(followers_url,'follower')
        gqueue.put((offset,j))
    
    def get_user_followees(self,user_id,offset,limit,gqueue):#获取用户关注的follwees (the ones that this user follows)
        followees_url='https://www.zhihu.com/api/v4/members/'+user_id+'/followees?include=data[*].answer_count,articles_count,gender,follower_count,is_followed,is_following,badge[?(type=best_answerer)].topics&offset='+str(offset)+'&limit='+str(limit)
        j=self.load_json(followees_url,'followee')
        gqueue.put((offset,j))
    
    def get_user_all(self,func,user_id,count):        #获取用户某项信息的全部内容
        gqueue=Queue.Queue()             #多线程获取，每个线程都将获取到的内容放在队列中
        limit=20
        offset=0
        for i in range(int(count/limit/self.get_batch_size+1)):
            ts=[]
            for j in range(self.get_batch_size):
                if offset>=count:
                    break
                t=threading.Thread(target=func,args=(user_id,offset,limit,gqueue))
                ts.append(t)
                offset+=limit
            for t in ts:
                t.start()
            for t in ts:
                t.join()
            if self.sleep_seconds_between_batch:
                time.sleep(self.sleep_seconds_between_batch)
        #将多线程存储在队列中的内容取出来，并按照offset排序
        ret=[]
        while not gqueue.empty():
            ret.append(gqueue.get())
        ret=sorted(ret,key=lambda a:a[0])
        #将排序后的内容取出，将其中的data部分组装成一个列表
        data=[]
        for a in ret:
            try:
                data.extend(a[1]['data'])
            except Exception,e:
                logging.error('get-None-data')
                pass
        return data
    
    def get_user_all_followees(self,user_id,count,dqueue):
        all_followees=self.get_user_all(self.get_user_followees,user_id,count)
        dqueue.put(('followee',all_followees))
    
    def get_user_all_followers(self,user_id,count,dqueue):
        all_followers=self.get_user_all(self.get_user_followers,user_id,count)
        dqueue.put(('follower',all_followers))
    
    def get_user_all_topics(self,user_id,count,dqueue):
        all_topics=self.get_user_all(self.get_user_topics,user_id,count)
        dqueue.put(('topic',all_topics))
    
    def get_user_all_questions(self,user_id,count,dqueue):
        all_questions=self.get_user_all(self.get_user_questions,user_id,count)
        dqueue.put(('question',all_questions))
        
    def get_user(self,user_id):       #获取特定用户的所有信息
        user={}
        profile=self.get_user_profile(user_id)    #先获取用户的profile
        try:
            following_count=profile["following_count"]        #从profile中获取following_count，following_topic_count等
            #follower_count=profile["follower_count"]
            question_count=profile["following_question_count"]
            topic_count=profile["following_topic_count"]
        except Exception,e:
            traceback.print_exc()
            logging.error(profile)
            logging.error('profile-error')
            #exit(0)
            uqueue.put((user_id,None))
            return
        #开三个线程，同时获取followee、topic、question数据
        queue=Queue.Queue()
        user_followees_thread=threading.Thread(target=self.get_user_all_followees,args=(user_id,following_count,queue))
        #user_followers_thread=threading.Thread(target=self.get_user_all_followers,args=(user_id,follower_count,queue))
        user_topics_thread=threading.Thread(target=self.get_user_all_topics,args=(user_id,topic_count,queue))
        user_questions_thread=threading.Thread(target=self.get_user_all_questions,args=(user_id,question_count,queue))
        
        user_followees_thread.start()
        user_topics_thread.start()
        user_questions_thread.start()
        
        user_followees_thread.join()
        user_topics_thread.join()
        user_questions_thread.join()
        ret=[]
        while not queue.empty():
            ret.append(queue.get())
        if len(ret)!=3:
            logging.error('not-get-user-all-error')
            return None
        ret=sorted(ret,key=lambda a:a[0])
        user_data={}
        user_data['profile']=profile
        user_data['followee']=ret[0][1]
        user_data['question']=ret[1][1]
        user_data['topic']=ret[2][1]
        return user_data

if __name__=='__main__':
    proxy_pool=proxy_pool.proxy_pool()
    zh=ZhihuAPI('cookies.json',proxy_pool)
    q=Queue.Queue()
    start_time=time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())
    print(start_time)
    try:
        zh.get_user('yatesxu',q)
    except Exception,e:
        traceback.print_exc()
        exit(0)
    start_time=time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())
    print(start_time)
    d=q.get()
    with open('out','w')as f:
        f.write(json.dumps(d,ensure_ascii=False,indent=1).encode('utf-8'))
