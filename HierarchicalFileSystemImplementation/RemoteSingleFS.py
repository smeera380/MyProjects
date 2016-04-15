#!/usr/bin/env python

import logging

import xmlrpclib
import pickle
from xmlrpclib import Binary

from collections import defaultdict
from errno import ENOENT
from stat import S_IFDIR, S_IFLNK, S_IFREG
from sys import argv, exit
from time import time

from fuse import FUSE, FuseOSError, Operations, LoggingMixIn

if not hasattr(__builtins__, 'bytes'):
    bytes = str

class RemoteSingleFS(LoggingMixIn, Operations):
    'Example memory filesystem. Supports only one level of files.'

    def __init__(self):
        self.files = {}
        self.data = defaultdict(bytes)
        self.fd = 0
        now = time()
        self.files['/'] = dict(st_mode=(S_IFDIR | 0755), st_ctime=now,
                               st_mtime=now, st_atime=now, st_nlink=2)
        serverInstance = xmlrpclib.ServerProxy('http://localhost:51234')
        serverInstance.put(Binary("root"),Binary(pickle.dumps(self.files)),3000)
        serverInstance.put(Binary("data"),Binary(pickle.dumps(self.data)),3000)

    def chmod(self, path, mode):
        serverInstance = xmlrpclib.ServerProxy('http://localhost:51234')
        self.files = pickle.loads(serverInstance.get(Binary("root"))["value"].data)
        self.files[path]['st_mode'] &= 0770000
        self.files[path]['st_mode'] |= mode
        serverInstance.put(Binary("root"),Binary(pickle.dumps(self.files)),3000)
        return 0

    def chown(self, path, uid, gid):
        serverInstance = xmlrpclib.ServerProxy('http://localhost:51234')
        self.files = pickle.loads(serverInstance.get(Binary("root"))["value"].data)
        self.files[path]['st_uid'] = uid
        self.files[path]['st_gid'] = gid
        serverInstance.put(Binary("root"),Binary(pickle.dumps(self.files)),3000)

    def create(self, path, mode):
        serverInstance = xmlrpclib.ServerProxy('http://localhost:51234')
        self.files = pickle.loads(serverInstance.get(Binary("root"))["value"].data)
        self.files[path] = dict(st_mode=(S_IFREG | mode), st_nlink=1,
                                st_size=0, st_ctime=time(), st_mtime=time(),
                                st_atime=time())

        self.fd += 1
        serverInstance.put(Binary("root"),Binary(pickle.dumps(self.files)),3000)
        return self.fd

    def getattr(self, path, fh=None):
        serverInstance = xmlrpclib.ServerProxy('http://localhost:51234')
        self.files = pickle.loads(serverInstance.get(Binary("root"))["value"].data)
        if path not in self.files:
            raise FuseOSError(ENOENT)

        return self.files[path]

    def getxattr(self, path, name, position=0):
        serverInstance = xmlrpclib.ServerProxy('http://localhost:51234')
        self.files = pickle.loads(serverInstance.get(Binary("root"))["value"].data)
        attrs = self.files[path].get('attrs', {})

        try:
            return attrs[name]
        except KeyError:
            return ''       # Should return ENOATTR

    def listxattr(self, path):
        serverInstance = xmlrpclib.ServerProxy('http://localhost:51234')
        self.files = pickle.loads(serverInstance.get(Binary("root"))["value"].data)
        attrs = self.files[path].get('attrs', {})
        return attrs.keys()

    def mkdir(self, path, mode):
        serverInstance = xmlrpclib.ServerProxy('http://localhost:51234')
        self.files = pickle.loads(serverInstance.get(Binary("root"))["value"].data)
        self.files[path] = dict(st_mode=(S_IFDIR | mode), st_nlink=2,
                                st_size=0, st_ctime=time(), st_mtime=time(),
                                st_atime=time())

        self.files['/']['st_nlink'] += 1
        serverInstance.put(Binary("root"),Binary(pickle.dumps(self.files)),3000)

    def open(self, path, flags):
        self.fd += 1
        return self.fd

    def read(self, path, size, offset, fh):
        serverInstance = xmlrpclib.ServerProxy('http://localhost:51234')
        self.data = pickle.loads(serverInstance.get(Binary("data"))["value"].data)
        return self.data[path][offset:offset + size]

    def readdir(self, path, fh):
        serverInstance = xmlrpclib.ServerProxy('http://localhost:51234')
        self.files = pickle.loads(serverInstance.get(Binary("root"))["value"].data)
        return ['.', '..'] + [x[1:] for x in self.files if x != '/']

    def readlink(self, path):
        serverInstance = xmlrpclib.ServerProxy('http://localhost:51234')
        self.data = pickle.loads(serverInstance.get(Binary("data"))["value"].data)
        return self.data[path]

    def removexattr(self, path, name):
        serverInstance = xmlrpclib.ServerProxy('http://localhost:51234')
        self.files = pickle.loads(serverInstance.get(Binary("root"))["value"].data)
        attrs = self.files[path].get('attrs', {})

        try:
            del attrs[name]
        except KeyError:
            pass        # Should return ENOATTR

    def rename(self, old, new):
        serverInstance = xmlrpclib.ServerProxy('http://localhost:51234')
        self.files = pickle.loads(serverInstance.get(Binary("root"))["value"].data)
        self.files[new] = self.files.pop(old)
        serverInstance.put(Binary("root"),Binary(pickle.dumps(self.files)),3000)

    def rmdir(self, path):
        serverInstance = xmlrpclib.ServerProxy('http://localhost:51234')
        self.files = pickle.loads(serverInstance.get(Binary("root"))["value"].data)
        self.files.pop(path)
        self.files['/']['st_nlink'] -= 1
        serverInstance.put(Binary("root"),Binary(pickle.dumps(self.files)),3000)

    def setxattr(self, path, name, value, options, position=0):
        # Ignore options
        serverInstance = xmlrpclib.ServerProxy('http://localhost:51234')
        self.files = pickle.loads(serverInstance.get(Binary("root"))["value"].data)
        attrs = self.files[path].setdefault('attrs', {})
        attrs[name] = value

    def statfs(self, path):
        return dict(f_bsize=512, f_blocks=4096, f_bavail=2048)

    def symlink(self, target, source):
        serverInstance = xmlrpclib.ServerProxy('http://localhost:51234')
        self.files = pickle.loads(serverInstance.get(Binary("root"))["value"].data)
        self.data = pickle.loads(serverInstance.get(Binary("data"))["value"].data)
        self.files[target] = dict(st_mode=(S_IFLNK | 0777), st_nlink=1,
                                  st_size=len(source))

        self.data[target] = source
        serverInstance.put(Binary("root"),Binary(pickle.dumps(self.files)),3000)
        serverInstance.put(Binary("data"),Binary(pickle.dumps(self.data)),3000)

    def truncate(self, path, length, fh=None):
        serverInstance = xmlrpclib.ServerProxy('http://localhost:51234')
        self.files = pickle.loads(serverInstance.get(Binary("root"))["value"].data)
        self.data = pickle.loads(serverInstance.get(Binary("data"))["value"].data)
        self.data[path] = self.data[path][:length]
        self.files[path]['st_size'] = length
        serverInstance.put(Binary("root"),Binary(pickle.dumps(self.files)),3000)
        serverInstance.put(Binary("data"),Binary(pickle.dumps(self.data)),3000)

    def unlink(self, path):
        serverInstance = xmlrpclib.ServerProxy('http://localhost:51234')
        self.files = pickle.loads(serverInstance.get(Binary("root"))["value"].data)
        self.files.pop(path)
        serverInstance.put(Binary("root"),Binary(pickle.dumps(self.files)),3000)

    def utimens(self, path, times=None):
        now = time()
        atime, mtime = times if times else (now, now)
        serverInstance = xmlrpclib.ServerProxy('http://localhost:51234')
        self.files = pickle.loads(serverInstance.get(Binary("root"))["value"].data)
        self.files[path]['st_atime'] = atime
        self.files[path]['st_mtime'] = mtime
        serverInstance.put(Binary("root"),Binary(pickle.dumps(self.files)),3000)

    def write(self, path, data, offset, fh):
        serverInstance = xmlrpclib.ServerProxy('http://localhost:51234')
        self.files = pickle.loads(serverInstance.get(Binary("root"))["value"].data)
        self.data = pickle.loads(serverInstance.get(Binary("data"))["value"].data)
        self.data[path] = self.data[path][:offset] + data
        self.files[path]['st_size'] = len(self.data[path])
        serverInstance.put(Binary("root"),Binary(pickle.dumps(self.files)),3000)
        serverInstance.put(Binary("data"),Binary(pickle.dumps(self.data)),3000)
        return len(data)


if __name__ == '__main__':
    if len(argv) != 2:
        print('usage: %s <mountpoint>' % argv[0])
        exit(1)

    logging.getLogger().setLevel(logging.DEBUG)
    fuse = FUSE(RemoteSingleFS(), argv[1], foreground=True)
