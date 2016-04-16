This is a Distributed File System implementation with Fault tolerance based on Quorum approach. Here, a separate Read and Write Quorum is used to realise Fault tolerance (Quorum -> Say there are 3 servers in total and Quorum is 2, then unless and until two servers agree upon a block of data, the same cannot be read or written, ie., upto one server failure can be tolerated and corrected).
An assumption made during the implementation is that of a single client. The client communicates to the Dataservers and the Metaserver through a Mediator. The Mediator retrives information from allt he dataservers and decide if the Quorum is met or not. If yes, server failures are transparent to the Client. Else, an error message will be sent. The dataserver stores the actual data. Metaserver holds the metadata information about the files, like the creation date, creation time, directories, hierarchy, etc.

1. Say current working directory is X. Copy the files metaserver.py,dataserver.py,mediator.py,filesystem.py,fuse,py and evaluate.sh into
directory X.

2. First get the Meta and DataServers up and running (say, with three data servers).
   python metaserver.py --port 51234
   python dataserver.py --port 9004
   python dataserver.py --port 9005
   python dataserver.py --port 9006

3. To get the Mediator up and running, use the below command (Note: Mediator by default configured to use port 9000) :
   python mediator.py --Qr=2 --Qw=2 --metaport=51234  --dataport=9004 --dataport=9005 --dataport=9006
   
4. To mount the filesystem, execute the below command:
   python filesystem.py fusemount 9000

5. Run the script evaluate.sh to test the basic functionalities.       
   ./evaluate.sh

6. To check the corrupt and repair functionality, please follow the below steps:
   6.1  Open Python shell.
   6.2 import xmlrpclib
       from xmlrpclib import Binary
   6.3 Create a dataserver proxy for corrupting the data. Let the dataserver port be 9005.
      >>> rpc_data2 = xmlrpclib.ServerProxy('http://localhost:9005',allow_none=True)
      >>> rpc_data2.list_contents()  // this lists the Data server contents before the corruption.
          True
      >>> rpc_data2.corrupt(Binary('/dir1/hello.txt'))
       Note : Assuming that /dir1/hello.txt has already been created with some data.
       Note: In the corrsponding dataserver's log, we can see the value of the data before and after corruption.
   6.4 To ensure that data corruption in one dataserver is transparent to the client,
       cd to fusemount
       cat dir1/hello.txt
       It should return the correct data.
	 
7. To check the terminate functioanlity, please follow the below commands:
   7.1 Repeat steps 6.1 and 6.2
   7.2 Create a dataserver proxy for initiating the termination. Say, we are using the dataserver port is 9005.
       >>> rpc_data2 = xmlrpclib.ServerProxy('http://localhost:9005',allow_none=True)
       >>> rpc_data2.terminate()
   7.3 To ensure that one dataserver termination is transparent to the client,
       cd to fusemount
       Try to retrieve an already existing data.
