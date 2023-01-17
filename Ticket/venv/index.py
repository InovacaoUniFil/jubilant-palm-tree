from flask import Flask, redirect, url_for, render_template, request, session
import requests

app = Flask(__name__)

@app.route("/")
def hello_world():
    return render_template("index.html")

@app.route("/ticket")
def tickets(data):  
    return render_template("index.html", data)

@app.route("/sendToMovi")
def send_to_movi():
    x = requests.get('https://api.movidesk.com/public/v1/persons?token=6c99cd06-187b-4ad4-9cb6-9524520adb47')
    print(x.status_code)
    print(x.content)
    return x.content