import cv2
import time
import mediapipe as mp
import numpy as np
import winsound
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import tkinter as tk
from tkinter import messagebox
from playsound import playsound


# Configuración de correo
SENDER_EMAIL = "xxxxxxxxxxxxxx"
PASSWORD = "xxxxxxxxxxxxxx"

def reproducir_audio():
    try:
        playsound("C:\\Users\\Daniel Romero\\Desktop\\neural\\harry.mp3")  # Cambia esta ruta a la correcta
        print("Audio reproducido con éxito.")
    except Exception as e:
        print(f"Error al reproducir el archivo: {e}")

# Parámetros de detección
umbral_EAR = 0.2  # Umbral para determinar ojos cerrados
umbral_tiempo_dormido = 3  # Segundos antes de activar la alarma

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

def iniciar_deteccion(nombre_usuario, correo_usuario):
    cap = cv2.VideoCapture(1)
    face_mesh = mp.solutions.face_mesh.FaceMesh(refine_landmarks=True)
    tiempo_inicio_cerrados = None
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        resultado = face_mesh.process(frame_rgb)
        h, w, _ = frame.shape
        ojos_cerrados = False

        if resultado.multi_face_landmarks:
            for rostro in resultado.multi_face_landmarks:
                puntos_ojos_derecho = [(int(rostro.landmark[idx].x * w), int(rostro.landmark[idx].y * h)) for idx in [33, 160, 158, 133, 153, 144]]
                EAR_derecho = calcular_EAR(np.array(puntos_ojos_derecho))
                
                puntos_ojos_izquierdo = [(int(rostro.landmark[idx].x * w), int(rostro.landmark[idx].y * h)) for idx in [362, 385, 387, 263, 373, 380]]
                EAR_izquierdo = calcular_EAR(np.array(puntos_ojos_izquierdo))
                
                EAR = (EAR_derecho + EAR_izquierdo) / 2.0
                
                if EAR < umbral_EAR:
                    ojos_cerrados = True
                    cv2.putText(frame, "Ojos Cerrados", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                    
                    if tiempo_inicio_cerrados is None:
                        tiempo_inicio_cerrados = time.time()
                    
                    tiempo_cerrados = time.time() - tiempo_inicio_cerrados
                    
                    if tiempo_cerrados >= umbral_tiempo_dormido:
                        print("¡ALERTA! Persona dormida")
                        # Reproducir el nuevo archivo de audio
                        try:
                            playsound("C:\\Users\\Daniel Romero\\Desktop\\neural\\alarma.mp3")  # Ruta correcta del archivo harry.mp3
                            print("Audio reproducido con éxito.")
                        except Exception as e:
                            print(f"Error al reproducir el archivo: {e}")
                        enviar_correo(nombre_usuario, correo_usuario)
                        tiempo_inicio_cerrados = None
                else:
                    ojos_cerrados = False
                    tiempo_inicio_cerrados = None
                    cv2.putText(frame, "Ojos Abiertos", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

                for punto in puntos_ojos_derecho + puntos_ojos_izquierdo:
                    cv2.circle(frame, punto, 2, (255, 0, 0), -1)
        
        cv2.imshow("Detección de Ojos", frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()

def iniciar_programa():
    nombre_usuario = entry_nombre.get()
    correo_usuario = entry_correo.get()
    
    if not nombre_usuario or not correo_usuario:
        messagebox.showwarning("Error", "Por favor, complete todos los campos.")
        return
    
    reproducir_audio()  # Llamamos a la función para reproducir el audio
    ventana.destroy()  # Cerrar ventana
    iniciar_deteccion(nombre_usuario, correo_usuario)

ventana = tk.Tk()
ventana.title("Detección de Sueño")
ventana.geometry("400x300")
ventana.configure(bg="#1e1e2e")

label_titulo = tk.Label(ventana, text="Sistema de Detección de Sueño", font=("Arial", 14, "bold"), fg="white", bg="#1e1e2e")
label_titulo.pack(pady=10)

label_nombre = tk.Label(ventana, text="Nombre:", font=("Arial", 12), fg="white", bg="#1e1e2e")
label_nombre.pack()
entry_nombre = tk.Entry(ventana, font=("Arial", 12))
entry_nombre.pack(pady=5)

label_correo = tk.Label(ventana, text="Correo Electrónico:", font=("Arial", 12), fg="white", bg="#1e1e2e")
label_correo.pack()
entry_correo = tk.Entry(ventana, font=("Arial", 12))
entry_correo.pack(pady=5)

btn_iniciar = tk.Button(ventana, text="Iniciar Detección", font=("Arial", 12, "bold"), bg="#4CAF50", fg="white", command=iniciar_programa)
btn_iniciar.pack(pady=20)

ventana.mainloop()
