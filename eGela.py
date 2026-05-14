# -*- coding: UTF-8 -*-
from tkinter import messagebox
import requests
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

    def check_credentials(self, ldapuser, ldappass, event=None):
        # Obtener los datos de sesión
        ldapuser = ldapuser.get()
        ldappass = ldappass.get()

        popup, progress_var, progress_bar = helper.progress("check_credentials", "Logging into eGela...")
        progress = 0
        progress_var.set(progress)
        progress_bar.update()

        # Primera peticion - Obtener MoodleSessionegela y logintoken
        metodo = 'GET'
        uri = "https://egela.ehu.eus/login/index.php"
        respuesta1 = requests.request(metodo, uri, allow_redirects=False, timeout=60)

        print(f'Solicitud1:\n\t{metodo} {uri}')
        print(f'Respuesta1:\n\t{respuesta1.status_code} {respuesta1.reason}')

        if respuesta1.status_code == 200:
            # Obtenemos la MoodleSessionegela y el logintoken
            MoodleSessionegela = respuesta1.headers['Set-Cookie'].split('MoodleSessionegela=')[1].split(';')[0]
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

        # Tercera peticion - Validar la sesión
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
            # print(respuesta3.text)
            exit(1)
        else:
            # Obtenemos la cabecera Location
            location = respuesta3.headers['Location']

        progress = 75
        progress_var.set(progress)
        progress_bar.update()
        time.sleep(1)
        popup.destroy()

        # Cuarta petición - Acceder a eGela
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
            soup = bs4.BeautifulSoup(respuesta4.text, 'html.parser')
            enlaces = soup.find_all('a')
            for enlace in enlaces:
                if "Sistemas Web" in enlace.text:
                    link_asignatura = enlace.get('href')
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

        # Obtener las secciones/temas
        metodo = 'GET'
        uri = self._curso  # Usamos la URL base guardada en el login
        cabeceras = {'Cookie': f'MoodleSessionegela={self._cookie}'}

        secciones = {}
        respuesta = requests.request(metodo, uri, headers=cabeceras, allow_redirects=False)

        if respuesta.status_code == 200:
            soup = bs4.BeautifulSoup(respuesta.text, 'html.parser')
            # Buscamos los enlaces de las secciones
            enlaces_temas = soup.find_all('a', {'class': 'nav-link'})

            for rdo in enlaces_temas:
                nombreTema = rdo.get('title') or rdo.text.strip()
                enlace = rdo.get('href')
                if enlace and "section=" in enlace:  # Filtramos para que sean secciones
                    secciones[nombreTema] = enlace

        # Si no encuentra secciones
        if not secciones:
            secciones["Principal"] = self._curso

        # Iterar por cada sección para buscar PDFs

        prog_step = 100 / len(secciones) if secciones else 100 # Calculamos el incremento de la barra según el número de secciones

        for nombreTema, url_seccion in secciones.items():
            res_sec = requests.request('GET', url_seccion, headers=cabeceras, allow_redirects=False)
            if res_sec.status_code == 200:
                soup_sec = bs4.BeautifulSoup(res_sec.text, 'html.parser')

                # Buscamos el contenedor de actividades
                divs_actividad = soup_sec.find_all('div', {'class': 'activity-instance d-flex flex-column'})

                for div in divs_actividad:
                    img = div.find('img')
                    # Verificamos si es un PDF por el icono o el texto
                    if img and 'pdf' in img.get('src', ''):
                        a = div.find('a')
                        if a:
                            pdf_link = a['href']
                            # Limpiamos el nombre del archivo
                            name = a.find('span').text.split(' Archivo')[0].strip().replace('/', ' ')

                            # Evitar duplicados
                            if not any(d['pdf_link'] == pdf_link for d in self._refs):
                                self._refs.append({'pdf_name': name, 'pdf_link': pdf_link})

            progress += prog_step
            progress_var.set(min(progress, 100))
            progress_bar.update()

        popup.destroy()
        return self._refs

    def get_pdf(self, selection):
        print("\t##### descargando PDF... #####")

        # Preparar cabeceras y datos del objeto seleccionado
        cabeceras = {'Cookie': f'MoodleSessionegela={self._cookie}'}
        pdf_object = self._refs[selection]

        pdf_name = pdf_object['pdf_name'] + ".pdf"
        pdf_url = pdf_object['pdf_link']

        # Petición al enlace de eGela para obtener la redirección (Location)
        res_redireccion = requests.request('GET', pdf_url, headers=cabeceras, allow_redirects=False)
        url_final = res_redireccion.headers['Location']

        # Petición final para descargar el contenido del PDF
        res_final = requests.request('GET', url_final, headers=cabeceras, allow_redirects=False)

        return pdf_name, res_final.content

    # Función para las búsquedas
    def search_pdfs(self, keyword):
        """
        Filtra la lista de PDFs descargados que coincidan con una palabra clave.
        """
        print(f"\t##### Buscando archivos con: '{keyword}' #####")
        results = [ref for ref in self._refs if keyword.lower() in ref['pdf_name'].lower()]

        if not results:
            print(f"No se han encontrado archivos que coincidan con '{keyword}'")

        return results