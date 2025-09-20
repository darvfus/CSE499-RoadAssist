#!/usr/bin/env python3
"""
Demo script for EmailServiceManager - Main email service orchestrator

This script demonstrates the complete email service functionality including:
- Service initialization with configuration validation
- Package management and provider creation
- Alert email sending with template rendering
- Configuration testing and error handling
"""

import sys
from datetime import datetime
from email_service import (
    EmailServiceManagerImpl, EmailConfig, UserData, AlertData,
    ProviderType, AuthMethod, AlertType
)


def demo_email_service_manager():
    """Demonstrate EmailServiceManager functionality"""
    print("=== Email Service Manager Demo ===\n")
    
    # Create service manager instance
    print("1. Creating EmailServiceManager...")
    service_manager = EmailServiceManagerImpl()
    print("✓ EmailServiceManager created successfully\n")
    
    # Create email configuration
    print("2. Creating email configuration...")
    config = EmailConfig(
        provider=ProviderType.GMAIL,
        smtp_server="smtp.gmail.com",
        smtp_port=587,
        use_tls=True,
        sender_email="your-email@gmail.com",  # Replace with actual email
        sender_password="your-app-password",   # Replace with actual app password
        auth_method=AuthMethod.APP_PASSWORD,
        timeout=30,
        max_retries=3
    )
    print("✓ Email configuration created")
    print(f"  Provider: {config.provider.value}")
    print(f"  SMTP Server: {config.smtp_server}:{config.smtp_port}")
    print(f"  Auth Method: {config.auth_method.value}\n")
    
    # Initialize service
    print("3. Initializing email service...")
    try:
        success = service_manager.initialize(config)
        if success:
            print("✓ Email service initialized successfully")
        else:
            print("✗ Email service initialization failed")
            return
    except Exception as e:
        print(f"✗ Initialization error: {e}")
        return
    
    print()
    
    # Get service status
    print("4. Getting service status...")
    status = service_manager.get_service_status()
    print("✓ Service status:")
    for key, value in status.items():
        print(f"  {key}: {value}")
    print()
    
    # Test email configuration
    print("5. Testing email configuration...")
    try:
        test_result = service_manager.test_email_configuration()
        print(f"✓ Configuration test completed")
        print(f"  Overall Success: {test_result.success}")
        print(f"  Provider: {test_result.provider}")
        print(f"  Connection Test: {test_result.connection_test}")
        print(f"  Auth Test: {test_result.auth_test}")
        print(f"  Send Test: {test_result.send_test}")
        print(f"  Test Duration: {test_result.test_duration:.2f}s")
        
        if test_result.error_messages:
            print("  Error Messages:")
            for error in test_result.error_messages:
                print(f"    - {error}")
    except Exception as e:
        print(f"✗ Configuration test error: {e}")
    
    print()
    
    # Create user and alert data
    print("6. Creating user and alert data...")
    user_data = UserData(
        name="John Doe",
        email="recipient@example.com",  # Replace with actual recipient
        user_id="user123",
        preferences={"language": "en", "timezone": "UTC"}
    )
    
    alert_data = AlertData(
        alert_type=AlertType.DROWSINESS,
        timestamp=datetime.now(),
        heart_rate=75,
        oxygen_saturation=98.5,
        additional_data={"location": "Highway 101", "speed": "65 mph"}
    )
    
    print("✓ User and alert data created")
    print(f"  User: {user_data.name} ({user_data.email})")
    print(f"  Alert: {alert_data.alert_type.value} at {alert_data.timestamp}")
    print()
    
    # Send alert email
    print("7. Sending alert email...")
    try:
        email_result = service_manager.send_alert_email(user_data, alert_data)
        
        if email_result.success:
            print("✓ Alert email sent successfully")
            print(f"  Email ID: {email_result.email_id}")
            print(f"  Message: {email_result.message}")
            if email_result.details:
                print("  Details:")
                for key, value in email_result.details.items():
                    print(f"    {key}: {value}")
        else:
            print("✗ Alert email sending failed")
            print(f"  Message: {email_result.message}")
            if email_result.details:
                print("  Details:")
                for key, value in email_result.details.items():
                    print(f"    {key}: {value}")
    except Exception as e:
        print(f"✗ Alert email error: {e}")
    
    print()
    
    # Test different alert types
    print("8. Testing different alert types...")
    alert_types = [AlertType.VITAL_SIGNS, AlertType.SYSTEM_ERROR, AlertType.TEST_EMAIL]
    
    for alert_type in alert_types:
        print(f"  Testing {alert_type.value} alert...")
        test_alert = AlertData(
            alert_type=alert_type,
            timestamp=datetime.now(),
            heart_rate=80 if alert_type == AlertType.VITAL_SIGNS else None,
            oxygen_saturation=95.0 if alert_type == AlertType.VITAL_SIGNS else None
        )
        
        try:
            result = service_manager.send_alert_email(user_data, test_alert)
            status = "✓" if result.success else "✗"
            print(f"    {status} {alert_type.value}: {result.message}")
        except Exception as e:
            print(f"    ✗ {alert_type.value}: Error - {e}")
    
    print()
    
    # Test configuration update
    print("9. Testing configuration update...")
    try:
        # Create updated configuration (same provider, different timeout)
        updated_config = EmailConfig(
            provider=ProviderType.GMAIL,
            smtp_server="smtp.gmail.com",
            smtp_port=587,
            use_tls=True,
            sender_email=config.sender_email,
            sender_password=config.sender_password,
            auth_method=AuthMethod.APP_PASSWORD,
            timeout=60,  # Increased timeout
            max_retries=5  # Increased retries
        )
        
        success = service_manager.update_configuration(updated_config)
        if success:
            print("✓ Configuration updated successfully")
            print(f"  New timeout: {updated_config.timeout}s")
            print(f"  New max retries: {updated_config.max_retries}")
        else:
            print("✗ Configuration update failed")
    except Exception as e:
        print(f"✗ Configuration update error: {e}")
    
    print()
    
    # Get supported providers
    print("10. Getting supported providers...")
    try:
        providers = service_manager.get_supported_providers()
        print("✓ Supported providers:")
        for provider in providers:
            print(f"  - {provider}")
    except Exception as e:
        print(f"✗ Error getting providers: {e}")
    
    print("\n=== Demo completed ===")


def demo_error_handling():
    """Demonstrate error handling capabilities"""
    print("\n=== Error Handling Demo ===\n")
    
    service_manager = EmailServiceManagerImpl()
    
    # Test with invalid configuration
    print("1. Testing with invalid configuration...")
    try:
        invalid_config = EmailConfig(
            provider=ProviderType.GMAIL,
            smtp_server="",  # Invalid empty server
            smtp_port=587,
            use_tls=True,
            sender_email="invalid-email",  # Invalid email format
            sender_password="password",
            auth_method=AuthMethod.APP_PASSWORD
        )
        
        success = service_manager.initialize(invalid_config)
        print(f"  Initialization result: {success}")
        
    except Exception as e:
        print(f"  ✓ Caught expected error: {e}")
    
    # Test sending email without initialization
    print("\n2. Testing email sending without initialization...")
    try:
        user_data = UserData(name="Test User", email="test@example.com")
        alert_data = AlertData(alert_type=AlertType.TEST_EMAIL, timestamp=datetime.now())
        
        result = service_manager.send_alert_email(user_data, alert_data)
        print(f"  ✓ Handled gracefully: {result.message}")
        
    except Exception as e:
        print(f"  ✗ Unexpected error: {e}")
    
    print("\n=== Error Handling Demo completed ===")


if __name__ == "__main__":
    print("Email Service Manager Demo")
    print("=" * 50)
    print()
    print("NOTE: This demo requires valid email credentials.")
    print("Please update the configuration with your actual:")
    print("- Gmail address")
    print("- Gmail App Password")
    print("- Recipient email address")
    print()
    
    response = input("Continue with demo? (y/n): ").lower().strip()
    if response != 'y':
        print("Demo cancelled.")
        sys.exit(0)
    
    try:
        demo_email_service_manager()
        demo_error_handling()
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user.")
    except Exception as e:
        print(f"\n\nDemo failed with error: {e}")
        import traceback
        traceback.print_exc()