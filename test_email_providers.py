"""
Unit tests for email providers
"""

import pytest
import smtplib
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from email_service.providers import (
    GmailProvider, OutlookProvider, YahooProvider, CustomSMTPProvider,
    EmailProviderFactory, BaseEmailProvider
)
from email_service.models import EmailConfig, EmailData, EmailResult
from email_service.enums import ProviderType, AuthMethod, Priority


class TestBaseEmailProvider:
    """Test cases for BaseEmailProvider"""
    
    def test_configure_valid_config(self):
        """Test configuring provider with valid configuration"""
        provider = GmailProvider()  # Use concrete implementation
        config = EmailConfig(
            provider=ProviderType.GMAIL,
            smtp_server="smtp.gmail.com",
            smtp_port=587,
            use_tls=True,
            sender_email="test@gmail.com",
            sender_password="password123",
            auth_method=AuthMethod.APP_PASSWORD
        )
        
        result = provider.configure(config)
        assert result is True
        assert provider.config == config
    
    def test_configure_invalid_config(self):
        """Test configuring provider with invalid configuration"""
        provider = GmailProvider()
        # Create a valid config first, then modify it to bypass __post_init__ validation
        config = EmailConfig(
            provider=ProviderType.GMAIL,
            smtp_server="smtp.gmail.com",
            smtp_port=587,
            use_tls=True,
            sender_email="test@gmail.com",
            sender_password="password",
            auth_method=AuthMethod.APP_PASSWORD
        )
        
        # Modify config to make it invalid after creation
        config.smtp_server = ""
        config.sender_password = ""
        
        result = provider.configure(config)
        assert result is False
    
    def test_validate_config_errors(self):
        """Test configuration validation with various errors"""
        provider = GmailProvider()
        # Create a valid config first, then modify it to test validation
        config = EmailConfig(
            provider=ProviderType.GMAIL,
            smtp_server="smtp.gmail.com",
            smtp_port=587,
            use_tls=True,
            sender_email="test@gmail.com",
            sender_password="password",
            auth_method=AuthMethod.APP_PASSWORD
        )
        
        # Modify config to introduce errors
        config.smtp_server = ""
        config.smtp_port = 99999
        config.sender_email = "invalid"
        config.sender_password = ""
        
        errors = provider.validate_config(config)
        assert len(errors) > 0
        assert any("email" in error.lower() for error in errors)
        assert any("server" in error.lower() for error in errors)
        assert any("port" in error.lower() for error in errors)
        assert any("password" in error.lower() for error in errors)


class TestGmailProvider:
    """Test cases for GmailProvider"""
    
    def test_validate_config_valid_gmail(self):
        """Test Gmail configuration validation with valid config"""
        provider = GmailProvider()
        config = EmailConfig(
            provider=ProviderType.GMAIL,
            smtp_server="smtp.gmail.com",
            smtp_port=587,
            use_tls=True,
            sender_email="test@gmail.com",
            sender_password="app_password",
            auth_method=AuthMethod.APP_PASSWORD
        )
        
        errors = provider.validate_config(config)
        assert len(errors) == 0
    
    def test_validate_config_password_warning(self):
        """Test Gmail validation shows warning for regular password"""
        provider = GmailProvider()
        config = EmailConfig(
            provider=ProviderType.GMAIL,
            smtp_server="smtp.gmail.com",
            smtp_port=587,
            use_tls=True,
            sender_email="test@gmail.com",
            sender_password="regular_password",
            auth_method=AuthMethod.PASSWORD
        )
        
        errors = provider.validate_config(config)
        assert any("App Passwords" in error for error in errors)
    
    def test_validate_config_invalid_gmail_server(self):
        """Test Gmail validation with wrong server"""
        provider = GmailProvider()
        config = EmailConfig(
            provider=ProviderType.GMAIL,
            smtp_server="wrong.server.com",
            smtp_port=587,
            use_tls=True,
            sender_email="test@gmail.com",
            sender_password="password",
            auth_method=AuthMethod.APP_PASSWORD
        )
        
        errors = provider.validate_config(config)
        assert any("smtp.gmail.com" in error for error in errors)
    
    def test_validate_config_invalid_gmail_port(self):
        """Test Gmail validation with wrong port"""
        provider = GmailProvider()
        config = EmailConfig(
            provider=ProviderType.GMAIL,
            smtp_server="smtp.gmail.com",
            smtp_port=25,  # Invalid for Gmail
            use_tls=True,
            sender_email="test@gmail.com",
            sender_password="password",
            auth_method=AuthMethod.APP_PASSWORD
        )
        
        errors = provider.validate_config(config)
        assert any("465" in error or "587" in error for error in errors)
    
    def test_validate_config_invalid_gmail_email(self):
        """Test Gmail validation with non-Gmail email"""
        provider = GmailProvider()
        config = EmailConfig(
            provider=ProviderType.GMAIL,
            smtp_server="smtp.gmail.com",
            smtp_port=587,
            use_tls=True,
            sender_email="test@yahoo.com",  # Wrong domain
            sender_password="password",
            auth_method=AuthMethod.APP_PASSWORD
        )
        
        errors = provider.validate_config(config)
        assert any("@gmail.com" in error for error in errors)
    
    @patch('smtplib.SMTP')
    def test_create_smtp_connection_tls(self, mock_smtp):
        """Test Gmail SMTP connection creation with TLS"""
        provider = GmailProvider()
        config = EmailConfig(
            provider=ProviderType.GMAIL,
            smtp_server="smtp.gmail.com",
            smtp_port=587,
            use_tls=True,
            sender_email="test@gmail.com",
            sender_password="password",
            auth_method=AuthMethod.APP_PASSWORD
        )
        provider.configure(config)
        
        mock_server = Mock()
        mock_smtp.return_value = mock_server
        
        result = provider._create_smtp_connection()
        
        mock_smtp.assert_called_once_with("smtp.gmail.com", 587, timeout=30)
        mock_server.starttls.assert_called_once()
        assert result == mock_server
    
    @patch('smtplib.SMTP_SSL')
    def test_create_smtp_connection_ssl(self, mock_smtp_ssl):
        """Test Gmail SMTP connection creation with SSL"""
        provider = GmailProvider()
        config = EmailConfig(
            provider=ProviderType.GMAIL,
            smtp_server="smtp.gmail.com",
            smtp_port=465,
            use_tls=True,
            sender_email="test@gmail.com",
            sender_password="password",
            auth_method=AuthMethod.APP_PASSWORD
        )
        provider.configure(config)
        
        mock_server = Mock()
        mock_smtp_ssl.return_value = mock_server
        
        result = provider._create_smtp_connection()
        
        mock_smtp_ssl.assert_called_once()
        assert result == mock_server
    
    @patch('smtplib.SMTP')
    def test_create_smtp_connection_error_handling(self, mock_smtp):
        """Test Gmail SMTP connection error handling"""
        provider = GmailProvider()
        config = EmailConfig(
            provider=ProviderType.GMAIL,
            smtp_server="smtp.gmail.com",
            smtp_port=587,
            use_tls=True,
            sender_email="test@gmail.com",
            sender_password="password",
            auth_method=AuthMethod.APP_PASSWORD
        )
        provider.configure(config)
        
        # Test connection error - SMTPConnectError requires code and msg parameters
        mock_smtp.side_effect = smtplib.SMTPConnectError(421, "Connection failed")
        
        with pytest.raises(smtplib.SMTPConnectError) as exc_info:
            provider._create_smtp_connection()
        
        assert "Failed to connect to Gmail SMTP server" in str(exc_info.value)
    
    @patch('smtplib.SMTP')
    def test_test_connection_success(self, mock_smtp):
        """Test successful Gmail connection test"""
        provider = GmailProvider()
        config = EmailConfig(
            provider=ProviderType.GMAIL,
            smtp_server="smtp.gmail.com",
            smtp_port=587,
            use_tls=True,
            sender_email="test@gmail.com",
            sender_password="password",
            auth_method=AuthMethod.APP_PASSWORD
        )
        provider.configure(config)
        
        mock_server = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        result = provider.test_connection()
        
        assert result is True
        mock_server.login.assert_called_once_with("test@gmail.com", "password")
    
    @patch('smtplib.SMTP')
    def test_test_connection_auth_failure(self, mock_smtp):
        """Test Gmail connection test with authentication failure"""
        provider = GmailProvider()
        config = EmailConfig(
            provider=ProviderType.GMAIL,
            smtp_server="smtp.gmail.com",
            smtp_port=587,
            use_tls=True,
            sender_email="test@gmail.com",
            sender_password="wrong_password",
            auth_method=AuthMethod.APP_PASSWORD
        )
        provider.configure(config)
        
        mock_server = Mock()
        mock_server.login.side_effect = smtplib.SMTPAuthenticationError(535, "Authentication failed")
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        result = provider.test_connection()
        
        assert result is False
    
    @patch('smtplib.SMTP')
    def test_send_email_success_with_details(self, mock_smtp):
        """Test successful Gmail email sending with detailed response"""
        provider = GmailProvider()
        config = EmailConfig(
            provider=ProviderType.GMAIL,
            smtp_server="smtp.gmail.com",
            smtp_port=587,
            use_tls=True,
            sender_email="test@gmail.com",
            sender_password="password",
            auth_method=AuthMethod.APP_PASSWORD
        )
        provider.configure(config)
        
        mock_server = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        email_data = EmailData(
            recipient="recipient@example.com",
            subject="Test Subject",
            body="Test body content",
            template_name="test",
            template_data={}
        )
        
        result = provider.send_email(email_data)
        
        assert result.success is True
        assert "Gmail" in result.message
        assert result.details["provider"] == "Gmail"
        assert result.details["smtp_server"] == "smtp.gmail.com"
        assert result.details["smtp_port"] == 587
    
    @patch('smtplib.SMTP')
    def test_send_email_auth_error_535(self, mock_smtp):
        """Test Gmail email sending with specific 535 auth error"""
        provider = GmailProvider()
        config = EmailConfig(
            provider=ProviderType.GMAIL,
            smtp_server="smtp.gmail.com",
            smtp_port=587,
            use_tls=True,
            sender_email="test@gmail.com",
            sender_password="wrong_password",
            auth_method=AuthMethod.APP_PASSWORD
        )
        provider.configure(config)
        
        mock_server = Mock()
        mock_server.login.side_effect = smtplib.SMTPAuthenticationError(535, "Authentication failed")
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        email_data = EmailData(
            recipient="recipient@example.com",
            subject="Test Subject",
            body="Test body content",
            template_name="test",
            template_data={}
        )
        
        result = provider.send_email(email_data)
        
        assert result.success is False
        assert "App Password required" in result.message
        assert result.details["error_type"] == "auth"
        assert "troubleshooting" in result.details
        assert len(result.details["troubleshooting"]) > 0
    
    @patch('smtplib.SMTP')
    def test_send_email_connection_error(self, mock_smtp):
        """Test Gmail email sending with connection error"""
        provider = GmailProvider()
        config = EmailConfig(
            provider=ProviderType.GMAIL,
            smtp_server="smtp.gmail.com",
            smtp_port=587,
            use_tls=True,
            sender_email="test@gmail.com",
            sender_password="password",
            auth_method=AuthMethod.APP_PASSWORD
        )
        provider.configure(config)
        
        # SMTPConnectError requires code and msg parameters
        mock_smtp.side_effect = smtplib.SMTPConnectError(421, "Connection refused")
        
        email_data = EmailData(
            recipient="recipient@example.com",
            subject="Test Subject",
            body="Test body content",
            template_name="test",
            template_data={}
        )
        
        result = provider.send_email(email_data)
        
        assert result.success is False
        assert "connect to Gmail SMTP server" in result.message
        assert result.details["error_type"] == "network"
        assert "troubleshooting" in result.details
    
    @patch('smtplib.SMTP')
    def test_send_email_recipients_refused(self, mock_smtp):
        """Test Gmail email sending with recipients refused error"""
        provider = GmailProvider()
        config = EmailConfig(
            provider=ProviderType.GMAIL,
            smtp_server="smtp.gmail.com",
            smtp_port=587,
            use_tls=True,
            sender_email="test@gmail.com",
            sender_password="password",
            auth_method=AuthMethod.APP_PASSWORD
        )
        provider.configure(config)
        
        mock_server = Mock()
        mock_server.send_message.side_effect = smtplib.SMTPRecipientsRefused({})
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        email_data = EmailData(
            recipient="invalid@example.com",
            subject="Test Subject",
            body="Test body content",
            template_name="test",
            template_data={}
        )
        
        result = provider.send_email(email_data)
        
        assert result.success is False
        assert "rejected recipient" in result.message
        assert result.details["error_type"] == "recipient"
    
    @patch('smtplib.SMTP')
    def test_send_email_data_error(self, mock_smtp):
        """Test Gmail email sending with data error"""
        provider = GmailProvider()
        config = EmailConfig(
            provider=ProviderType.GMAIL,
            smtp_server="smtp.gmail.com",
            smtp_port=587,
            use_tls=True,
            sender_email="test@gmail.com",
            sender_password="password",
            auth_method=AuthMethod.APP_PASSWORD
        )
        provider.configure(config)
        
        mock_server = Mock()
        mock_server.send_message.side_effect = smtplib.SMTPDataError(550, "Message rejected")
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        email_data = EmailData(
            recipient="recipient@example.com",
            subject="Test Subject",
            body="Test body content",
            template_name="test",
            template_data={}
        )
        
        result = provider.send_email(email_data)
        
        assert result.success is False
        assert "rejected email content" in result.message
        assert result.details["error_type"] == "content"
    
    def test_get_gmail_specific_info(self):
        """Test Gmail-specific information retrieval"""
        provider = GmailProvider()
        info = provider.get_gmail_specific_info()
        
        assert info["provider"] == "Gmail"
        assert info["smtp_server"] == "smtp.gmail.com"
        assert 465 in info["supported_ports"]
        assert 587 in info["supported_ports"]
        assert "port_descriptions" in info
        assert "auth_methods" in info
        assert "security_notes" in info
        assert "troubleshooting_url" in info


class TestOutlookProvider:
    """Test cases for OutlookProvider"""
    
    def test_validate_config_valid_outlook(self):
        """Test Outlook configuration validation with valid config"""
        provider = OutlookProvider()
        config = EmailConfig(
            provider=ProviderType.OUTLOOK,
            smtp_server="smtp-mail.outlook.com",
            smtp_port=587,
            use_tls=True,
            sender_email="test@outlook.com",
            sender_password="password",
            auth_method=AuthMethod.APP_PASSWORD
        )
        
        errors = provider.validate_config(config)
        assert len(errors) == 0
    
    def test_validate_config_valid_outlook_domains(self):
        """Test Outlook validation with various valid domains"""
        provider = OutlookProvider()
        valid_emails = [
            "test@outlook.com",
            "test@hotmail.com", 
            "test@live.com",
            "test@msn.com"
        ]
        
        for email in valid_emails:
            config = EmailConfig(
                provider=ProviderType.OUTLOOK,
                smtp_server="smtp-mail.outlook.com",
                smtp_port=587,
                use_tls=True,
                sender_email=email,
                sender_password="password",
                auth_method=AuthMethod.APP_PASSWORD
            )
            
            errors = provider.validate_config(config)
            domain_errors = [e for e in errors if "email address" in e.lower()]
            assert len(domain_errors) == 0, f"Failed for email: {email}"
    
    def test_validate_config_invalid_outlook_server(self):
        """Test Outlook validation with wrong server"""
        provider = OutlookProvider()
        config = EmailConfig(
            provider=ProviderType.OUTLOOK,
            smtp_server="smtp.gmail.com",  # Wrong server
            smtp_port=587,
            use_tls=True,
            sender_email="test@outlook.com",
            sender_password="password",
            auth_method=AuthMethod.APP_PASSWORD
        )
        
        errors = provider.validate_config(config)
        assert any("smtp-mail.outlook.com" in error for error in errors)
    
    @patch('smtplib.SMTP')
    def test_create_smtp_connection(self, mock_smtp):
        """Test Outlook SMTP connection creation"""
        provider = OutlookProvider()
        config = EmailConfig(
            provider=ProviderType.OUTLOOK,
            smtp_server="smtp-mail.outlook.com",
            smtp_port=587,
            use_tls=True,
            sender_email="test@outlook.com",
            sender_password="password",
            auth_method=AuthMethod.APP_PASSWORD
        )
        provider.configure(config)
        
        mock_server = Mock()
        mock_smtp.return_value = mock_server
        
        result = provider._create_smtp_connection()
        
        mock_smtp.assert_called_once_with("smtp-mail.outlook.com", 587, timeout=30)
        mock_server.starttls.assert_called_once()
        assert result == mock_server


class TestYahooProvider:
    """Test cases for YahooProvider"""
    
    def test_validate_config_valid_yahoo(self):
        """Test Yahoo configuration validation with valid config"""
        provider = YahooProvider()
        config = EmailConfig(
            provider=ProviderType.YAHOO,
            smtp_server="smtp.mail.yahoo.com",
            smtp_port=587,
            use_tls=True,
            sender_email="test@yahoo.com",
            sender_password="password",
            auth_method=AuthMethod.APP_PASSWORD
        )
        
        errors = provider.validate_config(config)
        assert len(errors) == 0
    
    def test_validate_config_invalid_yahoo_email(self):
        """Test Yahoo validation with non-Yahoo email"""
        provider = YahooProvider()
        config = EmailConfig(
            provider=ProviderType.YAHOO,
            smtp_server="smtp.mail.yahoo.com",
            smtp_port=587,
            use_tls=True,
            sender_email="test@gmail.com",  # Wrong domain
            sender_password="password",
            auth_method=AuthMethod.APP_PASSWORD
        )
        
        errors = provider.validate_config(config)
        assert any("@yahoo.com" in error for error in errors)


class TestCustomSMTPProvider:
    """Test cases for CustomSMTPProvider"""
    
    def test_validate_config_valid_custom(self):
        """Test Custom SMTP configuration validation with valid config"""
        provider = CustomSMTPProvider()
        config = EmailConfig(
            provider=ProviderType.CUSTOM,
            smtp_server="mail.example.com",
            smtp_port=587,
            use_tls=True,
            sender_email="test@example.com",
            sender_password="password",
            auth_method=AuthMethod.PASSWORD
        )
        
        errors = provider.validate_config(config)
        assert len(errors) == 0
    
    def test_validate_config_empty_server(self):
        """Test Custom SMTP validation with empty server"""
        provider = CustomSMTPProvider()
        # Create valid config first, then modify it
        config = EmailConfig(
            provider=ProviderType.CUSTOM,
            smtp_server="mail.example.com",
            smtp_port=587,
            use_tls=True,
            sender_email="test@example.com",
            sender_password="password",
            auth_method=AuthMethod.PASSWORD
        )
        
        # Modify to make server empty
        config.smtp_server = ""
        
        errors = provider.validate_config(config)
        assert any("server must be specified" in error.lower() for error in errors)
    
    @patch('smtplib.SMTP')
    def test_create_smtp_connection_tls(self, mock_smtp):
        """Test Custom SMTP connection creation with TLS"""
        provider = CustomSMTPProvider()
        config = EmailConfig(
            provider=ProviderType.CUSTOM,
            smtp_server="mail.example.com",
            smtp_port=587,
            use_tls=True,
            sender_email="test@example.com",
            sender_password="password",
            auth_method=AuthMethod.PASSWORD
        )
        provider.configure(config)
        
        mock_server = Mock()
        mock_smtp.return_value = mock_server
        
        result = provider._create_smtp_connection()
        
        mock_smtp.assert_called_once_with("mail.example.com", 587, timeout=30)
        mock_server.starttls.assert_called_once()
        assert result == mock_server
    
    @patch('smtplib.SMTP_SSL')
    def test_create_smtp_connection_ssl(self, mock_smtp_ssl):
        """Test Custom SMTP connection creation with SSL"""
        provider = CustomSMTPProvider()
        config = EmailConfig(
            provider=ProviderType.CUSTOM,
            smtp_server="mail.example.com",
            smtp_port=465,
            use_tls=True,
            sender_email="test@example.com",
            sender_password="password",
            auth_method=AuthMethod.PASSWORD
        )
        provider.configure(config)
        
        mock_server = Mock()
        mock_smtp_ssl.return_value = mock_server
        
        result = provider._create_smtp_connection()
        
        mock_smtp_ssl.assert_called_once()
        assert result == mock_server
    
    @patch('smtplib.SMTP')
    def test_create_smtp_connection_no_tls(self, mock_smtp):
        """Test Custom SMTP connection creation without TLS"""
        provider = CustomSMTPProvider()
        config = EmailConfig(
            provider=ProviderType.CUSTOM,
            smtp_server="mail.example.com",
            smtp_port=25,
            use_tls=False,  # No TLS
            sender_email="test@example.com",
            sender_password="password",
            auth_method=AuthMethod.PASSWORD
        )
        provider.configure(config)
        
        mock_server = Mock()
        mock_smtp.return_value = mock_server
        
        result = provider._create_smtp_connection()
        
        mock_smtp.assert_called_once_with("mail.example.com", 25, timeout=30)
        mock_server.starttls.assert_not_called()
        assert result == mock_server


class TestEmailProviderFactory:
    """Test cases for EmailProviderFactory"""
    
    def test_create_gmail_provider(self):
        """Test creating Gmail provider"""
        provider = EmailProviderFactory.create_provider(ProviderType.GMAIL)
        assert isinstance(provider, GmailProvider)
        assert provider.provider_name == "Gmail"
    
    def test_create_outlook_provider(self):
        """Test creating Outlook provider"""
        provider = EmailProviderFactory.create_provider(ProviderType.OUTLOOK)
        assert isinstance(provider, OutlookProvider)
        assert provider.provider_name == "Outlook"
    
    def test_create_yahoo_provider(self):
        """Test creating Yahoo provider"""
        provider = EmailProviderFactory.create_provider(ProviderType.YAHOO)
        assert isinstance(provider, YahooProvider)
        assert provider.provider_name == "Yahoo"
    
    def test_create_custom_provider(self):
        """Test creating Custom SMTP provider"""
        provider = EmailProviderFactory.create_provider(ProviderType.CUSTOM)
        assert isinstance(provider, CustomSMTPProvider)
        assert provider.provider_name == "Custom SMTP"
    
    def test_create_invalid_provider(self):
        """Test creating provider with invalid type"""
        with pytest.raises(ValueError, match="Unsupported provider type"):
            EmailProviderFactory.create_provider("invalid_type")
    
    def test_get_supported_providers(self):
        """Test getting list of supported providers"""
        providers = EmailProviderFactory.get_supported_providers()
        expected = [ProviderType.GMAIL, ProviderType.OUTLOOK, ProviderType.YAHOO, ProviderType.CUSTOM]
        assert providers == expected
    
    def test_get_provider_info_gmail(self):
        """Test getting Gmail provider information"""
        info = EmailProviderFactory.get_provider_info(ProviderType.GMAIL)
        assert info["name"] == "Gmail"
        assert info["smtp_server"] == "smtp.gmail.com"
        assert 465 in info["ports"]
        assert 587 in info["ports"]
        assert AuthMethod.APP_PASSWORD in info["auth_methods"]
        assert info["requires_app_password"] is True
    
    def test_get_provider_info_outlook(self):
        """Test getting Outlook provider information"""
        info = EmailProviderFactory.get_provider_info(ProviderType.OUTLOOK)
        assert info["name"] == "Outlook"
        assert info["smtp_server"] == "smtp-mail.outlook.com"
        assert info["ports"] == [587]
        assert AuthMethod.OAUTH2 in info["auth_methods"]
        assert info["requires_app_password"] is False


class TestEmailSending:
    """Test cases for email sending functionality"""
    
    @patch('smtplib.SMTP')
    def test_send_email_success(self, mock_smtp):
        """Test successful email sending"""
        provider = GmailProvider()
        config = EmailConfig(
            provider=ProviderType.GMAIL,
            smtp_server="smtp.gmail.com",
            smtp_port=587,
            use_tls=True,
            sender_email="test@gmail.com",
            sender_password="password",
            auth_method=AuthMethod.APP_PASSWORD
        )
        provider.configure(config)
        
        # Mock SMTP server
        mock_server = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        email_data = EmailData(
            recipient="recipient@example.com",
            subject="Test Subject",
            body="Test body content",
            template_name="test",
            template_data={}
        )
        
        result = provider.send_email(email_data)
        
        assert result.success is True
        assert "successfully" in result.message.lower()
        mock_server.login.assert_called_once_with("test@gmail.com", "password")
        mock_server.send_message.assert_called_once()
    
    @patch('smtplib.SMTP')
    def test_send_email_auth_failure(self, mock_smtp):
        """Test email sending with authentication failure"""
        provider = GmailProvider()
        config = EmailConfig(
            provider=ProviderType.GMAIL,
            smtp_server="smtp.gmail.com",
            smtp_port=587,
            use_tls=True,
            sender_email="test@gmail.com",
            sender_password="wrong_password",
            auth_method=AuthMethod.APP_PASSWORD
        )
        provider.configure(config)
        
        # Mock SMTP server to raise auth error
        mock_server = Mock()
        mock_server.login.side_effect = smtplib.SMTPAuthenticationError(535, "Authentication failed")
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        email_data = EmailData(
            recipient="recipient@example.com",
            subject="Test Subject",
            body="Test body content",
            template_name="test",
            template_data={}
        )
        
        result = provider.send_email(email_data)
        
        assert result.success is False
        assert "authentication failed" in result.message.lower()
        assert result.details["error_type"] == "auth"
    
    def test_send_email_no_config(self):
        """Test email sending without configuration"""
        provider = GmailProvider()
        
        email_data = EmailData(
            recipient="recipient@example.com",
            subject="Test Subject",
            body="Test body content",
            template_name="test",
            template_data={}
        )
        
        result = provider.send_email(email_data)
        
        assert result.success is False
        assert "not configured" in result.message.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])