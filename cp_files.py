import os
import shutil
import time

def cp_files():
    cp_time=time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())
    print('copy files at '+cp_time)
    try:
        shutil.copyfile('state/id_queue.txt','cpfiles/id_queue_'+cp_time+'.txt')
        shutil.copyfile('state/id_dict.txt','cpfiles/id_dict_'+cp_time+'.txt')
    except Exception,e:
        print('No-file')
    
last=os.listdir('data')
while True:
    ld=os.listdir('data')
    if len(ld)>len(last):
        cp_files()
    last=ld
    time.sleep(2)
    
