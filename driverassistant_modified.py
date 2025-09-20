import cv2
import time
import numpy as np
import pygame
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import tkinter as tk
from tkinter import messagebox
import os

# Initialize pygame mixer for audio
pygame.mixer.init()

# Email configuration
SENDER_EMAIL = "your_email@gmail.com"  # Replace with your email
PASSWORD = "your_app_password"  # Replace with your app password

def reproducir_audio():
    """Play audio using pygame instead of playsound"""
    try:
        # Create a simple beep sound if no audio file exists
        if not os.path.exists("alarm.wav"):
            # Generate a simple alarm sound
            duration = 1000  # milliseconds
            sample_rate = 22050
            frames = int(duration * sample_rate / 1000)
            
            # Create a sine wave for alarm sound
            arr = np.zeros((frames, 2))
            for i in range(frames):
                time_val = float(i) / sample_rate
                wave = 4096 * np.sin(2 * np.pi * 800 * time_val)  # 800 Hz tone
                arr[i][0] = wave
                arr[i][1] = wave
            
            # Convert to pygame sound
            sound = pygame.sndarray.make_sound(arr.astype(np.int16))
            sound.play()
            time.sleep(1)
        else:
            # Play existing audio file
            pygame.mixer.music.load("alarm.wav")
            pygame.mixer.music.play()
            
        print("Audio reproducido con éxito.")
    except Exception as e:
        print(f"Error al reproducir el archivo: {e}")
        # Fallback to system beep
        try:
            import winsound
            winsound.Beep(800, 1000)  # 800 Hz for 1 second
        except:
            print("No se pudo reproducir audio")

# Detection parameters
umbral_EAR = 0.25  # Threshold for closed eyes (adjusted for simpler detection)
umbral_tiempo_dormido = 3  # Seconds before triggering alarm

def obtener_signos_vitales():
    """Simulate vital signs"""
    frecuencia_cardiaca = np.random.randint(60, 100)
    oxigenacion = np.random.randint(90, 100)
    return frecuencia_cardiaca, oxigenacion

def enviar_correo(nombre_usuario, correo_usuario):
    """
    Enhanced email function that uses EmailServiceManager if available,
    otherwise falls back to basic email functionality for backward compatibility.
    """
    # Try to use enhanced email service first
    try:
        from email_service import (
            EmailServiceManagerImpl, EmailConfig, UserData, AlertData,
            ProviderType, AuthMethod, AlertType
        )
        from datetime import datetime
        
        # Create a temporary email service for this call
        email_service = EmailServiceManagerImpl()
        
        # Create basic email configuration
        email_config = EmailConfig(
            provider=ProviderType.GMAIL,
            smtp_server="smtp.gmail.com",
            smtp_port=465,
            use_tls=False,  # Using SSL instead
            sender_email=SENDER_EMAIL,
            sender_password=PASSWORD,
            auth_method=AuthMethod.APP_PASSWORD,
            timeout=30,
            max_retries=3
        )
        
        # Initialize service
        if email_service.initialize(email_config):
            # Get vital signs
            frecuencia_cardiaca, oxigenacion = obtener_signos_vitales()
            
            # Create user data
            user_data = UserData(
                name=nombre_usuario,
                email=correo_usuario,
                user_id=f"driver_{hash(nombre_usuario) % 10000}",
                preferences={"language": "es", "timezone": "UTC"}
            )
            
            # Create alert data
            alert_data = AlertData(
                alert_type=AlertType.DROWSINESS,
                timestamp=datetime.now(),
                heart_rate=frecuencia_cardiaca,
                oxygen_saturation=float(oxigenacion),
                additional_data={
                    "detection_method": "opencv_eye_detection",
                    "system_version": "driverassistant_modified_v1.0"
                }
            )
            
            # Send email through service manager
            result = email_service.send_alert_email(user_data, alert_data)
            
            if result.success:
                print(f"Email enviado exitosamente: {result.message}")
                return True
            else:
                print(f"Error enviando email: {result.message}")
                # Fall through to basic email
        
    except Exception as e:
        print(f"Error with enhanced email service, falling back to basic: {e}")
    
    # Fallback to basic email functionality
    return enviar_correo_basico(nombre_usuario, correo_usuario)

def enviar_correo_basico(nombre_usuario: str, correo_usuario: str) -> bool:
    """Send email alert using basic functionality"""
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
        print("Correo básico enviado correctamente.")
        return True
    except Exception as e:
        print(f"Error al enviar correo básico: {e}")
        return False

def calcular_EAR_simple(eye_region):
    """Calculate a simplified Eye Aspect Ratio using basic measurements"""
    if len(eye_region) < 6:
        return 0.3  # Default open eye value
    
    # Simple approximation: height vs width ratio
    height = abs(eye_region[1][1] - eye_region[5][1])
    width = abs(eye_region[0][0] - eye_region[3][0])
    
    if width == 0:
        return 0.3
    
    return height / width

def detectar_ojos_opencv(frame, face_cascade, eye_cascade):
    """Detect eyes using OpenCV Haar cascades"""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)
    
    eyes_detected = []
    
    for (x, y, w, h) in faces:
        cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
        roi_gray = gray[y:y+h, x:x+w]
        roi_color = frame[y:y+h, x:x+w]
        
        eyes = eye_cascade.detectMultiScale(roi_gray)
        for (ex, ey, ew, eh) in eyes:
            cv2.rectangle(roi_color, (ex, ey), (ex+ew, ey+eh), (0, 255, 0), 2)
            # Create simplified eye points for EAR calculation
            eye_points = [
                (x + ex, y + ey),  # left corner
                (x + ex, y + ey + eh//3),  # top
                (x + ex, y + ey + 2*eh//3),  # middle top
                (x + ex + ew, y + ey),  # right corner
                (x + ex, y + ey + 2*eh//3),  # middle bottom
                (x + ex, y + ey + eh)  # bottom
            ]
            eyes_detected.append(eye_points)
    
    return eyes_detected

def iniciar_deteccion(nombre_usuario, correo_usuario):
    """Start drowsiness detection using OpenCV"""
    cap = cv2.VideoCapture(0)
    
    # Load Haar cascade classifiers
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
    
    tiempo_inicio_cerrados = None
    
    print("Iniciando detección... Presiona 'q' para salir")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: No se pudo acceder a la cámara")
            break
        
        # Detect eyes
        eyes = detectar_ojos_opencv(frame, face_cascade, eye_cascade)
        
        ojos_cerrados = len(eyes) < 2  # If less than 2 eyes detected, consider closed
        
        if ojos_cerrados:
            cv2.putText(frame, "Ojos Cerrados - ALERTA", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            
            if tiempo_inicio_cerrados is None:
                tiempo_inicio_cerrados = time.time()
            
            tiempo_cerrados = time.time() - tiempo_inicio_cerrados
            cv2.putText(frame, f"Tiempo: {tiempo_cerrados:.1f}s", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
            if tiempo_cerrados >= umbral_tiempo_dormido:
                print("¡ALERTA! Persona dormida")
                cv2.putText(frame, "DORMIDO! DESPERTANDO...", (50, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
                reproducir_audio()
                enviar_correo(nombre_usuario, correo_usuario)
                tiempo_inicio_cerrados = None  # Reset timer
        else:
            tiempo_inicio_cerrados = None
            cv2.putText(frame, "Ojos Abiertos", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        # Show detection status
        status = f"Detectados: {len(eyes)} ojos"
        cv2.putText(frame, status, (50, frame.shape[0] - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        cv2.imshow("Detección de Sueño - Presiona 'q' para salir", frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()

def iniciar_programa():
    """Start the program with user input"""
    nombre_usuario = entry_nombre.get()
    correo_usuario = entry_correo.get()
    
    if not nombre_usuario or not correo_usuario:
        messagebox.showwarning("Error", "Por favor, complete todos los campos.")
        return
    
    print(f"Iniciando sistema para: {nombre_usuario}")
    print(f"Correo de alerta: {correo_usuario}")
    
    # Test audio
    reproducir_audio()
    
    ventana.destroy()  # Close window
    iniciar_deteccion(nombre_usuario, correo_usuario)

# Create GUI
ventana = tk.Tk()
ventana.title("Sistema de Detección de Sueño - Versión OpenCV")
ventana.geometry("450x350")
ventana.configure(bg="#1e1e2e")

label_titulo = tk.Label(ventana, text="Sistema de Detección de Sueño", font=("Arial", 14, "bold"), fg="white", bg="#1e1e2e")
label_titulo.pack(pady=10)

label_subtitulo = tk.Label(ventana, text="Versión con OpenCV (sin MediaPipe)", font=("Arial", 10), fg="gray", bg="#1e1e2e")
label_subtitulo.pack(pady=5)

label_nombre = tk.Label(ventana, text="Nombre:", font=("Arial", 12), fg="white", bg="#1e1e2e")
label_nombre.pack()
entry_nombre = tk.Entry(ventana, font=("Arial", 12))
entry_nombre.pack(pady=5)

label_correo = tk.Label(ventana, text="Correo Electrónico:", font=("Arial", 12), fg="white", bg="#1e1e2e")
label_correo.pack()
entry_correo = tk.Entry(ventana, font=("Arial", 12))
entry_correo.pack(pady=5)

# Instructions
label_instrucciones = tk.Label(ventana, text="Instrucciones:\n• Asegúrate de tener buena iluminación\n• Mira directamente a la cámara\n• Presiona 'q' para salir del detector", 
                              font=("Arial", 9), fg="lightgray", bg="#1e1e2e", justify="left")
label_instrucciones.pack(pady=10)

btn_iniciar = tk.Button(ventana, text="Iniciar Detección", font=("Arial", 12, "bold"), bg="#4CAF50", fg="white", command=iniciar_programa)
btn_iniciar.pack(pady=20)

if __name__ == "__main__":
    ventana.mainloop()