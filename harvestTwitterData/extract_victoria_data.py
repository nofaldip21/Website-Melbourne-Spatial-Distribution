from mpi4py import MPI
import math
import json
import os

def inserted_file (start,size) :
    end = start +size
    lines = []
    with open(FILE_NAME, 'rb') as f:
        f.seek(start)
        pointer = start
        while pointer < end :
            lineTemp = f.readline()
            pointer += len(lineTemp)
            if lineTemp == b'' :
                break
            line = lineTemp.decode('utf-8').strip()
            if line[-1] == ']' :
                line = line[:-1]
            if line[-1] == ',' :
                line = line[:-1]
            try :
                jsonLoad = json.loads(line)
                jsonLoad["_id"] = jsonLoad["id"]
                if 'victoria' in jsonLoad['doc']['includes']['places'][0]['full_name'].lower() :
                    lines.append(jsonLoad)
            except :
                continue
    jsonFile = DEST_FOLDER + "/clean json rank " +str(rank)+".json"
    with open(jsonFile, "w") as f:
        json.dump(lines, f)

#define MPI object
comm = MPI.COMM_WORLD
size = comm.Get_size()
rank = comm.Get_rank()

# If you want to try this code please insert twitter-huge.json on Dataset folder
FILE_NAME = 'Dataset/twitter-huge.json'
DEST_FOLDER ='SplitResult'

if rank == 0 :
    allMemory = os.path.getsize(FILE_NAME)
    #split the file base on cores
    splittedMemory = math.ceil((allMemory) // size)
    with open(FILE_NAME, 'rb') as f:
        line = f.readline()
        lastPointer = 0
        lastPointer += len(line)
        listOfChunkyfy = []
        while lastPointer < allMemory :
            beginPointer = lastPointer+1
            #move the pointer until reach the splittedMemory
            f.seek(beginPointer+splittedMemory)
            lastPointer = beginPointer+splittedMemory
            line = f.readline()
            lastPointer += len(line)
            listOfChunkyfy.append((beginPointer,lastPointer-beginPointer))
else :
    listOfChunkyfy = None
        
chunk = comm.scatter(listOfChunkyfy, root=0)
inserted_file(*chunk)     

