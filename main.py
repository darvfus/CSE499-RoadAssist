import cv2
import time
import mediapipe as mp
import numpy as np
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import tkinter as tk
from tkinter import messagebox
from playsound import playsound
import threading
import json
import os
from datetime import datetime
from typing import Optional

# Import the new email service
try:
    from email_service import (
        EmailServiceManagerImpl, EmailConfig, UserData, AlertData,
        ProviderType, AuthMethod, AlertType
    )
    EMAIL_SERVICE_AVAILABLE = True
except ImportError:
    print("Email service not available, using basic email functionality")
    EMAIL_SERVICE_AVAILABLE = False

# =============================
# CONFIGURACIÓN
# =============================
SENDER_EMAIL = "xxxxxxxxxxx"
PASSWORD = "xxxxxxxxxxxxxxxxx"
USUARIOS_FILE = "usuarios.json"
EMAIL_CONFIG_FILE = "email_config.json"

umbral_EAR = 0.2
umbral_tiempo_dormido = 3

# Global email service instance
email_service: Optional[EmailServiceManagerImpl] = None

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
# EMAIL SERVICE MANAGEMENT
# =============================
def cargar_config_email():
    """Load email configuration from file"""
    default_config = {
        "provider": "gmail",
        "smtp_server": "smtp.gmail.com",
        "smtp_port": 587,
        "use_tls": True,
        "sender_email": SENDER_EMAIL,
        "sender_password": PASSWORD,
        "auth_method": "app_password",
        "timeout": 30,
        "max_retries": 3
    }
    
    if os.path.exists(EMAIL_CONFIG_FILE):
        try:
            with open(EMAIL_CONFIG_FILE, "r") as f:
                config = json.load(f)
                return {**default_config, **config}
        except Exception as e:
            print(f"Error loading email config: {e}")
    
    return default_config

def guardar_config_email(config):
    """Save email configuration to file"""
    try:
        with open(EMAIL_CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=4)
        return True
    except Exception as e:
        print(f"Error saving email config: {e}")
        return False

def inicializar_servicio_email():
    """Initialize the email service with configuration"""
    global email_service
    
    if not EMAIL_SERVICE_AVAILABLE:
        print("Email service not available, using basic email")
        return False
    
    try:
        config_dict = cargar_config_email()
        
        # Check if email configuration is complete
        if not config_dict["sender_email"] or not config_dict["sender_password"]:
            print("Email configuration incomplete - using basic email fallback")
            return False
        
        # Create email service manager
        email_service = EmailServiceManagerImpl()
        
        # Create email configuration
        email_config = EmailConfig(
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
        
        # Initialize service
        success = email_service.initialize(email_config)
        
        if success:
            print("Email service initialized successfully")
            return True
        else:
            print("Failed to initialize email service")
            email_service = None
            return False
            
    except Exception as e:
        print(f"Error initializing email service: {e}")
        email_service = None
        return False

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
    """
    Enhanced email function that uses EmailServiceManager if available,
    otherwise falls back to basic email functionality for backward compatibility.
    """
    global email_service
    
    # Try to use enhanced email service first
    if EMAIL_SERVICE_AVAILABLE and email_service:
        try:
            return enviar_correo_mejorado(nombre_usuario, correo_usuario)
        except Exception as e:
            print(f"Error with enhanced email service, falling back to basic: {e}")
    
    # Fallback to basic email functionality
    return enviar_correo_basico(nombre_usuario, correo_usuario)

def enviar_correo_mejorado(nombre_usuario: str, correo_usuario: str) -> bool:
    """
    Send enhanced email using the new EmailServiceManager
    """
    global email_service
    
    if not email_service:
        print("Email service not initialized")
        return False
    
    try:
        # Get vital signs
        frecuencia_cardiaca, oxigenacion = obtener_signos_vitales()
        
        # Generate email ID for tracking
        import uuid
        email_id = str(uuid.uuid4())
        
        # Update status tracking - mark as sending
        try:
            import interfaz
            interfaz.marcar_email_enviando(email_id, correo_usuario)
        except:
            pass  # Interface might not be available
        
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
                "detection_method": "mediapipe_face_mesh",
                "system_version": "main_v1.0"
            }
        )
        
        # Send email through service manager
        result = email_service.send_alert_email(user_data, alert_data)
        
        # Update status tracking
        try:
            import interfaz
            interfaz.actualizar_estado_email(
                email_id, 
                correo_usuario, 
                result.success, 
                1, 
                None if result.success else result.message
            )
        except:
            pass  # Interface might not be available
        
        if result.success:
            print(f"Email enviado exitosamente: {result.message}")
            return True
        else:
            print(f"Error enviando email: {result.message}")
            return False
            
    except Exception as e:
        print(f"Error en envío de email mejorado: {e}")
        # Update status tracking for error
        try:
            import interfaz
            interfaz.actualizar_estado_email(email_id, correo_usuario, False, 1, str(e))
        except:
            pass
        return False

def enviar_correo_basico(nombre_usuario: str, correo_usuario: str) -> bool:
    """
    Basic email function for backward compatibility
    """
    import uuid
    email_id = str(uuid.uuid4())
    
    # Update status tracking - mark as sending
    try:
        import interfaz
        interfaz.marcar_email_enviando(email_id, correo_usuario)
    except:
        pass  # Interface might not be available
    
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
        
        # Update status tracking - success
        try:
            import interfaz
            interfaz.actualizar_estado_email(email_id, correo_usuario, True, 1, None)
        except:
            pass
        
        return True
    except Exception as e:
        print(f"Error al enviar correo básico: {e}")
        
        # Update status tracking - failure
        try:
            import interfaz
            interfaz.actualizar_estado_email(email_id, correo_usuario, False, 1, str(e))
        except:
            pass
        
        return False

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
# INTERFAZ GRÁFICA
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

    reg = tk.Toplevel()
    reg.title("Registro de Usuario")
    reg.geometry("300x200")
    tk.Label(reg, text="Nombre:").pack()
    entry_nombre = tk.Entry(reg)
    entry_nombre.pack()
    tk.Label(reg, text="Correo:").pack()
    entry_correo = tk.Entry(reg)
    entry_correo.pack()
    tk.Button(reg, text="Registrar", command=registrar).pack(pady=10)

def ventana_inicio():
    def iniciar():
        global detener, reiniciar
        nombre = entry_nombre.get()
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

    ini = tk.Toplevel()
    ini.title("Panel de Control")
    ini.geometry("300x200")

    tk.Label(ini, text="Nombre:").pack()
    entry_nombre = tk.Entry(ini)
    entry_nombre.pack()

    tk.Button(ini, text="Iniciar", bg="green", fg="white", command=iniciar).pack(pady=5)
    tk.Button(ini, text="Parar", bg="red", fg="white", command=parar).pack(pady=5)
    tk.Button(ini, text="Reiniciar", bg="orange", fg="white", command=reiniciar_btn).pack(pady=5)

def ventana_config_email():
    """Enhanced email configuration window with testing and status display"""
    def actualizar_campos_provider():
        """Update fields based on selected provider"""
        provider = provider_var.get()
        
        # Clear and update SMTP server and port based on provider
        smtp_entry.delete(0, tk.END)
        port_entry.delete(0, tk.END)
        
        if provider == "gmail":
            smtp_entry.insert(0, "smtp.gmail.com")
            port_entry.insert(0, "587")
            smtp_entry.config(state="disabled")
            port_entry.config(state="disabled")
        elif provider == "outlook":
            smtp_entry.insert(0, "smtp-mail.outlook.com")
            port_entry.insert(0, "587")
            smtp_entry.config(state="disabled")
            port_entry.config(state="disabled")
        elif provider == "yahoo":
            smtp_entry.insert(0, "smtp.mail.yahoo.com")
            port_entry.insert(0, "587")
            smtp_entry.config(state="disabled")
            port_entry.config(state="disabled")
        else:  # custom
            smtp_entry.config(state="normal")
            port_entry.config(state="normal")
    
    def test_email_config():
        """Test email configuration"""
        test_button.config(state="disabled", text="Probando...")
        status_label.config(text="Estado: Probando configuración...", fg="orange")
        config_window.update()
        
        def run_test():
            try:
                # Create temporary config for testing
                temp_config = {
                    "provider": provider_var.get(),
                    "sender_email": email_entry.get(),
                    "sender_password": password_entry.get(),
                    "smtp_server": smtp_entry.get(),
                    "smtp_port": int(port_entry.get()),
                    "use_tls": True,
                    "auth_method": "app_password",
                    "timeout": 30,
                    "max_retries": 3
                }
                
                if EMAIL_SERVICE_AVAILABLE:
                    # Test with enhanced email service
                    test_service = EmailServiceManagerImpl()
                    email_config = EmailConfig(
                        provider=ProviderType(temp_config["provider"]),
                        smtp_server=temp_config["smtp_server"],
                        smtp_port=temp_config["smtp_port"],
                        use_tls=temp_config["use_tls"],
                        sender_email=temp_config["sender_email"],
                        sender_password=temp_config["sender_password"],
                        auth_method=AuthMethod(temp_config["auth_method"]),
                        timeout=temp_config["timeout"],
                        max_retries=temp_config["max_retries"]
                    )
                    
                    if test_service.initialize(email_config):
                        test_result = test_service.test_email_configuration()
                        
                        if test_result.success:
                            status_label.config(text="Estado: ✓ Configuración válida", fg="green")
                            messagebox.showinfo("Éxito", "Configuración de email válida y funcional")
                        else:
                            error_msg = "\n".join(test_result.error_messages)
                            status_label.config(text="Estado: ✗ Error en configuración", fg="red")
                            messagebox.showerror("Error", f"Error en configuración:\n{error_msg}")
                    else:
                        status_label.config(text="Estado: ✗ Error de inicialización", fg="red")
                        messagebox.showerror("Error", "No se pudo inicializar el servicio de email")
                else:
                    # Basic test with standard SMTP
                    import smtplib
                    server = smtplib.SMTP(temp_config["smtp_server"], temp_config["smtp_port"])
                    server.starttls()
                    server.login(temp_config["sender_email"], temp_config["sender_password"])
                    server.quit()
                    
                    status_label.config(text="Estado: ✓ Configuración básica válida", fg="green")
                    messagebox.showinfo("Éxito", "Configuración básica de email válida")
                    
            except Exception as e:
                status_label.config(text="Estado: ✗ Error de conexión", fg="red")
                messagebox.showerror("Error", f"Error probando configuración:\n{str(e)}")
            finally:
                test_button.config(state="normal", text="Probar Configuración")
        
        # Run test in separate thread to avoid blocking UI
        threading.Thread(target=run_test, daemon=True).start()
    
    def guardar_config():
        """Save email configuration"""
        try:
            config = {
                "provider": provider_var.get(),
                "sender_email": email_entry.get(),
                "sender_password": password_entry.get(),
                "smtp_server": smtp_entry.get(),
                "smtp_port": int(port_entry.get()),
                "use_tls": True,
                "auth_method": "app_password",
                "timeout": 30,
                "max_retries": 3
            }
            
            if guardar_config_email(config):
                messagebox.showinfo("Éxito", "Configuración guardada correctamente")
                if inicializar_servicio_email():
                    messagebox.showinfo("Éxito", "Servicio de email reinicializado")
                    status_label.config(text="Estado: ✓ Configuración guardada y activa", fg="green")
                config_window.destroy()
            else:
                messagebox.showerror("Error", "No se pudo guardar la configuración")
                
        except ValueError:
            messagebox.showerror("Error", "Puerto debe ser un número válido")
        except Exception as e:
            messagebox.showerror("Error", f"Error guardando configuración: {str(e)}")
    
    def mostrar_ayuda_provider():
        """Show help for selected provider"""
        provider = provider_var.get()
        help_texts = {
            "gmail": """Gmail Configuration Help:
            
1. Enable 2-Factor Authentication in your Google Account
2. Generate an App Password:
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Generate password for 'Mail'
3. Use the App Password (not your regular password)
4. SMTP Server: smtp.gmail.com
5. Port: 587 (TLS) or 465 (SSL)""",
            
            "outlook": """Outlook Configuration Help:
            
1. Use your Outlook.com email and password
2. For better security, enable 2FA and use App Password
3. SMTP Server: smtp-mail.outlook.com
4. Port: 587 (TLS)
5. Supports OAuth2 for enhanced security""",
            
            "yahoo": """Yahoo Configuration Help:
            
1. Enable 2-Factor Authentication
2. Generate an App Password:
   - Go to Yahoo Account Security
   - Generate app password for 'Mail'
3. Use the App Password (not your regular password)
4. SMTP Server: smtp.mail.yahoo.com
5. Port: 587 (TLS) or 465 (SSL)""",
            
            "custom": """Custom SMTP Configuration Help:
            
1. Enter your SMTP server address
2. Enter the correct port (usually 587 for TLS, 465 for SSL)
3. Use your email credentials
4. Ensure your server supports TLS/SSL
5. Check with your email provider for specific settings"""
        }
        
        messagebox.showinfo("Ayuda", help_texts.get(provider, "No hay ayuda disponible"))
    
    # Load current configuration
    current_config = cargar_config_email()
    
    config_window = tk.Toplevel()
    config_window.title("Configuración Avanzada de Email")
    config_window.geometry("500x700")
    config_window.configure(bg="#f0f0f0")
    
    # Title
    title_label = tk.Label(config_window, text="Configuración de Email", 
                          font=("Arial", 16, "bold"), bg="#f0f0f0")
    title_label.pack(pady=10)
    
    # Status display
    status_label = tk.Label(config_window, text="Estado: Configuración no probada", 
                           fg="gray", bg="#f0f0f0")
    status_label.pack(pady=5)
    
    # Provider selection frame
    provider_frame = tk.LabelFrame(config_window, text="Proveedor de Email", 
                                  font=("Arial", 12, "bold"), bg="#f0f0f0")
    provider_frame.pack(pady=10, padx=20, fill="x")
    
    provider_var = tk.StringVar(value=current_config.get("provider", "gmail"))
    providers = [
        ("Gmail", "gmail"),
        ("Outlook/Hotmail", "outlook"),
        ("Yahoo", "yahoo"),
        ("Servidor Personalizado", "custom")
    ]
    
    for text, value in providers:
        rb = tk.Radiobutton(provider_frame, text=text, variable=provider_var, 
                           value=value, command=actualizar_campos_provider, bg="#f0f0f0")
        rb.pack(anchor="w", padx=10, pady=2)
    
    # Help button for provider
    help_button = tk.Button(provider_frame, text="Ayuda", command=mostrar_ayuda_provider,
                           bg="#e0e0e0")
    help_button.pack(pady=5)
    
    # Email configuration frame
    config_frame = tk.LabelFrame(config_window, text="Configuración", 
                                font=("Arial", 12, "bold"), bg="#f0f0f0")
    config_frame.pack(pady=10, padx=20, fill="x")
    
    # Email field
    tk.Label(config_frame, text="Email:", bg="#f0f0f0").pack(anchor="w", padx=10)
    email_entry = tk.Entry(config_frame, width=50)
    email_entry.pack(padx=10, pady=2)
    email_entry.insert(0, current_config.get("sender_email", ""))
    
    # Password field
    tk.Label(config_frame, text="Password/App Password:", bg="#f0f0f0").pack(anchor="w", padx=10)
    password_entry = tk.Entry(config_frame, width=50, show="*")
    password_entry.pack(padx=10, pady=2)
    password_entry.insert(0, current_config.get("sender_password", ""))
    
    # SMTP Server field
    tk.Label(config_frame, text="Servidor SMTP:", bg="#f0f0f0").pack(anchor="w", padx=10)
    smtp_entry = tk.Entry(config_frame, width=50)
    smtp_entry.pack(padx=10, pady=2)
    smtp_entry.insert(0, current_config.get("smtp_server", ""))
    
    # Port field
    tk.Label(config_frame, text="Puerto:", bg="#f0f0f0").pack(anchor="w", padx=10)
    port_entry = tk.Entry(config_frame, width=10)
    port_entry.pack(padx=10, pady=2)
    port_entry.insert(0, str(current_config.get("smtp_port", 587)))
    
    # Initialize fields based on current provider
    actualizar_campos_provider()
    
    # Buttons frame
    buttons_frame = tk.Frame(config_window, bg="#f0f0f0")
    buttons_frame.pack(pady=20)
    
    test_button = tk.Button(buttons_frame, text="Probar Configuración", 
                           command=test_email_config, bg="#4CAF50", fg="white",
                           font=("Arial", 10, "bold"))
    test_button.pack(side="left", padx=10)
    
    save_button = tk.Button(buttons_frame, text="Guardar", command=guardar_config,
                           bg="#2196F3", fg="white", font=("Arial", 10, "bold"))
    save_button.pack(side="left", padx=10)
    
    cancel_button = tk.Button(buttons_frame, text="Cancelar", 
                             command=config_window.destroy, bg="#f44336", fg="white",
                             font=("Arial", 10, "bold"))
    cancel_button.pack(side="left", padx=10)

# Initialize email service on startup
print("Initializing email service...")
inicializar_servicio_email()

root = tk.Tk()
root.title("Sistema de Detección de Sueño - Versión Mejorada")
root.geometry("350x250")

# Show email service status
email_status = "Email Service: Activo" if email_service else "Email Service: Básico"
status_label = tk.Label(root, text=email_status, fg="green" if email_service else "orange")
status_label.pack(pady=5)

tk.Button(root, text="Registrar Usuario", command=ventana_registro).pack(pady=10)
tk.Button(root, text="Iniciar Sesión", command=ventana_inicio).pack(pady=10)
tk.Button(root, text="Configurar Email", command=ventana_config_email).pack(pady=10)

root.mainloop()
