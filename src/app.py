from flask import Flask, render_template, url_for, request,redirect
from spotify_routes import spotify_routes
import requests  


app = Flask(__name__)


@app.route('/')
def home():
    return render_template("home.html")


app.register_blueprint(spotify_routes)

    
    
if __name__ == '__main__':
    # Bind to PORT if defined, otherwise default to 5000.
    app.run(host='0.0.0.0',debug=True)