# -*- coding: utf-8 -*-
"""
Created on Sun Dec 24 20:21:28 2017

@author: Admin
"""
import threading
import queue
import concurrent.futures
import os
import time

def count_number_of_files_worker(cpath):
    file_count = 0
    total_size = 0
    try:
        for entry in os.scandir(cpath):
            if entry.is_file():
                total_size = total_size + os.path.getsize(os.path.join(cpath,entry.name))
                file_count+= 1
    except PermissionError:
        pass        
    return (file_count, total_size)

def collect_subdirectory_worker(lock,ready_queue,result_pool):
    while True:
        try:
            cpath = ready_queue.get(timeout=0.1)
            subdir = []
            try:
                for entry in os.scandir(cpath):
                    if entry.is_dir():
                        subdir.append(os.path.join(cpath,entry.name))
                if len(subdir)>0:
                    for x in subdir:
                        ready_queue.put(x)
                    lock.acquire()
                    result_pool.extend(subdir)
                    lock.release()
            except PermissionError:
                pass
        except queue.Empty:
            return
            
def collect_file_information(path):

    begin = time.time()
    result_pool= [path]
    ready_queue = queue.Queue()
    ready_queue.put(path)
    lock = threading.Lock()
    worker_number = 20

    threads = [threading.Thread(target=collect_subdirectory_worker,args=(lock,ready_queue,result_pool)) for _ in range(worker_number)]
    for t in threads:
        t.start()
    
    for t in threads:
        t.join()
    
    threads = None
    
    total_files = 0
    total_size  = 0
    executor = concurrent.futures.ThreadPoolExecutor(max_workers = worker_number)
    for n,s in executor.map(count_number_of_files_worker,result_pool):
        total_files = total_files + n
        total_size  = total_size + s
    
    end = time.time()
    print('total number of files:{}, total bytes:{}, execution time:{}'.format(total_files,total_size,end-begin))
    
    
if __name__=="__main__":
    
    path = 'c:\\'
    collect_file_information(path)
    