import json
import os
from flask import Flask, request
from helper.nb_model import clasificar
from helper.telegram_api import enviarMensaje
from enum import Enum
from dotenv import load_dotenv
import psycopg2
load_dotenv()

DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASS = os.getenv('DB_PASS')
DB_HOST = os.getenv('DB_HOST')

class Emoji(str, Enum):
    MUY_FELIZ = u'\U0001F604'
    SWEAT = u'\U0001F605 	'
    LAGRIMA = u'\U0001F972'
    FELIZ_CACHETE_ROJO = u'\U0001F60A'
    NERD = u'\U0001F913'
    SUNGLASSES = u'\U0001F60E'
    TORPE = u'\U0001F616'
    CARA_AL_REVEZ = u'\U0001F643'

EtapaUser = Enum('EtapaUser', ['SALUDO', 'CONSULTA','CALIFICACION', 'SOPORTE_TECNICO'])

#Implementación asquerosa que funciona
dictUser = dict() #Contiene ID de usuarios activos con su etapa actual
listaTech = [] #IDs de todos los Técnicos
listaTechLibres = [] #IDs de Técnicos libres
dictConUser = dict() #Diccionario de Connecciones de Usuario a Soporte Técnico
dictConTech = dict() #Diccionario de Connecciones de Soporte Técnico a Usuario
dictUltMenUser = dict() #Diccionario que guarda el último mensaje de cada usuario
dictUltClasMod = dict() #Diccionario que guarda la clasificación del último mensaje de cada usuario #Si, ya se que hay que crear una clase, no hay tiempo :(

app = Flask(__name__)
@app.route('/')
def home():
    return 'OK', 200

@app.route('/telegram', methods=['POST', 'GET'])
def telegram():    
    data = request.get_json()
    procesarMensaje(data)   
    return 'OK', 200
    try:
        data = request.get_json()
        procesarMensaje(data)        
    except:
        pass
    finally:
        return 'OK', 200

def procesarMensaje(data):
    #analizamos el json
    query = data['message']['text']
    sender_id = data['message']['from']['id']
    print("***Mensaje recibido del id "+ str(sender_id)+ ": \"" + str(query) + "\"") #Para los logs
    words = query.split(' ')
    comando = words[0].lower()
    
    if len(words) > 1:
        comando = ''

    if sender_id in listaTech: #Es técnico                       #esta version de python no tiene switch asi que O(n) será qcy
        if comando == '/salir':
            terminarSesion(sender_id)  
            enviarMensaje(sender_id, "Ha cerrado sesión como Soporte Técnico.")
        elif comando == '/estadisticas':
            mostrarEstadisticas(sender_id)
        elif comando == '/consultas':
            mostrarConsultasUltimasCinco(sender_id)
        elif comando == '/desconectar':
            terminarConexion(sender_id)
            enviarMensaje(sender_id, "Se ha desconectado del usuario correctamente.\nVuelve a la lista de espera.")
        else: #lo que escribió no es un comando
            if sender_id in dictConTech:                
                enviarMensaje(dictConTech.get(sender_id), salvarMarkdown(query))
            else:
                enviarMensaje(sender_id, "No se encuentra conectado con ningún cliente actualmente.\nComandos disponibles:\n    /consultas\n    /estadisticas\n    /salir")
    
    else:  #Es usuario
        if not sender_id in dictUser:   #Si no es usuario lo agrega
            dictUser.update({sender_id: EtapaUser.SALUDO}) 

        if comando == '/soysoporte':
            terminarSesion(sender_id)
            listaTech.append(sender_id)
            listaTechLibres.append(sender_id)
            enviarMensaje(sender_id, "Ha iniciado sesión como Soporte Técnico correctamente.\nComandos disponibles:\n    /consultas\n    /estadisticas\n    /salir")
        
        elif comando == '/soporte':
            if dictUser.get(sender_id) == EtapaUser.SOPORTE_TECNICO:
                enviarMensaje(sender_id, "Ya te encuentras hablando con Soporte Técnico.\nSi desea terminar la conversación con Soporte Técnico utilice /salir")
            else:  
                codigoConexion = nuevaConexion(sender_id, data)               
                if codigoConexion != 0:        
                    enviarMensaje(sender_id, "Lo siento, el personal de Soporte Técnico no se encuentra disponible en el momento. "+Emoji.CARA_AL_REVEZ+"\nPor favor intente más tarde.")
        elif comando == '/salir':
            terminarSesion(sender_id)
            enviarMensaje(sender_id, "Tenga un buen día! Esperamos haberle ayudado!")        
        else:               
            etapa = dictUser.get(sender_id)
            if etapa == EtapaUser.SALUDO:
                enviarMensaje(sender_id, "Hola! Soy Tekly! "+Emoji.MUY_FELIZ+"\nMi función es proveer información sobre los problemas técnicos que tengas con tu teclado. "+Emoji.NERD+"\nPara realizar una consulta simplemente escríbala como mensaje.")
                enviarMensaje(sender_id, "Si desea comunicarse directamente con Soporte Técnico puede usar el comando /soporte")
                dictUser.update({sender_id: EtapaUser.CONSULTA})
            elif etapa == EtapaUser.CALIFICACION: 
                if comando == "/botbueno":                    
                    agregarConsulta(dictUltMenUser.get(sender_id), dictUltClasMod.get(sender_id), "bueno")
                    enviarMensaje(sender_id, "Me alegro mucho de haber sido útil! "+Emoji.SUNGLASSES+"\nSi tiene otra consulta puede escribirla o puede salir con /salir")
                    dictUser.update({sender_id: EtapaUser.CONSULTA})

                elif comando == "/botmalo":                    
                    agregarConsulta(dictUltMenUser.get(sender_id), dictUltClasMod.get(sender_id), "malo")
                    enviarMensaje(sender_id, "Lo siento mucho. He sido muy torpe. "+Emoji.TORPE+"\nSi lo desea puede intentar describir la consulta de otra manera o puede contactarse con soporte técnico con el comando /soporte")
                    dictUser.update({sender_id: EtapaUser.CONSULTA})
                else:
                    dictUser.update({sender_id: EtapaUser.CONSULTA})
                    etapa = dictUser.get(sender_id) #Para que solo vaya a consulta si pasa este caso

            if etapa == EtapaUser.CONSULTA:            
                clasificacion = clasificar(query)   
                dictUltMenUser.update({sender_id: query})  
                dictUltClasMod.update({sender_id: clasificacion})  
                enviarMensaje(sender_id, respuestasPredeterminadas(clasificacion))
                enviarMensaje(sender_id,"Para ayudarme a ser un mejor bot, me alegraría si clasificara mi respuesta con /botBueno "+Emoji.FELIZ_CACHETE_ROJO+ " o /botMalo "+Emoji.LAGRIMA+"\nSi escribió la consulta incorrectamente puede reintentarlo volviendo a enviar otro mensaje.")
                dictUser.update({sender_id: EtapaUser.CALIFICACION})    
            elif etapa == EtapaUser.SOPORTE_TECNICO:
                enviarMensaje(dictConUser.get(sender_id), salvarMarkdown(query))                
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
        ''' #Comentado para propósitos de la demo
    if sender_id in dictUltMenUser:
        dictUltMenUser.pop(sender_id)
    if sender_id in dictUltClasMod:
        dictUltClasMod.pop(sender_id)
        '''
def terminarConexion(sender_id):
    if sender_id in dictConTech: #Si el técnico la termina
        usuarioEnConexion = dictConTech.pop(sender_id)
        listaTechLibres.append(sender_id)
        dictConUser.pop(usuarioEnConexion)
        dictUser.pop(usuarioEnConexion)
        enviarMensaje(usuarioEnConexion, "Ha finalizado su conexión con Soporte Técnico.\nEspero que hayamos podido solucionar sus problemas." + Emoji.MUY_FELIZ)
    elif sender_id in dictConUser: #Si el usuario la termina
        tecnicoEnConexion = dictConUser.pop(sender_id)
        dictUser.pop(sender_id)
        listaTechLibres.append(tecnicoEnConexion)
        dictConTech.pop(tecnicoEnConexion)
        enviarMensaje(tecnicoEnConexion, "El usuario ha finalizado la conexión.")
    
def nuevaConexion(sender_id, data):
    if len(listaTechLibres) >0:                    
        tech_id = listaTechLibres.pop(0)
        dictConUser.update({sender_id: tech_id}) #establecemos la conexion
        dictConTech.update({tech_id: sender_id}) 
        dictUser.update({sender_id: EtapaUser.SOPORTE_TECNICO})
        enviarMensaje(sender_id, "Se ha establecido la conexión con nuestro personal de Soporte Técnico."+Emoji.FELIZ_CACHETE_ROJO+"\nLe atenderá en brevedad.")
        
        nombre = "No tiene"
        apellido = "No tiene"
        nombreUsuario = "No tiene"
        try:
            nombre = data['message']['from']['first_name']
        except:
            pass
        try:
            apellido = data['message']['from']['last_name']
        except:
            pass
        try:
            nombreUsuario = data['message']['from']['username']
        except:
            pass
        enviarMensaje(tech_id, "Conexión establecida.\n*Id usuario*: "+salvarMarkdown(sender_id)+"\n*Nombre:* "+salvarMarkdown(nombre)+"\n*Apellido:* "+salvarMarkdown(apellido)+"\n*Nombre de usuario:* "+salvarMarkdown(nombreUsuario)) 
        if dictUltMenUser.get(sender_id) == None:
            enviarMensaje(tech_id, "El usuario no ha realizado ninguna consulta antes de solicitar Soporte Técnico.")  
        else:
            enviarMensaje(tech_id, "La última consulta realizada por el usuario ha sido:\n"+salvarMarkdown(dictUltMenUser.get(sender_id)))  
        return 0  
    else:
        return -1

def agregarConsulta(mensaje,cl_bot,cl_usr):
    conn = psycopg2.connect(dbname=DB_NAME, user= DB_USER, password=DB_PASS, host = DB_HOST)
    cur = conn.cursor()
    cur.execute('INSERT INTO consulta (hora,msj,clsf_bot,clsf_usr) VALUES(CURRENT_TIMESTAMP,%s,%s,%s);', (mensaje, cl_bot, cl_usr))
    conn.commit()
    cur.close()
    conn.close()

def salvarMarkdown(text):
    texto = str(text)
    texto = texto.replace("*", "\*")
    texto = texto.replace("_", "\_")
    return texto

def mostrarConsultasUltimasCinco(sender_id):
    enviarMensaje(sender_id,"Se mostrarán las últimas 5 consultas calificadas:")
    conn = psycopg2.connect(dbname=DB_NAME, user= DB_USER, password=DB_PASS, host = DB_HOST)
    cur = conn.cursor()
    cur.execute("SELECT * FROM consulta ORDER BY hora desc LIMIT 5;")
    records = cur.fetchall()
    for row in records:
        enviarMensaje(sender_id,"*Id:* "+salvarMarkdown(row[0])+"\n*Hora:* "+salvarMarkdown(row[1])+"\n*Mensaje:* "+salvarMarkdown(row[2])+"\n*Clasificacion Bot:* "+salvarMarkdown(row[3])+"\n*Calificacion Usuario:* "+salvarMarkdown(row[4]))
    conn.commit()
    cur.close()
    conn.close()

def mostrarEstadisticas(sender_id):
    conn = psycopg2.connect(dbname=DB_NAME, user= DB_USER, password=DB_PASS, host = DB_HOST)
    cur = conn.cursor()
    
    cur.execute('SELECT COUNT(*) FROM consulta;')
    cantidadConsultas=cur.fetchall()[0][0]
    cur.execute("SELECT COUNT(*) FROM consulta WHERE clsf_usr='bueno';")
    cantidadConsultasBuenas=cur.fetchall()[0][0]
    cur.execute("SELECT COUNT(*) FROM consulta WHERE clsf_usr='malo';")
    cantidadConsultasMalas=cur.fetchall()[0][0]
    enviarMensaje(sender_id,"Se han calificado un total de *"+salvarMarkdown(cantidadConsultas)+"* consultas de las cuales hubo:\n   *"+salvarMarkdown(cantidadConsultasBuenas)+"* clasificadas correctamente\n   *"+salvarMarkdown(cantidadConsultasMalas)+"* clasificadas incorrectamente\nLa tasa de clasificación correcta es del *"+salvarMarkdown(float(f'{((cantidadConsultasBuenas / cantidadConsultas) * 100):.2f}'))+"%*")
   
    cur.execute("SELECT COUNT(*) FROM consulta WHERE hora >= NOW() - '1 day'::INTERVAL;")
    cantidadConsultas=cur.fetchall()[0][0]
    cur.execute("SELECT COUNT(*) FROM consulta WHERE clsf_usr='bueno' and hora >= NOW() - '1 day'::INTERVAL;")
    cantidadConsultasBuenas=cur.fetchall()[0][0]
    cur.execute("SELECT COUNT(*) FROM consulta WHERE clsf_usr='malo' and hora >= NOW() - '1 day'::INTERVAL;")
    cantidadConsultasMalas=cur.fetchall()[0][0]
    enviarMensaje(sender_id,"En las últimas 24 horas se han calificado un total de *"+salvarMarkdown(cantidadConsultas)+"* consultas de las cuales hubo:\n   *"+salvarMarkdown(cantidadConsultasBuenas)+"* clasificadas correctamente\n   *"+salvarMarkdown(cantidadConsultasMalas)+"* clasificadas incorrectamente\nLa tasa de clasificación correcta es del *"+salvarMarkdown(float(f'{((cantidadConsultasBuenas / cantidadConsultas) * 100):.2f}'))+"%*")
       
    conn.commit()
    cur.close()
    conn.close()

def respuestasPredeterminadas(clasificacion):
    if clasificacion=="tecla_rota":
        return "sos un tecla rota"
    elif clasificacion=="consulta_garantia":
        return "sos un consulta garantia"
    elif clasificacion=="configuracion_luces":
        return "sos un configuracion luces"
    elif clasificacion=="devoluciones_cambios":
        return "sos un devoluciones cambios"
    elif clasificacion=="voumen_roto":
        return "sos un voumen roto"
    elif clasificacion=="escribe_solo":
        return "sos un escribe solo"
    elif clasificacion=="configuracion_macros":
        return "sos un configuracion macros"
