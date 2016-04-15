#!/usr/bin/env python

import logging

import xmlrpclib
import pickle
from xmlrpclib import Binary

from collections import defaultdict
from errno import ENOENT
from stat import S_IFDIR,S_IFLNK,S_IFREG
from sys import argv,exit
from time import time

from fuse import FUSE,FuseOSError, Operations, LoggingMixIn

if not hasattr(__builtins__,'bytes'):
    bytes = str

class RemoteHierarchicalFS(LoggingMixIn, Operations):
    
    def __init__(self):
       self.files = {}
       self.data = defaultdict(bytes)
       self.fd = 0
       now =time()
       self.files['/'] = dict(st_mode=(S_IFDIR | 0755), st_ctime=now,
                              st_mtime=now, st_atime=now, st_nlink=2)
       serverInstance = xmlrpclib.ServerProxy('http://localhost:51234')
       serverInstance.put(Binary("root"),Binary(pickle.dumps(self.files)),3000)
       serverInstance.put(Binary("data"),Binary(pickle.dumps(self.data)),3000)


    def chmod(self,path,mode):
       serverInstance = xmlrpclib.ServerProxy('http://localhost:51234')
       self.files = pickle.loads(serverInstance.get(Binary("root"))["value"].data)
       pathlist = path.split('/')
       while '' in pathlist:
          pathlist.remove('')
       temp = self.files['/']
       for i in pathlist:
          temp[i]['st_mode'] &= 0770000
          temp[i]['st_mode'] |= mode
       serverInstance.put(Binary("root"),Binary(pickle.dumps(self.files)),3000)
       return 0

     
    def chown(self,path,uid,gid):
       serverInstance = xmlrpclib.ServerProxy('http://localhost:51234')
       self.files = pickle.loads(serverInstance.get(Binary("root"))["value"].data)
       pathlist = path.split('/')
       while '' in pathlist:
          pathlist.remove('')
       temp = self.files['/']
       for i in pathlist:
          temp[i]['st_uid'] = uid
          temp[i]['st_gid'] = gid
       serverInstance.put(Binary("root"),Binary(pickle.dumps(self.files)),3000)


    def create(self,path,mode):
       serverInstance = xmlrpclib.ServerProxy('http://localhost:51234')
       self.files = pickle.loads(serverInstance.get(Binary("root"))["value"].data)
       pathlist = path.split('/')
       while '' in pathlist:
          pathlist.remove('')
       pathlist.insert(0,'/')
       temp = self.files
       for i in pathlist:
          if pathlist.index(i) == len(pathlist)-1:
             temp[i] = dict(st_mode=(S_IFREG | mode), st_nlink=1,
                           st_size=0, st_ctime= time(),st_mtime=time(), 
                           st_atime=time())
             self.fd +=1
             break
          temp =temp[i]
       serverInstance.put(Binary("root"),Binary(pickle.dumps(self.files)),3000)
       return self.fd


    def getattr(self,path,fh=None):
       serverInstance = xmlrpclib.ServerProxy('http://localhost:51234')
       self.files = pickle.loads(serverInstance.get(Binary("root"))["value"].data)
       pathlist = path.split('/')
       while '' in pathlist:
          pathlist.remove('')
       #pathlist.insert(0,'/')
       temp = self.files['/']
       for i in pathlist:
          if i not in temp:
             raise FuseOSError(ENOENT)
          temp =temp[i]
       return temp


    def getxattr(self,path,name,position=0):
       serverInstance = xmlrpclib.ServerProxy('http://localhost:51234')
       self.files = pickle.loads(serverInstance.get(Binary("root"))["value"].data)
       pathlist = path.split('/')
       while '' in pathlist:
          pathlist.remove('')
       pathlist.insert(0,'/')
       temp = self.files
       for i in pathlist:
           attrs = temp[i].get('attrs',{})
           temp = temp[i]
       try:
           return attrs[name]
       except KeyError:
           return ''    #Should return ENOATTR       


     
    def listxattr(self,path):
       serverInstance = xmlrpclib.ServerProxy('http://localhost:51234')
       self.files = pickle.loads(serverInstance.get(Binary("root"))["value"].data)
       pathlist = path.split('/')
       while '' in pathlist:
          pathlist.remove('')
       pathlist.insert(0,'/')
       temp = self.files
       for i in pathlist:
          if pathlist.index(i) == len(pathlist)-1:
             attrs = temp[i].get('attrs',{})
             temp = temp[i]
       return attrs.keys()


    def mkdir(self,path,mode):
       serverInstance = xmlrpclib.ServerProxy('http://localhost:51234')
       self.files = pickle.loads(serverInstance.get(Binary("root"))["value"].data)
       pathlist = path.split('/')
       while '' in pathlist:
          pathlist.remove('')
       temp = self.files['/']
       for i in pathlist:
          if i in temp.keys():
             temp = temp[i]
          else:
             temp[i]  = dict(st_mode=(S_IFDIR | mode), st_nlink=2,st_size=0,
                              st_ctime=time(),st_mtime=time(), st_atime=time())
             temp['st_nlink']+=1
             temp = temp[i]
       serverInstance.put(Binary("root"),Binary(pickle.dumps(self.files)),3000)


    def open(self,path,flags):
       pathlist = path.split('/')
       while '' in pathlist:
          pathlist.remove('')
       temp = self.files['/']
       for i in pathlist:
          if pathlist.index(i) == len(pathlist)-1:
               self.fd+=1
               break
          temp = temp[i]
       return self.fd 
        


    def read(self,path,size,offset,fh):
       serverInstance = xmlrpclib.ServerProxy('http://localhost:51234')
       self.data = pickle.loads(serverInstance.get(Binary("data"))["value"].data)
       return self.data[path][offset:offset+size]


    def readdir(self,path,fh):
       serverInstance = xmlrpclib.ServerProxy('http://localhost:51234')
       self.files = pickle.loads(serverInstance.get(Binary("root"))["value"].data)
       pathlist = path.split('/')
       while '' in pathlist:
          pathlist.remove('')
       pathlist.insert(0,'/')
       temp = self.files
       dirlist =[]
       for i in pathlist:
          if pathlist.index(i) == len(pathlist)-1:
             for keys in temp[i]:
                if type(temp[i][keys])== type({}):
                    dirlist.append(keys)
             break
          temp = temp[i]
       return dirlist


    def readlink(self,path):
       serverInstance = xmlrpclib.ServerProxy('http://localhost:51234')
       self.data = pickle.loads(serverInstance.get(Binary("data"))["value"].data)
       return self.data[path]


    def removexattr(self,path,name):
       serverInstance = xmlrpclib.ServerProxy('http://localhost:51234')
       self.files = pickle.loads(serverInstance.get(Binary("root"))["value"].data)
       attrs = self.files[path].get('attrs',{})
        
       try:
          del attrs[name]
       except KeyError:
          pass      # Should return ENOATTR


    def rename(self,old,new):
       serverInstance = xmlrpclib.ServerProxy('http://localhost:51234')
       self.files = pickle.loads(serverInstance.get(Binary("root"))["value"].data)
       pathlistold = old.split('/')
       pathlistnew = new.split('/')
       while '' in pathlistold:
          pathlistold.remove('')
       while '' in pathlistnew:
          pathlistnew.remove('')
       temp = self.files['/']
       for i in pathlistnew:
           if pathlistnew.index(i) == len(pathlistnew)-1:
              temp[i] = temp.pop(pathlistold[pathlistnew.index(i)])
              break
           temp = temp[i]
       serverInstance.put(Binary("root"),Binary(pickle.dumps(self.files)),3000)

    def rmdir(self,path):
       serverInstance = xmlrpclib.ServerProxy('http://localhost:51234')
       self.files = pickle.loads(serverInstance.get(Binary("root"))["value"].data)
       pathlist = path.split('/')
       while '' in pathlist:
          pathlist.remove('')
       pathlist.insert(0,'/')
       temp = self.files
       for i in pathlist:
          if pathlist.index(i) == len(pathlist)-1:
              temp.pop(i)
              temp['st_nlink']-=1
              break
          temp = temp[i]           
       serverInstance.put(Binary("root"),Binary(pickle.dumps(self.files)),3000)


    def setxattr(self,path,name,value,options,position=0):
        serverInstance = xmlrpclib.ServerProxy('http://localhost:51234')
        self.files = pickle.loads(serverInstance.get(Binary("root"))["value"].data)
        attrs = self.files[path].setdefault('attrs',{})
        attrs[name]=value


    def statfs(self,path):
        return dict(f_bsize=512, f_blocks=4096, f_bavail=2048)


    def symlink(self,target,source):
        serverInstance = xmlrpclib.ServerProxy('http://localhost:51234')
        self.files = pickle.loads(serverInstance.get(Binary("root"))["value"].data)
        tgtPathList = target.split('/')
        srcPathList = source.split('/')
        while '' in tgtPathList:
            tgtPathList.remove('')
        while '' in srcPathList:
            srcPathList.remove('')
        temp = self.files['/']
        for i in tgtPathList:
            if tgtPathList.index(i) ==len(tgtPathList)-1:
                temp[i] = dict(st_mode=(S_IFLNK | 0777), st_nlink=1,
                                 st_size=len(source))
                break
            temp = temp[i]
        self.data[target] = source
        serverInstance.put(Binary("root"),Binary(pickle.dumps(self.files)),3000)


    def truncate(self,path,length,fh=None):
        serverInstance = xmlrpclib.ServerProxy('http://localhost:51234')
        self.files = pickle.loads(serverInstance.get(Binary("root"))["value"].data)
        self.data = pickle.loads(serverInstance.get(Binary("data"))["value"].data)
        self.data[path] = self.data[path][:length]
        pathlist = path.split('/')
        while '' in pathlist:
           pathlist.remove('')
        pathlist.insert(0,'/')
        temp = self.files
        for i in pathlist:
           if pathlist.index(i) == len(pathlist)-1:
               temp[i]['st_size'] = length
               break
           temp = temp[i]
        serverInstance.put(Binary("root"),Binary(pickle.dumps(self.files)),3000)
        serverInstance.put(Binary("data"),Binary(pickle.dumps(self.data)),3000)


    def unlink(self,path):
        serverInstance = xmlrpclib.ServerProxy('http://localhost:51234')
        self.files = pickle.loads(serverInstance.get(Binary("root"))["value"].data)
        pathlist = path.split('/')
        while '' in pathlist:
           pathlist.remove('')
        temp = self.files['/']
        for i in pathlist:
           if pathlist.index(i) == len(pathlist)-1:        
               temp.pop(i)
               break
           temp=temp[i]
        serverInstance.put(Binary("root"),Binary(pickle.dumps(self.files)),3000)
       

    def utimens(self,path,times=None):
        serverInstance = xmlrpclib.ServerProxy('http://localhost:51234')
        self.files = pickle.loads(serverInstance.get(Binary("root"))["value"].data)
        now=time()
        atime,mtime = times if times else (now,now)
        pathlist = path.split('/')
        while '' in pathlist:
           pathlist.remove('')
        temp = self.files['/']
        for i in pathlist:
               temp[i]['st_atime'] = atime
               temp[i]['st_mtime'] = mtime
        serverInstance.put(Binary("root"),Binary(pickle.dumps(self.files)),3000)
   


    def write(self, path, data, offset, fh):
        serverInstance = xmlrpclib.ServerProxy('http://localhost:51234')
        self.files = pickle.loads(serverInstance.get(Binary("root"))["value"].data)
        self.data = pickle.loads(serverInstance.get(Binary("data"))["value"].data)
        self.data[path] = self.data[path][:offset] + data
        pathlist = path.split('/')
        while '' in pathlist:
           pathlist.remove('')
        pathlist.insert(0,'/')
        temp = self.files
        for i in pathlist:
           if pathlist.index(i) == len(pathlist)-1:
               temp[i]['st_size'] = len(self.data[path])
               break
           temp = temp[i]
        serverInstance.put(Binary("root"),Binary(pickle.dumps(self.files)),3000)
        serverInstance.put(Binary("data"),Binary(pickle.dumps(self.data)),3000)
        return len(data)


if __name__ == '__main__':
   if len(argv) != 2:
      print('usage: %s <mountpoint>' % argv[0])
      exit(1)

   logging.getLogger().setLevel(logging.DEBUG)
   fuse = FUSE(RemoteHierarchicalFS(), argv[1], foreground=True, debug=True)      








    












