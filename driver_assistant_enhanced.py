#!/usr/bin/env python3
"""
Enhanced Driver Assistant with Email Service Integration

This version integrates the new EmailServiceManager for improved email functionality
while maintaining backward compatibility with existing features.
"""

import cv2
import time
import numpy as np
import pygame
import tkinter as tk
from tkinter import messagebox, ttk
import os
import threading
from datetime import datetime
from typing import Optional

# Import the new email service
from email_service import (
    EmailServiceManagerImpl, EmailConfig, UserData, AlertData,
    ProviderType, AuthMethod, AlertType
)

# Import existing database functionality
import db

# Initialize pygame mixer for audio
pygame.mixer.init()

# Global variables for detection control
detener = False
reiniciar = False
email_service: Optional[EmailServiceManagerImpl] = None

class EmailConfigManager:
    """Manages email configuration for the driver assistant"""
    
    def __init__(self):
        self.config_file = "email_config.json"
        self.default_config = {
            "provider": "gmail",
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "use_tls": True,
            "sender_email": "",
            "sender_password": "",
            "auth_method": "app_password",
            "timeout": 30,
            "max_retries": 3
        }
    
    def load_config(self) -> dict:
        """Load email configuration from file"""
        import json
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    return {**self.default_config, **config}
            return self.default_config.copy()
        except Exception as e:
            print(f"Error loading email config: {e}")
            return self.default_config.copy()
    
    def save_config(self, config: dict) -> bool:
        """Save email configuration to file"""
        import json
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=4)
            return True
        except Exception as e:
            print(f"Error saving email config: {e}")
            return False
    
    def create_email_config(self, config_dict: dict) -> EmailConfig:
        """Create EmailConfig object from dictionary"""
        return EmailConfig(
            provider=ProviderType(config_dict["provider"]),
            smtp_server=config_dict["smtp_server"],
            smtp_port=config_dict["smtp_port"],
            use_tls=config_dict["use_tls"],
            sender_email=config_dict["sender_email"],
            sender_password=config_dict["sender_password"],
            auth_method=AuthMethod(config_dict["auth_method"]),
            timeout=config_dict["timeout"],
            max_retries=config_dict["max_retries"]
        )

def reproducir_audio():
    """Play audio using pygame with fallback options"""
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

def obtener_signos_vitales():
    """Simulate vital signs - in real implementation, this would read from sensors"""
    frecuencia_cardiaca = np.random.randint(60, 100)
    oxigenacion = np.random.randint(90, 100)
    return frecuencia_cardiaca, oxigenacion

def enviar_correo_mejorado(nombre_usuario: str, correo_usuario: str) -> bool:
    """
    Send enhanced email using the new EmailServiceManager
    
    Args:
        nombre_usuario: User's name
        correo_usuario: User's email address
        
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    global email_service
    
    if not email_service:
        print("Email service not initialized, falling back to basic email")
        return enviar_correo_basico(nombre_usuario, correo_usuario)
    
    try:
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
                "system_version": "enhanced_v1.0"
            }
        )
        
        # Send email through service manager
        result = email_service.send_alert_email(user_data, alert_data)
        
        if result.success:
            print(f"Email enviado exitosamente: {result.message}")
            if result.email_id:
                print(f"ID del email: {result.email_id}")
            return True
        else:
            print(f"Error enviando email: {result.message}")
            if result.details:
                print(f"Detalles: {result.details}")
            return False
            
    except Exception as e:
        print(f"Error en envío de email mejorado: {e}")
        # Fallback to basic email
        return enviar_correo_basico(nombre_usuario, correo_usuario)

def enviar_correo_basico(nombre_usuario: str, correo_usuario: str) -> bool:
    """
    Fallback basic email function (backward compatibility)
    
    Args:
        nombre_usuario: User's name
        correo_usuario: User's email address
        
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    
    # Basic configuration - should be replaced with proper config
    SENDER_EMAIL = "your_email@gmail.com"  # Replace with actual email
    PASSWORD = "your_app_password"  # Replace with actual app password
    
    try:
        frecuencia_cardiaca, oxigenacion = obtener_signos_vitales()
        body = f"El usuario {nombre_usuario} se ha dormido.\n\nSignos vitales:\nFrecuencia Cardiaca: {frecuencia_cardiaca} BPM\nOxigenación: {oxigenacion}%"

        message = MIMEMultipart()
        message["From"] = SENDER_EMAIL
        message["To"] = correo_usuario
        message["Subject"] = "¡Alerta! Detección de sueño"
        message.attach(MIMEText(body, "plain"))
        
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(SENDER_EMAIL, PASSWORD)
        server.sendmail(SENDER_EMAIL, correo_usuario, message.as_string())
        server.quit()
        print("Correo básico enviado correctamente.")
        return True
    except Exception as e:
        print(f"Error al enviar correo básico: {e}")
        return False

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

def iniciar_deteccion(nombre_usuario: str, correo_usuario: str):
    """
    Start drowsiness detection using OpenCV with enhanced email functionality
    
    Args:
        nombre_usuario: User's name
        correo_usuario: User's email address
    """
    global detener, reiniciar
    
    cap = cv2.VideoCapture(0)
    
    # Load Haar cascade classifiers
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
    
    tiempo_inicio_cerrados = None
    umbral_tiempo_dormido = 3  # seconds
    
    print(f"Iniciando detección para {nombre_usuario}...")
    print("Presiona 'q' para salir, 'r' para reiniciar")
    
    while True:
        if detener:
            print("Detección detenida por el usuario.")
            break
        
        if reiniciar:
            print("Reiniciando detección...")
            reiniciar = False
            tiempo_inicio_cerrados = None
        
        ret, frame = cap.read()
        if not ret:
            print("Error: No se pudo acceder a la cámara")
            break
        
        # Detect eyes
        eyes = detectar_ojos_opencv(frame, face_cascade, eye_cascade)
        
        # Determine if eyes are closed (less than 2 eyes detected)
        ojos_cerrados = len(eyes) < 2
        
        if ojos_cerrados:
            cv2.putText(frame, "Ojos Cerrados - ALERTA", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            
            if tiempo_inicio_cerrados is None:
                tiempo_inicio_cerrados = time.time()
            
            tiempo_cerrados = time.time() - tiempo_inicio_cerrados
            cv2.putText(frame, f"Tiempo: {tiempo_cerrados:.1f}s", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
            if tiempo_cerrados >= umbral_tiempo_dormido:
                print("¡ALERTA! Persona dormida - Activando alarma y enviando email")
                cv2.putText(frame, "DORMIDO! DESPERTANDO...", (50, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
                
                # Play audio alarm
                reproducir_audio()
                
                # Send enhanced email
                email_enviado = enviar_correo_mejorado(nombre_usuario, correo_usuario)
                
                if email_enviado:
                    cv2.putText(frame, "Email enviado", (50, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                else:
                    cv2.putText(frame, "Error enviando email", (50, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                
                tiempo_inicio_cerrados = None  # Reset timer
        else:
            tiempo_inicio_cerrados = None
            cv2.putText(frame, "Ojos Abiertos", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        # Show detection status
        status = f"Detectados: {len(eyes)} ojos"
        cv2.putText(frame, status, (50, frame.shape[0] - 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Show email service status
        email_status = "Email: Mejorado" if email_service else "Email: Básico"
        cv2.putText(frame, email_status, (50, frame.shape[0] - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        
        cv2.imshow("Detección de Sueño Mejorada - 'q' salir, 'r' reiniciar", frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('r'):
            reiniciar = True
    
    cap.release()
    cv2.destroyAllWindows()

def parar_deteccion():
    """Stop the detection process"""
    global detener
    detener = True

def reiniciar_deteccion():
    """Restart the detection process"""
    global reiniciar
    reiniciar = True

def inicializar_servicio_email() -> bool:
    """
    Initialize the email service with configuration
    
    Returns:
        bool: True if initialization successful, False otherwise
    """
    global email_service
    
    try:
        config_manager = EmailConfigManager()
        config_dict = config_manager.load_config()
        
        # Check if email configuration is complete
        if not config_dict["sender_email"] or not config_dict["sender_password"]:
            print("Email configuration incomplete - using basic email fallback")
            return False
        
        # Create email service manager
        email_service = EmailServiceManagerImpl()
        
        # Create email configuration
        email_config = config_manager.create_email_config(config_dict)
        
        # Initialize service
        success = email_service.initialize(email_config)
        
        if success:
            print("Email service initialized successfully")
            
            # Test configuration
            test_result = email_service.test_email_configuration()
            if test_result.success:
                print("Email configuration test passed")
            else:
                print(f"Email configuration test failed: {test_result.error_messages}")
                print("Service initialized but may have issues")
            
            return True
        else:
            print("Failed to initialize email service")
            email_service = None
            return False
            
    except Exception as e:
        print(f"Error initializing email service: {e}")
        email_service = None
        return False

class EmailConfigWindow:
    """GUI window for email configuration"""
    
    def __init__(self, parent):
        self.parent = parent
        self.config_manager = EmailConfigManager()
        self.window = None
        
    def show(self):
        """Show the email configuration window"""
        if self.window:
            self.window.lift()
            return
        
        self.window = tk.Toplevel(self.parent)
        self.window.title("Configuración de Email")
        self.window.geometry("500x600")
        self.window.configure(bg="#1e1e2e")
        
        # Load current configuration
        config = self.config_manager.load_config()
        
        # Title
        title_label = tk.Label(self.window, text="Configuración del Servicio de Email", 
                              font=("Arial", 14, "bold"), fg="white", bg="#1e1e2e")
        title_label.pack(pady=10)
        
        # Provider selection
        tk.Label(self.window, text="Proveedor de Email:", font=("Arial", 12), 
                fg="white", bg="#1e1e2e").pack(anchor="w", padx=20)
        
        self.provider_var = tk.StringVar(value=config["provider"])
        provider_frame = tk.Frame(self.window, bg="#1e1e2e")
        provider_frame.pack(fill="x", padx=20, pady=5)
        
        providers = [("Gmail", "gmail"), ("Outlook", "outlook"), ("Yahoo", "yahoo"), ("Custom", "custom")]
        for text, value in providers:
            tk.Radiobutton(provider_frame, text=text, variable=self.provider_var, value=value,
                          fg="white", bg="#1e1e2e", selectcolor="#333").pack(side="left")
        
        # Email address
        tk.Label(self.window, text="Dirección de Email:", font=("Arial", 12), 
                fg="white", bg="#1e1e2e").pack(anchor="w", padx=20, pady=(10,0))
        self.email_entry = tk.Entry(self.window, font=("Arial", 12), width=40)
        self.email_entry.pack(padx=20, pady=5)
        self.email_entry.insert(0, config["sender_email"])
        
        # Password
        tk.Label(self.window, text="Contraseña/App Password:", font=("Arial", 12), 
                fg="white", bg="#1e1e2e").pack(anchor="w", padx=20, pady=(10,0))
        self.password_entry = tk.Entry(self.window, font=("Arial", 12), width=40, show="*")
        self.password_entry.pack(padx=20, pady=5)
        self.password_entry.insert(0, config["sender_password"])
        
        # SMTP Server (for custom)
        tk.Label(self.window, text="Servidor SMTP (solo para Custom):", font=("Arial", 12), 
                fg="white", bg="#1e1e2e").pack(anchor="w", padx=20, pady=(10,0))
        self.smtp_entry = tk.Entry(self.window, font=("Arial", 12), width=40)
        self.smtp_entry.pack(padx=20, pady=5)
        self.smtp_entry.insert(0, config["smtp_server"])
        
        # SMTP Port
        tk.Label(self.window, text="Puerto SMTP:", font=("Arial", 12), 
                fg="white", bg="#1e1e2e").pack(anchor="w", padx=20, pady=(10,0))
        self.port_entry = tk.Entry(self.window, font=("Arial", 12), width=10)
        self.port_entry.pack(padx=20, pady=5)
        self.port_entry.insert(0, str(config["smtp_port"]))
        
        # Buttons
        button_frame = tk.Frame(self.window, bg="#1e1e2e")
        button_frame.pack(pady=20)
        
        tk.Button(button_frame, text="Probar Configuración", font=("Arial", 12), 
                 bg="#FFA726", fg="white", command=self.test_config).pack(side="left", padx=5)
        
        tk.Button(button_frame, text="Guardar", font=("Arial", 12), 
                 bg="#4CAF50", fg="white", command=self.save_config).pack(side="left", padx=5)
        
        tk.Button(button_frame, text="Cancelar", font=("Arial", 12), 
                 bg="#E53935", fg="white", command=self.close).pack(side="left", padx=5)
        
        # Instructions
        instructions = tk.Text(self.window, height=8, width=60, font=("Arial", 9), 
                              bg="#2e2e2e", fg="lightgray", wrap="word")
        instructions.pack(padx=20, pady=10)
        
        instructions.insert("1.0", """Instrucciones:
1. Para Gmail: Habilita 2FA y genera una App Password
2. Para Outlook: Usa tu contraseña normal o App Password
3. Para Yahoo: Habilita App Passwords en configuración
4. Para Custom: Especifica servidor SMTP y puerto

Puertos comunes:
- Gmail: 587 (TLS) o 465 (SSL)
- Outlook: 587 (TLS)
- Yahoo: 587 (TLS) o 465 (SSL)""")
        
        instructions.config(state="disabled")
        
        self.window.protocol("WM_DELETE_WINDOW", self.close)
    
    def test_config(self):
        """Test the email configuration"""
        try:
            config = self.get_config_from_form()
            
            # Create temporary email service for testing
            test_service = EmailServiceManagerImpl()
            email_config = self.config_manager.create_email_config(config)
            
            messagebox.showinfo("Probando", "Probando configuración... Esto puede tomar unos segundos.")
            
            success = test_service.initialize(email_config)
            if success:
                test_result = test_service.test_email_configuration()
                if test_result.success:
                    messagebox.showinfo("Éxito", "Configuración de email válida!")
                else:
                    error_msg = "\n".join(test_result.error_messages)
                    messagebox.showwarning("Advertencia", f"Configuración parcialmente válida:\n{error_msg}")
            else:
                messagebox.showerror("Error", "No se pudo inicializar el servicio de email")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error probando configuración: {str(e)}")
    
    def save_config(self):
        """Save the email configuration"""
        try:
            config = self.get_config_from_form()
            
            if self.config_manager.save_config(config):
                messagebox.showinfo("Éxito", "Configuración guardada correctamente")
                
                # Reinitialize email service
                if inicializar_servicio_email():
                    messagebox.showinfo("Éxito", "Servicio de email reinicializado")
                else:
                    messagebox.showwarning("Advertencia", "Configuración guardada pero el servicio no se pudo inicializar")
                
                self.close()
            else:
                messagebox.showerror("Error", "No se pudo guardar la configuración")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error guardando configuración: {str(e)}")
    
    def get_config_from_form(self) -> dict:
        """Get configuration from form fields"""
        provider = self.provider_var.get()
        
        # Set default SMTP settings based on provider
        smtp_servers = {
            "gmail": "smtp.gmail.com",
            "outlook": "smtp-mail.outlook.com", 
            "yahoo": "smtp.mail.yahoo.com",
            "custom": self.smtp_entry.get()
        }
        
        return {
            "provider": provider,
            "smtp_server": smtp_servers.get(provider, self.smtp_entry.get()),
            "smtp_port": int(self.port_entry.get()),
            "use_tls": True,
            "sender_email": self.email_entry.get(),
            "sender_password": self.password_entry.get(),
            "auth_method": "app_password",
            "timeout": 30,
            "max_retries": 3
        }
    
    def close(self):
        """Close the configuration window"""
        if self.window:
            self.window.destroy()
            self.window = None

class EnhancedDriverAssistantGUI:
    """Enhanced GUI for the driver assistant with email configuration"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Sistema de Detección de Sueño - Versión Mejorada")
        self.root.geometry("500x600")
        self.root.configure(bg="#1e1e2e")
        
        self.email_config_window = None
        self.setup_gui()
        
        # Initialize database
        db.crear_tabla()
        
        # Initialize email service
        inicializar_servicio_email()
    
    def setup_gui(self):
        """Set up the GUI components"""
        # Title
        title_label = tk.Label(self.root, text="Sistema de Detección de Sueño", 
                              font=("Arial", 16, "bold"), fg="white", bg="#1e1e2e")
        title_label.pack(pady=10)
        
        subtitle_label = tk.Label(self.root, text="Versión Mejorada con Email Service", 
                                 font=("Arial", 10), fg="gray", bg="#1e1e2e")
        subtitle_label.pack(pady=5)
        
        # Email service status
        global email_service
        status_text = "Email Service: Activo" if email_service else "Email Service: Básico"
        status_color = "#4CAF50" if email_service else "#FFA726"
        
        self.status_label = tk.Label(self.root, text=status_text, font=("Arial", 10, "bold"), 
                                    fg=status_color, bg="#1e1e2e")
        self.status_label.pack(pady=5)
        
        # User login section
        login_frame = tk.LabelFrame(self.root, text="Iniciar Sesión", font=("Arial", 12, "bold"),
                                   fg="white", bg="#1e1e2e", bd=2)
        login_frame.pack(fill="x", padx=20, pady=10)
        
        tk.Label(login_frame, text="Nombre o Correo:", font=("Arial", 12), 
                fg="white", bg="#1e1e2e").pack(anchor="w", padx=10, pady=5)
        
        self.user_entry = tk.Entry(login_frame, font=("Arial", 12), width=40)
        self.user_entry.pack(padx=10, pady=5)
        
        button_frame1 = tk.Frame(login_frame, bg="#1e1e2e")
        button_frame1.pack(pady=10)
        
        tk.Button(button_frame1, text="Iniciar Detección", font=("Arial", 12, "bold"), 
                 bg="#4CAF50", fg="white", command=self.iniciar_programa).pack(side="left", padx=5)
        
        tk.Button(button_frame1, text="Parar", font=("Arial", 12, "bold"), 
                 bg="#E53935", fg="white", command=self.parar_programa).pack(side="left", padx=5)
        
        tk.Button(button_frame1, text="Reiniciar", font=("Arial", 12, "bold"), 
                 bg="#FF9800", fg="white", command=self.reiniciar_programa).pack(side="left", padx=5)
        
        # User registration section
        register_frame = tk.LabelFrame(self.root, text="Registrar Usuario", font=("Arial", 12, "bold"),
                                      fg="white", bg="#1e1e2e", bd=2)
        register_frame.pack(fill="x", padx=20, pady=10)
        
        tk.Label(register_frame, text="Nombre:", font=("Arial", 12), 
                fg="white", bg="#1e1e2e").pack(anchor="w", padx=10, pady=5)
        self.name_entry = tk.Entry(register_frame, font=("Arial", 12), width=40)
        self.name_entry.pack(padx=10, pady=5)
        
        tk.Label(register_frame, text="Correo:", font=("Arial", 12), 
                fg="white", bg="#1e1e2e").pack(anchor="w", padx=10, pady=5)
        self.email_entry = tk.Entry(register_frame, font=("Arial", 12), width=40)
        self.email_entry.pack(padx=10, pady=5)
        
        tk.Button(register_frame, text="Registrar Usuario", font=("Arial", 12, "bold"), 
                 bg="#2196F3", fg="white", command=self.registrar_usuario).pack(pady=10)
        
        # Configuration section
        config_frame = tk.LabelFrame(self.root, text="Configuración", font=("Arial", 12, "bold"),
                                    fg="white", bg="#1e1e2e", bd=2)
        config_frame.pack(fill="x", padx=20, pady=10)
        
        tk.Button(config_frame, text="Configurar Email", font=("Arial", 12, "bold"), 
                 bg="#9C27B0", fg="white", command=self.mostrar_config_email).pack(pady=10)
        
        # Instructions
        instructions_frame = tk.LabelFrame(self.root, text="Instrucciones", font=("Arial", 12, "bold"),
                                          fg="white", bg="#1e1e2e", bd=2)
        instructions_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        instructions_text = tk.Text(instructions_frame, height=8, font=("Arial", 9), 
                                   bg="#2e2e2e", fg="lightgray", wrap="word")
        instructions_text.pack(fill="both", expand=True, padx=10, pady=10)
        
        instructions_text.insert("1.0", """Instrucciones de uso:

1. Registra un usuario con nombre y correo electrónico
2. Configura el servicio de email (recomendado para mejor funcionalidad)
3. Inicia sesión con nombre o correo registrado
4. Inicia la detección - asegúrate de tener buena iluminación
5. El sistema detectará cuando cierres los ojos por más de 3 segundos
6. Se reproducirá una alarma y se enviará un email de alerta

Controles durante detección:
- Presiona 'q' para salir
- Presiona 'r' para reiniciar la detección

Nota: Si no configuras el email service, se usará el sistema básico de email.""")
        
        instructions_text.config(state="disabled")
    
    def iniciar_programa(self):
        """Start the detection program"""
        usuario = self.user_entry.get().strip().lower()
        if not usuario:
            messagebox.showwarning("Error", "Ingrese un nombre o correo.")
            return

        datos = db.buscar_usuario(usuario)
        if not datos:
            messagebox.showwarning("Error", "Usuario no registrado en la base de datos.")
            return

        nombre_usuario, correo_usuario = datos
        global detener
        detener = False
        
        print(f"Iniciando detección para: {nombre_usuario} ({correo_usuario})")
        threading.Thread(target=iniciar_deteccion, args=(nombre_usuario, correo_usuario), daemon=True).start()
        messagebox.showinfo("Iniciado", f"Detección iniciada para {nombre_usuario}")
    
    def parar_programa(self):
        """Stop the detection program"""
        parar_deteccion()
        messagebox.showinfo("Detenido", "Detección detenida.")
    
    def reiniciar_programa(self):
        """Restart the detection program"""
        reiniciar_deteccion()
        messagebox.showinfo("Reiniciado", "Detección reiniciada.")
    
    def registrar_usuario(self):
        """Register a new user"""
        nombre = self.name_entry.get().strip().lower()
        correo = self.email_entry.get().strip().lower()
        
        if not nombre or not correo:
            messagebox.showwarning("Error", "Debe ingresar nombre y correo.")
            return
        
        if db.agregar_usuario(nombre, correo):
            messagebox.showinfo("Éxito", "Usuario registrado correctamente.")
            self.name_entry.delete(0, tk.END)
            self.email_entry.delete(0, tk.END)
        else:
            messagebox.showerror("Error", "El nombre o correo ya existe.")
    
    def mostrar_config_email(self):
        """Show email configuration window"""
        if not self.email_config_window:
            self.email_config_window = EmailConfigWindow(self.root)
        self.email_config_window.show()
    
    def update_status(self):
        """Update the email service status display"""
        global email_service
        status_text = "Email Service: Activo" if email_service else "Email Service: Básico"
        status_color = "#4CAF50" if email_service else "#FFA726"
        self.status_label.config(text=status_text, fg=status_color)
    
    def run(self):
        """Run the GUI application"""
        self.root.mainloop()

def main():
    """Main function to run the enhanced driver assistant"""
    print("Iniciando Sistema de Detección de Sueño Mejorado...")
    
    try:
        app = EnhancedDriverAssistantGUI()
        app.run()
    except KeyboardInterrupt:
        print("\nAplicación interrumpida por el usuario.")
    except Exception as e:
        print(f"Error en la aplicación: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()