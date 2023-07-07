import json
from mpi4py import MPI
import couchdb
import math

def init_couchdb() :
    server_url = 'http://admin:admin@172.26.135.208:5984/'
    db_name = 'victoria-db-online'
    couch = couchdb.Server(server_url)
    if db_name not in couch:
        couch.create(db_name)
    db = couch[db_name]
    return db

db = init_couchdb()
num_split = 10

#define MPI object
comm = MPI.COMM_WORLD
size = comm.Get_size()
rank = comm.Get_rank()

print("================================uploading part "+str(rank)+"=============================")
DEST_FOLDER ='SplitResult/clean json rank '+str(rank)+'.json'
with open(DEST_FOLDER, 'rb') as f:
    alldata = json.load(f)
lenData = len(alldata)
print("length of data "+str(lenData))
splitter = math.ceil( lenData // num_split)
print("number of splitter "+str(splitter))
k = 0
currPos = 0
while currPos < lenData :
    try :
        lastPointer = currPos + splitter
        if lastPointer > lenData :
            db.update(alldata[currPos:])
            print(k)
            print("from "+str(currPos)+" to "+str(lenData))
            k += 1
            currPos = lenData 
        else :
            db.update(alldata[currPos:lastPointer])  
            print(k)
            print("from "+str(currPos)+" to "+str(lastPointer))
            k += 1
            currPos = lastPointer
    except :
        continue
print("======================== done for this part ===============================")