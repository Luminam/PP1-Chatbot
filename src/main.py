import json
from flask import Flask, request
from helper.nb_model import clasificar_modelo
from helper.telegram_api import sendMessage

app = Flask(__name__)

@app.route('/')
def home():
    return 'OK', 200

@app.route('/telegram', methods=['POST', 'GET'])
def telegram():
    try:
        data = request.get_json()
        print(json.dumps(data))
        print("Probando lugar: 1")
        message = data['message']
        print("Probando lugar: 2")
        query = message['text']
        print("Probando lugar: 3")
        sender_id = message['from']['id']
        print("Probando lugar: 4")

        #words = query.split(' ')
        #if words[0] == '/ask':







        print("Mensaje recibido: " + query)
        response = clasificar_modelo(query)
        print("Mensaje a mandar: " + response)
        sendMessage(sender_id, response)
    except:
        pass
    finally:
        return 'OK', 200