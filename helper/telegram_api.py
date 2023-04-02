import os
import requests
from dotenv import load_dotenv
load_dotenv()

TELEGRAM_API_KEY = os.getenv('TELEGRAM_API_KEY')

def sendMessage(sender_id:int, message:str) -> None:    
    url = f"https://api.telegram.org/bot{TELEGRAM_API_KEY}/sendMessage"
    payload = {
        "chat_id":sender_id,
        "text":message
    }
    headers = {"Content-Type": "application/json"}
    resp = requests.request("POST", url, json=payload, headers=headers)
    
    #print("Json a enviar: "+resp.text)

def enviarMensaje(sender_id, response):
    print("Mensaje a enviar: " + str(response) + "\nUsuario a  enviar: "+ str(sender_id))
    sendMessage(sender_id, response)