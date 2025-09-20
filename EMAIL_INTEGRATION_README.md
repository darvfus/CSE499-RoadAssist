# Email Service Integration for Driver Assistant

This document explains how the existing driver assistant files have been enhanced to use the new EmailServiceManager while maintaining backward compatibility.

## Overview

The integration provides:
- **Enhanced email functionality** with multiple provider support, retry logic, and templates
- **Backward compatibility** - existing code continues to work without changes
- **Automatic fallback** - if the enhanced service fails, it falls back to basic email
- **Easy configuration** - JSON-based email configuration

## Files Modified

### Core Integration Files

1. **`email_integration.py`** - Main integration module that provides backward-compatible email functionality
2. **`update_existing_files.py`** - Script to automatically update existing files
3. **`email_config_template.json`** - Template for email configuration

### Updated Driver Assistant Files

The following files have been enhanced to use the new email service:

1. **`main.py`** - Enhanced with email service integration and configuration GUI
2. **`driverassitant.py`** - Updated to use enhanced email service with fallback
3. **`driverassistant_modified.py`** - Updated with email service integration
4. **`driver_assistant_enhanced.py`** - Already had advanced integration

## How It Works

### Automatic Service Detection

The integration automatically detects if the enhanced email service is available:

```python
# Try to import enhanced email service
try:
    from email_service import EmailServiceManagerImpl, EmailConfig, ...
    EMAIL_SERVICE_AVAILABLE = True
except ImportError:
    EMAIL_SERVICE_AVAILABLE = False
```

### Enhanced Email Function

The `enviar_correo` function now works as follows:

1. **Try Enhanced Service**: Attempts to use EmailServiceManager with templates, retry logic, etc.
2. **Fallback to Basic**: If enhanced service fails, uses original SMTP functionality
3. **Error Handling**: Comprehensive error handling with user-friendly messages

```python
def enviar_correo(nombre_usuario: str, correo_usuario: str) -> bool:
    # Try enhanced service first
    if EMAIL_SERVICE_AVAILABLE and email_service:
        try:
            return enviar_correo_mejorado(nombre_usuario, correo_usuario)
        except Exception as e:
            print(f"Error with enhanced service, falling back: {e}")
    
    # Fallback to basic email
    return enviar_correo_basico(nombre_usuario, correo_usuario)
```

## Configuration

### Email Configuration File

Create `email_config.json` based on the template:

```json
{
    "provider": "gmail",
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "use_tls": true,
    "sender_email": "your_email@gmail.com",
    "sender_password": "your_app_password",
    "auth_method": "app_password",
    "timeout": 30,
    "max_retries": 3
}
```

### Supported Providers

- **Gmail**: smtp.gmail.com (ports 587/465)
- **Outlook**: smtp-mail.outlook.com (port 587)
- **Yahoo**: smtp.mail.yahoo.com (port 587)
- **Custom**: User-defined SMTP server

## Usage Examples

### Basic Usage (Existing Code)

Existing code continues to work without changes:

```python
# This still works exactly as before
enviar_correo("Usuario", "usuario@email.com")
```

### Advanced Usage

```python
from email_integration import (
    enviar_correo, 
    inicializar_email_service, 
    get_email_service_status
)

# Initialize service (optional - auto-initializes)
inicializar_email_service()

# Check service status
status = get_email_service_status()
print(f"Service type: {status['service_type']}")

# Send email (enhanced functionality)
success = enviar_correo("Usuario", "usuario@email.com")
```

## Features

### Enhanced Email Service Features

When the enhanced service is available:

- **Multiple Email Providers**: Gmail, Outlook, Yahoo, Custom SMTP
- **Email Templates**: Professional HTML and text templates
- **Retry Logic**: Automatic retry with exponential backoff
- **Delivery Tracking**: Unique email IDs and delivery confirmation
- **Error Handling**: Detailed error messages and troubleshooting
- **Package Management**: Automatic installation of required packages

### Backward Compatibility Features

- **Seamless Fallback**: Automatically uses basic email if enhanced service fails
- **No Code Changes**: Existing code works without modifications
- **Configuration Flexibility**: Can use config files or hardcoded credentials
- **Error Resilience**: Continues working even if email service has issues

## Installation and Setup

### 1. Copy Configuration Template

```bash
cp email_config_template.json email_config.json
```

### 2. Edit Configuration

Edit `email_config.json` with your email credentials:

```json
{
    "sender_email": "your_actual_email@gmail.com",
    "sender_password": "your_actual_app_password"
}
```

### 3. Test Integration

Run the example script:

```bash
python email_integration_example.py
```

### 4. Update Existing Files (Optional)

If you want to update other files:

```bash
python update_existing_files.py
```

## Security Considerations

### App Passwords

For Gmail and other providers, use App Passwords instead of regular passwords:

1. **Gmail**: Enable 2FA, then generate App Password in Google Account settings
2. **Outlook**: Use App Password or regular password (depending on account type)
3. **Yahoo**: Enable App Passwords in Yahoo Account Security

### Configuration Security

- Keep `email_config.json` secure and don't commit to version control
- Consider using environment variables for production deployments
- The enhanced service supports encrypted credential storage

## Troubleshooting

### Common Issues

1. **"Email service not available"**
   - The enhanced email service modules are not installed
   - Falls back to basic email automatically

2. **"Email configuration incomplete"**
   - Check `email_config.json` has valid sender_email and sender_password
   - Verify credentials are correct

3. **"SMTP connection failed"**
   - Check internet connection
   - Verify SMTP server and port settings
   - Ensure firewall allows SMTP connections

4. **"Authentication failed"**
   - Use App Passwords instead of regular passwords
   - Check if 2FA is enabled and configured correctly

### Debug Information

Enable debug information by checking service status:

```python
from email_integration import get_email_service_status
status = get_email_service_status()
print(status)
```

## Migration Guide

### From Basic Email to Enhanced

If you're currently using basic email functionality:

1. **No immediate changes needed** - integration provides backward compatibility
2. **Optional**: Create `email_config.json` for enhanced features
3. **Optional**: Update imports to use `email_integration` module directly

### From Enhanced Email Service

If you're already using the EmailServiceManager directly:

1. **Continue using direct imports** - no changes needed
2. **Optional**: Use `email_integration` module for simplified usage
3. **Benefit**: Automatic fallback if service initialization fails

## API Reference

### Main Functions

#### `enviar_correo(nombre_usuario: str, correo_usuario: str) -> bool`
Send email with automatic service detection and fallback.

#### `inicializar_email_service(config_file: str = "email_config.json") -> bool`
Initialize the enhanced email service. Returns True if successful.

#### `get_email_service_status() -> Dict[str, Any]`
Get current email service status and configuration information.

### Configuration Functions

#### `cargar_config_email(config_file: str) -> Dict[str, Any]`
Load email configuration from JSON file.

#### `guardar_config_email(config: Dict[str, Any], config_file: str) -> bool`
Save email configuration to JSON file.

## Support

For issues or questions:

1. Check the troubleshooting section above
2. Verify your email configuration
3. Test with the example script
4. Check service status for diagnostic information

The integration is designed to be robust and provide helpful error messages to guide troubleshooting.