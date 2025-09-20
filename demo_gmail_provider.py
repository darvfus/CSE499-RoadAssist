#!/usr/bin/env python3
"""
Demo script for Gmail Provider functionality
This script demonstrates the enhanced Gmail provider with improved error handling
"""

from email_service.providers import GmailProvider, EmailProviderFactory
from email_service.models import EmailConfig, EmailData
from email_service.enums import ProviderType, AuthMethod, Priority


def demo_gmail_provider():
    """Demonstrate Gmail provider functionality"""
    print("=== Gmail Provider Demo ===\n")
    
    # Create Gmail provider
    gmail_provider = EmailProviderFactory.create_provider(ProviderType.GMAIL)
    print(f"Created provider: {gmail_provider.provider_name}")
    
    # Show Gmail-specific information
    print("\n--- Gmail Provider Information ---")
    info = gmail_provider.get_gmail_specific_info()
    print(f"Provider: {info['provider']}")
    print(f"SMTP Server: {info['smtp_server']}")
    print(f"Supported Ports: {info['supported_ports']}")
    print("Port Descriptions:")
    for port, desc in info['port_descriptions'].items():
        print(f"  {port}: {desc}")
    print(f"Auth Methods: {info['auth_methods']}")
    print("Security Notes:")
    for note in info['security_notes']:
        print(f"  - {note}")
    print(f"Troubleshooting URL: {info['troubleshooting_url']}")
    
    # Test configuration validation
    print("\n--- Configuration Validation Tests ---")
    
    # Valid configuration
    valid_config = EmailConfig(
        provider=ProviderType.GMAIL,
        smtp_server="smtp.gmail.com",
        smtp_port=587,
        use_tls=True,
        sender_email="test@gmail.com",
        sender_password="app_password_here",
        auth_method=AuthMethod.APP_PASSWORD
    )
    
    errors = gmail_provider.validate_config(valid_config)
    print(f"Valid config errors: {len(errors)} - {errors}")
    
    # Invalid configuration - wrong server
    invalid_config = EmailConfig(
        provider=ProviderType.GMAIL,
        smtp_server="smtp.yahoo.com",  # Wrong server
        smtp_port=587,
        use_tls=True,
        sender_email="test@gmail.com",
        sender_password="password",
        auth_method=AuthMethod.APP_PASSWORD
    )
    
    errors = gmail_provider.validate_config(invalid_config)
    print(f"Invalid config errors: {len(errors)}")
    for error in errors:
        print(f"  - {error}")
    
    # Configuration with regular password (shows warning)
    password_config = EmailConfig(
        provider=ProviderType.GMAIL,
        smtp_server="smtp.gmail.com",
        smtp_port=587,
        use_tls=True,
        sender_email="test@gmail.com",
        sender_password="regular_password",
        auth_method=AuthMethod.PASSWORD  # Regular password
    )
    
    errors = gmail_provider.validate_config(password_config)
    print(f"Password config warnings: {len(errors)}")
    for error in errors:
        print(f"  - {error}")
    
    # Configure the provider
    print("\n--- Provider Configuration ---")
    success = gmail_provider.configure(valid_config)
    print(f"Configuration successful: {success}")
    
    # Create sample email data
    print("\n--- Email Data Preparation ---")
    email_data = EmailData(
        recipient="recipient@example.com",
        subject="Test Email from Gmail Provider",
        body="This is a test email sent using the enhanced Gmail provider with improved error handling.",
        template_name="test_template",
        template_data={
            "user_name": "Test User",
            "alert_type": "drowsiness",
            "timestamp": "2024-01-15 10:30:00"
        },
        priority=Priority.HIGH,
        html_body="<h1>Test Email</h1><p>This is a test email sent using the enhanced Gmail provider.</p>"
    )
    
    print(f"Email recipient: {email_data.recipient}")
    print(f"Email subject: {email_data.subject}")
    print(f"Email priority: {email_data.priority.value}")
    print(f"Has HTML body: {email_data.html_body is not None}")
    
    # Note: We won't actually send the email in this demo to avoid requiring real credentials
    print("\n--- Email Sending (Simulated) ---")
    print("Note: Email sending is not executed in this demo to avoid requiring real Gmail credentials.")
    print("In a real scenario, you would:")
    print("1. Set up a Gmail account with 2-Factor Authentication")
    print("2. Generate an App Password in Google Account settings")
    print("3. Use the App Password in the EmailConfig")
    print("4. Call gmail_provider.send_email(email_data)")
    
    # Show what the enhanced error handling would provide
    print("\n--- Enhanced Error Handling Features ---")
    print("The Gmail provider now includes:")
    print("- Specific error messages for different failure types")
    print("- Troubleshooting steps for common issues")
    print("- Gmail-specific authentication guidance")
    print("- SSL/TLS connection security")
    print("- Detailed error categorization")
    
    print("\n--- Error Types Handled ---")
    error_types = [
        ("SMTPAuthenticationError (535)", "App Password required - provides setup instructions"),
        ("SMTPConnectError", "Network/firewall issues - suggests troubleshooting steps"),
        ("SMTPRecipientsRefused", "Invalid recipient - suggests email validation"),
        ("SMTPDataError", "Content rejected - suggests content review"),
        ("SSL/TLS Errors", "Security issues - suggests network diagnostics")
    ]
    
    for error_type, description in error_types:
        print(f"  {error_type}: {description}")


if __name__ == "__main__":
    demo_gmail_provider()