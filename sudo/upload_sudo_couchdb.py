import couchdb
import sys, json 

sudo_file = sys.argv[1]

server_url = 'http://admin:admin@172.26.135.208:5984/'
db_name = sys.argv[2]
couch = couchdb.Server(server_url)
if db_name not in couch:
    couch.create(db_name)
db = couch[db_name]

with open(sudo_file) as sf:
    data = json.load(sf)
    for obj in data['features']:
        properties = obj['properties']
        db.save(properties)