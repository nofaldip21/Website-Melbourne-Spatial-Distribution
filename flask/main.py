from flask import Flask, render_template, request
from folium.plugins import StripePattern
from datetime import datetime
import pandas as pd
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import geopandas as gpd
import plotly.io as pio
import plotly.express as px
import folium
import json
import pandas as pd
import couchdb
import geopandas as gpd
from folium.plugins import StripePattern

STATIC = 'static'

app = Flask(__name__,template_folder='templates',static_folder=STATIC)

@app.route('/')
def home():
    try :
        # Connect to CouchDB server
        couch = couchdb.Server('http://admin:admin@172.26.135.208:5984/')

        # Select the desired database
        db = couch['household_income']
        db_lang = couch['language_spoken']
        db_tweet = couch['victoria-db-online']
        db_sport_mastodon = couch['mastodon_toots_sports']
        db_lang_mastodon = couch['mastodon_toots_language']

        # Select the view
        view_lang = db_lang.view('view_language_spoken/view_by_name')
        view_sport = db_tweet.view('sport_health/sport_view_v2',group=True)
        view_sport_mastodon = db_sport_mastodon.view('doc_sport/sport_keyword_view', group=True)
        view_lang_mastodon = db_lang_mastodon.view('word_view/most_language_view', group=True)

    except couchdb.ServerError as e:
        print("Connectiong Error in couchDB:", e)

    except couchdb.ResourceNotFound as e:
        print("the Database not found:", e)

    except Exception as e:
        print("Other error:", e)

    try :
        #load pre data
        all_docs = list(db.view('_all_docs', include_docs=True))
        df_rent = pd.read_csv('static/df_rent.csv',sep='\t')
        df_sport_sudo = pd.read_csv("static/df_sport_sudo.csv",sep="\t")
        df_lang_twitter = pd.read_csv("static/df_lang_tweeter.csv",sep="\t")
        geojson_data = "static/edited-georef.geojson"
        json_language_file = "static/language.json"
        with open(json_language_file,'r', encoding='utf-8') as f :
            lan_value = json.load(f)
    
    except FileNotFoundError as e:
        print("Cannot find the file:", e)

    except IOError as e:
        print("Error while input/output:", e)

    except Exception as e:
        print("Other error:", e)


    # Get sudo language data from couchdb
    lga_lang_dict = []
    total_non_eng = 0
    for row in view_lang:
        dict_temp={}
        dict_temp['lga_name_lower'] = row.key[0].lower()
        dict_temp['eng'] = 0
        dict_temp['non_eng'] = 0
        for i,val in row.value.items() :
            if i != 'english' :
                dict_temp['non_eng'] += val
                total_non_eng += val
            else :
                dict_temp['eng'] += val
        split_lga_name = dict_temp['lga_name_lower'].split(" - ")
        if len(split_lga_name) > 1 :
            for i in split_lga_name :
                dict_split = {}
                dict_split['lga_name_lower'] = i
                dict_split['eng'] = dict_temp['eng']
                dict_split['non_eng'] = dict_temp['non_eng']
                lga_lang_dict.append(dict_split)
            mul_val = len(split_lga_name) - 1
            total_non_eng += mul_val * dict_split['non_eng']
            continue
        lga_lang_dict.append(dict_temp)
    df_lang_sudo = pd.DataFrame(lga_lang_dict)
    df_lang_sudo['percentage_non_eng_sudo'] = df_lang_sudo['non_eng']

    list_dict = []
    total_low_income = 0
    for i in all_docs :
        dict_temp = {}
        dict_temp['id'] = i['doc']['lga_code_2021']
        dict_temp['value'] = i['doc']['hi_1_149_tot'] 
        dict_temp['value'] += i['doc']['hi_150_299_tot'] 
        dict_temp['value'] += i['doc']['hi_300_399_tot'] 
        dict_temp['value'] += i['doc']['hi_400_499_tot']
        dict_temp['value'] += i['doc']['hi_500_649_tot']
        dict_temp['value'] += i['doc']['hi_650_799_tot']
        total_low_income += dict_temp['value']
        list_dict.append(dict_temp)
        
    df = pd.DataFrame(list_dict)
    df['value'] = round(df['value'] * 100/total_low_income,2)

    # get sport tweet
    lga_sport_dict = []
    for row in view_sport:
        split_word = row.key.lower().split(', ')
        current_word = split_word[0]
        split_again = current_word.split(' - ')
        for i in split_again :
            dict_temp = {}
            dict_temp['lga_name_lower'] = i
            dict_temp['number_sport_tweet'] =  row.value
            lga_sport_dict.append(dict_temp)

    df_sport_tweet = pd.DataFrame(lga_sport_dict)

    # Get mastodon sport
    lga_nfacilities_dict = []
    for row in view_sport_mastodon:
        dict_temp={}
        dict_temp['word']=row.key
        dict_temp['number_of_hashtag']=row.value
        lga_nfacilities_dict.append(dict_temp)
    rent_sport = pd.DataFrame(lga_nfacilities_dict).sort_values('number_of_hashtag',ascending = False)

    # Get tweets mastodon language
    lga_nfacilities_dict = []
    for row in view_lang_mastodon:
        dict_temp={}
        dict_temp['country_code']=row.key
        dict_temp['number_of_language']=row.value
        lga_nfacilities_dict.append(dict_temp)
    rent_language = pd.DataFrame(lga_nfacilities_dict).sort_values('number_of_language',ascending = False)
        
    list_code_name = []
    for item,value in lan_value.items() :
        dict_temp = {}
        dict_temp['country_code'] = item
        dict_temp['country_name'] = value['name']
        list_code_name.append(dict_temp)
    df_country_code = pd.DataFrame(list_code_name)
    rent_language = rent_language.merge(df_country_code,on='country_code',how='left')

    # making the map object
    map_obj = folium.Map(location=[-37.8136, 144.9631], zoom_start=9)
    map_obj_lang = folium.Map(location=[-37.8136, 144.9631], zoom_start=9)
    map_obj_sport = folium.Map(location=[-37.8136, 144.9631], zoom_start=9)

    # build geojson data frame
    geoJSON_df = gpd.read_file(geojson_data)
    geoJSON_df['lga_name_lower'] = geoJSON_df['lga_name'].str.lower()
    geoData = geoJSON_df[['lga_code','lga_name','lga_name_lower','geometry']].merge(df,left_on = "lga_code",right_on = "id")
    geoData = geoData.merge(df_rent[['lga_name_lower','percentage']],on = 'lga_name_lower',how='left')
    geoData = geoData.merge(df_lang_sudo[['lga_name_lower','percentage_non_eng_sudo']],on = 'lga_name_lower',how='left')
    geoData = geoData.merge(df_sport_sudo,on = 'lga_name_lower',how='left')
    geoData = geoData.merge(df_lang_twitter,on = 'lga_name_lower',how='left')
    geoData = geoData.merge(df_sport_tweet,on = 'lga_name_lower',how='left')
    geoData = geoData.fillna(0)

    # build choropleth layer
    choropleth_layer = folium.Choropleth(
        geo_data=geojson_data,
        name="Area Percentage Low Income",
        data=df,
        columns=["id", "value"],
        key_on="feature.properties.lga_code",
        fill_color="RdPu",
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name="Percentage Low Income Area ",
    ).add_to(map_obj)

    choropleth_layer_lang = folium.Choropleth(
        geo_data=geojson_data,
        name="Area Percentage Non English",
        data=geoData,
        columns=["lga_code", "percentage_non_eng_sudo"],
        key_on="feature.properties.lga_code",
        fill_color="YlGnBu",
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name="Area Percentage Non English"
    ).add_to(map_obj_lang)

    choropleth_layer_sport = folium.Choropleth(
        geo_data=geojson_data,
        name="Area Number Sport Facilities",
        data=geoData,
        columns=["lga_code", "number_facilities"],
        key_on="feature.properties.lga_code",
        fill_color="YlGn",
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name="Area Number Sport Facilities"
    ).add_to(map_obj_sport)

    # style function
    style_function = lambda x: {'fillColor': '#ffffff', 
                                'color':'#000000', 
                                'fillOpacity': 0.1, 
                                'weight': 0.1}

    highlight_function = lambda x: {'fillColor': '#000000', 
                                    'color':'#000000', 
                                    'fillOpacity': 0.50, 
                                    'weight': 0.1}
    
    # Here we add cross-hatching (crossing lines) to display the Null values.
    nans = geoData[geoData["percentage"] > 0]['lga_code'].values
    gdf_nans = geoData[geoData['lga_code'].isin(nans)]
    sp = StripePattern(angle=45, color='grey', space_color='black')
    sp.add_to(map_obj)
    folium.features.GeoJson(name="Click for Tweets Rental Values",data=gdf_nans, style_function=lambda x :{'fillPattern': sp},show=True).add_to(map_obj)

    nans_lang = geoData[geoData["number_lang_twitter"] > 0]['lga_code'].values
    gdf_nans_lang = geoData[geoData['lga_code'].isin(nans_lang)]
    sp_lang = StripePattern(angle=45, color='grey', space_color='black')
    sp_lang.add_to(map_obj_lang)
    folium.features.GeoJson(name="Click for Tweets non English",data=gdf_nans_lang, style_function=lambda x :{'fillPattern': sp_lang},show=True).add_to(map_obj_lang)

    nans_sport = geoData[geoData["number_sport_tweet"] > 0]['lga_code'].values
    gdf_nans_sport = geoData[geoData['lga_code'].isin(nans_sport)]
    sp_sport = StripePattern(angle=45, color='grey', space_color='black')
    sp_sport.add_to(map_obj_sport)
    folium.features.GeoJson(name="Click for Tweets with Health or Sport",data=gdf_nans_sport, style_function=lambda x :{'fillPattern': sp_sport},show=True).add_to(map_obj_sport)

    NIL = folium.features.GeoJson(
        data = geoData,
        style_function=style_function,
        control=False, 
        highlight_function=highlight_function,
        tooltip=folium.features.GeoJsonTooltip(
            fields=['lga_name','value','percentage'],
            aliases=['Area','Percentage Low Income :','Percentage Number of Tweet :'],
            style=("background-color: white; color: #333333; font-family: arial; font-size: 12px; padding: 10px;")
        )
    )

    NIL_lang = folium.features.GeoJson(
        data = geoData,
        style_function=style_function,
        control=False, 
        highlight_function=highlight_function,
        tooltip=folium.features.GeoJsonTooltip(
            fields=['lga_name','percentage_non_eng_sudo',"number_lang_twitter"],
            aliases=['Area','Number non-Eng Language in Area :',"Number non-Eng Language Tweet in Area :"],
            style=("background-color: white; color: #333333; font-family: arial; font-size: 12px; padding: 10px;")
        )
    )

    NIL_sport = folium.features.GeoJson(
        data = geoData,
        style_function=style_function,
        control=False, 
        highlight_function=highlight_function,
        tooltip=folium.features.GeoJsonTooltip(
            fields=['lga_name','number_facilities','number_sport_tweet'],
            aliases=['Area :','number sport facilities :', 'number of sport or health related tweet :'],
            style=("background-color: white; color: #333333; font-family: arial; font-size: 12px; padding: 10px;")
        )
    )   

    choropleth_layer.add_child(NIL)
    map_obj.keep_in_front(NIL)
    folium.LayerControl().add_to(map_obj)

    choropleth_layer_lang.add_child(NIL_lang)
    map_obj_lang.keep_in_front(NIL_lang)
    folium.LayerControl().add_to(map_obj_lang)

    choropleth_layer_sport.add_child(NIL_sport)
    map_obj_sport.keep_in_front(NIL_sport)
    folium.LayerControl().add_to(map_obj_sport)
    
    # Bar Plot for Mastodon Data
    # Select the desired databases
    db_mastodon_lang = couch['mastodon_toots_language']
    db_mastodon_rent = couch['mastodon_toots_rent']
    db_mastodon_sports = couch['mastodon_toots_sports']
    
    all_docs1 = db_mastodon_lang.view('language_mast/language_mast_view',group=True)
    all_docs2 = db_mastodon_rent.view('rent_document/rent_views',group=True)
    all_docs3 = db_mastodon_sports.view('doc_sport/view_sport',group=True)

    
    list_dict1, list_dict2, list_dict3 = [], [], []
    for i in all_docs1 :
        dict_temp = {}
        dict_temp['created_at'] = pd.to_datetime(i.key[0]+" "+i.key[1]+":00:00")
        dict_temp['value'] = i.value
        dict_temp['type'] = 'Language Data'
        list_dict1.append(dict_temp)
    for i in all_docs2 :
        dict_temp = {}
        dict_temp['created_at'] = pd.to_datetime(i.key[0]+" "+i.key[1]+":00:00")
        dict_temp['value'] = i.value
        dict_temp['type'] = 'Rent Data'
        list_dict2.append(dict_temp)
    for i in all_docs3 :
        dict_temp = {}
        dict_temp['created_at'] = pd.to_datetime(i.key[0]+" "+i.key[1]+":00:00")
        dict_temp['value'] = i.value
        dict_temp['type'] = 'Sports Data'
        list_dict3.append(dict_temp)
    
    df1 = pd.DataFrame(list_dict1)
    df2 = pd.DataFrame(list_dict2)
    df3 = pd.DataFrame(list_dict3)

    df1.set_index('created_at', inplace=True)
    df2.set_index('created_at', inplace=True)
    df3.set_index('created_at', inplace=True)

    df1 = df1.resample('1H').sum()
    df2 = df2.resample('1H').sum()
    df3 = df3.resample('1H').sum()

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df1.index, y=df1.value, mode='lines', name='Language Data'))
    fig.add_trace(go.Scatter(x=df2.index, y=df2.value, mode='lines', name='Rent Data'))
    fig.add_trace(go.Scatter(x=df3.index, y=df3.value, mode='lines', name='Sports Data'))
    
    fig.update_layout(title='Mastodon toots by Topics Over Time', xaxis_title='Time', yaxis_title='Number of Toots')
    
    fig_sport = go.Figure()
    fig_sport.add_trace(go.Bar(x=rent_sport.word[0:10], y=rent_sport.number_of_hashtag[0:10], name='Mastodon Sport Number of Hashtag'))
    fig_sport.update_layout(title='Mastodon Sport Number of Hashtag')

    fig_language = go.Figure()
    fig_language.add_trace(go.Bar(x=rent_language.country_name[0:10], y=rent_language.number_of_language[0:10], name='Mastodon Language Non-English'))
    fig_language.update_layout(title='Mastodon Language Non-English')

    try :
    # Generate the HTML
        fig.write_html("static/mastodon_timeseries.html")
        fig_sport.write_html("static/mastodon_sport_hastag.html")
        fig_language.write_html("static/mastodon_language.html")
        map_obj.save('static/map.html')
        map_obj_lang.save('static/map_lang.html')
        map_obj_sport.save('static/map_sport.html')
    
    except IOError as e:
        print("Error while input/output:", e)

    except Exception as e:
        print("Other error:", e)
    
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5010)
