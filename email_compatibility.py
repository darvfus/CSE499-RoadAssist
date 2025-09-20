#!/usr/bin/env python3
"""
Email Compatibility Module

This module provides backward compatibility by wrapping the existing enviar_correo
function to use the new EmailServiceManager while maintaining the same interface.
"""

import os
import json
from datetime import datetime
from typing import Optional

from email_service import (
    EmailServiceManagerImpl, EmailConfig, UserData, AlertData,
    ProviderType, AuthMethod, AlertType
)

# Global email service instance
_email_service: Optional[EmailServiceManagerImpl] = None
_initialized = False

def _load_email_config() -> Optional[EmailConfig]:
    """Load email configuration from file or environment"""
    config_file = "email_config.json"
    
    # Try to load from config file
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                config_data = json.load(f)
                
            return EmailConfig(
                provider=ProviderType(config_data.get("provider", "gmail")),
                smtp_server=config_data.get("smtp_server", "smtp.gmail.com"),
                smtp_port=config_data.get("smtp_port", 587),
                use_tls=config_data.get("use_tls", True),
                sender_email=config_data.get("sender_email", ""),
                sender_password=config_data.get("sender_password", ""),
                auth_method=AuthMethod(config_data.get("auth_method", "app_password")),
                timeout=config_data.get("timeout", 30),
                max_retries=config_data.get("max_retries", 3)
            )
        except Exception as e:
            print(f"Error loading email config: {e}")
    
    # Try to load from environment variables
    sender_email = os.getenv("EMAIL_SENDER")
    sender_password = os.getenv("EMAIL_PASSWORD")
    
    if sender_email and sender_password:
        return EmailConfig(
            provider=ProviderType.GMAIL,
            smtp_server="smtp.gmail.com",
            smtp_port=587,
            use_tls=True,
            sender_email=sender_email,
            sender_password=sender_password,
            auth_method=AuthMethod.APP_PASSWORD,
            timeout=30,
            max_retries=3
        )
    
    return None

def _initialize_email_service() -> bool:
    """Initialize the email service if not already initialized"""
    global _email_service, _initialized
    
    if _initialized:
        return _email_service is not None
    
    _initialized = True
    
    try:
        config = _load_email_config()
        if not config:
            print("No email configuration found - enhanced email service disabled")
            return False
        
        _email_service = EmailServiceManagerImpl()
        success = _email_service.initialize(config)
        
        if success:
            print("Enhanced email service initialized successfully")
            return True
        else:
            print("Failed to initialize enhanced email service")
            _email_service = None
            return False
            
    except Exception as e:
        print(f"Error initializing enhanced email service: {e}")
        _email_service = None
        return False

def enviar_correo(nombre_usuario: str, correo_usuario: str) -> bool:
    """
    Enhanced version of enviar_correo that uses EmailServiceManager
    
    This function maintains backward compatibility with the original interface
    while providing enhanced functionality through the new email service.
    
    Args:
        nombre_usuario: User's name
        correo_usuario: User's email address
        
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    # Try to use enhanced email service
    if _initialize_email_service() and _email_service:
        try:
            # Get simulated vital signs (in real implementation, this would come from sensors)
            import numpy as np
            frecuencia_cardiaca = np.random.randint(60, 100)
            oxigenacion = np.random.randint(90, 100)
            
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
                    "detection_method": "compatibility_wrapper",
                    "system_version": "enhanced_v1.0"
                }
            )
            
            # Send email through enhanced service
            result = _email_service.send_alert_email(user_data, alert_data)
            
            if result.success:
                print(f"Enhanced email sent successfully: {result.message}")
                return True
            else:
                print(f"Enhanced email failed: {result.message}")
                # Fall back to basic email
                return _enviar_correo_basico(nombre_usuario, correo_usuario)
                
        except Exception as e:
            print(f"Error in enhanced email service: {e}")
            # Fall back to basic email
            return _enviar_correo_basico(nombre_usuario, correo_usuario)
    
    # Fall back to basic email implementation
    return _enviar_correo_basico(nombre_usuario, correo_usuario)

def _enviar_correo_basico(nombre_usuario: str, correo_usuario: str) -> bool:
    """
    Basic email implementation (fallback)
    
    This is the original email implementation for backward compatibility
    when the enhanced service is not available.
    """
    import smtplib
    import numpy as np
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    
    # Basic configuration - should be replaced with actual values
    SENDER_EMAIL = "your_email@gmail.com"  # Replace with actual email
    PASSWORD = "your_app_password"  # Replace with actual app password
    
    try:
        # Simulate vital signs
        frecuencia_cardiaca = np.random.randint(60, 100)
        oxigenacion = np.random.randint(90, 100)
        
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
        
        print("Basic email sent successfully.")
        return True
        
    except Exception as e:
        print(f"Error sending basic email: {e}")
        return False

def get_email_service_status() -> dict:
    """
    Get the status of the email service
    
    Returns:
        dict: Status information about the email service
    """
    _initialize_email_service()
    
    if _email_service:
        try:
            return _email_service.get_service_status()
        except Exception as e:
            return {
                "initialized": False,
                "error": str(e),
                "fallback": "basic_email"
            }
    else:
        return {
            "initialized": False,
            "service": "basic_email",
            "reason": "enhanced_service_not_available"
        }

def test_email_configuration() -> bool:
    """
    Test the current email configuration
    
    Returns:
        bool: True if configuration is valid, False otherwise
    """
    if _initialize_email_service() and _email_service:
        try:
            test_result = _email_service.test_email_configuration()
            return test_result.success
        except Exception as e:
            print(f"Error testing email configuration: {e}")
            return False
    else:
        print("Enhanced email service not available for testing")
        return False

# Backward compatibility aliases
obtener_signos_vitales = lambda: (np.random.randint(60, 100), np.random.randint(90, 100))

if __name__ == "__main__":
    # Test the compatibility module
    print("Testing email compatibility module...")
    
    # Test status
    status = get_email_service_status()
    print(f"Email service status: {status}")
    
    # Test configuration
    config_valid = test_email_configuration()
    print(f"Configuration valid: {config_valid}")
    
    # Test sending email (with dummy data)
    print("Testing email sending...")
    result = enviar_correo("Test User", "test@example.com")
    print(f"Email send result: {result}")