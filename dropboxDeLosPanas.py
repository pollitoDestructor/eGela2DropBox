import urllib.parse
import requests
import webbrowser
from socket import AF_INET, socket, SOCK_STREAM
import json

with open('app_keys.json') as json_file:
    data = json.load(json_file)
    app_key = data['app_key']
    app_secret = data['app_secret']

redirect_uri = "http://localhost:8090"
########################l##########################################################
# CODE: Abrir en el navegador la URI https://www.dropbox.com/oauth2/authorize #
###################################################################################
servidor = 'www.dropbox.com'
params = {'response_type': 'code',
'client_id': app_key,
'redirect_uri': redirect_uri }
params_encoded = urllib.parse.urlencode(params)
recurso = '/oauth2/authorize?' + params_encoded
uri = 'https://' + servidor + recurso
webbrowser.open_new(uri)


# Crear servidor local que escucha por el puerto 8090
server_socket = socket(AF_INET, SOCK_STREAM)
server_socket.bind(('localHost', 8090))
server_socket.listen(1)
print("\tLocal server listening on port 8090")
# Recibir la solicitude 302 del navegador
client_connection, client_address = server_socket.accept()
peticion = client_connection.recv(1024)
print("\tRequest from the browser received at local server:")
# Buscar en la petición el "auth_code"
primera_linea = peticion.decode('UTF8').split('\n')[0]
print(primera_linea)
aux_auth_code = primera_linea.split(' ')[1]
auth_code = aux_auth_code[7:].split('&')[0]
print ("\tauth_code:" + auth_code)
# Devolver una respuesta al usuario
http_response = "HTTP/1.1 200 OK\r\n\r\n" \
                "<html>" \
                "<head><title>Prueba</title></head>" \
                "<body>The authentication flow has completed. Close this window.</body>" \
                "</html>"
client_connection.sendall(http_response.encode(encoding="utf-8"))
client_connection.close()
server_socket.close()


###################################################################################
# ACCESS_TOKEN: Obtener el TOKEN https://www.api.dropboxapi.com/1/oauth2/token #
###################################################################################
params = {'code': auth_code,
'grant_type': 'authorization_code',
'client_id': app_key,
'client_secret': app_secret,
'redirect_uri': redirect_uri}
cabeceras={'User-Agent':'Python Client',
'Content-Type': 'application/x-www-form-urlencoded'}
uri='https://api.dropboxapi.com/oauth2/token'
respuesta = requests.post( uri, headers=cabeceras,data=params)
print (respuesta.status_code)
json_respuesta = json.loads(respuesta.content)
access_token = json_respuesta['access_token']
print ("Access_Token:"+ access_token)

print("/list_folder")
uri = 'https://api.dropboxapi.com/2/files/list_folder'
path= ""
datos = {'path': path}
datos_encoded = json.dumps(datos)
print("Datuak: " + datos_encoded)
cabeceras = {'Host': 'api.dropboxapi.com',
             'Authorization': 'Bearer ' + access_token,
             'Content-Type': 'application/json'}
respuesta = requests.post(uri, headers=cabeceras, data=datos_encoded,allow_redirects=False)
status = respuesta.status_code
print ("\tStatus: " + str(status))
contenido = respuesta.text
print("\tContenido:")
contenido_json = json.loads(contenido)
print("Ficheros en "+ path)
for entrie in contenido_json["entries"]:
    print(entrie['name'])