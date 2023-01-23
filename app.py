from flask import Flask, render_template, request,jsonify
from flask_ngrok import run_with_ngrok
from flask_cors import CORS
import re
import requests
import json
import detectlanguage
from detectlanguage import simple_detect # import the translator
from flask_sqlalchemy import SQLAlchemy
import datetime
from chat import chatBot
chatBot = chatBot()
#import nltk
#nltk.download('punkt')
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql+psycopg2://admin:COLnBQtTVptNTzQqqVHgUnUmyMFWLcjR@dpg-cf35u11a6gdpa6rl6k70-a.oregon-postgres.render.com/chatbot_8gbl"
# DATABASE_URI = 'postgres+psycopg2://postgres:password@localhost:5432/books'
db = SQLAlchemy(app)
CORS(app)
## Database
class chat(db.Model):
    chat_id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(1000))
    answer = db.Column(db.String(1000))
    lang = db.Column(db.String(5))
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
with app.app_context():
    db.create_all()
#from flask import get_response
class translator:
    api_url = "https://translate.googleapis.com/translate_a/single"
    client = "?client=gtx&dt=t"
    dt = "&dt=t"
    #fROM English to Kinyarwanda
    def translate(text : str , target_lang : str, source_lang : str):
        sl = f"&sl={source_lang}"
        tl = f"&tl={target_lang}"
        r = requests.get(translator.api_url+ translator.client + translator.dt + sl + tl + "&q=" + text)
        return json.loads(r.text)[0][0][0]
# use this link to get your api key https://detectlanguage.com/
detectlanguage.configuration.api_key = "13e26484ba8a0a3d865573c4868de0a0"
detectlanguage.configuration.secure = True
def process_question(text : str):
  source_lang = simple_detect(text)
  resp = translator.translate(text=text, target_lang='en', source_lang=source_lang)
  return resp, source_lang
def process_answer(text : str, source_lang):
  resp = translator.translate(text=text, target_lang=source_lang, source_lang='en')
  return resp
# create two routes
def preprocessing(text):
    text = text.lower()
    url_pattern = re.compile(r'https?://\S+|www\.\S+')
    html_pattern = re.compile('<.*?>')
    text = url_pattern.sub(r'', text)
    text = html_pattern.sub(r'', text)
    text = re.sub(r"[^\w\d'\s]+", ' ', text)
    return text
Q = []
R = []
def process(QUESTION: str):
    Q.append(QUESTION)
    USER_QUERY, SL = process_question(QUESTION) #Translate the original question into english and store the source lang
    RESPONSE = chatBot.get_response(USER_QUERY) #Asking the chatbot question
    ORIGINAL_RESPONSE = process_answer(RESPONSE, SL)
    R.append(ORIGINAL_RESPONSE)
    return ORIGINAL_RESPONSE, SL
@app.route("/",  methods=["GET"])
def index_get():
    return render_template("index.html")
@app.route("/predict",methods=["POST"])
def predict():
    text = request.get_json().get("message")
    #check if text is valid (I let it for you)
    response, sl = process(text)
    # we jsonify our response
    message = {"answer":response}
    query = chat(question=text, answer=response, lang=sl)
    db.session.add(query)
    db.session.commit()
    return jsonify(message)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)