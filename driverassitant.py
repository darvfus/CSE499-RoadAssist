import cv2
import time
import mediapipe as mp
import numpy as np
from playsound import playsound
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import tkinter as tk
from tkinter import messagebox

from storage import init_db, log_event  # import database functions


# ------------------------------
# Email configuration
# ------------------------------
SENDER_EMAIL = "xxxxxxxxxxxxxx"
PASSWORD = "xxxxxxxxxxxxxx"


# ------------------------------
# Play audio function
# ------------------------------
def reproducir_audio():
    try:
        playsound("C:\\Users\\Daniel Romero\\Desktop\\neural\\harry.mp3")  # test sound
        print("Audio reproducido con éxito.")
    except Exception as e:
        print(f"Error al reproducir el archivo: {e}")


# ------------------------------
# Detection parameters
# ------------------------------
umbral_EAR = 0.2  # Threshold to consider eyes closed
umbral_tiempo_dormido = 3  # Seconds of closed eyes before triggering


# ------------------------------
# Fake vital signs (random for now)
# ------------------------------
def obtener_signos_vitales():
    frecuencia_cardiaca = np.random.randint(60, 100)
    oxigenacion = np.random.randint(90, 100)
    return frecuencia_cardiaca, oxigenacion


# ------------------------------
# Email sender
# ------------------------------
def enviar_correo(nombre_usuario, correo_usuario):
    frecuencia_cardiaca, oxigenacion = obtener_signos_vitales()
    body = (
        f"El usuario {nombre_usuario} se ha dormido.\n\n"
        f"Signos vitales:\nFrecuencia Cardiaca: {frecuencia_cardiaca} BPM\n"
        f"Oxigenación: {oxigenacion}%"
    )

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
        return "Success"
    except Exception as e:
        print(f"Error al enviar correo: {e}")
        return "Failed"


# ------------------------------
# EAR (Eye Aspect Ratio) calculator
# ------------------------------
def calcular_EAR(puntos):
    A = np.linalg.norm(puntos[1] - puntos[5])
    B = np.linalg.norm(puntos[2] - puntos[4])
    C = np.linalg.norm(puntos[0] - puntos[3])
    return (A + B) / (2.0 * C)


# ------------------------------
# Drowsiness detection loop
# ------------------------------
def iniciar_deteccion(nombre_usuario, correo_usuario):
    cap = cv2.VideoCapture(1)  # adjust if wrong camera index
    face_mesh = mp.solutions.face_mesh.FaceMesh(refine_landmarks=True)
    tiempo_inicio_cerrados = None

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        resultado = face_mesh.process(frame_rgb)
        h, w, _ = frame.shape
        tiempo_cerrados = 0  # reset each frame

        if resultado.multi_face_landmarks:
            for rostro in resultado.multi_face_landmarks:
                puntos_ojos_derecho = [
                    (int(rostro.landmark[idx].x * w), int(rostro.landmark[idx].y * h))
                    for idx in [33, 160, 158, 133, 153, 144]
                ]
                EAR_derecho = calcular_EAR(np.array(puntos_ojos_derecho))

                puntos_ojos_izquierdo = [
                    (int(rostro.landmark[idx].x * w), int(rostro.landmark[idx].y * h))
                    for idx in [362, 385, 387, 263, 373, 380]
                ]
                EAR_izquierdo = calcular_EAR(np.array(puntos_ojos_izquierdo))

                EAR = (EAR_derecho + EAR_izquierdo) / 2.0

                if EAR < umbral_EAR:
                    cv2.putText(
                        frame, "Ojos Cerrados", (50, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2
                    )

                    if tiempo_inicio_cerrados is None:
                        tiempo_inicio_cerrados = time.time()

                    tiempo_cerrados = time.time() - tiempo_inicio_cerrados

                    # trigger once per sleep episode
                    if tiempo_cerrados >= umbral_tiempo_dormido:
                        print("¡ALERTA! Persona dormida")

                        # collect metrics
                        frecuencia_cardiaca, oxigenacion = obtener_signos_vitales()
                        duration_closed = tiempo_cerrados
                        ear_value = EAR

                        # alarm
                        alarm_status = "Success"
                        try:
                            playsound("C:\\Users\\Daniel Romero\\Desktop\\neural\\alarma.mp3")
                            print("Audio reproducido con éxito.")
                        except Exception as e:
                            print(f"Error al reproducir el archivo: {e}")
                            alarm_status = "Failed"

                        # email
                        email_status = enviar_correo(nombre_usuario, correo_usuario)

                        # log event
                        log_event(
                            nombre_usuario,
                            correo_usuario,
                            "Drowsiness Detected",
                            frecuencia_cardiaca,
                            oxigenacion,
                            duration_closed,
                            ear_value,
                            email_status,
                            alarm_status
                        )

                        # reset so we don’t spam continuously
                        tiempo_inicio_cerrados = None

                else:
                    tiempo_inicio_cerrados = None
                    cv2.putText(
                        frame, "Ojos Abiertos", (50, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2
                    )

                # draw eyes landmarks
                for punto in puntos_ojos_derecho + puntos_ojos_izquierdo:
                    cv2.circle(frame, punto, 2, (255, 0, 0), -1)

        cv2.imshow("Detección de Ojos", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


# ------------------------------
# GUI start function
# ------------------------------
def iniciar_programa():
    init_db()  # make sure DB is ready

    nombre_usuario = entry_nombre.get()
    correo_usuario = entry_correo.get()

    if not nombre_usuario or not correo_usuario:
        messagebox.showwarning("Error", "Por favor, complete todos los campos.")
        return

    reproducir_audio()
    ventana.destroy()
    iniciar_deteccion(nombre_usuario, correo_usuario)


# ------------------------------
# GUI setup
# ------------------------------
ventana = tk.Tk()
ventana.title("Detección de Sueño")
ventana.geometry("400x300")
ventana.configure(bg="#1e1e2e")

label_titulo = tk.Label(
    ventana, text="Sistema de Detección de Sueño",
    font=("Arial", 14, "bold"), fg="white", bg="#1e1e2e"
)
label_titulo.pack(pady=10)

label_nombre = tk.Label(
    ventana, text="Nombre:", font=("Arial", 12),
    fg="white", bg="#1e1e2e"
)
label_nombre.pack()
entry_nombre = tk.Entry(ventana, font=("Arial", 12))
entry_nombre.pack(pady=5)

label_correo = tk.Label(
    ventana, text="Correo Electrónico:", font=("Arial", 12),
    fg="white", bg="#1e1e2e"
)
label_correo.pack()
entry_correo = tk.Entry(ventana, font=("Arial", 12))
entry_correo.pack(pady=5)

btn_iniciar = tk.Button(
    ventana, text="Iniciar Detección", font=("Arial", 12, "bold"),
    bg="#4CAF50", fg="white", command=iniciar_programa
)
btn_iniciar.pack(pady=20)

ventana.mainloop()

    