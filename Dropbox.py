import requests
import urllib
import webbrowser
from socket import AF_INET, socket, SOCK_STREAM
import json
import helper
import os
import time

# Cargo las credenciales de la aplicacion
with open('dropbox_secret.json') as f:
    secrets = json.load(f)
    app_key = secrets['app_key']
    app_secret = secrets['app_secret']
server_addr = "localhost"
server_port = 8090
redirect_uri = "http://" + server_addr + ":" + str(server_port)

class Dropbox:
    _access_token = ""
    _path = "/"
    _files = []
    _root = None
    _msg_listbox = None

    def __init__(self, root):
        self._root = root

    def local_server(self):
        # por el puerto 8090 esta escuchando el servidor que generamos
        server_socket = socket(AF_INET, SOCK_STREAM)
        server_socket.bind((server_addr, server_port))
        server_socket.listen(1)
        print("\tLocal server listening on port " + str(server_port))

        # recibe la redireccio 302 del navegador
        client_connection, client_address = server_socket.accept()
        peticion = client_connection.recv(1024)

        # buscar en solicitud el "auth_code"
        primera_linea =peticion.decode('UTF8').split('\n')[0]
        aux_auth_code = primera_linea.split(' ')[1]
        auth_code = aux_auth_code[7:].split('&')[0]

        # devolver una respuesta al usuario
        http_response = "HTTP/1.1 200 OK\r\n\r\n" \
                    "<html>" \
                    "<head><title>Prueba</title></head>" \
                    "<body>The authentication flow has completed. Close this window.</body>" \
                    "</html>"
        client_connection.sendall(http_response.encode(encoding="utf-8"))
        time.sleep(1)
        client_connection.close()
        server_socket.close()

        return auth_code

    def do_oauth(self):
        # Navegador en localhost + puerto
        url = f"https://www.dropbox.com/oauth2/authorize?response_type=code&client_id={app_key}&redirect_uri={urllib.parse.quote(redirect_uri)}"
        webbrowser.open(url)
        auth_code = self.local_server()
        params = {
        'code': auth_code,
        'grant_type': 'authorization_code',
        'client_id': app_key,
        'client_secret': app_secret,
        'redirect_uri': redirect_uri
        }
        cabeceras={
            'User-Agent': 'Python Client',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        uri = 'https://api.dropboxapi.com/oauth2/token'
        response = requests.post(uri, data=params, headers=cabeceras)
        json_response = json.loads(response.content)
        self._access_token = json_response['access_token']

        self._root.destroy()

    def list_folder(self, msg_listbox):
        print("/list_folder")

        # 1. Dropbox usa "" para la raíz.
        # Usamos una variable local 'query_path' para no romper self._path permanentemente
        query_path = self._path if self._path != "/" else ""

        # 2. Asegúrate de que el nombre del token coincide con el que guardas en do_oauth
        # Si en do_oauth usaste self._atoken, aquí debe ser self._atoken
        token = getattr(self, '_access_token', getattr(self, '_atoken', None))

        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

        url = 'https://api.dropboxapi.com/2/files/list_folder'
        data = {
            'path': query_path,
            'recursive': False,
            'include_media_info': False,
            'include_deleted': False,
            'include_has_explicit_shared_members': False,
            'include_mounted_folders': True,
            'include_non_downloadable_files': True
        }

        response = requests.post(url, headers=headers, json=data)

        # 3. Verificación de seguridad antes de parsear el JSON
        if response.status_code == 200:
            contenido_json = response.json()
            # Actualizamos la lista usando tu helper
            self._files = helper.update_listbox2(msg_listbox, self._path, contenido_json)
        else:
            print(f"Error de Dropbox ({response.status_code}): {response.text}")
            # Si el error es 409 es que el path es inválido (ej: enviar "/" en vez de "")
            # Si el error es 401 es que el token no es válido

    def transfer_file(self, file_path, file_data):
        print("/upload")
        uri = 'https://content.dropboxapi.com/2/files/upload'
        headers = {
            'Authorization': f'Bearer {self._access_token}',
            'Content-Type': 'application/octet-stream',
            'Dropbox-API-Arg': json.dumps({
                'path': file_path,
                'mode': 'add',
                'autorename': True,
                'mute': False
            })
        }
        response = requests.post(uri, headers=headers, data=file_data)
        if response.status_code == 200:
            print("File uploaded successfully.")
        else:
            print("Error uploading file.")

    def delete_file(self, file_path):
        print("/delete_file")
        uri = 'https://api.dropboxapi.com/2/files/delete_v2'
        headers = {
            'Authorization': f'Bearer {self._access_token}',
            'Content-Type': 'application/json'
        }
        data = {
            'path': file_path
        }
        response = requests.post(uri, headers=headers, json=data)
        if response.status_code == 200:
            print("File deleted successfully.")
        else:
            print("Error deleting file.")

    def create_folder(self, path):
        print("/create_folder")
        print(path)
        if self._path == "/":
            self._path = ""
        uri = 'https://api.dropboxapi.com/2/files/create_folder_v2'
        headers = {
            'Authorization': f'Bearer {self._access_token}',
            'Content-Type': 'application/json'
        }
        data = {
            'path': path,
            'autorename': False
        }
        response = requests.post(uri, headers=headers, json=data)
        if response.status_code == 200:
            print("Folder created successfully.")
        else:
            print("Error creating folder.")
            print(response.content)

    def share_files(self, files):
        # Obtenemos el link para compartir
        # https://api.dropboxapi.com/2/sharing/create_shared_link_with_settings
        print("/share_file")
        uri = 'https://api.dropboxapi.com/2/sharing/create_shared_link_with_settings'
        headers = {
            'Authorization': f'Bearer {self._access_token}',
            'Content-Type': 'application/json'
        }
        links = []
        for file in files:
            data = {
                'path': file,
                "settings": {
                    "access": "viewer",
                    "allow_download": True,
                    "audience": "public",
                    "requested_visibility": "public"
                }
            }
            response = requests.post(uri, headers=headers, json=data)
            if response.status_code == 200:
                print("File shared successfully.")
                # Obtenemos el link
                link = json.loads(response.content)['url']
                links.append(link)
            else:
                print("Already exist.")
                # Pide el link
                # https://content.dropboxapi.com/2/sharing/get_shared_link_file
                data = {
                    'path': file
                }
                response = requests.post(uri, headers=headers, json=data)
                print(response.status_code)
                if response.status_code == 409:
                    print("File shared successfully.")
                    # Obtenemos el link
                    link = json.loads(response.content)['error']['shared_link_already_exists']['metadata']['url']
                    links.append(link)
                else:
                    print("Error sharing file.")
                    print(response.content)
        return links

    def download_file(self, files):
        print("/download_file")
        uri = 'https://content.dropboxapi.com/2/files/download'
        for file in files:
            headers = {
            'Authorization': f'Bearer {self._access_token}',
            'Content-Type': 'application/octet-stream',
            'Dropbox-API-Arg': json.dumps({
                'path': file
            })
        }
            response = requests.post(uri, headers=headers)
            if response.status_code == 200:
                print("File downloaded successfully.")
                with open(file.split("/")[-1], 'wb') as f:
                    f.write(response.content)
            else:
                print("Error downloading file.")
                print(response.content)
                return False
        return True

    def whoami(self):
        print("/whoami")
        uri = 'https://api.dropboxapi.com/2/users/get_current_account'
        headers = {
            'Authorization': f'Bearer {self._access_token}',
        }
        response = requests.post(uri, headers=headers)
        if response.status_code == 200:
            print("User info obtained successfully.")
            return json.loads(response.content)
        else:
            print("Error obtaining user info.")
            print(response.content)
            return None