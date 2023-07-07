import couchdb

# Tweets/toots languages vs Languages spoken (at home) in an area
def scenario2():
    # Connect to CouchDB server
    couch = couchdb.Server('http://admin:admin@172.26.135.208:5984/')

    # Get tweets
    db_tweet = couch['victoria-db-online']

    # Get mastodon toots

    # Get view
    db_lang = couch['language_spoken']
    view = db_lang.view('view_language_spoken/city_languages')

    # Process view and put into a dictionary
    # lga_lang_dict = {
    #   lga_code_1: {
    #       'language1': 1,
    #      'language2': 1,
    #       ...
    #   },
    #   lga_code_2: {
    #       'language1': 1,
    #       'language2': 1,
    #      ...
    #   },
    #   ...
    # }
    lga_lang_dict = dict()
    for row in view:
        lga = row.key
        lang = row.value
        lga_lang_dict.update({lga: lang})

    print(lga_lang_dict)

if __name__ == '__main__':
    scenario2()
