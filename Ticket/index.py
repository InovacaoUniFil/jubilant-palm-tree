from flask import Flask, redirect, url_for, render_template, request, session
import json
import requests
import time

movi_api_url = 'https://unidev.movidesk.com/public/v1/'

movi_token = 'token=6c99cd06-187b-4ad4-9cb6-9524520adb47'

app = Flask(__name__)

@app.route("/", methods = ['POST'])
def hello_world():
    return render_template("index.html", requestData = request.form, error = "")

@app.route("/sendToMovi", methods = ['POST'])
def send_to_movi():
    if (str(request.form["text_input"]) == "") or (str(request.form["category_type"]) == "") or (str(request.form["subject_type"]) == ""):
        return render_template("index.html", requestData = request.form, error = "Preencha todos os campos")
    user = requests.get(movi_api_url+'persons?'+movi_token+'&id='+str(request.form["custom_user_login"]))
    if(user.status_code==404):
        movi_person_data = {
            'id' : str(request.form["custom_user_login"]),
            'isActive' : True,
            'personType' : 1,
            'profileType' :2,
            'businessName' : str(request.form["custom_user_name"]),
            'userName' : str(request.form["custom_user_email"]),
            'password' : str(request.form["custom_user_login"]),
        }
        user = requests.post(movi_api_url+'persons?'+movi_token, json = movi_person_data)
        while True:
            user = requests.get(movi_api_url+'persons?'+movi_token+'&id='+str(request.form["custom_user_login"]))
            if user.status_code!=404:
                break
            time.sleep(5)
        user = json.loads(user.content)
    else:
        user = json.loads(user.content)

    movi_ticket_data = {
    "type" : 2,
    "createdBy" : {
        "id" : user["id"],
        "personType" : user["personType"],
        "profileType" : user["profileType"]
    },
    "clients" : [{
        "id" : user["id"],
        "personType" : user["personType"],
        "profileType" : user["profileType"]
    }],
    "subject" : str(request.form["subject_type"]),
    "category" : str(request.form["category_type"]),
    "actions" : [
        {
        "type" : 2,
        "description" : str(request.form["text_input"])
        }
    ],
    "customFieldValues" : [
        {
        "customFieldId" : 136148,
        "customFieldRuleId" : 68649,
        "line" : 1,
        "value" : str(request.form["custom_canvas_course_name"])
        }
    ]
    }
    requests.post(movi_api_url+'tickets?'+movi_token, json = movi_ticket_data)
    return render_template("sucesso.html",username=str(request.form["custom_user_email"]), password=str(request.form["custom_user_login"]))

@app.route("/loginToMovi", methods = ['POST'])
def login_to_movi():
    print("https://unidev.movidesk.com/Account/Authenticate?"+movi_token+"&userName="+str(request.form["username"])+"&password="+str(request.form["password"]))
    return redirect("https://unidev.movidesk.com/Account/Authenticate?"+movi_token+"&userName="+str(request.form["username"])+"&password="+str(request.form["password"]))