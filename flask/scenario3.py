import couchdb

# Tweets/toots mentioning sports/health vs number of sports and 
# recreation facilities in an area
def scenario3():
    # Connect to CouchDB server
    couch = couchdb.Server('http://admin:admin@172.26.135.208:5984/')

    # Get tweets
    db_tweet = couch['victoria-db-online']

    # Get mastodon toots

    # Get view
    db_srf = couch['sport_and_recreation_facility']
    view = db_srf.view('nfacilities_lga/nfacilities_lga', group=True)

    # Process view and put into a dictionary
    # lga_nfacilities_dict = {
    #     {lga_name_1: number of facilities},
    #     {lga_name_2: number of facilities},
    #     ...
    # }
    lga_nfacilities_dict = dict()
    for row in view:
        lga = row.key
        n_facilities = row.value
        lga_nfacilities_dict.update({lga: n_facilities})

    print(lga_nfacilities_dict)

if __name__ == '__main__':
    scenario3()
