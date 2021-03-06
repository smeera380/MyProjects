#!/usr/bin/env python
"""
Author: David Wolinsky
Version: 0.02

Description:
The XmlRpc API for this library is:
  get(base64 key)
    Returns the value and ttl associated with the given key using a dictionary
      or an empty dictionary if there is no matching key
    Example usage:
      rv = rpc.get(Binary("key"))
      print rv => {"value": Binary, "ttl": 1000}
      print rv["value"].data => "value"
  put(base64 key, base64 value, int ttl)
    Inserts the key / value pair into the hashtable, using the same key will
      over-write existing values
    Example usage:  rpc.put(Binary("key"), Binary("value"), 1000)
  print_content()
    Print the contents of the HT
  read_file(string filename)
    Store the contents of the Hahelperable into a file
  write_file(string filename)
    Load the contents of the file into the Hahelperable
"""
import SocketServer,SimpleXMLRPCServer
import sys, getopt, pickle, time, threading, xmlrpclib, unittest
from datetime import datetime, timedelta
from xmlrpclib import Binary
from SimpleXMLRPCServer import SimpleXMLRPCRequestHandler

class SimpleThreadedXMLRPCServer(SocketServer.ThreadingMixIn, SimpleXMLRPCServer.SimpleXMLRPCServer):
  pass

quit = 0

# Presents a HT interface
class DataServer:
  def __init__(self):
    self.data = {}
    self.next_check = datetime.now() + timedelta(minutes = 5)

  def count(self):
    # Remove expired entries
    self.next_check = datetime.now() - timedelta(minutes = 5)
    self.check()
    return len(self.data)


  # Retrieve something from the HT
  def get(self, key):
    # Remove expired entries
    self.check()
    # Default return value
    rv = {}
    # If the key is in the data structure, return properly formated results
    print('$$$$$$$$$$$$$$ Get method : Key initial')
    print(key)

    key = key.data
    print(key)
    print('GET DONE')
    
    if key in self.data:
      ent = self.data[key]
      now = datetime.now()
      if ent[1] > now:
        ttl = (ent[1] - now).seconds
        rv = {"value": Binary(ent[0]), "ttl": ttl}
      else:
        del self.data[key]

      if ttl<=0:
         del self.data[key]
    return rv

  # Insert something into the HT
  def put(self, key, value, ttl):
    # Remove expired entries
    self.check()
    end = datetime.now() + timedelta(seconds = ttl)
    self.data[key.data] = (value.data, end)
    if ttl==0:
      del self.data[key.data]
   
    return True

    
  # Load contents from a file
  def read_file(self, filename):
    f = open(filename.data, "rb")
    self.data = pickle.load(f)
    f.close()
    return True

  # Write contents to a file
  def write_file(self, filename):
    f = open(filename.data, "wb")
    pickle.dump(self.data, f)
    f.close()
    return True

  # Print the contents of the hashtable
  def print_content(self,key):
    print self.data
    if key in self.data:
      print('Data exists')
      print(self.data[key]) 
    return True

  def list_contents(self):
    print ('@@@@@@@@@@@@@ content')
    for i in self.data:
     print('Key :  ' , i, '  Value : ',pickle.loads(self.data[i][0]))
    return True



  # Remove expired entries
  def check(self):
    now = datetime.now()
    if self.next_check > now:
      return
    self.next_check = datetime.now() + timedelta(minutes = 5)
    to_remove = []
    for key, value in self.data.items():
      if value[1] < now:
        to_remove.append(key)
    for key in to_remove:
      del self.data[key]
      

  def getrecoverydata(self):
    return self.data
    print('$$$$$$$$$$$$$$ Printing the data to be cloned')
    print self.data

  def recoverdata(self,recdata):
    self.data = recdata
    print('$$$$$$$$$$$$$$$$$  Print data recovered!!!')

  def corrupt(self, key):
    keyorg= key
    self.check()
    key = key.data
    print('$$$$$$$$$$$$$$ Corrupt method: Printing key initial')
    print(key)
    
    if key in self.data:
      print('Data exists')
      print(self.data[key])    
      cvalue = 'JUNK'
      value = Binary(pickle.dumps(cvalue))
      print('Corrupted value')
      print value
      self.put(keyorg, value, 6000)

    print('$$$$$$$$$$ After corruption')
    print(self.data[key])


  def terminate(self):
    global quit
    quit = 1 
    return 1

       
def main():
  optlist, args = getopt.getopt(sys.argv[1:], "", ["port=", "test"])
  ports = []
  for k,v in optlist:
    if '--port' in k:
       ports.append(k)
       serve(int(v))


# Start the xmlrpc server

def serve(port):
  data_server = {}
  sht = {}
  data_server[port]= SimpleXMLRPCServer.SimpleXMLRPCServer(('', port),allow_none=True)
  data_server[port].register_introspection_functions()
  sht[port] = DataServer()
  data_server[port].register_function(sht[port].get)
  data_server[port].register_function(sht[port].put)
  data_server[port].register_function(sht[port].print_content)
  data_server[port].register_function(sht[port].read_file)
  data_server[port].register_function(sht[port].write_file)
  data_server[port].register_function(sht[port].corrupt)
  data_server[port].register_function(sht[port].list_contents)
  data_server[port].register_function(sht[port].getrecoverydata)
  data_server[port].register_function(sht[port].recoverdata)
  data_server[port].register_function(sht[port].terminate)
  print('$$$$$$$$$$$$$$$$$$$$$ Data Server : Printing port ')
  print(port)

  while not quit:
    data_server[port].handle_request()

'''
class ServerThread(threading.Thread):
   def __init__(self,port):
       threading.Thread.__init__(self)
       self.localServer = SimpleThreadedXMLRPCServer(("localhost",port))
       sht = DataServer()
       self.localServer.register_function(sht.get) 
       self.localServer.register_function(sht.put) 
       self.localServer.register_function(sht.print_content) 
       self.localServer.register_function(sht.read_file) 
       self.localServer.register_function(sht.write_file) 

   def run(self):
       self.localServer.serve_forever()
'''

if __name__ == "__main__":
  main()

