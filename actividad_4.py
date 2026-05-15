# -*- coding: UTF-8 -*-
import tkinter as tk
import os
import eGela
import Dropbox
import helper
import time
from urllib.parse import unquote
from tkinter import messagebox
import tkinter.ttk as ttk

##########################################################################################################

def make_entry(parent, caption, width=None, **options):
    label = tk.Label(parent, text=caption)
    label.pack(side=tk.TOP)
    entry = tk.Entry(parent, **options)
    entry.config(width=width)
    entry.pack(side=tk.TOP, padx=10, fill=tk.BOTH)
    return entry

def make_listbox(messages_frame):
    messages_frame.config(bd=1, relief="ridge")
    scrollbar = tk.Scrollbar(messages_frame)
    msg_listbox = tk.Listbox(messages_frame, height=20, width=70, exportselection=0, selectmode=tk.EXTENDED)
    msg_listbox.configure(yscrollcommand=scrollbar.set)
    scrollbar.configure(command=msg_listbox.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    return msg_listbox

def transfer_files():
    popup, progress_var, progress_bar = helper.progress("transfer_file", "Transfering files...")
    progress = 0
    progress_var.set(progress)
    progress_bar.update()
    progress_step = float(100.0 / len(selected_items1))

    for each in selected_items1:
        pdf_name, pdf_file = egela.get_pdf(each)

        progress_bar.update()
        newroot.update()

        if dropbox._path == "/":
            path = "/" + unquote(pdf_name)
            print("----------------------: " + pdf_name)
            print("----------------------: " + unquote(pdf_name))
        else:
            path = dropbox._path + "/" + pdf_name
        dropbox.transfer_file(path, pdf_file)

        progress += progress_step
        progress_var.set(progress)
        progress_bar.update()
        newroot.update()

        time.sleep(0.1)

    popup.destroy()
    dropbox.list_folder(msg_listbox2)
    msg_listbox2.yview(tk.END)

def delete_files():
    popup, progress_var, progress_bar = helper.progress("delete_file", "Deleting files...")
    progress = 0
    progress_var.set(progress)
    progress_bar.update()
    progress_step = float(100.0 / len(selected_items2))

    for each in selected_items2:
        if dropbox._path == "/":
            path = "/" + dropbox._files[each]['name']
        else:
            path = dropbox._path + "/" + dropbox._files[each]['name']
            print(path)
        dropbox.delete_file(path)

        progress += progress_step
        progress_var.set(progress)
        progress_bar.update()

    popup.destroy()
    dropbox.list_folder(msg_listbox2)

def name_folder(folder_name):
    if dropbox._path == "/":
        dropbox._path = dropbox._path + str(folder_name)
    else:
        dropbox._path = dropbox._path + '/' + str(folder_name)
    dropbox.create_folder(dropbox._path)
    var.set(dropbox._path)
    dropbox._root.destroy()
    dropbox.list_folder(msg_listbox2)

def create_folder():
    popup = tk.Toplevel(newroot)
    popup.geometry('200x100')
    popup.title('Dropbox')
    if os.name == 'nt':
        popup.iconbitmap('favicon.ico')
    helper.center(popup)

    login_frame = tk.Frame(popup, padx=10, pady=10)
    login_frame.pack(fill=tk.BOTH, expand=True)

    label = tk.Label(login_frame, text="Create folder")
    label.pack(side=tk.TOP)
    entry_field = tk.Entry(login_frame, width=35)
    # entry_field.bind("<Return>", name_folder)
    entry_field.pack(side=tk.TOP)
    send_button = tk.Button(login_frame, text="Send", command=lambda: name_folder(entry_field.get()))
    send_button.pack(side=tk.TOP)
    dropbox._root = popup

# Nueva función para realizar búsquedas
def ejecutar_busqueda():
    palabra = entrada_buscar.get()
    resultados = egela.search_pdfs(palabra)
    msg_listbox1.delete(0, tk.END) # Limpia los PDFs actuales
    for res in resultados:
        msg_listbox1.insert(tk.END, res['pdf_name']) # Inserta los PDFs filtrados


def show_storage():
    used, total, restante = dropbox.get_storage_usage()
    if used is not None:
        popup = tk.Toplevel(newroot)
        popup.title('Dropbox Storage')
        # No fijamos geometry para que se ajuste al contenido
        if os.name == 'nt':
            popup.iconbitmap('favicon.ico')

        # Contenedor principal
        main_frame = tk.Frame(popup, padx=20, pady=15)
        main_frame.pack()

        tk.Label(main_frame, text="Uso de Almacenamiento", font=('Arial', 10, 'bold')).pack(pady=(0, 10))

        # --- BARRA DE PROGRESO ---
        # Calculamos el porcentaje: (Usado / Total) * 100
        porcentaje = (used / total * 100) if total > 0 else 0

        progress_bar = ttk.Progressbar(main_frame, orient='horizontal', length=200, mode='determinate')
        progress_bar.pack(pady=5)
        progress_bar['value'] = porcentaje

        # Etiqueta de porcentaje
        tk.Label(main_frame, text=f"{porcentaje:.2f}% ocupado", font=('Arial', 8, 'italic')).pack()

        # --- TEXTO DETALLADO ---
        info_text = f"Usado: {used:.2f} MB\n"
        if total > 0:
            info_text += f"Total: {total:.2f} MB\n"
        if restante > 0:
            info_text += f"Disponible: {restante:.2f} MB"

        tk.Label(main_frame, text=info_text, justify=tk.LEFT).pack(pady=10)

        # --- BOTÓN CERRAR ---
        tk.Button(main_frame, text="Cerrar", width=10, command=popup.destroy).pack(pady=(5, 0))

        # Ajustar
        popup.update_idletasks()
        helper.center(popup)
    else:
        messagebox.showerror("Error", "No se pudo obtener la información del espacio.")

##########################################################################################################

def check_credentials(event=None):
    egela.check_credentials(ldapuser, ldapass)

def on_selecting1(event):
    global selected_items1
    widget = event.widget
    selected_items1 = widget.curselection()
    print(selected_items1)

def on_selecting2(event):
    global selected_items2
    widget = event.widget
    selected_items2 = widget.curselection()
    print(selected_items2)

def on_double_clicking2(event):
    widget = event.widget
    selection = widget.curselection()
    if selection[0] == 0 and dropbox._path != "/":
        head, tail = os.path.split(dropbox._path)
        dropbox._path = head
    else:
        selected_file = dropbox._files[selection[0]]
        if selected_file['.tag'] == 'folder':
            if dropbox._path == "/":
                dropbox._path = dropbox._path + selected_file['name']
            else:
                dropbox._path = dropbox._path + '/' + selected_file['name']
    var.set(dropbox._path)
    dropbox.list_folder(msg_listbox2)

##########################################################################################################
# Login eGela
root = tk.Tk()
root.geometry('250x200')
if os.name == 'nt':
    root.iconbitmap('favicon.ico')
root.title('Login eGela')
helper.center(root)
egela = eGela.eGela(root)

login_frame = tk.Frame(root, padx=10, pady=10)
login_frame.pack(fill=tk.BOTH, expand=True)

ldapuser = make_entry(login_frame, "LDAP user:", 16)
ldapass = make_entry(login_frame, "LDAP password:", 16, show="*")
ldapass.bind("<Return>", check_credentials)

button = tk.Button(login_frame, borderwidth=4, text="Login", width=10, pady=8, command=check_credentials)
button.pack(side=tk.BOTTOM)

root.mainloop()

if not egela._login:
    exit()
# Si nos logeamos en eGela cogemos las referencias a los pdfs
pdfs = egela.get_pdf_refs()

##########################################################################################################
# Login Dropbox
root = tk.Tk()
root.geometry('250x100')
if os.name == 'nt':
    root.iconbitmap('favicon.ico')
root.title('Login Dropbox')
helper.center(root)

login_frame = tk.Frame(root, padx=10, pady=10)
login_frame.pack(fill=tk.BOTH, expand=True)
# Login and Authorize in Drobpox
dropbox = Dropbox.Dropbox(root)

label = tk.Label(login_frame, text="Login and Authorize\nin Drobpox")
label.pack(side=tk.TOP)
button = tk.Button(login_frame, borderwidth=4, text="Login", width=10, pady=8, command=dropbox.do_oauth)
button.pack(side=tk.BOTTOM)

root.mainloop()

##########################################################################################################
# eGela -> Dropbox

newroot = tk.Tk()
newroot.geometry("850x400")
if os.name == 'nt':
    newroot.iconbitmap('favicon.ico')
newroot.title("eGela -> Dropbox")  #
helper.center(newroot)

newroot.rowconfigure(0, weight=1)
newroot.rowconfigure(1, weight=5)
newroot.columnconfigure(0, weight=6)
newroot.columnconfigure(1, weight=1)
newroot.columnconfigure(2, weight=6)
newroot.columnconfigure(3, weight=1)

# Cabecera eGela con Buscador
frame_cabecera_egela = tk.Frame(newroot)
frame_cabecera_egela.grid(row=0, column=0, sticky="nsew")

var2 = tk.StringVar()
var2.set("PDFs en Sistemas Web")
label2 = tk.Label(frame_cabecera_egela, textvariable=var2)
label2.pack(side=tk.LEFT, padx=10)

# El buscador pegado a la derecha del nombre
entrada_buscar = tk.Entry(frame_cabecera_egela, width=15)
entrada_buscar.pack(side=tk.LEFT, padx=5)
btn_buscar = tk.Button(frame_cabecera_egela, text="🔍", command=ejecutar_busqueda)
btn_buscar.pack(side=tk.LEFT)

# Etigueta del directorio de Dropbox (0,2)
var = tk.StringVar()
var.set(dropbox._path)
label = tk.Label(newroot, textvariable=var)
label.grid(row=0, column=2, ipadx=5, ipady=5)

# Frame con lista de PDFs e eGela (1,0)
selected_items1 = None
messages_frame1 = tk.Frame(newroot)
msg_listbox1 = make_listbox(messages_frame1)
msg_listbox1.bind('<<ListboxSelect>>', on_selecting1)
msg_listbox1.pack(side=tk.LEFT, fill=tk.BOTH)
# messages_frame1.pack()
messages_frame1.grid(row=1, column=0, ipadx=10, ipady=10, padx=2, pady=2)  #

# Frame con boton >>> (1,1)
frame1 = tk.Frame(newroot)
button1 = tk.Button(frame1, borderwidth=4, text=">>>", width=10, pady=8, command=transfer_files)
button1.pack()
frame1.grid(row=1, column=1, ipadx=5, ipady=5)

# Frame con ficheros en Dropbox (1,2)
selected_items2 = None
messages_frame2 = tk.Frame(newroot)
msg_listbox2 = make_listbox(messages_frame2)
msg_listbox2.bind('<<ListboxSelect>>', on_selecting2)
msg_listbox2.bind('<Double-Button-1>', on_double_clicking2)
msg_listbox2.pack(side=tk.RIGHT, fill=tk.BOTH)

# messages_frame2.pack()
messages_frame2.grid(row=1, column=2, ipadx=10, ipady=10, padx=2, pady=2)

# Frame con botones Create y Delete (1,3)

frame2 = tk.Frame(newroot)
button2 = tk.Button(frame2, borderwidth=4, background="red", text="Delete", width=10, pady=8, command=delete_files)
button2.pack(padx=2, pady=2)
button3 = tk.Button(frame2, borderwidth=4, text="Create folder", width=10, pady=8, command=create_folder)
button3.pack(padx=2, pady=2)
button4 = tk.Button(frame2, borderwidth=4, background="#4CAF50", fg="white", text="Storage Info", width=10, pady=8, command=show_storage)
button4.pack(padx=2, pady=2)
frame2.grid(row=1, column=3, ipadx=10, ipady=10)


for each in pdfs:
    msg_listbox1.insert(tk.END, each['pdf_name'])
    msg_listbox1.yview(tk.END)

dropbox.list_folder(msg_listbox2)

newroot.mainloop()