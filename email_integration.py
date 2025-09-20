"""
Email Integration Module

This module provides backward-compatible email functionality that automatically
uses the enhanced EmailServiceManager when available, or falls back to basic
email functionality for existing code.

Usage:
    from email_integration import enviar_correo, inicializar_email_service
    
    # Initialize the service (optional, will auto-initialize if not called)
    inicializar_email_service()
    
    # Send email (works with both enhanced and basic functionality)
    enviar_correo("Usuario", "usuario@email.com")
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
import os
from datetime import datetime
from typing import Optional, Dict, Any
import numpy as np

# Try to import the enhanced email service
try:
    from email_service import (
        EmailServiceManagerImpl, EmailConfig, UserData, AlertData,
        ProviderType, AuthMethod, AlertType
    )
    EMAIL_SERVICE_AVAILABLE = True
except ImportError:
    EMAIL_SERVICE_AVAILABLE = False

# Global email service instance
_email_service: Optional[EmailServiceManagerImpl] = None
_email_config: Optional[Dict[str, Any]] = None

# Default configuration
DEFAULT_EMAIL_CONFIG = {
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

def obtener_signos_vitales():
    """Simulate vital signs - compatible with existing code"""
    frecuencia_cardiaca = np.random.randint(60, 100)
    oxigenacion = np.random.randint(90, 100)
    return frecuencia_cardiaca, oxigenacion

def cargar_config_email(config_file: str = "email_config.json") -> Dict[str, Any]:
    """Load email configuration from file"""
    if os.path.exists(config_file):
        try:
            with open(config_file, "r") as f:
                config = json.load(f)
                return {**DEFAULT_EMAIL_CONFIG, **config}
        except Exception as e:
            print(f"Error loading email config: {e}")
    
    return DEFAULT_EMAIL_CONFIG.copy()

def guardar_config_email(config: Dict[str, Any], config_file: str = "email_config.json") -> bool:
    """Save email configuration to file"""
    try:
        with open(config_file, "w") as f:
            json.dump(config, f, indent=4)
        return True
    except Exception as e:
        print(f"Error saving email config: {e}")
        return False

def inicializar_email_service(config_file: str = "email_config.json", 
                             sender_email: str = "", 
                             sender_password: str = "") -> bool:
    """
    Initialize the email service with configuration
    
    Args:
        config_file: Path to email configuration file
        sender_email: Fallback sender email if not in config
        sender_password: Fallback sender password if not in config
        
    Returns:
        bool: True if enhanced service initialized, False if using basic
    """
    global _email_service, _email_config
    
    if not EMAIL_SERVICE_AVAILABLE:
        print("Enhanced email service not available, using basic email")
        return False
    
    try:
        # Load configuration
        _email_config = cargar_config_email(config_file)
        
        # Use fallback credentials if not in config
        if not _email_config["sender_email"] and sender_email:
            _email_config["sender_email"] = sender_email
        if not _email_config["sender_password"] and sender_password:
            _email_config["sender_password"] = sender_password
        
        # Check if email configuration is complete
        if not _email_config["sender_email"] or not _email_config["sender_password"]:
            print("Email configuration incomplete - using basic email fallback")
            return False
        
        # Create email service manager
        _email_service = EmailServiceManagerImpl()
        
        # Create email configuration
        email_config = EmailConfig(
            provider=ProviderType(_email_config["provider"]),
            smtp_server=_email_config["smtp_server"],
            smtp_port=_email_config["smtp_port"],
            use_tls=_email_config["use_tls"],
            sender_email=_email_config["sender_email"],
            sender_password=_email_config["sender_password"],
            auth_method=AuthMethod(_email_config["auth_method"]),
            timeout=_email_config["timeout"],
            max_retries=_email_config["max_retries"]
        )
        
        # Initialize service
        success = _email_service.initialize(email_config)
        
        if success:
            print("Enhanced email service initialized successfully")
            return True
        else:
            print("Failed to initialize enhanced email service, using basic email")
            _email_service = None
            return False
            
    except Exception as e:
        print(f"Error initializing enhanced email service: {e}")
        _email_service = None
        return False

def enviar_correo(nombre_usuario: str, correo_usuario: str, 
                 sender_email: str = "", sender_password: str = "") -> bool:
    """
    Send email using enhanced service if available, otherwise basic email
    
    Args:
        nombre_usuario: User's name
        correo_usuario: User's email address
        sender_email: Fallback sender email for basic functionality
        sender_password: Fallback sender password for basic functionality
        
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    global _email_service
    
    # Auto-initialize if not already done
    if _email_service is None and EMAIL_SERVICE_AVAILABLE:
        inicializar_email_service(sender_email=sender_email, sender_password=sender_password)
    
    # Try enhanced email service first
    if _email_service:
        try:
            return _enviar_correo_mejorado(nombre_usuario, correo_usuario)
        except Exception as e:
            print(f"Error with enhanced email service, falling back to basic: {e}")
    
    # Fallback to basic email functionality
    return _enviar_correo_basico(nombre_usuario, correo_usuario, sender_email, sender_password)

def _enviar_correo_mejorado(nombre_usuario: str, correo_usuario: str) -> bool:
    """Send enhanced email using EmailServiceManager"""
    global _email_service
    
    if not _email_service:
        return False
    
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
                "detection_method": "integrated_system",
                "system_version": "email_integration_v1.0"
            }
        )
        
        # Send email through service manager
        result = _email_service.send_alert_email(user_data, alert_data)
        
        if result.success:
            print(f"Enhanced email sent successfully: {result.message}")
            if result.email_id:
                print(f"Email ID: {result.email_id}")
            return True
        else:
            print(f"Error sending enhanced email: {result.message}")
            return False
            
    except Exception as e:
        print(f"Error in enhanced email sending: {e}")
        return False

def _enviar_correo_basico(nombre_usuario: str, correo_usuario: str, 
                         sender_email: str = "", sender_password: str = "") -> bool:
    """Send basic email for backward compatibility"""
    global _email_config
    
    # Use config or fallback credentials
    if _email_config:
        email = _email_config["sender_email"]
        password = _email_config["sender_password"]
        smtp_server = _email_config["smtp_server"]
        smtp_port = _email_config["smtp_port"]
    else:
        email = sender_email
        password = sender_password
        smtp_server = "smtp.gmail.com"
        smtp_port = 465
    
    if not email or not password:
        print("No email credentials available for basic email")
        return False
    
    try:
        frecuencia_cardiaca, oxigenacion = obtener_signos_vitales()
        body = f"El usuario {nombre_usuario} se ha dormido.\n\nSignos vitales:\nFrecuencia Cardiaca: {frecuencia_cardiaca} BPM\nOxigenación: {oxigenacion}%"

        message = MIMEMultipart()
        message["From"] = email
        message["To"] = correo_usuario
        message["Subject"] = "¡Alerta! Detección de sueño"
        message.attach(MIMEText(body, "plain"))
        
        # Use appropriate SMTP configuration
        if smtp_port == 465:
            server = smtplib.SMTP_SSL(smtp_server, smtp_port)
        else:
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
        
        server.login(email, password)
        server.sendmail(email, correo_usuario, message.as_string())
        server.quit()
        print("Basic email sent successfully.")
        return True
        
    except Exception as e:
        print(f"Error sending basic email: {e}")
        return False

def test_email_configuration() -> bool:
    """Test the current email configuration"""
    global _email_service
    
    if _email_service:
        try:
            test_result = _email_service.test_email_configuration()
            if test_result.success:
                print("Enhanced email configuration test passed")
                return True
            else:
                print(f"Enhanced email configuration test failed: {test_result.error_messages}")
                return False
        except Exception as e:
            print(f"Error testing enhanced email configuration: {e}")
            return False
    else:
        print("Enhanced email service not available for testing")
        return False

def get_email_service_status() -> Dict[str, Any]:
    """Get current email service status"""
    global _email_service, _email_config
    
    status = {
        "enhanced_service_available": EMAIL_SERVICE_AVAILABLE,
        "enhanced_service_initialized": _email_service is not None,
        "configuration_loaded": _email_config is not None,
        "service_type": "enhanced" if _email_service else "basic"
    }
    
    if _email_service:
        try:
            service_status = _email_service.get_service_status()
            status.update(service_status)
        except Exception as e:
            status["service_error"] = str(e)
    
    return status

# Backward compatibility aliases
enviar_correo_mejorado = _enviar_correo_mejorado
enviar_correo_basico = _enviar_correo_basico