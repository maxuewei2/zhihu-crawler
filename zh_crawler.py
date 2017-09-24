#encoding=utf-8
from zh_api import ZhihuAPI
import copy
import time
import thread
import json
import os
import threading
import proxy_pool
import Queue
import traceback

id_queue=[]       #待获取的用户列表
id_dict={}        #已获取的用户字典
error_ids=[]      #获取出错的用户列表
out=[]            #保存输出信息的字符串列表
data_file_name=None    #数据文件名
out_file_name=None     #输出信息文件名
is_first=True      #是否是本轮获取的第一个用户

def handle_user(zh_api,user_id,uq):     #给定一个user_id，获取用户信息，并以宽度遍历扩展id_queue
    global out
    global data_file_name
    global id_queue
    global id_dict
    global error_ids
    try:
        user_data=zh.get_user(user_id)
    except Exception,e:
        traceback.print_exc()
        #exit(0)
    if user_data==None:
        error_ids.append(user_id)
        return 
    print('\t'+user_id)
    out.append(str('\t'+user_id))
    user_followees=user_data['followee']   
    followee_list=[f['url_token'] for f in user_followees ]  #获取用户的关注列表
    new_follow_list=list(set(followee_list)-set(id_dict))   #取关注列表中未被获取过的部分
    id_queue.extend(new_follow_list)   #以该用户的关注列表扩充id_queue
    id_dict[user_id]=1
    uq.put(' '.join(['"'+user_id+'":',json.dumps(user_data),'\n']))
    
#写数据文件
def append_write_data(data_str):
    if data_str=="":
        return
    global data_file_name
    global is_first
    with open(data_file_name,'r+b') as data_file:
        data_file.seek(-1,2)
        append_str=[] if is_first else [', ']
        append_str.extend(data_str)
        append_str.append('}')
        data_file.write(''.join(append_str))
        is_first=0

#在保持列表中元素顺序的前提下，移除列表中的重复元素
def remove_duplicate_keep_order(old_list):
    item_dict={}
    new_list=[]
    for item in old_list:
        if item not in item_dict:
            item_dict[item]=1
            new_list.append(item)
    return new_list

#保存id_dict和id_queue到文件中，即保存当前爬取的状态
def write_state():
    global id_queue
    global id_dict
    global error_ids
    id_queue=remove_duplicate_keep_order(id_queue)
    with open('state/id_queue.txt','w') as queue_file:
        queue_file.write(json.dumps(id_queue))
    with open('state/id_dict.txt','w') as dict_file:
        dict_file.write(json.dumps(id_dict))
    with open('state/error_ids.txt','w') as error_file:
        error_file.write(json.dumps(error_ids))

#从文件中读取id_dict和id_queue，即恢复之前爬取的状态，以从该状态继续        
def load_state():
    global id_queue
    global id_dict
    global error_ids
    with open('state/id_queue.txt','r') as queue_file:
        id_queue=json.loads(queue_file.read())
    with open('state/id_dict.txt','r') as dict_file:
        id_dict=json.loads(dict_file.read())
    with open('state/error_ids.txt','r') as error_file:
        error_ids=json.loads(error_file.read())
    
    
def main(zh_api,user_batch_size,sleep_seconds_between_user):
    global out
    global data_file_name
    global out_file_name
    global is_first
    is_first=1
    while zh_api.proxy_pool.get_size()<5:    #待获取到至少5个代理再继续程序
        time.sleep(1)
    start_time=time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())
    load_state()
    num=0
    data_file_name='data/data_'+start_time+'.txt'
    out_file_name='out/out_'+start_time+'.txt'
    with open(data_file_name,'w') as f:
        f.write('{}')
    with open(out_file_name,'w') as f:
        f.write('')
    print(start_time)
    lnum=0
    while True:
        uq=Queue.Queue()
        uts=[]
        for i in range(user_batch_size):    #多线程同时获取多个用户
            user_id=id_queue.pop(0)
            num+=1
            u_thread=threading.Thread(target=handle_user,args=(zh_api,user_id,uq))
            uts.append(u_thread)
        for u_thread in uts:
            u_thread.start()
        for u_thread in uts:
            u_thread.join()
        data_str=[]
        i=0
        while not uq.empty():
            if i!=0:
                data_str.append(',')
            data_str.append(uq.get())
            i+=1
        append_write_data(data_str)
        if num-lnum>=10:
            lnum=num
            out_str='crawl num= '+str(len(id_dict))+'\n'+'queue num= '+str(len(id_queue))
            print(out_str)
            out.append(out_str)
            with open(out_file_name,'a') as out_file:
                out_file.write('\n'.join(out))
            out=[]
            write_state()
        if num>=100:
            write_state()
            return
        if sleep_seconds_between_user:
            time.sleep(sleep_seconds_between_user)
        is_first_into_pause=True
        while True:
            if os.path.isfile('pause'):
                if is_first_into_pause:
                    write_state()
                    is_first_into_pause=False
                time.sleep(1)
            else:
                break
        

if __name__ == '__main__' :
    print('================================================')
    proxy_pool=proxy_pool.proxy_pool()
    #从x.txt中读取数字，以确定该使用哪个cookie文件，即以哪个账户登录
    jsonfilenames=os.listdir('cookies')
    jsonfilenames=[name for name in jsonfilenames if name.endswith('.json')]
    jsonfilenames=sorted(jsonfilenames)
    if not jsonfilenames:
        print("please run 'python zhihu_client.py' to create cookie file.")
        exit(-1)
    with open('state/x.txt','r') as f:
        ss=f.readline().strip()
        jx=int(ss)
    with open('state/x.txt','w') as f:
        f.write(str(jx+1))
    jl=len(jsonfilenames)
    jfname=jsonfilenames[jx%jl]
    print('use '+jfname)
    
    """ 
    调节此处的get_batch_size、sleep_seconds_between_batch、user_batch_size、sleep_seconds_between_user可调整爬取速度
    :get_batch_size                多线程获取多页数据时，同时爬取的页数
    :sleep_seconds_between_batch   多线程获取多页数据时，各轮(batch)之间停歇的时间
    :user_batch_size               多线程获取用户数据时，同时爬取的用户数
    :sleep_seconds_between_user    多线程获取用户数据时，各轮(batch)之间停歇的时间
    """
    get_batch_size=100
    sleep_seconds_between_batch=0
    user_batch_size=1
    sleep_seconds_between_user=0
    
    zh=ZhihuAPI('cookies/'+jfname,proxy_pool,get_batch_size,sleep_seconds_between_batch)
    for i in range(1):
        main(zh,user_batch_size,sleep_seconds_between_user)
    proxy_pool.stop=True
    exit(0)
