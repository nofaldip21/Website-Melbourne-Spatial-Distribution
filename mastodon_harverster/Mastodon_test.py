from mastodon import Mastodon, MastodonNotFoundError, MastodonRatelimitError, StreamListener
import requests
import csv, os, time, json, re, sys
import argparse
import couchdb


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
    db_name = 'mastodon_toots_test'
    couch = couchdb.Server(server_url)
    if db_name not in couch:
        couch.create(db_name)
    db = couch[db_name]
    return db


db = init_couchdb()

# with open('mastodon_toots.json', 'r') as f:
#     db.save(f)


# rate limit is 300 per 5 minutes
# “wait” mode will, once the limit is hit, 
#  wait and retry the request as soon as the rate limit resets, until it succeeds.
print("ratelimit:", mastodon.ratelimit_limit)
print("remaining:", mastodon.ratelimit_remaining)

keywords = ["rent",
            "price",
            "house",
            "apartment", 
            "flat", 
            "unit",
            "room", 
            "accommodation",
            "health",
            "fitness",
            "sports",
            "physical",
            "marathon",
            "basketball",
            "cricket",
            "tennis",
            "languages",
            "spoken"
           ]

keywords_re = re.compile("|".join(keywords))

class Listener(StreamListener):
    def on_update(self, status):
        # print(status['geo'])
        for doc in status['account']['fields']:
            print(doc.keys())
        # doc = {}
        # doc['id'] = status['id']
        # doc['created_at'] = status['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        # doc['language'] = status['language']
        # doc['url'] = status['url']
        # doc['reblog'] = status['reblog']
        # doc['content'] = status['content']
        # print(status.keys())
        # print(status)
        # if keywords_re.search(doc['content']):
        #     print("Matched! Saving to couchdb...")
        #     print(doc['content'])
        #     print(status)
        #     db.save(doc)
        #     # with open('mastodon_toots.json', 'a') as f:
        #     #     json.dump(status, f, indent=4)
        # else:
        #     print("No match.")
        
print("streaming...")
listener = Listener()

mastodon.stream_public(listener)

# toots = mastodon.timeline_public(limit=10)
# toot_dicts = [toot.__dict__ for toot in toots]
# print(toots[0])

# with open('mastodon_toots.json', 'w') as f:
#     json.dump(toots, f, indent=4, default=str)
