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
        print("Json recibido: "+json.dumps(data))
        message = data['message']
        query = message['text']
        sender_id = message['from']['id']
        print("Mensaje recibido: " + query)

        words = query.split(' ')

        if words[0] == '/ask':
            pass
        else:
            response = clasificar_modelo(query)
            print("Mensaje a mandar: " + response)
            sendMessage(sender_id, response)
    except:
        pass
    finally:
        return 'OK', 200
