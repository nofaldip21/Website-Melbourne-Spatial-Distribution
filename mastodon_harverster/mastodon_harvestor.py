from mastodon import Mastodon, MastodonNotFoundError, MastodonRatelimitError, StreamListener
import requests
import csv, os, time, json, re
import couchdb
import flask
import sys
from flask import request, jsonify
app = flask.Flask(__name__)

os.environ['CLIENT_ID'] = sys.argv[1]
os.environ['SECRET'] = sys.argv[2]
os.environ['MASTODON_ACCESS_TOKEN'] = sys.argv[3]
os.environ['SERVERURL'] = sys.argv[4]
os.environ['DB'] = sys.argv[5]
os.environ['PORT'] = sys.argv[6]

def init_couchdb() :
    server_url = 'http://admin:admin@172.26.135.208:5984'
    db_name = os.environ['DB']
    couch = couchdb.Server(server_url)
    if db_name not in couch:
        couch.create(db_name)
    db = couch[db_name]
    return db

db = init_couchdb()

class Listener(StreamListener):
    def __init__(self, keys:object):
        # Constructor with only name
        self.keys = keys
        # print('keys', self.keys)
        
    def on_update(self, status, ):
        doc = {}
        doc['id'] = status['id']
        doc['created_at'] = status['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        doc['language'] = status['language']
        doc['url'] = status['url']
        doc['reblog'] = status['reblog']
        doc['content'] = status['content']
        
        if self.keys.search(doc['content']):
            print("Matched! Saving to couchdb...")
            print(doc['content'])
            db.save(doc)
        else:
            print("No match.")

@app.route("/api/v1/harvest",  methods = ['POST'])
def api_insert():
    keywords = request.get_json()
    keywords_re = re.compile("|".join(keywords))
    listener = Listener(keywords_re)
    
    mastodon = Mastodon(
        client_id = os.environ['CLIENT_ID'],
        client_secret =  os.environ['SECRET'],
        access_token = os.environ['MASTODON_ACCESS_TOKEN'],
        api_base_url = os.environ['SERVERURL']
    )
    
    mastodon.stream_public(listener)

    return 'complete'

if __name__ == '__main__':

    # print(os.environ['CLIENT_ID'])
    # print( os.environ['SECRET'])
    # print(os.environ['MASTODON_ACCESS_TOKEN'])
    # print(os.environ['SERVERURL'])
    
    app.run(host="0.0.0.0", port=sys.argv[6])