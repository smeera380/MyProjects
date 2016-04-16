This is a Fuse file system implementation with persistent data storage using Mongodb. i.e., remounting the File system should preserve the previously created data. The implementation also includes an in-memory caching layer in the File system, for better performance and to avoid disk access.

1. Say current working directory is X. Copy the files remote_tree.py , cache_remote_tree.py and evaluate.sh into directory X.

2. Create a mountpoint (directory to mount the File system, say 'fusemount') in X. 
   mkdir fusemount
   directory structure: X/fusemount
   
3. From directory X, execute remote_tree.py as below : 
     python remote_tree.py fusemount <url>
	 url can be any string enclosed within quotes

   Note : remote_tree.py will have the FS Implementation without the Cache. The interaction will be directly with the Mongodb.

4. The data in the DB can be verified using a MongoDB Shell.
     Go to the installation dir of the Mongod
   	 execute ./bin/mongo

	 show dbs
	 use files
	 db.files.find()	 

5. To verify the persistence of file storage, unmount the FS and then do a remount. Traverse to cd X/fusemount
   The data should be accessible.	

6. To clear the data existing data in the db for the connection 'files', do a db.files.remove({}) from a MongoDB Shell. 

7. Run the cache_remote_tree.py as below:
     python cache_remote_tree.py fusemount 

   Note : cache_remote_tree.py will have the FS Implementation with Cache.   

9. Repeat Step 5 to verify the persistence.	

	 
