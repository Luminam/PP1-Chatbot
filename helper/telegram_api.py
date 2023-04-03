import os
import requests
from dotenv import load_dotenv
load_dotenv()

TELEGRAM_API_KEY = os.getenv('TELEGRAM_API_KEY')

def sendMessage(sender_id:int, message:str) -> None:    
    url = f"https://api.telegram.org/bot{TELEGRAM_API_KEY}/sendMessage"
    payload = {
        "chat_id":sender_id,
        "text":message,
        "parse_mode": "Markdown"
    }
    headers = {"Content-Type": "application/json"}
    requests.request("POST", url, json=payload, headers=headers)
    

def enviarMensaje(sender_id, response):
    print("***Mensaje a enviar a la id "+ str(sender_id)+ ": \"" + str(response) + "\"") #Para los logs
    sendMessage(sender_id, response)