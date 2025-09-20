"""
Unit Tests for Email Testing Utilities

Tests the comprehensive email testing utilities including connection validation,
configuration verification, and mock providers.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import smtplib
import socket
from datetime import datetime

from email_service.testing_utils import (
    EmailTestingUtils, MockEmailProvider, MockSMTPServer,
    create_test_config, create_test_email_data, create_test_user_data,
    create_test_alert_data, ConnectionTestResult, ConfigValidationResult
)
from email_service.models import EmailConfig, EmailData, EmailResult
from email_service.enums import ProviderType, AuthMethod, Priority, AlertType


class TestEmailTestingUtils(unittest.TestCase):
    """Test cases for EmailTestingUtils class"""
    
    def setUp(self):
        self.testing_utils = EmailTestingUtils()
        self.test_config = create_test_config(ProviderType.GMAIL)
    
    def test_init(self):
        """Test EmailTestingUtils initialization"""
        utils = EmailTestingUtils()
        self.assertEqual(len(utils.test_results), 0)
        self.assertEqual(len(utils.connection_cache), 0)
    
    @patch('socket.create_connection')
    @patch('smtplib.SMTP')
    def test_smtp_connection_success(self, mock_smtp, mock_socket):
        """Test successful SMTP connection"""
        # Mock successful connection
        mock_socket.return_value = Mock()
        mock_server = Mock()
        mock_server.ehlo.return_value = None
        mock_server.has_extn.return_value = True
        mock_server.starttls.return_value = None
        mock_server.esmtp_features = {'auth': 'PLAIN LOGIN'}
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        result = self.testing_utils.test_smtp_connection(self.test_config)
        
        self.assertTrue(result.success)
        self.assertEqual(result.server, "smtp.gmail.com")
        self.assertEqual(result.port, 587)
        self.assertTrue(result.tls_supported)
        self.assertIn('PLAIN', result.auth_methods)
    
    @patch('socket.create_connection')
    def test_smtp_connection_timeout(self, mock_socket):
        """Test SMTP connection timeout"""
        mock_socket.side_effect = socket.timeout("Connection timeout")
        
        result = self.testing_utils.test_smtp_connection(self.test_config)
        
        self.assertFalse(result.success)
        self.assertIn("Connection timeout", result.error_message)
    
    @patch('socket.create_connection')
    def test_smtp_connection_dns_error(self, mock_socket):
        """Test SMTP connection DNS error"""
        mock_socket.side_effect = socket.gaierror("DNS resolution failed")
        
        result = self.testing_utils.test_smtp_connection(self.test_config)
        
        self.assertFalse(result.success)
        self.assertIn("DNS resolution failed", result.error_message)
    
    @patch('socket.create_connection')
    def test_smtp_connection_refused(self, mock_socket):
        """Test SMTP connection refused"""
        mock_socket.side_effect = ConnectionRefusedError("Connection refused")
        
        result = self.testing_utils.test_smtp_connection(self.test_config)
        
        self.assertFalse(result.success)
        self.assertIn("Connection refused", result.error_message)
    
    def test_validate_email_config_valid_gmail(self):
        """Test validation of valid Gmail configuration"""
        config = create_test_config(ProviderType.GMAIL)
        result = self.testing_utils.validate_email_config(config)
        
        self.assertTrue(result.valid)
        self.assertEqual(len(result.errors), 0)
    
    def test_validate_email_config_invalid_email(self):
        """Test validation with invalid email address"""
        config = create_test_config(ProviderType.GMAIL)
        config.sender_email = "invalid_email"
        
        result = self.testing_utils.validate_email_config(config)
        
        self.assertFalse(result.valid)
        self.assertIn("Invalid sender email address", result.errors)
    
    def test_validate_email_config_empty_server(self):
        """Test validation with empty SMTP server"""
        config = create_test_config(ProviderType.GMAIL)
        config.smtp_server = ""
        
        result = self.testing_utils.validate_email_config(config)
        
        self.assertFalse(result.valid)
        self.assertIn("SMTP server cannot be empty", result.errors)
    
    def test_validate_email_config_invalid_port(self):
        """Test validation with invalid port"""
        config = create_test_config(ProviderType.GMAIL)
        config.smtp_port = 70000
        
        result = self.testing_utils.validate_email_config(config)
        
        self.assertFalse(result.valid)
        self.assertIn("SMTP port must be between 1 and 65535", result.errors)
    
    def test_validate_email_config_gmail_warnings(self):
        """Test Gmail-specific validation warnings"""
        config = create_test_config(ProviderType.GMAIL)
        config.smtp_server = "wrong.server.com"
        config.smtp_port = 25
        
        result = self.testing_utils.validate_email_config(config)
        
        self.assertTrue(result.valid)  # No errors, just warnings
        self.assertIn("Gmail typically uses smtp.gmail.com", result.warnings)
        self.assertIn("Gmail typically uses port 587 (TLS) or 465 (SSL)", result.warnings)
    
    def test_validate_email_config_security_warnings(self):
        """Test security-related validation warnings"""
        config = create_test_config(ProviderType.GMAIL)
        config.smtp_port = 25
        config.use_tls = False
        
        result = self.testing_utils.validate_email_config(config)
        
        self.assertIn("Port 25 is often blocked and insecure", result.warnings)
        self.assertIn("Unencrypted email transmission is insecure", result.warnings)
        self.assertIn("Enable TLS encryption", result.suggestions)
    
    @patch('email_service.testing_utils.EmailTestingUtils.test_smtp_connection')
    @patch('smtplib.SMTP')
    def test_email_authentication_success(self, mock_smtp, mock_connection_test):
        """Test successful email authentication"""
        # Mock successful connection test
        mock_connection_test.return_value = ConnectionTestResult(
            success=True, server="smtp.gmail.com", port=587,
            ssl_supported=False, tls_supported=True, auth_methods=['PLAIN'],
            response_time=0.5
        )
        
        # Mock successful SMTP authentication
        mock_server = Mock()
        mock_server.ehlo.return_value = None
        mock_server.starttls.return_value = None
        mock_server.login.return_value = None
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        result = self.testing_utils.test_email_authentication(self.test_config)
        
        self.assertTrue(result.success)
        self.assertTrue(result.connection_test)
        self.assertTrue(result.auth_test)
        self.assertEqual(len(result.error_messages), 0)
    
    @patch('email_service.testing_utils.EmailTestingUtils.test_smtp_connection')
    def test_email_authentication_connection_failure(self, mock_connection_test):
        """Test email authentication with connection failure"""
        # Mock failed connection test
        mock_connection_test.return_value = ConnectionTestResult(
            success=False, server="smtp.gmail.com", port=587,
            ssl_supported=False, tls_supported=False, auth_methods=[],
            response_time=0.5, error_message="Connection failed"
        )
        
        result = self.testing_utils.test_email_authentication(self.test_config)
        
        self.assertFalse(result.success)
        self.assertFalse(result.connection_test)
        self.assertFalse(result.auth_test)
        self.assertIn("Connection failed", result.error_messages[0])
    
    @patch('email_service.testing_utils.EmailTestingUtils.test_smtp_connection')
    @patch('smtplib.SMTP')
    def test_email_authentication_auth_failure(self, mock_smtp, mock_connection_test):
        """Test email authentication with auth failure"""
        # Mock successful connection test
        mock_connection_test.return_value = ConnectionTestResult(
            success=True, server="smtp.gmail.com", port=587,
            ssl_supported=False, tls_supported=True, auth_methods=['PLAIN'],
            response_time=0.5
        )
        
        # Mock authentication failure
        mock_server = Mock()
        mock_server.ehlo.return_value = None
        mock_server.starttls.return_value = None
        mock_server.login.side_effect = smtplib.SMTPAuthenticationError(535, "Authentication failed")
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        result = self.testing_utils.test_email_authentication(self.test_config)
        
        self.assertFalse(result.success)
        self.assertTrue(result.connection_test)
        self.assertFalse(result.auth_test)
        self.assertIn("Authentication failed", result.error_messages[0])
    
    @patch('email_service.testing_utils.EmailTestingUtils.test_email_authentication')
    @patch('smtplib.SMTP')
    def test_send_test_email_success(self, mock_smtp, mock_auth_test):
        """Test successful test email sending"""
        # Mock successful authentication test
        mock_auth_test.return_value = Mock(
            success=True, connection_test=True, auth_test=True, error_messages=[]
        )
        
        # Mock successful email sending
        mock_server = Mock()
        mock_server.ehlo.return_value = None
        mock_server.starttls.return_value = None
        mock_server.login.return_value = None
        mock_server.send_message.return_value = None
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        result = self.testing_utils.send_test_email(
            self.test_config, "test@example.com", "Test Subject"
        )
        
        self.assertTrue(result.success)
        self.assertTrue(result.connection_test)
        self.assertTrue(result.auth_test)
        self.assertTrue(result.send_test)
    
    def test_get_test_summary_no_tests(self):
        """Test test summary with no tests run"""
        summary = self.testing_utils.get_test_summary()
        self.assertEqual(summary["message"], "No tests have been run")
    
    def test_get_test_summary_with_tests(self):
        """Test test summary with some tests run"""
        # Add some mock test results
        from email_service.models import TestResult
        
        self.testing_utils.test_results = [
            TestResult(True, "gmail", True, True, True, [], 1.0),
            TestResult(False, "outlook", True, False, False, ["Auth failed"], 2.0),
            TestResult(True, "yahoo", True, True, True, [], 1.5)
        ]
        
        summary = self.testing_utils.get_test_summary()
        
        self.assertEqual(summary["total_tests"], 3)
        self.assertEqual(summary["successful_tests"], 2)
        self.assertAlmostEqual(summary["success_rate"], 66.67, places=1)
        self.assertAlmostEqual(summary["average_duration"], 1.5, places=1)
        self.assertEqual(set(summary["providers_tested"]), {"gmail", "outlook", "yahoo"})


class TestMockEmailProvider(unittest.TestCase):
    """Test cases for MockEmailProvider class"""
    
    def setUp(self):
        self.mock_provider = MockEmailProvider()
        self.test_config = create_test_config()
        self.test_email_data = create_test_email_data()
    
    def test_init_default(self):
        """Test MockEmailProvider default initialization"""
        provider = MockEmailProvider()
        self.assertFalse(provider.should_fail)
        self.assertIsNone(provider.fail_on)
        self.assertFalse(provider.configured)
        self.assertEqual(len(provider.sent_emails), 0)
    
    def test_init_with_failure(self):
        """Test MockEmailProvider initialization with failure settings"""
        provider = MockEmailProvider(should_fail=True, fail_on='send_email')
        self.assertTrue(provider.should_fail)
        self.assertEqual(provider.fail_on, 'send_email')
    
    def test_configure_success(self):
        """Test successful configuration"""
        result = self.mock_provider.configure(self.test_config)
        self.assertTrue(result)
        self.assertTrue(self.mock_provider.configured)
        self.assertEqual(self.mock_provider.config, self.test_config)
    
    def test_configure_failure(self):
        """Test configuration failure"""
        provider = MockEmailProvider(should_fail=True, fail_on='configure')
        result = provider.configure(self.test_config)
        self.assertFalse(result)
        self.assertFalse(provider.configured)
    
    def test_test_connection_success(self):
        """Test successful connection test"""
        self.mock_provider.configure(self.test_config)
        result = self.mock_provider.test_connection()
        self.assertTrue(result)
        self.assertTrue(self.mock_provider.connection_tested)
    
    def test_test_connection_failure(self):
        """Test connection test failure"""
        provider = MockEmailProvider(should_fail=True, fail_on='test_connection')
        provider.configure(self.test_config)
        result = provider.test_connection()
        self.assertFalse(result)
    
    def test_test_connection_not_configured(self):
        """Test connection test when not configured"""
        result = self.mock_provider.test_connection()
        self.assertFalse(result)
    
    def test_send_email_success(self):
        """Test successful email sending"""
        self.mock_provider.configure(self.test_config)
        result = self.mock_provider.send_email(self.test_email_data)
        
        self.assertTrue(result.success)
        self.assertEqual(result.message, "Mock email sent successfully")
        self.assertIsNotNone(result.email_id)
        self.assertEqual(len(self.mock_provider.sent_emails), 1)
    
    def test_send_email_failure(self):
        """Test email sending failure"""
        provider = MockEmailProvider(should_fail=True, fail_on='send_email')
        provider.configure(self.test_config)
        result = provider.send_email(self.test_email_data)
        
        self.assertFalse(result.success)
        self.assertEqual(result.message, "Mock send failure")
        self.assertIsNone(result.email_id)
        self.assertEqual(len(provider.sent_emails), 0)
    
    def test_validate_config_valid(self):
        """Test configuration validation with valid config"""
        errors = self.mock_provider.validate_config(self.test_config)
        self.assertEqual(len(errors), 0)
    
    def test_validate_config_invalid(self):
        """Test configuration validation with invalid config"""
        invalid_config = create_test_config()
        invalid_config.sender_email = ""
        invalid_config.smtp_server = ""
        
        errors = self.mock_provider.validate_config(invalid_config)
        self.assertEqual(len(errors), 2)
        self.assertIn("Sender email is required", errors)
        self.assertIn("SMTP server is required", errors)
    
    def test_get_sent_emails(self):
        """Test getting sent emails list"""
        self.mock_provider.configure(self.test_config)
        
        # Send multiple emails
        for i in range(3):
            email_data = create_test_email_data(f"test{i}@example.com")
            self.mock_provider.send_email(email_data)
        
        sent_emails = self.mock_provider.get_sent_emails()
        self.assertEqual(len(sent_emails), 3)
        
        # Verify it's a copy (not the original list)
        sent_emails.clear()
        self.assertEqual(len(self.mock_provider.sent_emails), 3)
    
    def test_reset(self):
        """Test resetting mock provider state"""
        self.mock_provider.configure(self.test_config)
        self.mock_provider.test_connection()
        self.mock_provider.send_email(self.test_email_data)
        
        # Verify state before reset
        self.assertTrue(self.mock_provider.configured)
        self.assertTrue(self.mock_provider.connection_tested)
        self.assertEqual(len(self.mock_provider.sent_emails), 1)
        
        # Reset and verify
        self.mock_provider.reset()
        self.assertFalse(self.mock_provider.configured)
        self.assertFalse(self.mock_provider.connection_tested)
        self.assertEqual(len(self.mock_provider.sent_emails), 0)
        self.assertIsNone(self.mock_provider.config)


class TestMockSMTPServer(unittest.TestCase):
    """Test cases for MockSMTPServer class"""
    
    def test_context_manager(self):
        """Test MockSMTPServer as context manager"""
        server = MockSMTPServer()
        self.assertFalse(server.connected)
        
        with server:
            self.assertTrue(server.connected)
        
        self.assertFalse(server.connected)
    
    def test_ehlo_success(self):
        """Test successful EHLO command"""
        server = MockSMTPServer()
        server.ehlo()
        self.assertTrue(server.ehlo_called)
    
    def test_ehlo_failure(self):
        """Test EHLO command failure"""
        server = MockSMTPServer(fail_on='ehlo')
        with self.assertRaises(smtplib.SMTPException):
            server.ehlo()
    
    def test_starttls_success(self):
        """Test successful STARTTLS command"""
        server = MockSMTPServer()
        server.starttls()
        self.assertTrue(server.starttls_called)
    
    def test_starttls_failure(self):
        """Test STARTTLS command failure"""
        server = MockSMTPServer(fail_on='starttls')
        with self.assertRaises(smtplib.SMTPException):
            server.starttls()
    
    def test_login_success(self):
        """Test successful login"""
        server = MockSMTPServer()
        server.login("user@example.com", "password")
        self.assertTrue(server.authenticated)
    
    def test_login_failure(self):
        """Test login failure"""
        server = MockSMTPServer(fail_on='login')
        with self.assertRaises(smtplib.SMTPAuthenticationError):
            server.login("user@example.com", "password")
    
    def test_send_message_success(self):
        """Test successful message sending"""
        server = MockSMTPServer()
        message = Mock()
        server.send_message(message)
        self.assertEqual(len(server.messages_sent), 1)
        self.assertEqual(server.messages_sent[0], message)
    
    def test_send_message_failure(self):
        """Test message sending failure"""
        server = MockSMTPServer(fail_on='send')
        with self.assertRaises(smtplib.SMTPException):
            server.send_message(Mock())
    
    def test_has_extn(self):
        """Test extension checking"""
        server = MockSMTPServer()
        self.assertTrue(server.has_extn('STARTTLS'))
        self.assertTrue(server.has_extn('AUTH'))
        self.assertFalse(server.has_extn('UNKNOWN'))
    
    def test_esmtp_features(self):
        """Test ESMTP features property"""
        server = MockSMTPServer()
        features = server.esmtp_features
        self.assertEqual(features['auth'], 'PLAIN LOGIN')


class TestHelperFunctions(unittest.TestCase):
    """Test cases for helper functions"""
    
    def test_create_test_config_gmail(self):
        """Test creating Gmail test configuration"""
        config = create_test_config(ProviderType.GMAIL)
        self.assertEqual(config.provider, ProviderType.GMAIL)
        self.assertEqual(config.smtp_server, "smtp.gmail.com")
        self.assertEqual(config.smtp_port, 587)
        self.assertTrue(config.use_tls)
        self.assertEqual(config.auth_method, AuthMethod.APP_PASSWORD)
    
    def test_create_test_config_outlook(self):
        """Test creating Outlook test configuration"""
        config = create_test_config(ProviderType.OUTLOOK)
        self.assertEqual(config.provider, ProviderType.OUTLOOK)
        self.assertEqual(config.smtp_server, "smtp-mail.outlook.com")
        self.assertEqual(config.smtp_port, 587)
        self.assertEqual(config.auth_method, AuthMethod.PASSWORD)
    
    def test_create_test_config_yahoo(self):
        """Test creating Yahoo test configuration"""
        config = create_test_config(ProviderType.YAHOO)
        self.assertEqual(config.provider, ProviderType.YAHOO)
        self.assertEqual(config.smtp_server, "smtp.mail.yahoo.com")
        self.assertEqual(config.smtp_port, 587)
        self.assertEqual(config.auth_method, AuthMethod.APP_PASSWORD)
    
    def test_create_test_email_data(self):
        """Test creating test email data"""
        email_data = create_test_email_data("custom@example.com")
        self.assertEqual(email_data.recipient, "custom@example.com")
        self.assertEqual(email_data.subject, "Test Email")
        self.assertEqual(email_data.priority, Priority.NORMAL)
        self.assertIn("user_name", email_data.template_data)
    
    def test_create_test_user_data(self):
        """Test creating test user data"""
        user_data = create_test_user_data()
        self.assertEqual(user_data.name, "Test User")
        self.assertEqual(user_data.email, "testuser@example.com")
        self.assertEqual(user_data.user_id, "test_123")
    
    def test_create_test_alert_data(self):
        """Test creating test alert data"""
        alert_data = create_test_alert_data()
        self.assertEqual(alert_data.alert_type, AlertType.DROWSINESS)
        self.assertEqual(alert_data.heart_rate, 75)
        self.assertEqual(alert_data.oxygen_saturation, 98.5)
        self.assertIsInstance(alert_data.timestamp, datetime)


if __name__ == '__main__':
    unittest.main()