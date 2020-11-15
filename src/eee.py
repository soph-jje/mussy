import os
import base64
import json
import requests

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore


from google.cloud import tasks_v2

from google.oauth2 import service_account


cred = credentials.Certificate("C:/Users/elgue/Downloads/phirst-e425b-f32568f62ac2.json")
firebase_admin.initialize_app(cred, {
  'projectId': 'phirst-e425b',
})

db = firestore.client()





credentials = service_account.Credentials. from_service_account_file('C:/Users/elgue/Downloads/phirst-e425b-f32568f62ac2.json')





client = tasks_v2.CloudTasksClient(credentials=credentials)
parent = client.queue_path('phirst-e425b', 'us-central1', 'update-artist-albums-queue')

payload = {'artists':["metallica","carseat","aphex"]}

task = {
    "http_request":{
        "http_method":'POST',
        "url":'http://ptsv2.com/t/2o85t-1605412810/post',
        "body": json.dumps(payload).encode()
    }
}


response = client.create_task(parent=parent, task=task)
print(response)

#artists-----------------------------------------------------------------------------------------------------------------------------------------------------------
def refresh_token(user_id):
    doc_ref = db.collection(u'users').document(u'{0}'.format(user_id))
    doc = doc_ref.get()
    if doc.exists:
        doc = doc.to_dict()
        if 'refresh_token' in doc.keys():
            refresh_token = doc['refresh_token']
    token = requests.get(
        url="https://us-central1-phirst-e425b.cloudfunctions.net/auth-token",
        params={"refresh_token": refresh_token}
    ).json()["data"]["access_token"]
    # print(token)
    return token


def get_followed_artists(access_token,after=None):
    if after is not None:
        params = {"type":"artist", "limit":50,"after":after}
    else:
        params = {"type":"artist", "limit":50}

    artists = requests.get(
        url="https://api.spotify.com/v1/me/following",
        params=params,
        headers = {"Authorization": f"Bearer  {access_token}"}
    )
    return artists.json()["artists"]["items"]


def add_users_followed_artists_to_db(user_id,artists):
    user_ref = db.collection(u'users').document(u'{0}'.format(user_id))
    for artist in artists:
        user_ref.set({
            'followed_artists': firestore.ArrayUnion([artist["id"]])},
            merge=True)

def set_users_followed_artists(user_id):
    access_token = refresh_token(user_id)
    followed_artists = get_followed_artists(access_token)
    while ((len(followed_artists)%50)==0):
        followed_artists.extend(get_followed_artists(access_token,followed_artists[-1]["id"]))    
    add_users_followed_artists_to_db(user_id,followed_artists)
    return{"data":{"message":"success"}}




# set_users_followed_artists("QMtZyXsDQtNhMcoQwwE5Ill9qgC2")





#albums---------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def diff_users_artists_db(user_artists):
    doc_ref = db.collection(u'artists').stream()
    db_artists = {doc.id for doc in doc_ref}
    user_artists = {artist for artist in user_artists}
    return user_artists.difference(db_artists)
    
def get_artists_by_user(userid):
    doc_ref = db.collection(u'users').document(u'{0}'.format(userid))
    doc = doc_ref.get()
    if doc.exists:
        doc = doc.to_dict()
        if 'followed_artists' in doc.keys():
            return diff_users_artists_db(artist for artist in doc["followed_artists"])

def auth():
    CLIENT_ID = "5a1f81af466646cc80d5280641e4b609"
    CLIENT_SECRET = "f1fd209e815048d4a775c8e8c8432633"
    auth_str = bytes('{}:{}'.format(CLIENT_ID, CLIENT_SECRET), 'utf-8')
    b64_auth_str = base64.b64encode(auth_str).decode('utf-8')
    authorization = requests.post(
        "https://accounts.spotify.com/api/token",
        data = {"grant_type":"client_credentials"},
        headers = {"Authorization": f"Basic {b64_auth_str}"}
    )
    return authorization.json()

def get_artist_albums(artist_id,access_token,offset):
    artist_albums = requests.get(
        url = f"https://api.spotify.com/v1/artists/{artist_id}/albums",
        headers = {"Authorization": f"Bearer {access_token}"},
        params= {"limit":50, "include_groups":"album,single", "offset":f"{offset}", "country":"US"}
    )
    return artist_albums.json()


def get_albums_by_user(userid):
    all_albums = []
    artist_ids = get_artists_by_user(userid)
    # print(len(artist_ids))
    if(len(artist_ids)==0):
        return{"data":{"message":"No diff in artists"}}
    access_token = auth()["access_token"]
    for artist in artist_ids:
        get_albums = get_artist_albums(artist,access_token,0)
        artist_albums = get_albums["items"]
        total = get_albums["total"]
        # print(artist)
        # print(total)
        off = 50
        while(off<total):
            artist_albums.extend(get_artist_albums(artist,access_token,off)["items"])
            off = off+50
        # print(len(all_albums))
        all_albums.extend(artist_albums)
        # print(len(all_albums))
    if(len(all_albums)==0):
        return{"data":{"message":"No albums to add"}}
    all_albums = eliminate_duplicate_albums(all_albums)
    add_albums_to_db(all_albums)
    return {"data":{"message":"success","albums":all_albums,"total":len(all_albums)}}


def eliminate_duplicate_albums(albums):
    helping_set = set()
    filtered_albums = []
    for album in albums:
        if(album["name"] not in helping_set):
            helping_set.add(album["name"])
            filtered_albums.append(album)
    return filtered_albums


def add_albums_to_db(albums):
    for album in albums:
        album_ref = db.collection(u'albums').document(u'{0}'.format(album["id"]))
        album_ref.set({
            "album_group": album["album_group"],
            "album_type": album["album_type"],
            "external_urls":album["external_urls"],
            "href":album["href"],
            "id":album["id"],
            "images":album["images"],
            "name":album["name"],
            "uri":album["uri"]
        },merge=True)
        artists_refs = []
        for artist in album["artists"]:
            artist_ref = db.collection(u'artists').document(u'{0}'.format(artist["id"]))
            artists_refs.append(artist_ref)
            artist_ref.set(artist,merge=True)
            artist_ref.set({
                'albums': firestore.ArrayUnion([album_ref]) 
            },merge=True)

        album_ref.set({
            "artists": artists_refs
        },merge=True)

def try_parsing_date(text):
    for fmt in ('%Y-%m-%d', '%Y', '%Y-%m'):
        try:
            return datetime.datetime.strptime(text, fmt)
        except ValueError:
            pass
    return text

#all albums--------------------------------------------------------------------------------------------------------------------------------------






