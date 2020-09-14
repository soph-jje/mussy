from flask import Blueprint, request
from spotify_client import SpotifyClient
import json

spotify_routes = Blueprint('spotify_routes', __name__)

with open("./config.json") as file:
    config = json.load(file)



@spotify_routes.route('/auth')
def index():
    return SpotifyClient.auth(config['client_id'],"code",config['redirect_uri'],"user-read-recently-played user-read-private")

@spotify_routes.route('/getToken')
def getToken():
    code = request.args.get('code')
    return SpotifyClient.getToken(code,config['redirect_uri'],config['client_id'],config['client_secret'])

@spotify_routes.route('/refreshToken')
def refreshToken():
    refreshToken = request.args.get('refresh_token')
    return SpotifyClient.refreshToken(refreshToken,config['client_id'],config['client_secret'])

@spotify_routes.route('/getLastFiftySongs')
def getLastFiftySongs():
    access_token = request.args.get('access_token')
    return SpotifyClient.getLastFiftySongs(access_token)
