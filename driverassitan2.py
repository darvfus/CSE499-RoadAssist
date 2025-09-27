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
import datetime
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# =============================
# CONFIGURACIÓN
# =============================
SENDER_EMAIL = "20203mc210@utez.edu.mx"
PASSWORD = "TU_CONTRASEÑA_DE_APLICACIÓN"
USUARIOS_FILE = "usuarios.json"

umbral_EAR = 0.2
umbral_tiempo_dormido = 3

# =============================
# MANEJO DE USUARIOS
# =============================
def cargar_usuarios():
    if os.path.exists(USUARIOS_FILE):
        with open(USUARIOS_FILE, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
            except json.JSONDecodeError:
                pass
    return {}

def guardar_usuarios(usuarios):
    with open(USUARIOS_FILE, "w", encoding="utf-8") as f:
        json.dump(usuarios, f, indent=4, ensure_ascii=False)

usuarios = cargar_usuarios()
eventos_sueño = []  # Lista para registrar eventos de sueño

# =============================
# FUNCIONES AUXILIARES
# =============================
def reproducir_audio(ruta_audio):
    try:
        playsound(ruta_audio)
    except Exception as e:
        print(f"Error al reproducir el archivo: {e}")

def obtener_signos_vitales():
    frecuencia_cardiaca = np.random.randint(60, 100)
    respiracion = np.random.randint(12, 20)
    presion = f"{np.random.randint(110, 120)}/{np.random.randint(70, 80)}"
    temperatura = round(np.random.uniform(36.5, 37.5), 1)
    return frecuencia_cardiaca, respiracion, presion, temperatura

def enviar_correo(nombre_usuario, correo_usuario):
    frecuencia_cardiaca, respiracion, presion, temperatura = obtener_signos_vitales()
    body = f"El usuario {nombre_usuario} se ha dormido.\n\nSignos vitales:\nFrecuencia Cardiaca: {frecuencia_cardiaca} BPM\nRespiración: {respiracion} rpm\nPresión: {presion}\nTemperatura: {temperatura}°C"

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
# CÁLCULOS DE SALIDA
# =============================
def calcular_imc(peso, estatura):
    return peso / (estatura ** 2)

def clasificar_imc(imc):
    if imc < 18.5:
        return "Bajo (riesgo)"
    elif 18.5 <= imc < 25:
        return "Normal"
    elif 25 <= imc < 30:
        return "Sobrepeso"
    else:
        return "Peligro (Obesidad)"

def calcular_edad_metabolica(edad, imc, sexo):
    ajuste = 0
    if sexo.lower() == "hombre":
        ajuste = 2
    elif sexo.lower() == "mujer":
        ajuste = -2
    return edad + int((imc - 22)) + ajuste

# =============================
# DETECCIÓN DE SUEÑO
# =============================
detener = False
reiniciar = False

def iniciar_deteccion(nombre_usuario, correo_usuario):
    global detener, reiniciar, eventos_sueño
    cap = cv2.VideoCapture(0)
    face_mesh = mp.solutions.face_mesh.FaceMesh(refine_landmarks=True)
    tiempo_inicio_cerrados = None

    while cap.isOpened():
        if detener:
            break

        if reiniciar:
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
                        reproducir_audio(r"C:\Users\Daniel Romero\Desktop\neural\alarma.mp3")
                        enviar_correo(nombre_usuario, correo_usuario)
                        evento = f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Usuario dormido"
                        eventos_sueño.append(evento)
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
# GRÁFICA DE SIGNOS VITALES
# =============================
def mostrar_grafica():
    plt.ion()
    fig, axs = plt.subplots(2, 2, figsize=(8, 6))
    plt.subplots_adjust(hspace=0.5)

    x_data, fc_data, resp_data, temp_data, presion_data = [], [], [], [], []

    def animar(i):
        t = len(x_data)
        x_data.append(t)
        fc, resp, presion, temp = obtener_signos_vitales()
        fc_data.append(fc)
        resp_data.append(resp)
        presion_data.append(int(presion.split("/")[0]))
        temp_data.append(temp)

        axs[0,0].cla(); axs[0,0].plot(x_data, fc_data, "r-"); axs[0,0].set_title("Frecuencia Cardiaca")
        axs[0,1].cla(); axs[0,1].plot(x_data, resp_data, "g-"); axs[0,1].set_title("Respiración")
        axs[1,0].cla(); axs[1,0].plot(x_data, presion_data, "b-"); axs[1,0].set_title("Presión Sistólica")
        axs[1,1].cla(); axs[1,1].plot(x_data, temp_data, "m-"); axs[1,1].set_title("Temperatura")

    ani = FuncAnimation(fig, animar, interval=3000)
    plt.show(block=False)

    while not detener:
        plt.pause(1)
    plt.close(fig)

# =============================
# INTERFAZ GRÁFICA
# =============================
def ventana_registro():
    def registrar():
        nombre = entry_nombre.get()
        correo = entry_correo.get()
        try:
            edad = int(entry_edad.get())
            estatura = float(entry_estatura.get()) / 100
            peso = float(entry_peso.get())
        except ValueError:
            messagebox.showerror("Error", "Edad, estatura y peso deben ser numéricos.")
            return
        sexo = entry_sexo.get()

        if not nombre or not correo or not sexo:
            messagebox.showwarning("Error", "Complete todos los campos.")
            return

        usuarios[nombre] = {"correo": correo, "edad": edad, "sexo": sexo, "estatura": estatura, "peso": peso}
        guardar_usuarios(usuarios)
        messagebox.showinfo("Registro", "Usuario registrado con éxito.")
        reg.destroy()

    reg = tk.Toplevel(bg="#e8f0fe")
    reg.title("Registro de Usuario")
    reg.geometry("300x350")

    tk.Label(reg, text="Registro de Usuario", font=("Arial", 14, "bold"), bg="#e8f0fe").pack(pady=10)
    tk.Label(reg, text="Nombre:", bg="#e8f0fe").pack()
    entry_nombre = tk.Entry(reg); entry_nombre.pack()
    tk.Label(reg, text="Correo:", bg="#e8f0fe").pack()
    entry_correo = tk.Entry(reg); entry_correo.pack()
    tk.Label(reg, text="Edad:", bg="#e8f0fe").pack()
    entry_edad = tk.Entry(reg); entry_edad.pack()
    tk.Label(reg, text="Sexo (Hombre/Mujer):", bg="#e8f0fe").pack()
    entry_sexo = tk.Entry(reg); entry_sexo.pack()
    tk.Label(reg, text="Estatura (cm):", bg="#e8f0fe").pack()
    entry_estatura = tk.Entry(reg); entry_estatura.pack()
    tk.Label(reg, text="Peso (kg):", bg="#e8f0fe").pack()
    entry_peso = tk.Entry(reg); entry_peso.pack()
    tk.Button(reg, text="Registrar", bg="#4CAF50", fg="white", command=registrar).pack(pady=10)

def iniciar():
    global detener, reiniciar
    nombre = entry_usuario.get()
    if nombre not in usuarios:
        messagebox.showerror("Error", "Usuario no registrado.")
        return

    reproducir_audio(r"C:\Users\Daniel Romero\Desktop\neural\harry.mp3")
    threading.Thread(target=mostrar_grafica, daemon=True).start()
    correo = usuarios[nombre]["correo"]
    detener = False
    threading.Thread(target=iniciar_deteccion, args=(nombre, correo), daemon=True).start()

def parar():
    global detener
    detener = True

def reiniciar_btn():
    global reiniciar
    reiniciar = True

def salir_guardando():
    global detener, eventos_sueño
    detener = True
    nombre = entry_usuario.get()
    if nombre not in usuarios:
        root.destroy()
        return

    datos = usuarios[nombre]
    imc = calcular_imc(datos["peso"], datos["estatura"])
    clasificacion = clasificar_imc(imc)
    edad_metabolica = calcular_edad_metabolica(datos["edad"], imc, datos["sexo"])

    reporte = f"""
Reporte de Usuario - {nombre}
Fecha: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

Edad: {datos['edad']} años
Sexo: {datos['sexo']}
Estatura: {datos['estatura']:.2f} m
Peso: {datos['peso']} kg

IMC: {imc:.2f}
Clasificación: {clasificacion}

Edad metabólica estimada: {edad_metabolica} años

Historial de eventos de sueño:
"""
    for evento in eventos_sueño:
        reporte += f"{evento}\n"
        reporte += "\nHistorial de signos vitales:\n"


    with open("reporte_usuario.txt", "w", encoding="utf-8") as f:
        f.write(reporte)

    messagebox.showinfo("Salida", "Datos guardados en 'reporte_usuario.txt'")
    root.destroy()

# =============================
# VENTANA PRINCIPAL
# =============================
root = tk.Tk()
root.title("Sistema de Detección de Sueño")
root.geometry("350x400")
root.configure(bg="#e8f0fe")

tk.Label(root, text="Sistema de Detección de Sueño", font=("Arial", 16, "bold"), bg="#e8f0fe", fg="#1a73e8").pack(pady=15)

tk.Button(root, text="Registrar Usuario", command=ventana_registro, bg="#34a853", fg="white", font=("Arial", 12, "bold"), width=20).pack(pady=10)

tk.Label(root, text="Nombre de usuario:", bg="#e8f0fe", font=("Arial", 12)).pack(pady=5)
entry_usuario = tk.Entry(root, font=("Arial", 12))
entry_usuario.pack()

tk.Button(root, text="Iniciar Sesión", bg="#1a73e8", fg="white", font=("Arial", 12, "bold"), command=iniciar, width=20).pack(pady=5)
tk.Button(root, text="Parar", bg="#ea4335", fg="white", font=("Arial", 12, "bold"), command=parar, width=20).pack(pady=5)
tk.Button(root, text="Reiniciar", bg="#fbbc05", fg="black", font=("Arial", 12, "bold"), command=reiniciar_btn, width=20).pack(pady=5)
tk.Button(root, text="Salir y Guardar Reporte", bg="black", fg="white", font=("Arial", 12, "bold"), command=salir_guardando, width=20).pack(pady=15)

root.mainloop()
