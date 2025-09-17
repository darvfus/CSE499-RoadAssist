# interfaz.py
import tkinter as tk
from tkinter import messagebox
import threading
import main
import db

db.crear_tabla()  # asegurar tabla creada al inicio

def iniciar_programa():
    usuario = entry_usuario.get().strip().lower()
    if not usuario:
        messagebox.showwarning("Error", "Ingrese un nombre o correo.")
        return

    datos = db.buscar_usuario(usuario)
    if not datos:
        messagebox.showwarning("Error", "Usuario no registrado en la base de datos.")
        return

    nombre_usuario, correo_usuario = datos
    main.deteniendo = False
    threading.Thread(target=main.iniciar_deteccion, args=(nombre_usuario, correo_usuario), daemon=True).start()

def parar_programa():
    main.parar_deteccion()
    messagebox.showinfo("Info", "Detección detenida.")

def registrar_usuario():
    nombre = entry_nombre.get().strip().lower()
    correo = entry_correo.get().strip().lower()
    if not nombre or not correo:
        messagebox.showwarning("Error", "Debe ingresar nombre y correo.")
        return
    if db.agregar_usuario(nombre, correo):
        messagebox.showinfo("Éxito", "Usuario registrado correctamente.")
    else:
        messagebox.showerror("Error", "El nombre o correo ya existe.")

ventana = tk.Tk()
ventana.title("Interfaz de Detección de Sueño con BD")
ventana.geometry("450x400")
ventana.configure(bg="#1e1e2e")

label_titulo = tk.Label(ventana, text="Detección de Sueño", font=("Arial", 14, "bold"), fg="white", bg="#1e1e2e")
label_titulo.pack(pady=10)

# Entrada de usuario existente
label_usuario = tk.Label(ventana, text="Nombre o Correo:", font=("Arial", 12), fg="white", bg="#1e1e2e")
label_usuario.pack()
entry_usuario = tk.Entry(ventana, font=("Arial", 12))
entry_usuario.pack(pady=5)

btn_iniciar = tk.Button(ventana, text="Iniciar", font=("Arial", 12, "bold"), bg="#4CAF50", fg="white", command=iniciar_programa)
btn_iniciar.pack(pady=5)

btn_parar = tk.Button(ventana, text="Parar", font=("Arial", 12, "bold"), bg="#E53935", fg="white", command=parar_programa)
btn_parar.pack(pady=5)

# Registro de nuevos usuarios
label_registro = tk.Label(ventana, text="Registrar nuevo usuario", font=("Arial", 12, "bold"), fg="yellow", bg="#1e1e2e")
label_registro.pack(pady=10)

label_nombre = tk.Label(ventana, text="Nombre:", font=("Arial", 12), fg="white", bg="#1e1e2e")
label_nombre.pack()
entry_nombre = tk.Entry(ventana, font=("Arial", 12))
entry_nombre.pack(pady=5)

label_correo = tk.Label(ventana, text="Correo:", font=("Arial", 12), fg="white", bg="#1e1e2e")
label_correo.pack()
entry_correo = tk.Entry(ventana, font=("Arial", 12))
entry_correo.pack(pady=5)

btn_registrar = tk.Button(ventana, text="Registrar", font=("Arial", 12, "bold"), bg="#2196F3", fg="white", command=registrar_usuario)
btn_registrar.pack(pady=5)

ventana.mainloop()
