from mastodon import Mastodon, MastodonNotFoundError, MastodonRatelimitError, StreamListener
import requests
import csv, os, time, json, re, sys
import argparse
import couchdb
import flask
from flask import request, jsonify
app = flask.Flask(__name__)
tokens = json.load(open('tokens.json', 'r'))
TOPICS = ['rent', 'sports', 'language']

parser = argparse.ArgumentParser()
parser.add_argument('-s', '--server', help='Mastodon server', default='mastodon.au')
parser.add_argument('-t', '--topic', help='Topic to search for', default='rent')

args = parser.parse_args()
server = args.server
topic = args.topic

if topic not in TOPICS:
    print('Invalid topic. Please choose from: ', TOPICS)
    sys.exit()
    
if server not in tokens.keys():
    print('Invalid server. Please choose from: ', tokens.keys())
    sys.exit()

os.environ['MASTODON_ACCESS_TOKEN'] = tokens[server]['access_token']

# Mastodon API
mastodon = Mastodon(
    client_id= tokens[server]['client_key'],
    client_secret= tokens[server]['client_secret'],
    access_token = os.environ['MASTODON_ACCESS_TOKEN'],
    api_base_url = 'https://' + server
)

# CouchDB
def init_couchdb() :
    server_url = 'http://admin:admin@172.26.135.208:5984'
    db_name = f'mastodon_toots_{topic}'
    couch = couchdb.Server(server_url)
    if db_name not in couch:
        couch.create(db_name)
    db = couch[db_name]
    return db

db = init_couchdb()

class Listener(StreamListener):
    def __init__(self, keys:object, server:str, topic:str):
        # Constructor with only name
        self.keys = keys
        self.server = server
        self.topic = topic
        print('keys: ', self.keys)
        print('server: ', self.server)
        print('topic: ', self.topic)
        
    def on_update(self, status):
        if self.topic == 'rent':
            self.harvest_rent(status)
        elif self.topic == 'sports':
            self.harvest_sports(status)
        elif self.topic == 'language':
            self.harvest_language(status)
        else:
            print('Invalid topic. Please choose from: ', TOPICS)
            sys.exit()
    
    def harvest_rent(self, status):
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
    
    def harvest_language(self, status):
        # retrieve all toots from the server
        doc = {}
        doc['id'] = status['id']
        doc['created_at'] = status['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        doc['language'] = status['language']
        doc['url'] = status['url']
        doc['reblog'] = status['reblog']
        doc['content'] = status['content']
        print("Matched! Saving to couchdb...")
        print(doc['content'])
        db.save(doc)
    
    def harvest_sports(self, status):
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
    print("keywords", keywords)
    keywords_re = re.compile("|".join(keywords))
    # print("keywords_re", keywords_re)
    listener = Listener(keywords_re, server, topic)

    mastodon.stream_public(listener)
    
    return 'Harvesting Complete'

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5001)