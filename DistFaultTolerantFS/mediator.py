#!/usr/bin/env python
import sys, SimpleXMLRPCServer, getopt, pickle, time, threading, xmlrpclib, unittest
from datetime import datetime, timedelta
from xmlrpclib import Binary

if not hasattr(__builtins__,'bytes'):
    bytes = str


class Mediator:
   def __init__(self,dataports,metaport,Qr,Qw):

      self.dataports = dataports
      # Initialising the meta server proxy instance 
      self.rpc_meta = xmlrpclib.ServerProxy('http://localhost:'+str(metaport),allow_none=True)

      # Initialising the data server proxy instance
      self.rpc_data ={}
      for i in self.dataports:
        self.rpc_data[i] = xmlrpclib.ServerProxy('http://localhost:'+str(i),allow_none=True)

      self.Qr = Qr
      self.Qw = Qw
      self.ds = len(dataports)

   def checksum(self,data):
        return reduce(lambda x,y:x+y, map(ord, data))
   
   def get_meta(self,key):
      print('$$$$$$$$$$$$$$ Mediator: get_meta')
      res = self.rpc_meta.get(key)
      return res   

   
   def put_meta(self,key,value):
      self.rpc_meta.put(key, value, 6000)

   def remove_meta(self,key,value):
      self.rpc_meta.put(key,value,0)

   def remove_data(self,key,value):
     for i in self.dataports:
       self.rpc_data[i].put(key,value,0)

   def recoverdata(self,validserver,cleanservers):
      recoveredData = {}
      recoveredData = self.rpc_data[validserver].getrecoverydata();
      print('$$$$$$$$$$$$  Printing the recovered data')
      print(recoveredData)
      for i in cleanservers:
          self.rpc_data[i].recoverdata(recoveredData)

   def get_data_list(self,key,metadata):
      result = {}
      cleanservers =0
      for i in self.dataports:
        try:
          res = self.rpc_data[i].get(key)
          if res == {}:
            print('$$$$$$$$$$$$  Server clean : Server is: ')
            print(i)
            result[i]=dict(data = 1, checksum = 0, valbit =-1)
            print(result)
          if "value" in res:
            result[i] = dict(data = pickle.loads(res["value"].data),checksum = self.checksum(pickle.loads(res["value"].data)))
            if result[i]['checksum'] == metadata['checksum']:
              result[i]['valbit'] = 1
            else:
              result[i]['valbit'] = 0
          else:
            None
        except:
          pass
      return result



   def get_data(self,key):
      result={}
      corruptserver = []
      cleanservers =[]

      metadata = self.get_meta(key)
      if "value" in  metadata:
         metadata = pickle.loads(metadata["value"].data)


      result = self.get_data_list(key,metadata)
      if result == None:
         return None

      print('$$$$$$$$$$  Result is')
      print(result)

      # Getting the Corrupt and the Valid Servers
      for i in result:
        if result[i]['valbit']==0:
              corruptserver.append(i)
        elif result[i]['valbit'] ==-1:
              cleanservers.append(i)
        else:
              valdata=result[i]['data']
              validserver = i

      print('$$$$$$$$$$  CleanServers :')
      print(cleanservers)
      print('$$$$$$$$$$  Valid Servers :')
      print(validserver)
      print('$$$$$$$$$$  Corrupt Servers :')
      print(corruptserver)

      self.recoverdata(validserver,cleanservers) 


      # All servers good, no need to repair
      if len(corruptserver) == 0:
         print('$$$$$$$$$$$$$$$$$$  All Good!!')
         return self.rpc_data[validserver].get(key)

      # If number of good servers less than the Quorum, then repair and client request should fail
      if (len(self.dataports)-len(corruptserver)) < self.Qr :
	 print('REPAIR!!!!:(')
         self.repair(corruptserver,key,valdata)
         return None

      # If number of good servers equal to or more than the Quorum, then repair corrupt server and send valid value to the client
      else:
         print('$$$$$$$$$$$$ Good yo go')
         self.repair(corruptserver,key,valdata)
         return self.rpc_data[validserver].get(key)
      return None



   def repair(self,corruptserver,key,valdata):
      for i in corruptserver:
        self.rpc_data[i].put(key,Binary(pickle.dumps(valdata)),6000)
      print('$$$$$$$$$$$$$$ Value has been repaired')



   # TO DO -> Quorum
   def put_data(self,key,value):
      for i in self.dataports:
         self.rpc_data[i].put(key, value, 6000)


   #def check_and_repair(self,key):
      

def main():
  optlist, args = getopt.getopt(sys.argv[1:], "", ["Qr=","Qw=","metaport=","dataport=", "test"])
  dataports=[]
  for k,v in optlist:
    if '--metaport' in k:
       mp=int(v)
    if '--dataport' in k:
       dataports.append(int(v))
    if '--Qr' in k:
       qr= int(v)
    if '--Qw' in k:
       qw= int(v)
  port=9000
  print('$$$$$$$$$$$$$$$$$$$ Mediator : Printing dataports[]')
  print(dataports)
  serve(dataports,mp,qr,qw,port)
  
  # IMPORTANT! Will the control return here? serve_forever()??
  logging.getLogger().setLevel(logging.DEBUG)
  #fuse = FUSE(Mediator(), argv[1], foreground=True,debug=True)

# Start the xmlrpc mediator server : say, python mediator.py <Qr> <Qw> <meta_port> <data_port1>....<data_portN>
def serve(dataports,metaport,qr,qw,port):
  med_server = SimpleXMLRPCServer.SimpleXMLRPCServer(('', port),allow_none=True)
  med_server.register_introspection_functions()
  sht = Mediator(dataports,metaport,qr,qw)
  med_server.register_function(sht.get_meta)
  med_server.register_function(sht.put_meta)
  med_server.register_function(sht.get_data)
  med_server.register_function(sht.put_data)
  med_server.register_function(sht.remove_data)
  med_server.register_function(sht.remove_meta)
  print('$$$$$$$$$$$$$$ INitiating the mediator')
  med_server.serve_forever()


if __name__ == '__main__':
   main()
