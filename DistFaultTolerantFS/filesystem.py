#!/usr/bin/env python

import logging
import xmlrpclib
import pickle
import sys
from hashlib import md5
from xmlrpclib import Binary

from collections import defaultdict
from errno import ENOENT
from stat import S_IFDIR,S_IFLNK,S_IFREG
from sys import argv,exit
from time import time

from fuse import FUSE,FuseOSError, Operations, LoggingMixIn

if not hasattr(__builtins__,'bytes'):
    bytes = str

class Error(Exception):
  pass

class FileExistsError(Error):
  ''' Raised when directories with existing files are being removed '''
  pass


class ClientNode:
   def __init__(self,med_port):

      # Initialising the Mediator Server Instance
      self.rpc_med  = xmlrpclib.ServerProxy('http://localhost:'+str(med_port),allow_none=True)      
      
   
   def get_meta(self,key):
      res = self.rpc_med.get_meta(Binary(key))
      if "value" in res:
         return pickle.loads(res["value"].data)
      else:
         return None   


   def put_meta(self,key,value):
      self.rpc_med.put_meta(Binary(key), Binary(pickle.dumps(value)))


   def get_data(self,key):
      print('$$$$$$$$$$$$$$$$$ Fiel system get data call!!!!')
      res = self.rpc_med.get_data(Binary(key))
      if "value" in res:
         return pickle.loads(res["value"].data)
      else:
         return None  
   
   def put_data(self,key,value):
      self.rpc_med.put_data(Binary(key), Binary(pickle.dumps(value)))

   def remove_meta(self,path,value):
      self.rpc_med.remove_meta(Binary(path),Binary(pickle.dumps(value)))

   def remove_data(self,path,value):
      self.rpc_med.remove_data(Binary(path),Binary(pickle.dumps(value)))

class FSOper():
   def __init__(self,med_port):
      # to put the root into the server, initialise the ClientNode class.
        self.files = {}
        self.data = defaultdict(bytes)
        self.fd = 0
        now = time()
        self.files['/'] = dict(st_mode=(S_IFDIR | 0755), st_ctime=now,
                   st_mtime=now, st_atime=now, st_nlink=2,children=[])
        self.CN = ClientNode(med_port);
        self.CN.put_meta('/',self.files['/'])   
        self.CN.put_data('/',{})        
        self.fd = 0

   def checksum(self,data):
        return reduce(lambda x,y:x+y, map(ord, data))


   def getParentPath(self,path):
        pth = '/'
        pathlist = path.split('/')
        while '' in pathlist:
          pathlist.remove('')
        if pathlist:
          pathlist.remove(pathlist[len(pathlist)-1])
   	for j in pathlist:
      	  pth += str(j)+'/'
        if pth =='/':
          pth
        else:
          pth = pth[:-1]
        return pth      


   def getCurrentNode(self,path):
       return path[path.rfind('/')+1:]

   # Updating the meta data
   def upd_meta(self,path,mode,uid,gid,op):
      metadata ={}
      metadata = self.CN.get_meta(path)
      if op == 'chmod':
        self.files[path]['st_mode'] &= 0770000
        self.files[path]['st_mode'] |= mode
        metadata['st_mode'] &= 0770000
        metadata['st_mode'] |= mode
      else:
        metadata['st_uid'] = uid
        metadata['st_gid'] = gid 
        self.files[path]['st_uid'] = uid
        self.files[path]['st_gid'] = gid 
       
      #call ClientNode put to put the updated value into the server here.
      self.CN.put_meta(path,metadata)
      
       

   # Creating a new file.
   def create_file(self,path,mode):
        self.files[path] = dict(st_mode=(S_IFREG | mode), st_nlink=1,
                             st_size=0, st_ctime=time(), st_mtime=time(),
                                st_atime=time(),checksum=0)
        self.fd+=1
        # Adding the child entry to the parent
        parentPath = self.getParentPath(path)
        self.files[parentPath]['children'].append(path[path.rfind('/')+1:])
        # Putting the updated Meta data information into the Server(current and its parent)
        self.CN.put_meta(path,self.files[path])
        self.CN.put_meta(parentPath,self.files[parentPath])

        return self.fd

   # getattr
   def get_attrmeta(self,path):
        if path not in self.files:
            raise FuseOSError(ENOENT)
        return self.files[path]       

   # Creating a new directory 
   def create_dir(self,path,mode):
        parentPath = self.getParentPath(path)
        self.files[path] = dict(st_mode=(S_IFDIR | mode), st_nlink=2,
                            st_size=0, st_ctime=time(), st_mtime=time(),
                                st_atime=time(),children=[])
        self.files[parentPath]['st_nlink'] += 1
        # Adding the child entry to parent children list
        self.files[parentPath]['children'].append(path[path.rfind('/')+1:])

        # Putting the updated Meta data information into the Server(current and its parent)
        self.CN.put_meta(path,self.files[path])
        self.CN.put_meta(parentPath,self.files[parentPath])        
        

   # open
   def openFile(self,path):
        self.fd += 1
        return self.fd

   # read data
   def readData(self,path,size,offset):
        print('################################## INside read data!!!')
        return self.CN.get_data(path)[offset:offset + size]
        #return self.data[path][offset:offset + size]

   #List the files
   def listdir(self,path):
	list_dir = self.CN.get_meta(path)
	return ['.', '..'] + list_dir['children']
        #shreturn ['.', '..'] + self.files[path]['children']
        

   # Rename the files
   def rename(self,old,new):
        parentPath = self.getParentPath(old)
        oldNode = self.getCurrentNode(old)
        newNode = self.getCurrentNode(new)
        current_meta = self.files[old]
        current_data = self.data[old]
        remote_parent_meta = self.files[parentPath]

        if 'children' in current_meta.keys():   # Implies it is a directory
          self.files[new] = self.files.pop(old)
          # Adding the new node into the Meta server and removing the earlier node.
          self.CN.put_meta(new,self.files[new])
          self.CN.remove_meta(old,current_meta)

          # Adding the new node into the Data server and removing the earlier node.
          self.data[new] = self.data.pop(old)
          self.CN.put_data(new,self.data[new])
          self.CN.remove_data(old,current_data)
       
          self.files[parentPath]['children'].remove(oldNode)
          self.files[parentPath]['children'].append(newNode)
          self.CN.put_meta(parentPath,self.files[parentPath]) 
        else:
          self.files[new] = self.files.pop(old)
          # Adding the new node into the Meta server and removing the earlier node.
          self.CN.put_meta(new,self.files[new])
          self.CN.remove_meta(old,current_meta)

          # Adding the new node into the Data server and removing the earlier node.
          self.data[new] = self.data.pop(old)
          self.CN.put_data(new,self.data[new])
          self.CN.remove_data(old,current_data)     
          self.files[parentPath]['children'].remove(oldNode)
          self.files[parentPath]['children'].append(newNode)
          self.CN.put_meta(parentPath,self.files[parentPath]) 



   # Remove files
   def remove(self,path):
        parentPath = self.getParentPath(path)
        curNode = self.getCurrentNode(path)
        current_meta = self.files[path]
        current_data = self.data[path]
        remote_parent_meta = self.files[parentPath]

        # Checking if it is a file or directory that is being removed

        if 'children' in current_meta.keys():   # Implies it is a directory
            print('$$$$$$$$$$$$$ After remove dir :',self.CN.get_meta(parentPath), curNode)
            print('$$$$$$$$$$$$$$ Removing parent path: ', self.files[parentPath])
            self.files.pop(path)
            self.files[parentPath]['children'].remove(curNode)
            self.files[parentPath]['st_nlink'] -= 1
            self.CN.put_meta(parentPath, remote_parent_meta)
            self.CN.remove_meta(path,current_meta)
        else:  # Implies it is a file.
            self.files.pop(path)
            self.files[parentPath]['children'].remove(curNode)
            self.CN.put_meta(parentPath, remote_parent_meta)
            self.CN.remove_meta(path,current_meta)
            self.CN.remove_data(path,current_data)

   # Truncate Data
   def truncate(self,path,length):
        self.data[path] = self.data[path][:length]
        self.files[path]['st_size'] = length
        # Putting the updated Data information into the Server(current and its parent)
        self.CN.put_data(path,self.data[path])
        self.CN.put_meta(path.self.files[path])

   # Write Data
   def writeData(self,path,data,offset):
        self.data[path] = self.data[path][:offset] + data
        chksum = self.checksum(self.data[path])
        self.files[path]['st_size'] = len(self.data[path])
        self.files[path]['checksum'] = chksum

        # Putting the updated Meta data information into the Server(current and its parent)
        self.CN.put_data(path,self.data[path])
        self.CN.put_meta(path,self.files[path]) 

        return len(data)

   # TO DO : But where is it used?
   def readLink(self,path):
        return self.data[path]

   
   def removexattr(self,path,name):
        attrs = self.files[path].get('attrs', {})
        try:
            del attrs[name]
        except KeyError:
            pass        # Should return ENOATTR
   
   def getxattr(self,path,name):
        attrs = self.files[path].get('attrs', {})
        try:
            return attrs[name]
        except KeyError:
            return ''       # Should return ENOATTR

    


class Memory(LoggingMixIn, Operations):

    def __init__(self,med_port):
        self.FS = FSOper(med_port)

    def chmod(self, path, mode):
        self.FS.upd_meta(path,mode=mode,op='chmod')
        return 0

    def chown(self, path, uid, gid):
        self.FS.upd_meta(path,uid=uid,gid=gid,op='chmod')

    def create(self, path, mode):
        fd = self.FS.create_file(path,mode)
        return fd

    def getattr(self, path, fh=None):
        metadict ={}
        metadict = self.FS.get_attrmeta(path)
        return metadict

    # is this getting used anywhere?
    def getxattr(self, path, name, position=0):
        retval = self.FS.getxattr(path,name)
        return retval

    # is this getting used anywhere?
    def listxattr(self, path):
        attrs = self.files[path].get('attrs', {})
        return attrs.keys()



    def mkdir(self, path, mode):
        self.FS.create_dir(path,mode)

    def open(self, path, flags):
        fd = self.FS.openFile(path)
        return fd

    def read(self, path, size, offset, fh):
        data = self.FS.readData(path,size,offset)
        return data

    def readdir(self, path, fh):
        listdir = self.FS.listdir(path)
        return listdir

    '''
    def readlink(self, path):
        data = self.FS.readLink(path)
        return data
    '''

    def removexattr(self, path, name):
        self.FS.removexattr(path,name)
    
    def rename(self, old, new):
        self.FS.rename(old,new)
    
    def rmdir(self, path):
        self.FS.remove(path)

    '''
    def setxattr(self, path, name, value, options, position=0):
        # Ignore options
        attrs = self.files[path].setdefault('attrs', {})
        attrs[name] = value

    def statfs(self, path):
        return dict(f_bsize=512, f_blocks=4096, f_bavail=2048)

    def symlink(self, target, source):
        self.files[target] = dict(st_mode=(S_IFLNK | 0777), st_nlink=1,
                                  st_size=len(source))

        self.data[target] = source
    '''

    def truncate(self, path, length, fh=None):
        self.FS.truncate(path,length)
    
    def unlink(self, path):
        self.FS.remove(path)


    '''
    def utimens(self, path, times=None):
        now = time()
        atime, mtime = times if times else (now, now)
        self.files[path]['st_atime'] = atime
        self.files[path]['st_mtime'] = mtime
    '''

    def write(self, path, data, offset, fh):
        dataLen = self.FS.writeData(path,data,offset)
        return dataLen
    

if __name__ == '__main__':
  if len(argv) != 3:
    print 'usage: %s <mountpoint> <remote hashtable>' % argv[0]
    exit(1)
  med_port = argv[2]

  logging.getLogger().setLevel(logging.DEBUG)
  fuse = FUSE(Memory(med_port), argv[1], foreground=True,debug=True)
