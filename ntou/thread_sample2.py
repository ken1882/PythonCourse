# -*- coding: utf-8 -*-
"""
Created on Sun Dec 24 20:21:28 2017

@author: Admin
"""
import threading
import queue
import os
import time

def count_number_of_files_worker(lock,dir_queue):
    global global_file_count, global_total_size
    file_count = 0
    total_size = 0
    while True:
        try:
            cpath = dir_queue.get(timeout=0.3)
            try:
                for entry in os.scandir(cpath):
                    if entry.is_file():
                        total_size = total_size + os.path.getsize(os.path.join(cpath,entry.name))
                        file_count+= 1
            except PermissionError:
                pass        
        except queue.Empty:
            break
    lock.acquire()
    global_file_count += file_count
    global_total_size += total_size
    lock.release()
    return 

def collect_subdirectory_worker(ready_queue,dir_queue):
    while True:
        try:
            cpath = ready_queue.get(timeout=0.1)
            try:
                for entry in os.scandir(cpath):
                    if entry.is_dir():
                        p = os.path.join(cpath,entry.name)
                        ready_queue.put(p)
                        dir_queue.put(p)
            except PermissionError:
                pass
        except queue.Empty:
            return
            
def collect_file_information(path):
    global global_file_count, global_total_size
    global_file_count, global_total_size = 0, 0

    begin = time.time()

    ready_queue = queue.Queue()
    ready_queue.put(path)
    
    dir_queue = queue.Queue()
    dir_queue.put(path)    
    
    lock = threading.Lock()
    worker_number = 8

    producer = [threading.Thread(target=collect_subdirectory_worker,args=(ready_queue,dir_queue)) for _ in range(worker_number)]
    for t in producer:
        t.start()
    
    consumer = [threading.Thread(target=count_number_of_files_worker,args=(lock,dir_queue)) for _ in range(worker_number)]
    
    for t in consumer:
        t.start()

    for t in producer:
        t.join()

    for t in consumer:
        t.join()
    
    end = time.time()
    print('total number of files:{}, total bytes:{}, execution time:{}'.format(global_file_count,global_total_size,end-begin))
    
    
if __name__=="__main__":
    
    path = 'c:\\'
    collect_file_information(path)
    