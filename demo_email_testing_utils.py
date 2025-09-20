"""
Demo script for Email Testing Utilities

This script demonstrates how to use the comprehensive email testing utilities
for validating email configurations, testing connections, and using mock providers.
"""

import sys
import time
from datetime import datetime

from email_service.testing_utils import (
    EmailTestingUtils, MockEmailProvider, MockSMTPServer,
    create_test_config, create_test_email_data, create_test_user_data,
    create_test_alert_data
)
from email_service.enums import ProviderType, AuthMethod


def demo_connection_testing():
    """Demonstrate SMTP connection testing"""
    print("=" * 60)
    print("SMTP Connection Testing Demo")
    print("=" * 60)
    
    testing_utils = EmailTestingUtils()
    
    # Test different provider configurations
    providers = [
        (ProviderType.GMAIL, "Gmail"),
        (ProviderType.OUTLOOK, "Outlook"),
        (ProviderType.YAHOO, "Yahoo")
    ]
    
    for provider_type, provider_name in providers:
        print(f"\n--- Testing {provider_name} Connection ---")
        config = create_test_config(provider_type)
        
        # Test connection (this will fail without real credentials, but shows the process)
        try:
            result = testing_utils.test_smtp_connection(config, timeout=5)
            print(f"Server: {result.server}:{result.port}")
            print(f"Success: {result.success}")
            print(f"SSL Supported: {result.ssl_supported}")
            print(f"TLS Supported: {result.tls_supported}")
            print(f"Auth Methods: {result.auth_methods}")
            print(f"Response Time: {result.response_time:.2f}s")
            
            if not result.success:
                print(f"Error: {result.error_message}")
        except Exception as e:
            print(f"Connection test failed: {str(e)}")


def demo_config_validation():
    """Demonstrate email configuration validation"""
    print("\n" + "=" * 60)
    print("Email Configuration Validation Demo")
    print("=" * 60)
    
    testing_utils = EmailTestingUtils()
    
    # Test valid configuration
    print("\n--- Valid Gmail Configuration ---")
    valid_config = create_test_config(ProviderType.GMAIL)
    result = testing_utils.validate_email_config(valid_config)
    
    print(f"Valid: {result.valid}")
    print(f"Errors: {result.errors}")
    print(f"Warnings: {result.warnings}")
    print(f"Suggestions: {result.suggestions}")
    
    # Test invalid configuration
    print("\n--- Invalid Configuration ---")
    invalid_config = create_test_config(ProviderType.GMAIL)
    invalid_config.sender_email = "invalid_email"
    invalid_config.smtp_server = ""
    invalid_config.smtp_port = 70000
    
    result = testing_utils.validate_email_config(invalid_config)
    print(f"Valid: {result.valid}")
    print(f"Errors: {result.errors}")
    
    # Test configuration with warnings
    print("\n--- Configuration with Warnings ---")
    warning_config = create_test_config(ProviderType.GMAIL)
    warning_config.smtp_server = "wrong.server.com"
    warning_config.smtp_port = 25
    warning_config.use_tls = False
    
    result = testing_utils.validate_email_config(warning_config)
    print(f"Valid: {result.valid}")
    print(f"Warnings: {result.warnings}")
    print(f"Suggestions: {result.suggestions}")


def demo_mock_provider():
    """Demonstrate mock email provider usage"""
    print("\n" + "=" * 60)
    print("Mock Email Provider Demo")
    print("=" * 60)
    
    # Test successful mock provider
    print("\n--- Successful Mock Provider ---")
    mock_provider = MockEmailProvider()
    config = create_test_config()
    email_data = create_test_email_data()
    
    # Configure and test
    configure_result = mock_provider.configure(config)
    print(f"Configuration successful: {configure_result}")
    
    connection_result = mock_provider.test_connection()
    print(f"Connection test successful: {connection_result}")
    
    # Send test emails
    for i in range(3):
        email_data.recipient = f"test{i}@example.com"
        email_data.subject = f"Test Email {i+1}"
        result = mock_provider.send_email(email_data)
        print(f"Email {i+1} sent: {result.success}, ID: {result.email_id}")
    
    # Check sent emails
    sent_emails = mock_provider.get_sent_emails()
    print(f"Total emails sent: {len(sent_emails)}")
    
    # Test failing mock provider
    print("\n--- Failing Mock Provider ---")
    failing_provider = MockEmailProvider(should_fail=True, fail_on='send_email')
    failing_provider.configure(config)
    
    result = failing_provider.send_email(email_data)
    print(f"Email send result: {result.success}")
    print(f"Error message: {result.message}")
    
    # Reset and test
    print("\n--- Reset Mock Provider ---")
    mock_provider.reset()
    print(f"Configured after reset: {mock_provider.configured}")
    print(f"Emails after reset: {len(mock_provider.get_sent_emails())}")


def demo_mock_smtp_server():
    """Demonstrate mock SMTP server usage"""
    print("\n" + "=" * 60)
    print("Mock SMTP Server Demo")
    print("=" * 60)
    
    # Test successful SMTP operations
    print("\n--- Successful SMTP Operations ---")
    server = MockSMTPServer()
    
    with server:
        print(f"Connected: {server.connected}")
        
        server.ehlo()
        print(f"EHLO called: {server.ehlo_called}")
        
        server.starttls()
        print(f"STARTTLS called: {server.starttls_called}")
        
        server.login("test@example.com", "password")
        print(f"Authenticated: {server.authenticated}")
        
        # Send messages
        for i in range(2):
            message = f"Test message {i+1}"
            server.send_message(message)
        
        print(f"Messages sent: {len(server.messages_sent)}")
        print(f"Extensions supported: STARTTLS={server.has_extn('STARTTLS')}, AUTH={server.has_extn('AUTH')}")
    
    print(f"Connected after context: {server.connected}")
    
    # Test failing SMTP operations
    print("\n--- Failing SMTP Operations ---")
    failing_server = MockSMTPServer(fail_on='login')
    
    try:
        failing_server.login("test@example.com", "wrong_password")
    except Exception as e:
        print(f"Login failed as expected: {type(e).__name__}")


def demo_authentication_testing():
    """Demonstrate email authentication testing"""
    print("\n" + "=" * 60)
    print("Email Authentication Testing Demo")
    print("=" * 60)
    
    testing_utils = EmailTestingUtils()
    
    # Note: This will fail without real credentials, but shows the testing process
    print("\n--- Gmail Authentication Test ---")
    gmail_config = create_test_config(ProviderType.GMAIL)
    
    try:
        result = testing_utils.test_email_authentication(gmail_config)
        print(f"Overall success: {result.success}")
        print(f"Connection test: {result.connection_test}")
        print(f"Authentication test: {result.auth_test}")
        print(f"Test duration: {result.test_duration:.2f}s")
        
        if result.error_messages:
            print("Error messages:")
            for error in result.error_messages:
                print(f"  - {error}")
    except Exception as e:
        print(f"Authentication test failed: {str(e)}")


def demo_test_summary():
    """Demonstrate test result summary"""
    print("\n" + "=" * 60)
    print("Test Summary Demo")
    print("=" * 60)
    
    testing_utils = EmailTestingUtils()
    
    # Add some mock test results
    from email_service.models import TestResult
    
    test_results = [
        TestResult(True, "gmail", True, True, True, [], 1.2),
        TestResult(False, "outlook", True, False, False, ["Authentication failed"], 2.1),
        TestResult(True, "yahoo", True, True, True, [], 1.8),
        TestResult(False, "custom", False, False, False, ["Connection timeout"], 5.0),
        TestResult(True, "gmail", True, True, True, [], 1.1)
    ]
    
    testing_utils.test_results = test_results
    
    summary = testing_utils.get_test_summary()
    print(f"Total tests: {summary['total_tests']}")
    print(f"Successful tests: {summary['successful_tests']}")
    print(f"Success rate: {summary['success_rate']:.1f}%")
    print(f"Average duration: {summary['average_duration']:.2f}s")
    print(f"Providers tested: {summary['providers_tested']}")
    print(f"Common errors: {summary['common_errors']}")


def demo_helper_functions():
    """Demonstrate helper functions for creating test data"""
    print("\n" + "=" * 60)
    print("Helper Functions Demo")
    print("=" * 60)
    
    # Create test configurations
    print("\n--- Test Configurations ---")
    for provider in [ProviderType.GMAIL, ProviderType.OUTLOOK, ProviderType.YAHOO]:
        config = create_test_config(provider)
        print(f"{provider.value}: {config.smtp_server}:{config.smtp_port} (TLS: {config.use_tls})")
    
    # Create test data
    print("\n--- Test Data ---")
    email_data = create_test_email_data("demo@example.com")
    print(f"Email recipient: {email_data.recipient}")
    print(f"Email subject: {email_data.subject}")
    print(f"Template data: {email_data.template_data}")
    
    user_data = create_test_user_data()
    print(f"User: {user_data.name} ({user_data.email})")
    
    alert_data = create_test_alert_data()
    print(f"Alert: {alert_data.alert_type.value} at {alert_data.timestamp}")
    print(f"Vitals: HR={alert_data.heart_rate}, SpO2={alert_data.oxygen_saturation}")


def main():
    """Run all demo functions"""
    print("Email Testing Utilities Demo")
    print("This demo shows how to use the comprehensive email testing utilities.")
    print("Note: Some tests may fail without real email credentials, but demonstrate the testing process.")
    
    try:
        demo_config_validation()
        demo_mock_provider()
        demo_mock_smtp_server()
        demo_test_summary()
        demo_helper_functions()
        
        # Connection and authentication tests (may fail without real credentials)
        print("\n" + "=" * 60)
        print("Note: The following tests require real email credentials and may fail:")
        print("=" * 60)
        
        demo_connection_testing()
        demo_authentication_testing()
        
    except KeyboardInterrupt:
        print("\nDemo interrupted by user.")
    except Exception as e:
        print(f"\nDemo failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("Demo completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()