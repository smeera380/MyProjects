This is a Hiearachical Fuse FS implementation in Python extended to support remote storage. The hierarchicalFS.py file deals with the implementation of the hierarchical in-memory FUSE file system. The crux of the implementation lies in the structure and maintenence of a data structure which manages the Python file system, here, dictionaries. The code mainly deals with the realisation of the common file system fucntionalities like, Creating a directory or File, listing , renaming , changing directories, etc.
As an extension to this basic implementation, remoteHierarchicalFS.py is constructed as a Client-Server model with the Server being a remote machine housing the data, and the client sends xmlrpc calls to the Server to retrieve or modify data. Here, the server is assumed to be the localhost itself.

1. Say current working directory is X. Copy the files hierachicalFS.py, remoteHierarchicalFS.py , fuse.py, simpleht.py and evaluate.sh in directory X.

--------------------Local Hierachical FS Implementation ------------------------
1. Create a mountpoint (directory to mount the File system, say 'fusemount') in X. 

   mkdir fusemount
   directory structure: X/fusemount

2. From directory X, execute:
   python hierarchicalFS.py fusemount

3. Open another terminal. 
   cd to X directory.

4. Execute ./evaluate.sh
This file executes the basic file system operations and their result.

5. Further operations can be carried out by changing to the 'fusemount' directory.

---------------------Remote Hierachical FS Implementation --------------------------
1. Create a mountpoint (directory to mount the File system, say 'fusemount') in X. 

   mkdir fusemount
   directory structure: X/fusemount

2. Start a server instance.
   python simpleht.py

3. To mount the filesystem, from directory X, execute:
   python remoteHierarchicalFS.py fusemount

4. Execute ./evaluate.sh
This file executes the basic file system operations and their result.

5. Further operations can be carried out by changing to the 'fusemount' directory.
