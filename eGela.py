# -*- coding: UTF-8 -*-
from http.cookiejar import Cookie
from tkinter import messagebox
import requests
import urllib.parse
import bs4
import time
import helper

class eGela:
    _login = 0
    _cookie = ""
    _curso = ""
    _refs = []
    _root = None

    def __init__(self, root):
        self._root = root

    def check_credentials(self, username, ldapuser, ldappass, event=None):
        # Sacamos el username del objeto tk.Entry
        username = username.get().upper()
        ldapuser = ldapuser.get()
        ldappass = ldappass.get()

        popup, progress_var, progress_bar = helper.progress("check_credentials", "Logging into eGela...")
        progress = 0
        progress_var.set(progress)
        progress_bar.update()

        # Primera peticion - Obtener MoodleSessionegela y logintoken
        metodo = 'GET'
        uri = "https://egela.ehu.eus/login/index.php"
        respuesta1=requests.request(metodo, uri, allow_redirects=False, timeout=60)

        print(f'Solicitud1:\n\t{metodo} {uri}')
        print(f'Respuesta1:\n\t{respuesta1.status_code} {respuesta1.reason}')

        if respuesta1.status_code == 200:
            ## Obtenemos la MoodleSessionegela y el logintoken
            ### Cabecera SetCookie: MoodleSessionegela
            MoodleSessionegela = respuesta1.headers['Set-Cookie'].split('MoodleSessionegela=')[1].split(';')[0]
            ### logintoken campo input del fomulario
            logintoken = respuesta1.text.split('logintoken" value="')[1].split('"')[0]
        else:
            print("Error al obtener MoodleSessionegela y logintoken.")
            print(respuesta1.status_code)
            exit(1)

        progress = 25
        progress_var.set(progress)
        progress_bar.update()
        time.sleep(1)


        # Segunda peticion - Autenticacion
        metodo = 'POST'
        uri = "https://egela.ehu.eus/login/index.php"
        cabeceras = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Cookie': f'MoodleSessionegela={MoodleSessionegela}'
        }
        cuerpo = {
            'username': ldapuser,
            'password': ldappass,
            'logintoken': logintoken
        }
        respuesta2 = requests.request(metodo, uri, headers=cabeceras, data=cuerpo, allow_redirects=False)

        print('==================================================')
        print(f'Solicitud2:\n\t{metodo} {uri}')
        print(f'\t{cuerpo}')
        print(f'Respuesta2:\n\t{respuesta2.status_code} {respuesta2.reason}')
        print(f'\t{respuesta2.headers["Location"]}\n\t{respuesta2.headers["Set-Cookie"]}')

        if respuesta2.status_code == 303:
            # Obtenemos la cabecera Location
            location = respuesta2.headers['Location']
            MoodleSessionegela = respuesta2.headers['Set-Cookie'].split('MoodleSessionegela=')[1].split(';')[0]
        else:
            print("Error al autenticarse. Revisa tus credenciales.")
            print(respuesta2.status_code)
            exit(1)

        progress = 50
        progress_var.set(progress)
        progress_bar.update()
        time.sleep(1)

        # Tercera peticion - Validar la sesion
        metodo = 'GET'
        uri = location
        cabeceras = {
            'Cookie': f'MoodleSessionegela={MoodleSessionegela}'
        }
        respuesta3 = requests.request(metodo, uri, headers=cabeceras, allow_redirects=False)

        print('==================================================')
        print(f'Solicitud3:\n\t{metodo} {uri}')
        print(f'Respuesta3:\n\t{respuesta3.status_code} {respuesta3.reason}')
        print(f'\t{respuesta3.headers["Location"]}')

        if respuesta3.status_code != 303:
            print("Error al autenticarse. Revisa tus credenciales.")
            print(respuesta3.status_code)
            #print(respuesta3.text)
            exit(1)
        else:
            # Obtenemos la cabecera Location
            location = respuesta3.headers['Location']

        progress = 75
        progress_var.set(progress)
        progress_bar.update()
        time.sleep(1)
        popup.destroy()

        # Cuarta peticion - Acceder a eGela y buscar mi nombre
        metodo = 'GET'
        uri = location
        cabeceras = {
            'Cookie': f'MoodleSessionegela={MoodleSessionegela}'
        }
        respuesta4 = requests.request(metodo, uri, headers=cabeceras, allow_redirects=False)

        print('==================================================')
        print(f'Solicitud4:\n\t{metodo} {uri}')
        print(f'Respuesta4:\n\t{respuesta4.status_code} {respuesta4.reason}')

        progress = 100
        progress_var.set(progress)
        progress_bar.update()
        time.sleep(1)
        popup.destroy()

        if respuesta4.status_code == 200:
            # Buscamos mi nombre dentro del div class="logininfo"
            if username in respuesta4.text:
                soup = bs4.BeautifulSoup(respuesta4.text, 'html.parser')
                enlaces = soup.find_all('a')
                for enlace in enlaces:
                    if "Sistemas Web" in enlace.text:
                        link_asignatura=enlace.get('href')
                print("Autenticacion correcta.")
                self._root.destroy()
                self._login = 1
                self._cookie = MoodleSessionegela
                self._curso = link_asignatura
            else:
                messagebox.showinfo("Alert Message", "Login incorrect!")
                exit(1)

    def get_pdf_refs(self):
        popup, progress_var, progress_bar = helper.progress("get_pdf_refs", "Downloading PDF list...")
        progress = 0
        progress_var.set(progress)
        progress_bar.update()

        metodo = 'GET'
        uri = self._curso+'&section=0'
        cabeceras = {
            'Cookie': f'MoodleSessionegela={self._cookie}'
        }
        secciones = {}  # Define la variable "secciones"
        respuesta6 = requests.request(metodo, uri, headers=cabeceras, allow_redirects=False)
        if respuesta6.status_code == 200:
            # Obtenemos los elementos li dentro de la clase ul "nav nav-tabs mb-3"
            # De cada li obtenemos el href y su title del elemento a
            # El resultado se añadira en el diccionario "secciones" con el title del a como clave y el enlace a la seccion como valor
            # Si el a es de la clase "nav-link active" se añade a "secciones" con el title del a como clave y el enlace sw como valor
            soup = bs4.BeautifulSoup(respuesta6.text, 'html.parser')
            if soup.find('ul', class_='nav nav-tabs mb-3') is None:
                secciones["asignatura"] = self._curso
            else:
                ul = soup.find('ul', class_='nav nav-tabs mb-3')
                lis = ul.find_all('li')
                for li in lis:
                    a = li.find('a')
                    if a.has_attr('href'):
                        secciones[a['title']] = a['href']
                    else:
                        secciones[a['title']] = self._curso+'&section=0#tabs-tree-start'

        for key, value in secciones.items():
            metodo = 'GET'
            uri = value
            cabeceras = {
                'Cookie': f'MoodleSessionegela={self._cookie}'
            }
            respuesta = requests.request(metodo, uri, headers=cabeceras, allow_redirects=False)
            if respuesta.status_code == 200:
                # Buscamos el ul con clase "section img-text"
                # Dentro del ul nos quedamos con los li de clase "activity resource modtype_resource"
                # De esos li elegimos los que en img tienen src "pdf"
                # De esos li que tenga un enlace a un archivo PDF cogemos el href del a y el span con el nombre del archivo
                # Como nos hace una redireccion cogemos el Location de la cabecera que sera el enlace al PDF
                soup = bs4.BeautifulSoup(respuesta.text, 'html.parser')
                ul = soup.find('ul', class_='topics')
                lis = ul.find_all('li', class_='activity resource modtype_resource')
                for li in lis:
                    img = li.find('img')
                    if 'pdf' in img['src']:
                        a = li.find('a')
                        pdf = a['href']
                        name = a.find('span').text.replace('/', ' ')
                        self._refs.append({'pdf_name': name, 'pdf_link': pdf})
                        # Actualizar la barra
                        progress += 100/len(lis)
                        progress_var.set(progress)
                        progress_bar.update()
        popup.destroy()
        return self._refs

    def get_pdf(self, selection):

        cabeceras = {
            'Cookie': f'MoodleSessionegela={self._cookie}'
        }
        pdf_object = self._refs[selection]
        name = pdf_object['pdf_name']+".pdf"
        pdf = pdf_object['pdf_link']
        pdf_response = requests.request('GET', pdf, headers=cabeceras, allow_redirects=False)
        pdf_link = requests.request('GET', pdf_response.headers['Location'], headers=cabeceras, allow_redirects=False)

        return name, pdf_link.content