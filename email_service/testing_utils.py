"""
Email Testing Utilities

This module provides comprehensive testing utilities for the email service,
including connection validation, mock providers, and configuration verification.
"""

import smtplib
import ssl
import socket
import time
from typing import Dict, List, Optional, Any, Tuple
from unittest.mock import Mock, MagicMock
from dataclasses import dataclass
from datetime import datetime

from .models import (
    EmailConfig, EmailData, EmailResult, DeliveryResult, 
    TestResult, UserData, AlertData, EmailContent
)
from .enums import ProviderType, AuthMethod, Priority, AlertType, DeliveryStatusType
from .interfaces import EmailProvider


@dataclass
class ConnectionTestResult:
    """Result of SMTP connection test"""
    success: bool
    server: str
    port: int
    ssl_supported: bool
    tls_supported: bool
    auth_methods: List[str]
    response_time: float
    error_message: Optional[str] = None


@dataclass
class ConfigValidationResult:
    """Result of configuration validation"""
    valid: bool
    errors: List[str]
    warnings: List[str]
    suggestions: List[str]


class EmailTestingUtils:
    """Comprehensive email testing utilities"""
    
    def __init__(self):
        self.test_results: List[TestResult] = []
        self.connection_cache: Dict[str, ConnectionTestResult] = {}
    
    def test_smtp_connection(self, config: EmailConfig, timeout: int = 10) -> ConnectionTestResult:
        """
        Test SMTP server connection and capabilities
        
        Args:
            config: Email configuration to test
            timeout: Connection timeout in seconds
            
        Returns:
            ConnectionTestResult with detailed connection information
        """
        start_time = time.time()
        server_key = f"{config.smtp_server}:{config.smtp_port}"
        
        # Check cache first
        if server_key in self.connection_cache:
            cached_result = self.connection_cache[server_key]
            if time.time() - start_time < 300:  # Cache for 5 minutes
                return cached_result
        
        result = ConnectionTestResult(
            success=False,
            server=config.smtp_server,
            port=config.smtp_port,
            ssl_supported=False,
            tls_supported=False,
            auth_methods=[],
            response_time=0.0
        )
        
        try:
            # Test basic connection
            sock = socket.create_connection((config.smtp_server, config.smtp_port), timeout)
            sock.close()
            
            # Test SMTP capabilities
            if config.smtp_port == 465:  # SSL port
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL(config.smtp_server, config.smtp_port, timeout=timeout, context=context) as server:
                    result.ssl_supported = True
                    result.auth_methods = self._get_auth_methods(server)
                    result.success = True
            else:  # TLS port
                with smtplib.SMTP(config.smtp_server, config.smtp_port, timeout=timeout) as server:
                    server.ehlo()
                    if server.has_extn('STARTTLS'):
                        server.starttls()
                        result.tls_supported = True
                        server.ehlo()  # Re-identify after STARTTLS
                    
                    result.auth_methods = self._get_auth_methods(server)
                    result.success = True
                    
        except socket.timeout:
            result.error_message = f"Connection timeout to {config.smtp_server}:{config.smtp_port}"
        except socket.gaierror as e:
            result.error_message = f"DNS resolution failed: {str(e)}"
        except ConnectionRefusedError:
            result.error_message = f"Connection refused by {config.smtp_server}:{config.smtp_port}"
        except Exception as e:
            result.error_message = f"Connection error: {str(e)}"
        
        result.response_time = time.time() - start_time
        self.connection_cache[server_key] = result
        return result
    
    def _get_auth_methods(self, server: smtplib.SMTP) -> List[str]:
        """Extract supported authentication methods from SMTP server"""
        auth_methods = []
        try:
            if server.has_extn('AUTH'):
                auth_line = server.esmtp_features.get('auth', '')
                auth_methods = auth_line.split()
        except:
            pass
        return auth_methods
    
    def validate_email_config(self, config: EmailConfig) -> ConfigValidationResult:
        """
        Validate email configuration comprehensively
        
        Args:
            config: Email configuration to validate
            
        Returns:
            ConfigValidationResult with validation details
        """
        errors = []
        warnings = []
        suggestions = []
        
        # Basic validation
        if not config.sender_email or "@" not in config.sender_email:
            errors.append("Invalid sender email address")
        
        if not config.smtp_server:
            errors.append("SMTP server cannot be empty")
        
        if not (1 <= config.smtp_port <= 65535):
            errors.append("SMTP port must be between 1 and 65535")
        
        if not config.sender_password:
            errors.append("Sender password cannot be empty")
        
        # Provider-specific validation
        if config.provider == ProviderType.GMAIL:
            if config.smtp_server != "smtp.gmail.com":
                warnings.append("Gmail typically uses smtp.gmail.com")
            if config.smtp_port not in [587, 465]:
                warnings.append("Gmail typically uses port 587 (TLS) or 465 (SSL)")
            if config.auth_method != AuthMethod.APP_PASSWORD:
                suggestions.append("Consider using App Password for Gmail authentication")
        
        elif config.provider == ProviderType.OUTLOOK:
            if config.smtp_server != "smtp-mail.outlook.com":
                warnings.append("Outlook typically uses smtp-mail.outlook.com")
            if config.smtp_port != 587:
                warnings.append("Outlook typically uses port 587")
        
        elif config.provider == ProviderType.YAHOO:
            if config.smtp_server != "smtp.mail.yahoo.com":
                warnings.append("Yahoo typically uses smtp.mail.yahoo.com")
            if config.smtp_port != 587:
                warnings.append("Yahoo typically uses port 587")
        
        # Security validation
        if config.smtp_port == 25:
            warnings.append("Port 25 is often blocked and insecure")
            suggestions.append("Consider using port 587 (TLS) or 465 (SSL)")
        
        if not config.use_tls and config.smtp_port != 465:
            warnings.append("Unencrypted email transmission is insecure")
            suggestions.append("Enable TLS encryption")
        
        return ConfigValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions
        )
    
    def test_email_authentication(self, config: EmailConfig) -> TestResult:
        """
        Test email authentication without sending an email
        
        Args:
            config: Email configuration to test
            
        Returns:
            TestResult with authentication test details
        """
        start_time = time.time()
        test_result = TestResult(
            success=False,
            provider=config.provider.value,
            connection_test=False,
            auth_test=False,
            send_test=False,
            error_messages=[],
            test_duration=0.0
        )
        
        try:
            # Test connection first
            conn_result = self.test_smtp_connection(config)
            test_result.connection_test = conn_result.success
            
            if not conn_result.success:
                test_result.error_messages.append(f"Connection failed: {conn_result.error_message}")
                return test_result
            
            # Test authentication
            if config.smtp_port == 465:  # SSL
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL(config.smtp_server, config.smtp_port, context=context) as server:
                    server.login(config.sender_email, config.sender_password)
                    test_result.auth_test = True
            else:  # TLS
                with smtplib.SMTP(config.smtp_server, config.smtp_port) as server:
                    server.ehlo()
                    if config.use_tls:
                        server.starttls()
                        server.ehlo()
                    server.login(config.sender_email, config.sender_password)
                    test_result.auth_test = True
            
            test_result.success = test_result.connection_test and test_result.auth_test
            
        except smtplib.SMTPAuthenticationError as e:
            test_result.error_messages.append(f"Authentication failed: {str(e)}")
        except smtplib.SMTPException as e:
            test_result.error_messages.append(f"SMTP error: {str(e)}")
        except Exception as e:
            test_result.error_messages.append(f"Unexpected error: {str(e)}")
        
        test_result.test_duration = time.time() - start_time
        self.test_results.append(test_result)
        return test_result
    
    def send_test_email(self, config: EmailConfig, recipient: str, 
                       subject: str = "Email Service Test") -> TestResult:
        """
        Send a test email to verify complete functionality
        
        Args:
            config: Email configuration to use
            recipient: Test email recipient
            subject: Test email subject
            
        Returns:
            TestResult with complete test details
        """
        start_time = time.time()
        test_result = TestResult(
            success=False,
            provider=config.provider.value,
            connection_test=False,
            auth_test=False,
            send_test=False,
            error_messages=[],
            test_duration=0.0
        )
        
        try:
            # First test authentication
            auth_result = self.test_email_authentication(config)
            test_result.connection_test = auth_result.connection_test
            test_result.auth_test = auth_result.auth_test
            test_result.error_messages.extend(auth_result.error_messages)
            
            if not auth_result.success:
                return test_result
            
            # Send test email
            test_body = f"""
This is a test email from the Driver Assistant Email Service.

Test Details:
- Provider: {config.provider.value}
- Server: {config.smtp_server}:{config.smtp_port}
- Timestamp: {datetime.now().isoformat()}
- Authentication: {config.auth_method.value}

If you received this email, the email service is working correctly.
"""
            
            email_data = EmailData(
                recipient=recipient,
                subject=subject,
                body=test_body,
                template_name="system_test",
                template_data={"timestamp": datetime.now().isoformat()},
                priority=Priority.HIGH
            )
            
            # Use the actual email sending logic
            if config.smtp_port == 465:  # SSL
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL(config.smtp_server, config.smtp_port, context=context) as server:
                    server.login(config.sender_email, config.sender_password)
                    message = self._create_email_message(config, email_data)
                    server.send_message(message)
                    test_result.send_test = True
            else:  # TLS
                with smtplib.SMTP(config.smtp_server, config.smtp_port) as server:
                    server.ehlo()
                    if config.use_tls:
                        server.starttls()
                        server.ehlo()
                    server.login(config.sender_email, config.sender_password)
                    message = self._create_email_message(config, email_data)
                    server.send_message(message)
                    test_result.send_test = True
            
            test_result.success = all([
                test_result.connection_test,
                test_result.auth_test,
                test_result.send_test
            ])
            
        except Exception as e:
            test_result.error_messages.append(f"Send test failed: {str(e)}")
        
        test_result.test_duration = time.time() - start_time
        self.test_results.append(test_result)
        return test_result
    
    def _create_email_message(self, config: EmailConfig, email_data: EmailData):
        """Create email message for sending"""
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        message = MIMEMultipart()
        message["From"] = config.sender_email
        message["To"] = email_data.recipient
        message["Subject"] = email_data.subject
        
        message.attach(MIMEText(email_data.body, "plain"))
        
        if email_data.html_body:
            message.attach(MIMEText(email_data.html_body, "html"))
        
        return message
    
    def get_test_summary(self) -> Dict[str, Any]:
        """Get summary of all test results"""
        if not self.test_results:
            return {"message": "No tests have been run"}
        
        total_tests = len(self.test_results)
        successful_tests = sum(1 for result in self.test_results if result.success)
        
        return {
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "success_rate": successful_tests / total_tests * 100,
            "average_duration": sum(r.test_duration for r in self.test_results) / total_tests,
            "providers_tested": list(set(r.provider for r in self.test_results)),
            "common_errors": self._get_common_errors()
        }
    
    def _get_common_errors(self) -> List[str]:
        """Get most common error messages from test results"""
        error_counts = {}
        for result in self.test_results:
            for error in result.error_messages:
                error_counts[error] = error_counts.get(error, 0) + 1
        
        return sorted(error_counts.keys(), key=lambda x: error_counts[x], reverse=True)[:5]


class MockEmailProvider(EmailProvider):
    """Mock email provider for unit testing"""
    
    def __init__(self, should_fail: bool = False, fail_on: str = None):
        self.should_fail = should_fail
        self.fail_on = fail_on  # 'configure', 'test_connection', 'send_email'
        self.configured = False
        self.config = None
        self.sent_emails = []
        self.connection_tested = False
    
    def configure(self, config: EmailConfig) -> bool:
        if self.should_fail and self.fail_on == 'configure':
            return False
        self.configured = True
        self.config = config
        return True
    
    def test_connection(self) -> bool:
        if self.should_fail and self.fail_on == 'test_connection':
            return False
        self.connection_tested = True
        return self.configured
    
    def send_email(self, email_data: EmailData) -> EmailResult:
        if self.should_fail and self.fail_on == 'send_email':
            return EmailResult(
                success=False,
                message="Mock send failure",
                email_id=None
            )
        
        email_id = f"mock_{len(self.sent_emails) + 1}"
        self.sent_emails.append({
            'id': email_id,
            'data': email_data,
            'timestamp': datetime.now()
        })
        
        return EmailResult(
            success=True,
            message="Mock email sent successfully",
            email_id=email_id
        )
    
    def validate_config(self, config: EmailConfig) -> List[str]:
        errors = []
        if not config.sender_email:
            errors.append("Sender email is required")
        if not config.smtp_server:
            errors.append("SMTP server is required")
        return errors
    
    def get_sent_emails(self) -> List[Dict]:
        """Get list of emails sent through this mock provider"""
        return self.sent_emails.copy()
    
    def reset(self):
        """Reset mock provider state"""
        self.sent_emails.clear()
        self.configured = False
        self.connection_tested = False
        self.config = None


class MockSMTPServer:
    """Mock SMTP server for testing"""
    
    def __init__(self, fail_on: Optional[str] = None):
        self.fail_on = fail_on
        self.connected = False
        self.authenticated = False
        self.messages_sent = []
        self.ehlo_called = False
        self.starttls_called = False
    
    def __enter__(self):
        self.connected = True
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.connected = False
    
    def ehlo(self):
        if self.fail_on == 'ehlo':
            raise smtplib.SMTPException("EHLO failed")
        self.ehlo_called = True
    
    def starttls(self):
        if self.fail_on == 'starttls':
            raise smtplib.SMTPException("STARTTLS failed")
        self.starttls_called = True
    
    def login(self, username: str, password: str):
        if self.fail_on == 'login':
            raise smtplib.SMTPAuthenticationError(535, "Authentication failed")
        self.authenticated = True
    
    def send_message(self, message):
        if self.fail_on == 'send':
            raise smtplib.SMTPException("Send failed")
        self.messages_sent.append(message)
    
    def has_extn(self, extension: str) -> bool:
        return extension.upper() in ['STARTTLS', 'AUTH']
    
    @property
    def esmtp_features(self):
        return {'auth': 'PLAIN LOGIN'}


def create_test_config(provider: ProviderType = ProviderType.GMAIL) -> EmailConfig:
    """Create a test email configuration"""
    configs = {
        ProviderType.GMAIL: EmailConfig(
            provider=ProviderType.GMAIL,
            smtp_server="smtp.gmail.com",
            smtp_port=587,
            use_tls=True,
            sender_email="test@gmail.com",
            sender_password="test_password",
            auth_method=AuthMethod.APP_PASSWORD
        ),
        ProviderType.OUTLOOK: EmailConfig(
            provider=ProviderType.OUTLOOK,
            smtp_server="smtp-mail.outlook.com",
            smtp_port=587,
            use_tls=True,
            sender_email="test@outlook.com",
            sender_password="test_password",
            auth_method=AuthMethod.PASSWORD
        ),
        ProviderType.YAHOO: EmailConfig(
            provider=ProviderType.YAHOO,
            smtp_server="smtp.mail.yahoo.com",
            smtp_port=587,
            use_tls=True,
            sender_email="test@yahoo.com",
            sender_password="test_password",
            auth_method=AuthMethod.APP_PASSWORD
        )
    }
    return configs.get(provider, configs[ProviderType.GMAIL])


def create_test_email_data(recipient: str = "test@example.com") -> EmailData:
    """Create test email data"""
    return EmailData(
        recipient=recipient,
        subject="Test Email",
        body="This is a test email body",
        template_name="test_template",
        template_data={"user_name": "Test User", "timestamp": datetime.now().isoformat()},
        priority=Priority.NORMAL
    )


def create_test_user_data() -> UserData:
    """Create test user data"""
    return UserData(
        name="Test User",
        email="testuser@example.com",
        user_id="test_123"
    )


def create_test_alert_data() -> AlertData:
    """Create test alert data"""
    return AlertData(
        alert_type=AlertType.DROWSINESS,
        timestamp=datetime.now(),
        heart_rate=75,
        oxygen_saturation=98.5
    )