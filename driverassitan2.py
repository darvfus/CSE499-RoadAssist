import tkinter as tk
from tkinter import messagebox
import threading
import cv2
import time
import mediapipe as mp
import numpy as np
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
import os
from playsound import playsound

# =============================
# CONFIGURACIÓN
# =============================
SENDER_EMAIL = "20203mc210@utez.edu.mx"
PASSWORD = "8a7d56a162l3c11b"
USUARIOS_FILE = "usuarios.json"

umbral_EAR = 0.2
umbral_tiempo_dormido = 3

# =============================
# MANEJO DE USUARIOS
# =============================
def cargar_usuarios():
    if os.path.exists(USUARIOS_FILE):
        with open(USUARIOS_FILE, "r") as f:
            return json.load(f)
    return {}

def guardar_usuarios(usuarios):
    with open(USUARIOS_FILE, "w") as f:
        json.dump(usuarios, f, indent=4)

usuarios = cargar_usuarios()

# =============================
# FUNCIONES AUXILIARES
# =============================
def reproducir_audio(ruta):
    try:
        playsound(ruta)
    except Exception as e:
        print(f"Error al reproducir el archivo: {e}")

def obtener_signos_vitales():
    frecuencia_cardiaca = np.random.randint(60, 100)
    oxigenacion = np.random.randint(90, 100)
    return frecuencia_cardiaca, oxigenacion

def enviar_correo(nombre_usuario, correo_usuario):
    frecuencia_cardiaca, oxigenacion = obtener_signos_vitales()
    body = f"El usuario {nombre_usuario} se ha dormido.\n\nSignos vitales:\nFrecuencia Cardiaca: {frecuencia_cardiaca} BPM\nOxigenación: {oxigenacion}%"

    message = MIMEMultipart()
    message["From"] = SENDER_EMAIL
    message["To"] = correo_usuario
    message["Subject"] = "¡Alerta! Detección de sueño"
    message.attach(MIMEText(body, "plain"))
    
    try:
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(SENDER_EMAIL, PASSWORD)
        server.sendmail(SENDER_EMAIL, correo_usuario, message.as_string())
        server.quit()
        print("Correo enviado correctamente.")
    except Exception as e:
        print(f"Error al enviar correo: {e}")

def calcular_EAR(puntos):
    A = np.linalg.norm(puntos[1] - puntos[5])
    B = np.linalg.norm(puntos[2] - puntos[4])
    C = np.linalg.norm(puntos[0] - puntos[3])
    return (A + B) / (2.0 * C)

# =============================
# DETECCIÓN DE SUEÑO
# =============================
detener = False
reiniciar = False

def iniciar_deteccion(nombre_usuario, correo_usuario):
    global detener, reiniciar
    cap = cv2.VideoCapture(0)
    face_mesh = mp.solutions.face_mesh.FaceMesh(refine_landmarks=True)
    tiempo_inicio_cerrados = None

    while True:
        if detener:
            print("Detección detenida.")
            break

        if reiniciar:
            print("Reiniciando detección...")
            reiniciar = False
            tiempo_inicio_cerrados = None

        ret, frame = cap.read()
        if not ret:
            break

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        resultado = face_mesh.process(frame_rgb)
        h, w, _ = frame.shape

        if resultado.multi_face_landmarks:
            for rostro in resultado.multi_face_landmarks:
                puntos_ojos_derecho = [(int(rostro.landmark[idx].x * w), int(rostro.landmark[idx].y * h)) for idx in [33, 160, 158, 133, 153, 144]]
                EAR_derecho = calcular_EAR(np.array(puntos_ojos_derecho))
                
                puntos_ojos_izquierdo = [(int(rostro.landmark[idx].x * w), int(rostro.landmark[idx].y * h)) for idx in [362, 385, 387, 263, 373, 380]]
                EAR_izquierdo = calcular_EAR(np.array(puntos_ojos_izquierdo))
                
                EAR = (EAR_derecho + EAR_izquierdo) / 2.0

                if EAR < umbral_EAR:
                    cv2.putText(frame, "Ojos Cerrados", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                    if tiempo_inicio_cerrados is None:
                        tiempo_inicio_cerrados = time.time()
                    elif time.time() - tiempo_inicio_cerrados >= umbral_tiempo_dormido:
                        print("¡ALERTA! Persona dormida")
                        reproducir_audio("C:\\Users\\Daniel Romero\\Desktop\\neural\\alarma.mp3")
                        enviar_correo(nombre_usuario, correo_usuario)
                        tiempo_inicio_cerrados = None
                else:
                    tiempo_inicio_cerrados = None
                    cv2.putText(frame, "Ojos Abiertos", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        cv2.imshow("Detección de Ojos", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()

# =============================
# INTERFAZ GRÁFICA MEJORADA
# =============================
def ventana_registro():
    def registrar():
        nombre = entry_nombre.get()
        correo = entry_correo.get()
        if not nombre or not correo:
            messagebox.showwarning("Error", "Complete todos los campos.")
            return
        usuarios[nombre] = correo
        guardar_usuarios(usuarios)
        messagebox.showinfo("Registro", "Usuario registrado con éxito.")
        reg.destroy()

    reg = tk.Toplevel(bg="#e8f0fe")
    reg.title("Registro de Usuario")
    reg.geometry("300x200")

    tk.Label(reg, text="Registro de Usuario", font=("Arial", 14, "bold"), bg="#e8f0fe").pack(pady=10)
    tk.Label(reg, text="Nombre:", bg="#e8f0fe").pack()
    entry_nombre = tk.Entry(reg)
    entry_nombre.pack()
    tk.Label(reg, text="Correo:", bg="#e8f0fe").pack()
    entry_correo = tk.Entry(reg)
    entry_correo.pack()
    tk.Button(reg, text="Registrar", bg="#4CAF50", fg="white", command=registrar).pack(pady=10)

def iniciar():
    global detener, reiniciar
    nombre = entry_usuario.get()
    if nombre not in usuarios:
        messagebox.showerror("Error", "Usuario no registrado.")
        return
    correo = usuarios[nombre]
    detener = False
    threading.Thread(target=iniciar_deteccion, args=(nombre, correo), daemon=True).start()

def parar():
    global detener
    detener = True

def reiniciar_btn():
    global reiniciar
    reiniciar = True

# =============================
# VENTANA PRINCIPAL
# =============================
root = tk.Tk()
root.title("Sistema de Detección de Sueño")
root.geometry("350x350")
root.configure(bg="#e8f0fe")

# Título
tk.Label(root, text="Sistema de Detección de Sueño", font=("Arial", 16, "bold"), bg="#e8f0fe", fg="#1a73e8").pack(pady=15)

# Registro
tk.Button(root, text="Registrar Usuario", command=ventana_registro, bg="#34a853", fg="white", font=("Arial", 12, "bold"), width=20).pack(pady=10)

# Usuario
tk.Label(root, text="Nombre de usuario:", bg="#e8f0fe", font=("Arial", 12)).pack(pady=5)
entry_usuario = tk.Entry(root, font=("Arial", 12))
entry_usuario.pack()

# Botones principales
tk.Button(root, text="Iniciar Sesión", bg="#1a73e8", fg="white", font=("Arial", 12, "bold"), command=iniciar, width=20).pack(pady=5)
tk.Button(root, text="Parar", bg="#ea4335", fg="white", font=("Arial", 12, "bold"), command=parar, width=20).pack(pady=5)
tk.Button(root, text="Reiniciar", bg="#fbbc05", fg="black", font=("Arial", 12, "bold"), command=reiniciar_btn, width=20).pack(pady=5)

# Cerrar programa
tk.Button(root, text="Salir", bg="black", fg="white", font=("Arial", 12, "bold"), command=root.quit, width=20).pack(pady=15)

root.mainloop()
