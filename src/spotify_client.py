import requests
import json
import time


class SpotifyClient:

    @staticmethod
    def auth(client_id:str, response_type:str ,redirect_url:str, scope:str):
        return  f"https://accounts.spotify.com/authorize?client_id={client_id}&response_type={response_type}&redirect_uri={redirect_url}&scope={scope}"

    @staticmethod
    def getToken(code:str, redirect_uri:str, client_id:str, client_secret:str):

        r = requests.post(
            "https://accounts.spotify.com/api/token",
            data= {"grant_type": "authorization_code", "code": code, "redirect_uri": redirect_uri, "client_id":client_id, "client_secret":client_secret},
            headers= {"content-type": "application/x-www-form-urlencoded"}
        )
        return r.json()

    @staticmethod
    def refreshToken(refreshToken:str, client_id:str, client_secret:str):
        r = requests.post(
            "https://accounts.spotify.com/api/token",
            data={"grant_type": "refresh_token", "refresh_token": refreshToken, "client_id":client_id, "client_secret":client_secret},
            headers= {"content-type": "application/x-www-form-urlencoded"}   
        )
        return r.json()
    
    @staticmethod
    def getLastFiftySongs(access_token:str):
        timestamp = int(time.time())
        r = requests.get(
            "https://api.spotify.com/v1/me/player/recently-played",
            params = {"type":"track", "limit":50,"after": timestamp},
            headers = {"Authorization": f"Bearer {access_token}"}
        )
        return r.json()
    
    







