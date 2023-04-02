import json
from flask import Flask, request
from helper.nb_model import clasificar
from helper.telegram_api import enviarMensaje
from enum import Enum
from dotenv import load_dotenv
load_dotenv()

class Emoji(str, Enum):
    MUYTRISTE = u'\U0001F62D'
    TRISTE = u'\U0001F600'
    FELIZ = u'\U00002614'

EtapaUser = Enum('EtapaUser', ['SALUDO', 'CONSULTA','CALIFICACION', 'SOPORTE_TECNICO'])

dictUser = dict() #Contiene ID de usuarios activos con su etapa actual
listaTech = [] #IDs de todos los Técnicos
listaTechLibres = [] #IDs de Técnicos libres
dictConUser = dict() #Diccionario de Connecciones de Usuario a Soporte Técnico
dictConTech = dict() #Diccionario de Connecciones de Soporte Técnico a Usuario

app = Flask(__name__)
@app.route('/')
def home():
    return 'OK', 200

@app.route('/telegram', methods=['POST', 'GET'])
def telegram():
    try:
        data = request.get_json()
        print("Json recibido: " + json.dumps(data))
        procesarMensaje(data)        
    except:
        pass
    finally:
        return 'OK', 200

def procesarMensaje(data):
    #analizamos el json
    query = data['message']['text']
    sender_id = data['message']['from']['id']
    words = query.split(' ')
    comando = words[0].lower()
    if len(words) > 1:
        comando = ''

    if sender_id in listaTech: #Es técnico                       #esta version de python no tiene switch asi que O(n) será qcy
        if comando == '/salir':
            terminarSesion(sender_id)  
            enviarMensaje(sender_id, "Ha cerrado sesión como Soporte Técnico.")
        elif comando == '/estadisticas':
            mostrarEstadisticas()
        elif comando == '/consultas':
            mostrarConsultas()
        elif comando == '/desconectar':
            terminarConexion(sender_id)
            enviarMensaje(sender_id, "Se ha desconectado del usuario correctamente.\nVuelve a la lista de espera.")
        else: #lo que escribió no es un comando
            if sender_id in dictConTech:                
                enviarMensaje(dictConTech.get(sender_id), query)
            else:
                enviarMensaje(sender_id, "No se encuentra conectado con ningún cliente actualmente.\nSi desea salir utilice \"/salir\".")
    
    else:  #Es usuario
        if not sender_id in dictUser:   #Si no es usuario lo agrega
            dictUser.update({sender_id: EtapaUser.SALUDO}) 

        if comando == '/soysoporte':
            terminarSesion(sender_id)
            listaTech.append(sender_id)
            listaTechLibres.append(sender_id)
            enviarMensaje(sender_id, "Ha sido agregado correctamente como Soporte Técnico.")
        
        elif comando == '/soporte':
            if dictUser.get(sender_id) == EtapaUser.SOPORTE_TECNICO:
                enviarMensaje(sender_id, "Ya te encuentras hablando con Soporte Técnico.\nPara desconectarse del soporte utilice el comando \"/salir\".")
            else:  
                codigoConexion = nuevaConexion(sender_id, data)               
                if codigoConexion != 0:        
                    enviarMensaje(sender_id, "Lo sentimos, el personal de Soporte Técnico no se encuentra disponible en el momento.\nPor favor intente más tarde.")
        elif comando == '/salir':
            terminarSesion(sender_id)
            enviarMensaje(sender_id, "Adios! Esperamos haberle ayudado!")        
        else:               
            etapa = dictUser.get(sender_id)
            if etapa == EtapaUser.SALUDO:
                enviarMensaje(sender_id, "Hola! Soy Tekly, el mejor chatbot.\nPor favor realice su consulta.")
                dictUser.update({sender_id: EtapaUser.CONSULTA})
            elif etapa == EtapaUser.CALIFICACION: 
                if comando == "bueno":
                    enviarMensaje(sender_id, "Dijiste bueno")
                elif comando == "malo":
                    enviarMensaje(sender_id, "Dijiste malo")
                else:
                    dictUser.update({sender_id: EtapaUser.CONSULTA})
                    etapa = dictUser.get(sender_id)
            #FALTA LA LOGICA DE ESTA PARTE


            if etapa == EtapaUser.CONSULTA:                
                response = clasificar(query)
                enviarMensaje(sender_id, response)
                enviarMensaje(sender_id,"Si le ayudo puede escribir Bueno o Malo. O Reintentar")
                dictUser.update({sender_id: EtapaUser.CALIFICACION})    
            elif etapa == EtapaUser.SOPORTE_TECNICO:
                enviarMensaje(dictConUser.get(sender_id), query)                
            else:       
                pass

def terminarSesion(sender_id):
    if sender_id in dictConTech:
        terminarConexion(sender_id)
    if sender_id in dictConUser:
        terminarConexion(sender_id)
    if sender_id in listaTechLibres:
        listaTechLibres.remove(sender_id)
    if sender_id in listaTech:
        listaTech.remove(sender_id)
    if sender_id in dictUser:
        dictUser.pop(sender_id)

def terminarConexion(sender_id):
    if sender_id in dictConTech: #Si el técnico la termina
        usuarioEnConexion = dictConTech.pop(sender_id)
        listaTechLibres.append(sender_id)
        dictConUser.pop(usuarioEnConexion)
        dictUser.pop(usuarioEnConexion)
        enviarMensaje(usuarioEnConexion, "Ha finalizado su conección con Soporte Técnico.\nEspero que hayamos podido solucionar sus problemas.")
    elif sender_id in dictConUser: #Si el usuario la termina
        tecnicoEnConexion = dictConUser.pop(sender_id)
        dictUser.pop(sender_id)
        listaTechLibres.append(tecnicoEnConexion)
        dictConTech.pop(tecnicoEnConexion)
        enviarMensaje(tecnicoEnConexion, "El usuario ha finalizado la conección.")
    
def nuevaConexion(sender_id, data):
    if len(listaTechLibres) >0:                    
        tech_id = listaTechLibres.pop(0)
        dictConUser.update({sender_id: tech_id}) #establecemos la conexion
        dictConTech.update({tech_id: sender_id}) 
        dictUser.update({sender_id: EtapaUser.SOPORTE_TECNICO})
        enviarMensaje(sender_id, "Se ha establecido la conección con nuestro personal de Soporte Técnico.\nLe atenderá en brevedad.")
        enviarMensaje(tech_id, "Conección establecida.\nId_usuario: "+str(sender_id)+"\nNombre: "+str(data['message']['from']['first_name'])+"\nApellido: "+str(data['message']['from']['last_name'])+"\nNombre de usuario: "+str(data['message']['from']['username']))  
        return 0  
    else:
        return -1

def mostrarEstadisticas():
    pass

def mostrarConsultas():
    pass
