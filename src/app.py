from flask import Flask, render_template, url_for, request,redirect
import requests


app = Flask(__name__)


@app.route('/')
def home():
    return "hola macaco!"

    
if __name__ == '__main__':
    # Bind to PORT if defined, otherwise default to 5000.
    app.run(host='0.0.0.0',debug=True)