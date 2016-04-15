This is a Hiearachical Fuse FS implementation in Python.

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
