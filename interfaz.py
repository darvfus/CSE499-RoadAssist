# interfaz.py
import tkinter as tk
from tkinter import messagebox, ttk
import threading
import main
import db
import json
import os
from datetime import datetime
from typing import Optional, Dict, Any
import time

# Import email service components
try:
    from email_service import (
        EmailServiceManagerImpl, EmailConfig, UserData, AlertData,
        ProviderType, AuthMethod, AlertType, TestResult, DeliveryStatusType
    )
    EMAIL_SERVICE_AVAILABLE = True
except ImportError:
    print("Email service not available, using basic email functionality")
    EMAIL_SERVICE_AVAILABLE = False

db.crear_tabla()  # asegurar tabla creada al inicio

# Global variables for email status tracking
email_delivery_status = {}
email_status_window = None
email_service_manager = None
current_email_config = None

def inicializar_servicio_email_startup():
    """Initialize email service on startup if configuration exists"""
    global email_service_manager, current_email_config
    
    if not EMAIL_SERVICE_AVAILABLE:
        return
    
    try:
        # Try to load existing configuration from main.py
        import main
        if hasattr(main, 'email_service') and main.email_service:
            email_service_manager = main.email_service
            print("Email service loaded from main module")
        else:
            # Try to initialize from saved configuration
            config_file = "email_config.json"
            if os.path.exists(config_file):
                import json
                with open(config_file, 'r') as f:
                    config_data = json.load(f)
                
                if config_data.get('sender_email') and config_data.get('sender_password'):
                    email_config = EmailConfig(
                        provider=ProviderType(config_data.get('provider', 'gmail')),
                        smtp_server=config_data.get('smtp_server', 'smtp.gmail.com'),
                        smtp_port=config_data.get('smtp_port', 587),
                        use_tls=config_data.get('use_tls', True),
                        sender_email=config_data['sender_email'],
                        sender_password=config_data['sender_password'],
                        auth_method=AuthMethod(config_data.get('auth_method', 'app_password'))
                    )
                    
                    email_service_manager = EmailServiceManagerImpl()
                    if email_service_manager.initialize(email_config):
                        current_email_config = email_config
                        print("Email service initialized from saved configuration")
                    else:
                        email_service_manager = None
                        print("Failed to initialize email service from saved configuration")
    except Exception as e:
        print(f"Error initializing email service on startup: {e}")

# Initialize email service on startup
inicializar_servicio_email_startup()

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
    
    # Check email service status before starting
    if EMAIL_SERVICE_AVAILABLE and not email_service_manager:
        respuesta = messagebox.askyesno(
            "Email no configurado", 
            "El servicio de email no está configurado. ¿Desea continuar sin notificaciones por email?"
        )
        if not respuesta:
            return
    
    main.deteniendo = False
    threading.Thread(target=main.iniciar_deteccion, args=(nombre_usuario, correo_usuario), daemon=True).start()
    
    # Show status message
    if EMAIL_SERVICE_AVAILABLE and email_service_manager:
        messagebox.showinfo("Iniciado", f"Detección iniciada para {nombre_usuario}\nNotificaciones por email: Activas")
    else:
        messagebox.showinfo("Iniciado", f"Detección iniciada para {nombre_usuario}\nNotificaciones por email: Desactivadas")

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

def abrir_configuracion_email():
    """Open email configuration window"""
    if not EMAIL_SERVICE_AVAILABLE:
        messagebox.showerror("Error", "Email service not available")
        return
    
    config_window = tk.Toplevel(ventana)
    config_window.title("Configuración de Email")
    config_window.geometry("500x600")
    config_window.configure(bg="#1e1e2e")
    config_window.resizable(False, False)
    
    # Make window modal
    config_window.transient(ventana)
    config_window.grab_set()
    
    # Title
    title_label = tk.Label(config_window, text="Configuración de Email", 
                          font=("Arial", 14, "bold"), fg="white", bg="#1e1e2e")
    title_label.pack(pady=10)
    
    # Provider selection
    provider_frame = tk.Frame(config_window, bg="#1e1e2e")
    provider_frame.pack(pady=10, padx=20, fill="x")
    
    tk.Label(provider_frame, text="Proveedor de Email:", 
             font=("Arial", 10), fg="white", bg="#1e1e2e").pack(anchor="w")
    
    provider_var = tk.StringVar(value="gmail")
    provider_combo = ttk.Combobox(provider_frame, textvariable=provider_var, 
                                 values=["gmail", "outlook", "yahoo", "custom"], 
                                 state="readonly", width=30)
    provider_combo.pack(pady=5, fill="x")
    
    # Email configuration fields
    fields_frame = tk.Frame(config_window, bg="#1e1e2e")
    fields_frame.pack(pady=10, padx=20, fill="both", expand=True)
    
    # Sender email
    tk.Label(fields_frame, text="Email del remitente:", 
             font=("Arial", 10), fg="white", bg="#1e1e2e").pack(anchor="w")
    sender_email_entry = tk.Entry(fields_frame, font=("Arial", 10), width=40)
    sender_email_entry.pack(pady=5, fill="x")
    
    # Password
    tk.Label(fields_frame, text="Contraseña/App Password:", 
             font=("Arial", 10), fg="white", bg="#1e1e2e").pack(anchor="w")
    password_entry = tk.Entry(fields_frame, font=("Arial", 10), width=40, show="*")
    password_entry.pack(pady=5, fill="x")
    
    # SMTP Server (for custom)
    smtp_server_label = tk.Label(fields_frame, text="Servidor SMTP:", 
                                font=("Arial", 10), fg="white", bg="#1e1e2e")
    smtp_server_entry = tk.Entry(fields_frame, font=("Arial", 10), width=40)
    
    # SMTP Port (for custom)
    smtp_port_label = tk.Label(fields_frame, text="Puerto SMTP:", 
                              font=("Arial", 10), fg="white", bg="#1e1e2e")
    smtp_port_entry = tk.Entry(fields_frame, font=("Arial", 10), width=40)
    
    # TLS checkbox
    use_tls_var = tk.BooleanVar(value=True)
    tls_checkbox = tk.Checkbutton(fields_frame, text="Usar TLS", 
                                 variable=use_tls_var, fg="white", bg="#1e1e2e",
                                 selectcolor="#1e1e2e")
    
    def on_provider_change(*args):
        """Handle provider selection change"""
        provider = provider_var.get()
        
        if provider == "custom":
            smtp_server_label.pack(anchor="w", pady=(10, 0))
            smtp_server_entry.pack(pady=5, fill="x")
            smtp_port_label.pack(anchor="w")
            smtp_port_entry.pack(pady=5, fill="x")
            tls_checkbox.pack(anchor="w", pady=5)
        else:
            smtp_server_label.pack_forget()
            smtp_server_entry.pack_forget()
            smtp_port_label.pack_forget()
            smtp_port_entry.pack_forget()
            tls_checkbox.pack_forget()
            
            # Set default values for known providers
            if provider == "gmail":
                smtp_server_entry.delete(0, tk.END)
                smtp_server_entry.insert(0, "smtp.gmail.com")
                smtp_port_entry.delete(0, tk.END)
                smtp_port_entry.insert(0, "587")
                use_tls_var.set(True)
            elif provider == "outlook":
                smtp_server_entry.delete(0, tk.END)
                smtp_server_entry.insert(0, "smtp-mail.outlook.com")
                smtp_port_entry.delete(0, tk.END)
                smtp_port_entry.insert(0, "587")
                use_tls_var.set(True)
            elif provider == "yahoo":
                smtp_server_entry.delete(0, tk.END)
                smtp_server_entry.insert(0, "smtp.mail.yahoo.com")
                smtp_port_entry.delete(0, tk.END)
                smtp_port_entry.insert(0, "587")
                use_tls_var.set(True)
    
    provider_var.trace("w", on_provider_change)
    on_provider_change()  # Initialize
    
    # Status display
    status_frame = tk.Frame(config_window, bg="#1e1e2e")
    status_frame.pack(pady=10, padx=20, fill="x")
    
    status_label = tk.Label(status_frame, text="Estado: No configurado", 
                           font=("Arial", 10), fg="yellow", bg="#1e1e2e")
    status_label.pack(anchor="w")
    
    # Buttons
    button_frame = tk.Frame(config_window, bg="#1e1e2e")
    button_frame.pack(pady=20, padx=20, fill="x")
    
    def test_configuration():
        """Test email configuration"""
        try:
            # Create configuration
            provider_type = ProviderType(provider_var.get())
            
            if provider_var.get() == "custom":
                smtp_server = smtp_server_entry.get().strip()
                smtp_port = int(smtp_port_entry.get().strip()) if smtp_port_entry.get().strip() else 587
                use_tls = use_tls_var.get()
            else:
                if provider_var.get() == "gmail":
                    smtp_server = "smtp.gmail.com"
                    smtp_port = 587
                elif provider_var.get() == "outlook":
                    smtp_server = "smtp-mail.outlook.com"
                    smtp_port = 587
                elif provider_var.get() == "yahoo":
                    smtp_server = "smtp.mail.yahoo.com"
                    smtp_port = 587
                use_tls = True
            
            config = EmailConfig(
                provider=provider_type,
                smtp_server=smtp_server,
                smtp_port=smtp_port,
                use_tls=use_tls,
                sender_email=sender_email_entry.get().strip(),
                sender_password=password_entry.get(),
                auth_method=AuthMethod.APP_PASSWORD
            )
            
            # Initialize email service manager if not already done
            global email_service_manager
            if not email_service_manager:
                email_service_manager = EmailServiceManagerImpl()
            
            # Test configuration
            status_label.config(text="Estado: Probando configuración...", fg="yellow")
            config_window.update()
            
            # Initialize with config
            if email_service_manager.initialize(config):
                test_result = email_service_manager.test_email_configuration()
                
                if test_result.success:
                    status_label.config(text="Estado: Configuración válida ✓", fg="green")
                    messagebox.showinfo("Éxito", "Configuración de email probada exitosamente")
                else:
                    error_msg = "\n".join(test_result.error_messages)
                    status_label.config(text="Estado: Error en configuración ✗", fg="red")
                    messagebox.showerror("Error", f"Error en configuración:\n{error_msg}")
            else:
                status_label.config(text="Estado: Error de inicialización ✗", fg="red")
                messagebox.showerror("Error", "Error al inicializar el servicio de email")
                
        except Exception as e:
            status_label.config(text="Estado: Error ✗", fg="red")
            messagebox.showerror("Error", f"Error al probar configuración: {str(e)}")
    
    def save_configuration():
        """Save email configuration"""
        try:
            # Create configuration
            provider_type = ProviderType(provider_var.get())
            
            if provider_var.get() == "custom":
                smtp_server = smtp_server_entry.get().strip()
                smtp_port = int(smtp_port_entry.get().strip()) if smtp_port_entry.get().strip() else 587
                use_tls = use_tls_var.get()
            else:
                if provider_var.get() == "gmail":
                    smtp_server = "smtp.gmail.com"
                    smtp_port = 587
                elif provider_var.get() == "outlook":
                    smtp_server = "smtp-mail.outlook.com"
                    smtp_port = 587
                elif provider_var.get() == "yahoo":
                    smtp_server = "smtp.mail.yahoo.com"
                    smtp_port = 587
                use_tls = True
            
            config = EmailConfig(
                provider=provider_type,
                smtp_server=smtp_server,
                smtp_port=smtp_port,
                use_tls=use_tls,
                sender_email=sender_email_entry.get().strip(),
                sender_password=password_entry.get(),
                auth_method=AuthMethod.APP_PASSWORD
            )
            
            # Initialize email service manager if not already done
            global email_service_manager, current_email_config
            if not email_service_manager:
                email_service_manager = EmailServiceManagerImpl()
            
            # Initialize with config
            if email_service_manager.initialize(config):
                current_email_config = config
                messagebox.showinfo("Éxito", "Configuración de email guardada exitosamente")
                config_window.destroy()
            else:
                messagebox.showerror("Error", "Error al guardar la configuración")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar configuración: {str(e)}")
    
    # Test button
    test_btn = tk.Button(button_frame, text="Probar Configuración", 
                        font=("Arial", 10, "bold"), bg="#FFA500", fg="white",
                        command=test_configuration)
    test_btn.pack(side="left", padx=5)
    
    # Save button
    save_btn = tk.Button(button_frame, text="Guardar", 
                        font=("Arial", 10, "bold"), bg="#4CAF50", fg="white",
                        command=save_configuration)
    save_btn.pack(side="left", padx=5)
    
    # Cancel button
    cancel_btn = tk.Button(button_frame, text="Cancelar", 
                          font=("Arial", 10, "bold"), bg="#E53935", fg="white",
                          command=config_window.destroy)
    cancel_btn.pack(side="right", padx=5)

def mostrar_estado_email():
    """Show email delivery status window"""
    global email_status_window
    
    if email_status_window and email_status_window.winfo_exists():
        email_status_window.lift()
        return
    
    email_status_window = tk.Toplevel(ventana)
    email_status_window.title("Estado de Entrega de Emails")
    email_status_window.geometry("600x400")
    email_status_window.configure(bg="#1e1e2e")
    
    # Title
    title_label = tk.Label(email_status_window, text="Estado de Entrega de Emails", 
                          font=("Arial", 14, "bold"), fg="white", bg="#1e1e2e")
    title_label.pack(pady=10)
    
    # Create treeview for email status
    columns = ("ID", "Destinatario", "Estado", "Intentos", "Tiempo")
    tree_frame = tk.Frame(email_status_window, bg="#1e1e2e")
    tree_frame.pack(pady=10, padx=20, fill="both", expand=True)
    
    tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)
    
    # Configure columns
    tree.heading("ID", text="ID Email")
    tree.heading("Destinatario", text="Destinatario")
    tree.heading("Estado", text="Estado")
    tree.heading("Intentos", text="Intentos")
    tree.heading("Tiempo", text="Tiempo")
    
    tree.column("ID", width=100)
    tree.column("Destinatario", width=200)
    tree.column("Estado", width=100)
    tree.column("Intentos", width=80)
    tree.column("Tiempo", width=120)
    
    # Scrollbar
    scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    
    tree.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    
    # Status info
    info_frame = tk.Frame(email_status_window, bg="#1e1e2e")
    info_frame.pack(pady=10, padx=20, fill="x")
    
    status_info_label = tk.Label(info_frame, text="Total emails: 0 | Exitosos: 0 | Fallidos: 0", 
                                font=("Arial", 10), fg="white", bg="#1e1e2e")
    status_info_label.pack()
    
    def actualizar_estado():
        """Update email status display"""
        # Clear existing items
        for item in tree.get_children():
            tree.delete(item)
        
        # Add current email statuses
        total = len(email_delivery_status)
        exitosos = sum(1 for status in email_delivery_status.values() if status.get('success', False))
        fallidos = total - exitosos
        
        for email_id, status in email_delivery_status.items():
            estado_texto = "Exitoso" if status.get('success', False) else "Fallido"
            if status.get('sending', False):
                estado_texto = "Enviando..."
            elif status.get('queued', False):
                estado_texto = "En cola"
            
            tree.insert("", "end", values=(
                email_id[:8] + "...",  # Shortened ID
                status.get('recipient', 'N/A'),
                estado_texto,
                status.get('attempts', 0),
                status.get('timestamp', 'N/A')
            ))
        
        status_info_label.config(text=f"Total emails: {total} | Exitosos: {exitosos} | Fallidos: {fallidos}")
        
        # Schedule next update
        email_status_window.after(2000, actualizar_estado)
    
    # Buttons
    button_frame = tk.Frame(email_status_window, bg="#1e1e2e")
    button_frame.pack(pady=10)
    
    refresh_btn = tk.Button(button_frame, text="Actualizar", 
                           font=("Arial", 10, "bold"), bg="#2196F3", fg="white",
                           command=actualizar_estado)
    refresh_btn.pack(side="left", padx=5)
    
    clear_btn = tk.Button(button_frame, text="Limpiar", 
                         font=("Arial", 10, "bold"), bg="#FF9800", fg="white",
                         command=lambda: email_delivery_status.clear() or actualizar_estado())
    clear_btn.pack(side="left", padx=5)
    
    close_btn = tk.Button(button_frame, text="Cerrar", 
                         font=("Arial", 10, "bold"), bg="#E53935", fg="white",
                         command=email_status_window.destroy)
    close_btn.pack(side="right", padx=5)
    
    # Start updating
    actualizar_estado()

def actualizar_estado_email(email_id: str, recipient: str, success: bool, attempts: int = 1, error_message: str = None):
    """Update email delivery status"""
    global email_delivery_status
    
    email_delivery_status[email_id] = {
        'recipient': recipient,
        'success': success,
        'attempts': attempts,
        'timestamp': datetime.now().strftime("%H:%M:%S"),
        'error_message': error_message,
        'sending': False,
        'queued': False
    }

def marcar_email_enviando(email_id: str, recipient: str):
    """Mark email as currently being sent"""
    global email_delivery_status
    
    email_delivery_status[email_id] = {
        'recipient': recipient,
        'success': False,
        'attempts': 0,
        'timestamp': datetime.now().strftime("%H:%M:%S"),
        'sending': True,
        'queued': False
    }

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

# Email configuration section
if EMAIL_SERVICE_AVAILABLE:
    label_email_config = tk.Label(ventana, text="Configuración de Email", font=("Arial", 12, "bold"), fg="cyan", bg="#1e1e2e")
    label_email_config.pack(pady=(20, 5))
    
    # Email service status indicator
    def actualizar_estado_servicio():
        """Update email service status display"""
        if email_service_manager and current_email_config:
            status_text = "Estado: Servicio configurado ✓"
            status_color = "green"
        elif email_service_manager:
            status_text = "Estado: Servicio disponible"
            status_color = "yellow"
        else:
            status_text = "Estado: No configurado"
            status_color = "orange"
        
        email_status_indicator.config(text=status_text, fg=status_color)
        ventana.after(5000, actualizar_estado_servicio)  # Update every 5 seconds
    
    email_status_indicator = tk.Label(ventana, text="Estado: Verificando...", font=("Arial", 9), fg="gray", bg="#1e1e2e")
    email_status_indicator.pack(pady=2)
    
    btn_config_email = tk.Button(ventana, text="Configurar Email", font=("Arial", 10, "bold"), bg="#9C27B0", fg="white", command=abrir_configuracion_email)
    btn_config_email.pack(pady=2)
    
    btn_estado_email = tk.Button(ventana, text="Estado de Emails", font=("Arial", 10, "bold"), bg="#FF5722", fg="white", command=mostrar_estado_email)
    btn_estado_email.pack(pady=2)
    
    # Start status updates
    actualizar_estado_servicio()

ventana.mainloop()
