from flask import Flask, redirect, url_for, render_template, request, session
import json
import requests
import time
from werkzeug.utils import secure_filename
import os

movi_url = 'https://unimovi.movidesk.com/'
movi_api_url = movi_url+'public/v1/'

movi_token = 'token=ad262c74-d928-4602-a793-7989aff45afb'

UPLOAD_FOLDER = './SaveFolder'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 2 * 1000 * 1000

def create_new_user(cpf,name,email):
    print("create_new_user")
    movi_person_data = {
        'id' : str(cpf),
        'isActive' : True,
        'personType' : 1,
        'profileType' :2,
        'businessName' : str(name),
        'userName' : str(email),
        'password' : str(cpf),
    }
    user = requests.post(movi_api_url+'persons?'+movi_token, json = movi_person_data)
    time.sleep(0.5)
    print("created user")
    while True:
        user = requests.get(movi_api_url+'persons?'+movi_token+'&id='+str(cpf))
        if user.status_code!=404:
            break
        time.sleep(0.5)
    return json.loads(user.content)

def create_tutor_user(cpf,name,email,course_name):
    print("create_tutor_user")
    if email == None:
        email = cpf
    movi_person_data = {
        'id' : cpf,
        'isActive' : True,
        'personType' : 1,
        'profileType' :1,
        'accessProfile' :"Tutores",
        'businessName' : str(name),
        'userName' : str(email),
        'password' : str(cpf),
        'teams': ["Curso - "+str(course_name)]
    }
    course = requests.post(movi_api_url+'persons?'+movi_token, json = movi_person_data)
    print("create Tutor")
    time.sleep(0.5)
    return json.loads(course.content)

def create_course_user(id_curso,name):
    print("create_course_user")
    movi_person_data = {
        'id' : str(id_curso),
        'isActive' : True,
        'personType' : 1,
        'profileType' :1,
        'accessProfile' :"Tutores",
        'businessName' : str(name),
        'userName' : str(name),
        'password' : str(id_curso)+"12345678",
        'teams': ["Curso - "+str(name)]
    }
    course = requests.post(movi_api_url+'persons?'+movi_token, json = movi_person_data)
    time.sleep(0.5)
    print("Discipline")
    return json.loads(course.content)

def create_ticket(user):
    return user

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/", methods = ['POST'])
def hello_world():
    return render_template("index.html", requestData = request.form, error = "")

@app.route("/sendToMovi", methods = ['POST'])
def send_to_movi():
    #Check if Form is filled or return error
    print("Check if Form is filled or return error")
    if (str(request.form["text_input"]) == "") or (str(request.form["category_type"]) == "") or (str(request.form["subject_type"]) == ""):
        return render_template("index.html", requestData = request.form, error = "Todos os campos são obrigatórios!")

    #Check if user exists or create new user
    print("Check if user exists or create new user")
    user = requests.get(movi_api_url+'persons?'+movi_token+'&id='+str(request.form["custom_user_login"]))
    if(user.status_code==404):
        user = create_new_user(request.form["custom_user_login"],request.form["custom_user_name"],request.form["custom_user_email"])
    else:
        user = json.loads(user.content)
        
    #alimentar Webhook
    print("alimentar Webhook")
    if str(request.form["custom_canvas_course_id"]) != "$Canvas.course.id":
        enrollment_data = requests.get("https://unifil.test.instructure.com/api/v1/courses/"+str(request.form["custom_canvas_course_id"])+"/enrollments",headers={'Authorization':"Bearer 9257~E3ojV8VWw6jgoDh6nWCCRwje4YiT7twjHzmstImnpmdKbX590DItxn7oT8Wye7qe"} ,verify="./static/certs.pem")
        if (len(json.loads(enrollment_data.content)) > 0):
            print(json.loads(enrollment_data.content))
            enrollment_data = json.loads(enrollment_data.content)[0]
        else:
            enrollment_data = {"sis_section_id" : "None"}
    else:
        enrollment_data = {"sis_section_id" : "None"}
    #Get student Data from Webook
    print("Get student Data from Webook")
    bearer = requests.post("https://webhook.unifil.br/login",headers={"Content-Type": "application/json"},data=json.dumps({"username":"tamadeu","email":"tamadeu@unifil.br","password":"1b396ec5-5b2a-4bcf-88d6-c63800b15408"}) ,verify="./static/certs.pem")
    time.sleep(0.5)
    bearer = json.loads(bearer.content)["token"]
    student_data = requests.get("https://webhook.unifil.br/aluno",headers={'Authorization':"Bearer "+bearer,"Content-Type": "application/json"},data=json.dumps({"sis_section_id" : str(enrollment_data["sis_section_id"]), "cpf" : str(request.form["custom_user_login"]) }) ,verify="./static/certs.pem")
    if(json.loads(student_data.content)["aluno"] == []): return render_template("index.html", requestData = request.form, error ="O seu usuário não foi encontrado no sistema de Ticket, entre em contato com um coordenador/suporte. (Codigo: Erro_de_Webhook:STUDENT_NOT_FOUND)")
    student_data = json.loads(student_data.content)["aluno"][0]
    print(student_data)
    if student_data["nome_aluno"] == None:
        return render_template("index.html", requestData = request.form, error ="Erro: Aluno não cadastrado")
    if len(student_data["nome_curso"]) > 64:
        student_data["nome_curso"] = student_data["nome_curso"][:60]

    #Cadatra o curso no sistema se este não esta cadastrado
    print("Cadatra o curso no sistema se este não esta cadastrado")
    course = requests.get(movi_api_url+'persons?'+movi_token+'&id='+str(student_data["id_curso"]))
    if course.status_code == 404:
        course = create_course_user(str(student_data["id_curso"]),str(student_data["nome_curso"]))
    course = requests.get(movi_api_url+'persons?'+movi_token+'&id='+str(student_data["id_curso"]))
    
    #Cadastra o tutor no sistema se este não esta cadastrado
    print("Cadastra o tutor no sistema se este não esta cadastrado")
    if student_data["cpf_tutor"] != None:
        tutor = requests.get(movi_api_url+'persons?'+movi_token+'&id='+str(student_data["cpf_tutor"]))
        if tutor.status_code == 404:
            tutor = create_tutor_user(str(student_data["cpf_tutor"]),str(student_data["nome_tutor"]),str(student_data["email_tutor"]),str(student_data["nome_curso"]))
        else:
            #Se o tutor não esta vinculado à disciplina no Movidesk, vincula o tutor
            tutor = json.loads(tutor.content)
            if ("Curso - "+str(student_data["nome_curso"])) not in tutor["teams"]:
                teams = tutor["teams"].copy()
                teams.append(("Curso - "+str(student_data["nome_curso"])))
                tutor = requests.patch(movi_api_url+'persons?'+movi_token+'&id='+str(student_data["cpf_tutor"]),headers={"Content-Type": "application/json"},data=json.dumps({"teams":teams}))
                time.sleep(0.5)
    #Get subject name from form, if it exists
    print("Get subject name from form, if it exists")
    coursename = str(request.form["custom_canvas_course_name"])
    if len(student_data["nome_curso"]) > 64:
        coursename = str(request.form["custom_canvas_course_name"])[:60]
    if coursename == "$Canvas.course.name":
        coursename = "Nenhuma Disciplina Selecionada"
    #Create a Ticket
    print("Create a Ticket")
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
    "owner" : str(student_data["nome_curso"]),
    "ownerTeam" : "Curso - "+str(student_data["nome_curso"]),
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
        },
        {
        "customFieldId" : 136788,
        "customFieldRuleId" : 69085,
        "line" : 1,
        "value" : str(student_data["nome_polo"])
        }
    ]
    }
    print(movi_ticket_data)
    ticket_response = requests.post(movi_api_url+'tickets?'+movi_token, json = movi_ticket_data)
    time.sleep(0.5)
    print(ticket_response.content)
    ticket_response = json.loads(ticket_response.content)
    print(ticket_response)
    while True:
        ticket = requests.get(movi_api_url+'tickets?'+movi_token+"&id="+str(ticket_response["id"]))
        if ticket.status_code!=404:
            break
        time.sleep(0.5)
    print("Attach a file to a ticket if there is one")
    #Attach a file to a ticket if there is one
    if('file' in request.files):
        ticket = json.loads(ticket.content)
        action_id = ticket["actions"][0]["id"]
        file = request.files['file']
        if allowed_file(file.filename):
            print(file.filename)
            attach_request = requests.post(movi_api_url+"ticketFileUpload?"+movi_token+"&id="+str(ticket_response["id"])+"&actionId="+str(action_id),files={'file':(file.filename,file)})
    return render_template("sucesso.html",username=str(request.form["custom_user_email"]), password=str(request.form["custom_user_login"]))

@app.route("/loginToMovi", methods = ['POST'])
def login_to_movi():
    return redirect(movi_url+"Account/Authenticate?"+movi_token+"&userName="+str(request.form["username"])+"&password="+str(request.form["password"]))
    
@app.route("/loginNoTicket", methods = ['POST'])
def movi_login_no_ticket():
    return redirect(movi_url+"Account/Authenticate?"+movi_token+"&userName="+str(request.form["custom_user_email"])+"&password="+str(request.form["custom_user_login"]))
