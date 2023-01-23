from flask import Flask, redirect, url_for, render_template, request, session
import json
import requests
import time
from werkzeug.utils import secure_filename
import os

movi_api_url = 'https://unimovi.movidesk.com/public/v1/'

movi_token = 'token=ad262c74-d928-4602-a793-7989aff45afb'

UPLOAD_FOLDER = './SaveFolder'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
            time.sleep(1)
        user = json.loads(user.content)
    else:
        user = json.loads(user.content)

    coursename = str(request.form["custom_canvas_course_name"])
    if coursename == "$Canvas.course.name":
        coursename = "Nenhuma Disciplina Selecionada"
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
        "customFieldId" : 136678,
        "customFieldRuleId" : 69008,
        "line" : 1,
        "value" : coursename
        }
    ]
    }
    ticket_response = requests.post(movi_api_url+'tickets?'+movi_token, json = movi_ticket_data)
    time.sleep(1)
    ticket_response = json.loads(ticket_response.content)
    print(ticket_response)
    while True:
        ticket = requests.get(movi_api_url+'tickets?'+movi_token+"&id="+str(ticket_response["id"]))
        if ticket.status_code!=404:
            break
        time.sleep(1)
    #print(request.form['file'])
    if('file' in request.files):
        ticket = json.loads(ticket.content)
        action_id = ticket["actions"][0]["id"]
        file = request.files['file']
        #return request.form['file']
            #file.save(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))
            #print(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))
            #return redirect(url_for('download_file', name=file.filename))
            #print(request.form["file_input"])    
            #print(movi_api_url+"ticketFileUpload?"+movi_token+"&id="+str(ticket_response["id"])+"&actionId="+str(action_id)) 
        print(file.filename)
        attach_request = requests.post(movi_api_url+"ticketFileUpload?"+movi_token+"&id="+str(ticket_response["id"])+"&actionId="+str(action_id),files={'file':(file.filename,file)})
        print(attach_request)
    return render_template("sucesso.html",username=str(request.form["custom_user_email"]), password=str(request.form["custom_user_login"]))

@app.route("/loginToMovi", methods = ['POST'])
def login_to_movi():
    return redirect("https://unimovi.movidesk.com/Account/Authenticate?"+movi_token+"&userName="+str(request.form["username"])+"&password="+str(request.form["password"]))
    
@app.route("/loginNoTicket", methods = ['POST'])
def movi_login_no_ticket():
    return redirect("https://unimovi.movidesk.com/Account/Authenticate?"+movi_token+"&userName="+str(request.form["custom_user_email"])+"&password="+str(request.form["custom_user_login"]))
