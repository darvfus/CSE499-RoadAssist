"""
Concrete Email Provider Implementations
"""

import smtplib
import ssl
from typing import List, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from .interfaces import EmailProvider
from .models import EmailConfig, EmailData, EmailResult
from .enums import ProviderType, AuthMethod, ErrorType


class BaseEmailProvider(EmailProvider):
    """Base implementation of EmailProvider with common functionality"""
    
    def __init__(self):
        self.config: Optional[EmailConfig] = None
        self.smtp_connection: Optional[smtplib.SMTP] = None
    
    def configure(self, config: EmailConfig) -> bool:
        """Configure the email provider with given settings"""
        try:
            validation_errors = self.validate_config(config)
            if validation_errors:
                return False
            
            self.config = config
            return True
        except Exception:
            return False
    
    def validate_config(self, config: EmailConfig) -> List[str]:
        """Validate configuration and return list of errors"""
        errors = []
        
        if not config.sender_email or "@" not in config.sender_email:
            errors.append("Invalid sender email address")
        
        if not config.smtp_server:
            errors.append("SMTP server cannot be empty")
        
        if not (1 <= config.smtp_port <= 65535):
            errors.append("SMTP port must be between 1 and 65535")
        
        if not config.sender_password:
            errors.append("Sender password cannot be empty")
        
        return errors
    
    def test_connection(self) -> bool:
        """Test connection to the email server"""
        if not self.config:
            return False
        
        try:
            with self._create_smtp_connection() as server:
                server.login(self.config.sender_email, self.config.sender_password)
                return True
        except Exception:
            return False
    
    def send_email(self, email_data: EmailData) -> EmailResult:
        """Send an email using this provider"""
        if not self.config:
            return EmailResult(
                success=False,
                message="Provider not configured",
                details={"error": "No configuration available"}
            )
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.config.sender_email
            msg['To'] = email_data.recipient
            msg['Subject'] = email_data.subject
            
            # Add text body
            text_part = MIMEText(email_data.body, 'plain')
            msg.attach(text_part)
            
            # Add HTML body if available
            if email_data.html_body:
                html_part = MIMEText(email_data.html_body, 'html')
                msg.attach(html_part)
            
            # Send email
            with self._create_smtp_connection() as server:
                server.login(self.config.sender_email, self.config.sender_password)
                server.send_message(msg)
            
            return EmailResult(
                success=True,
                message="Email sent successfully",
                details={"recipient": email_data.recipient}
            )
            
        except smtplib.SMTPAuthenticationError as e:
            return EmailResult(
                success=False,
                message="Authentication failed",
                details={"error": str(e), "error_type": "auth"}
            )
        except smtplib.SMTPConnectError as e:
            return EmailResult(
                success=False,
                message="Connection failed",
                details={"error": str(e), "error_type": "network"}
            )
        except Exception as e:
            return EmailResult(
                success=False,
                message="Failed to send email",
                details={"error": str(e), "error_type": "general"}
            )
    
    def _create_smtp_connection(self) -> smtplib.SMTP:
        """Create SMTP connection - to be overridden by subclasses"""
        raise NotImplementedError("Subclasses must implement _create_smtp_connection")


class GmailProvider(BaseEmailProvider):
    """Gmail email provider implementation with enhanced error handling"""
    
    def __init__(self):
        super().__init__()
        self.provider_name = "Gmail"
    
    def validate_config(self, config: EmailConfig) -> List[str]:
        """Validate Gmail-specific configuration"""
        errors = super().validate_config(config)
        
        # Gmail-specific validations
        if config.provider != ProviderType.GMAIL:
            errors.append("Provider type must be GMAIL")
        
        if config.smtp_server and config.smtp_server != "smtp.gmail.com":
            errors.append("Gmail SMTP server must be smtp.gmail.com")
        
        if config.smtp_port not in [465, 587]:
            errors.append("Gmail SMTP port must be 465 (SSL) or 587 (TLS)")
        
        if not config.sender_email.endswith("@gmail.com"):
            errors.append("Gmail provider requires a @gmail.com email address")
        
        if config.auth_method not in [AuthMethod.APP_PASSWORD, AuthMethod.PASSWORD]:
            errors.append("Gmail supports APP_PASSWORD or PASSWORD authentication")
        
        # Gmail-specific security recommendations
        if config.auth_method == AuthMethod.PASSWORD:
            errors.append("Gmail strongly recommends using App Passwords instead of regular passwords for security")
        
        return errors
    
    def test_connection(self) -> bool:
        """Test connection to Gmail with enhanced error handling"""
        if not self.config:
            return False
        
        try:
            with self._create_smtp_connection() as server:
                # Test authentication
                server.login(self.config.sender_email, self.config.sender_password)
                return True
        except smtplib.SMTPAuthenticationError as e:
            # Gmail-specific authentication error handling
            error_code = e.smtp_code if hasattr(e, 'smtp_code') else 0
            if error_code == 535:
                # Most common Gmail auth error - likely App Password issue
                print(f"Gmail Authentication Error: {e}")
                print("Troubleshooting steps:")
                print("1. Ensure 2-Factor Authentication is enabled on your Gmail account")
                print("2. Generate an App Password in your Google Account settings")
                print("3. Use the App Password instead of your regular Gmail password")
                print("4. Verify your email address is correct")
            return False
        except smtplib.SMTPConnectError as e:
            print(f"Gmail Connection Error: {e}")
            print("Troubleshooting steps:")
            print("1. Check your internet connection")
            print("2. Verify Gmail SMTP server (smtp.gmail.com) is accessible")
            print("3. Check if your firewall is blocking SMTP ports (465/587)")
            return False
        except Exception as e:
            print(f"Gmail Connection Error: {e}")
            return False
    
    def send_email(self, email_data: EmailData) -> EmailResult:
        """Send email via Gmail with enhanced error handling"""
        if not self.config:
            return EmailResult(
                success=False,
                message="Gmail provider not configured",
                details={"error": "No configuration available", "provider": "Gmail"}
            )
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.config.sender_email
            msg['To'] = email_data.recipient
            msg['Subject'] = email_data.subject
            
            # Add text body
            text_part = MIMEText(email_data.body, 'plain')
            msg.attach(text_part)
            
            # Add HTML body if available
            if email_data.html_body:
                html_part = MIMEText(email_data.html_body, 'html')
                msg.attach(html_part)
            
            # Send email with Gmail-specific connection handling
            with self._create_smtp_connection() as server:
                server.login(self.config.sender_email, self.config.sender_password)
                server.send_message(msg)
            
            return EmailResult(
                success=True,
                message="Email sent successfully via Gmail",
                details={
                    "recipient": email_data.recipient,
                    "provider": "Gmail",
                    "smtp_server": self.config.smtp_server,
                    "smtp_port": self.config.smtp_port
                }
            )
            
        except smtplib.SMTPAuthenticationError as e:
            error_code = e.smtp_code if hasattr(e, 'smtp_code') else 0
            if error_code == 535:
                return EmailResult(
                    success=False,
                    message="Gmail authentication failed - App Password required",
                    details={
                        "error": str(e),
                        "error_type": "auth",
                        "provider": "Gmail",
                        "troubleshooting": [
                            "Enable 2-Factor Authentication on Gmail",
                            "Generate App Password in Google Account settings",
                            "Use App Password instead of regular password",
                            "Verify email address is correct"
                        ]
                    }
                )
            else:
                return EmailResult(
                    success=False,
                    message="Gmail authentication failed",
                    details={
                        "error": str(e),
                        "error_type": "auth",
                        "provider": "Gmail",
                        "error_code": error_code
                    }
                )
        except smtplib.SMTPConnectError as e:
            return EmailResult(
                success=False,
                message="Failed to connect to Gmail SMTP server",
                details={
                    "error": str(e),
                    "error_type": "network",
                    "provider": "Gmail",
                    "troubleshooting": [
                        "Check internet connection",
                        "Verify Gmail SMTP server accessibility",
                        "Check firewall settings for SMTP ports",
                        "Try different SMTP port (465 or 587)"
                    ]
                }
            )
        except smtplib.SMTPRecipientsRefused as e:
            return EmailResult(
                success=False,
                message="Gmail rejected recipient email address",
                details={
                    "error": str(e),
                    "error_type": "recipient",
                    "provider": "Gmail",
                    "troubleshooting": [
                        "Verify recipient email address is valid",
                        "Check if recipient domain accepts emails",
                        "Ensure sender reputation is good"
                    ]
                }
            )
        except smtplib.SMTPDataError as e:
            return EmailResult(
                success=False,
                message="Gmail rejected email content",
                details={
                    "error": str(e),
                    "error_type": "content",
                    "provider": "Gmail",
                    "troubleshooting": [
                        "Check email content for spam-like characteristics",
                        "Reduce email size if too large",
                        "Verify email format is correct"
                    ]
                }
            )
        except Exception as e:
            return EmailResult(
                success=False,
                message="Failed to send email via Gmail",
                details={
                    "error": str(e),
                    "error_type": "general",
                    "provider": "Gmail"
                }
            )
    
    def _create_smtp_connection(self) -> smtplib.SMTP:
        """Create Gmail SMTP connection with enhanced error handling"""
        if not self.config:
            raise ValueError("No configuration available")
        
        try:
            if self.config.smtp_port == 465:
                # SSL connection for port 465
                context = ssl.create_default_context()
                # Gmail-specific SSL context settings
                context.check_hostname = True
                context.verify_mode = ssl.CERT_REQUIRED
                
                server = smtplib.SMTP_SSL(
                    self.config.smtp_server, 
                    self.config.smtp_port, 
                    context=context,
                    timeout=self.config.timeout
                )
            else:
                # TLS connection for port 587
                server = smtplib.SMTP(
                    self.config.smtp_server, 
                    self.config.smtp_port,
                    timeout=self.config.timeout
                )
                # Start TLS with Gmail-specific settings
                context = ssl.create_default_context()
                context.check_hostname = True
                context.verify_mode = ssl.CERT_REQUIRED
                server.starttls(context=context)
            
            return server
            
        except smtplib.SMTPConnectError as e:
            # Re-raise with enhanced message but preserve original error structure
            error_msg = (f"Failed to connect to Gmail SMTP server {self.config.smtp_server}:{self.config.smtp_port}. "
                        f"Original error: {e}")
            raise smtplib.SMTPConnectError(e.smtp_code if hasattr(e, 'smtp_code') else 421, error_msg)
        except ssl.SSLError as e:
            raise ssl.SSLError(
                f"SSL/TLS error connecting to Gmail: {e}. "
                f"This may indicate a network or firewall issue."
            )
        except Exception as e:
            raise Exception(f"Unexpected error creating Gmail SMTP connection: {e}")
    
    def get_gmail_specific_info(self) -> dict:
        """Get Gmail-specific configuration information"""
        return {
            "provider": "Gmail",
            "smtp_server": "smtp.gmail.com",
            "supported_ports": [465, 587],
            "port_descriptions": {
                465: "SMTP over SSL (recommended)",
                587: "SMTP with STARTTLS"
            },
            "auth_methods": ["App Password (recommended)", "Regular Password (not recommended)"],
            "security_notes": [
                "2-Factor Authentication must be enabled for App Passwords",
                "App Passwords are more secure than regular passwords",
                "Regular passwords may be blocked by Gmail security",
                "Less secure app access must be enabled for regular passwords"
            ],
            "troubleshooting_url": "https://support.google.com/accounts/answer/185833"
        }


class OutlookProvider(BaseEmailProvider):
    """Outlook email provider implementation"""
    
    def __init__(self):
        super().__init__()
        self.provider_name = "Outlook"
    
    def validate_config(self, config: EmailConfig) -> List[str]:
        """Validate Outlook-specific configuration"""
        errors = super().validate_config(config)
        
        # Outlook-specific validations
        if config.provider != ProviderType.OUTLOOK:
            errors.append("Provider type must be OUTLOOK")
        
        if config.smtp_server and config.smtp_server != "smtp-mail.outlook.com":
            errors.append("Outlook SMTP server must be smtp-mail.outlook.com")
        
        if config.smtp_port != 587:
            errors.append("Outlook SMTP port must be 587")
        
        valid_domains = ["@outlook.com", "@hotmail.com", "@live.com", "@msn.com"]
        if not any(config.sender_email.endswith(domain) for domain in valid_domains):
            errors.append("Outlook provider requires an Outlook/Hotmail/Live/MSN email address")
        
        if config.auth_method not in [AuthMethod.APP_PASSWORD, AuthMethod.OAUTH2, AuthMethod.PASSWORD]:
            errors.append("Outlook supports APP_PASSWORD, OAUTH2, or PASSWORD authentication")
        
        return errors
    
    def _create_smtp_connection(self) -> smtplib.SMTP:
        """Create Outlook SMTP connection"""
        if not self.config:
            raise ValueError("No configuration available")
        
        # Outlook uses TLS on port 587
        server = smtplib.SMTP(
            self.config.smtp_server, 
            self.config.smtp_port,
            timeout=self.config.timeout
        )
        server.starttls()
        
        return server


class YahooProvider(BaseEmailProvider):
    """Yahoo email provider implementation"""
    
    def __init__(self):
        super().__init__()
        self.provider_name = "Yahoo"
    
    def validate_config(self, config: EmailConfig) -> List[str]:
        """Validate Yahoo-specific configuration"""
        errors = super().validate_config(config)
        
        # Yahoo-specific validations
        if config.provider != ProviderType.YAHOO:
            errors.append("Provider type must be YAHOO")
        
        if config.smtp_server and config.smtp_server != "smtp.mail.yahoo.com":
            errors.append("Yahoo SMTP server must be smtp.mail.yahoo.com")
        
        if config.smtp_port not in [465, 587]:
            errors.append("Yahoo SMTP port must be 465 (SSL) or 587 (TLS)")
        
        if not config.sender_email.endswith("@yahoo.com"):
            errors.append("Yahoo provider requires a @yahoo.com email address")
        
        if config.auth_method not in [AuthMethod.APP_PASSWORD, AuthMethod.PASSWORD]:
            errors.append("Yahoo supports APP_PASSWORD or PASSWORD authentication")
        
        return errors
    
    def _create_smtp_connection(self) -> smtplib.SMTP:
        """Create Yahoo SMTP connection"""
        if not self.config:
            raise ValueError("No configuration available")
        
        if self.config.smtp_port == 465:
            # SSL connection
            context = ssl.create_default_context()
            server = smtplib.SMTP_SSL(
                self.config.smtp_server, 
                self.config.smtp_port, 
                context=context,
                timeout=self.config.timeout
            )
        else:
            # TLS connection (port 587)
            server = smtplib.SMTP(
                self.config.smtp_server, 
                self.config.smtp_port,
                timeout=self.config.timeout
            )
            server.starttls()
        
        return server


class CustomSMTPProvider(BaseEmailProvider):
    """Custom SMTP provider for user-defined servers"""
    
    def __init__(self):
        super().__init__()
        self.provider_name = "Custom SMTP"
    
    def validate_config(self, config: EmailConfig) -> List[str]:
        """Validate custom SMTP configuration"""
        errors = super().validate_config(config)
        
        # Custom SMTP validations
        if config.provider != ProviderType.CUSTOM:
            errors.append("Provider type must be CUSTOM")
        
        # More flexible validation for custom providers
        if not config.smtp_server or len(config.smtp_server.strip()) == 0:
            errors.append("Custom SMTP server must be specified")
        
        if config.auth_method not in [AuthMethod.PASSWORD, AuthMethod.APP_PASSWORD]:
            errors.append("Custom SMTP supports PASSWORD or APP_PASSWORD authentication")
        
        return errors
    
    def _create_smtp_connection(self) -> smtplib.SMTP:
        """Create custom SMTP connection"""
        if not self.config:
            raise ValueError("No configuration available")
        
        if self.config.use_tls:
            if self.config.smtp_port == 465:
                # SSL connection
                context = ssl.create_default_context()
                server = smtplib.SMTP_SSL(
                    self.config.smtp_server, 
                    self.config.smtp_port, 
                    context=context,
                    timeout=self.config.timeout
                )
            else:
                # TLS connection
                server = smtplib.SMTP(
                    self.config.smtp_server, 
                    self.config.smtp_port,
                    timeout=self.config.timeout
                )
                server.starttls()
        else:
            # Plain connection (not recommended)
            server = smtplib.SMTP(
                self.config.smtp_server, 
                self.config.smtp_port,
                timeout=self.config.timeout
            )
        
        return server


class EmailProviderFactory:
    """Factory class for creating email providers"""
    
    @staticmethod
    def create_provider(provider_type: ProviderType) -> EmailProvider:
        """Create an email provider instance based on type"""
        if provider_type == ProviderType.GMAIL:
            return GmailProvider()
        elif provider_type == ProviderType.OUTLOOK:
            return OutlookProvider()
        elif provider_type == ProviderType.YAHOO:
            return YahooProvider()
        elif provider_type == ProviderType.CUSTOM:
            return CustomSMTPProvider()
        else:
            raise ValueError(f"Unsupported provider type: {provider_type}")
    
    @staticmethod
    def get_supported_providers() -> List[ProviderType]:
        """Get list of supported provider types"""
        return [
            ProviderType.GMAIL,
            ProviderType.OUTLOOK,
            ProviderType.YAHOO,
            ProviderType.CUSTOM
        ]
    
    @staticmethod
    def get_provider_info(provider_type: ProviderType) -> dict:
        """Get information about a specific provider"""
        provider_info = {
            ProviderType.GMAIL: {
                "name": "Gmail",
                "smtp_server": "smtp.gmail.com",
                "ports": [465, 587],
                "auth_methods": [AuthMethod.APP_PASSWORD, AuthMethod.PASSWORD],
                "requires_app_password": True
            },
            ProviderType.OUTLOOK: {
                "name": "Outlook",
                "smtp_server": "smtp-mail.outlook.com",
                "ports": [587],
                "auth_methods": [AuthMethod.APP_PASSWORD, AuthMethod.OAUTH2, AuthMethod.PASSWORD],
                "requires_app_password": False
            },
            ProviderType.YAHOO: {
                "name": "Yahoo",
                "smtp_server": "smtp.mail.yahoo.com",
                "ports": [465, 587],
                "auth_methods": [AuthMethod.APP_PASSWORD, AuthMethod.PASSWORD],
                "requires_app_password": True
            },
            ProviderType.CUSTOM: {
                "name": "Custom SMTP",
                "smtp_server": "user-defined",
                "ports": "user-defined",
                "auth_methods": [AuthMethod.PASSWORD, AuthMethod.APP_PASSWORD],
                "requires_app_password": False
            }
        }
        
        return provider_info.get(provider_type, {})