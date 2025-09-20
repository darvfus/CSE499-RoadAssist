"""
Email Error Handler - Comprehensive error handling for email operations
"""

import smtplib
import ssl
import socket
from typing import List, Dict, Any
from datetime import datetime

from .interfaces import EmailErrorHandler
from .models import ErrorResponse
from .enums import ErrorType


class EmailErrorHandlerImpl(EmailErrorHandler):
    """
    Concrete implementation of email error handling.
    
    Provides categorized error handling with user-friendly messages
    and specific troubleshooting steps for different error scenarios.
    """
    
    def __init__(self):
        """Initialize the error handler"""
        self.error_patterns = self._initialize_error_patterns()
    
    def handle_package_error(self, error: Exception) -> ErrorResponse:
        """Handle package installation errors"""
        error_message = str(error)
        
        if "permission" in error_message.lower():
            return ErrorResponse(
                error_type=ErrorType.PACKAGE_ERROR,
                message="Package installation failed due to permission issues",
                details=f"Permission error: {error_message}",
                troubleshooting_steps=[
                    "Run the application as administrator",
                    "Check if pip is installed and accessible",
                    "Verify write permissions to Python site-packages directory",
                    "Try installing packages manually: pip install smtplib email"
                ],
                recoverable=True
            )
        elif "network" in error_message.lower() or "connection" in error_message.lower():
            return ErrorResponse(
                error_type=ErrorType.PACKAGE_ERROR,
                message="Package installation failed due to network issues",
                details=f"Network error: {error_message}",
                troubleshooting_steps=[
                    "Check internet connection",
                    "Verify firewall settings allow pip to access PyPI",
                    "Try using a different network or VPN",
                    "Check if corporate proxy is blocking pip"
                ],
                recoverable=True
            )
        else:
            return ErrorResponse(
                error_type=ErrorType.PACKAGE_ERROR,
                message="Package installation failed",
                details=f"Installation error: {error_message}",
                troubleshooting_steps=[
                    "Check if Python and pip are properly installed",
                    "Try updating pip: python -m pip install --upgrade pip",
                    "Clear pip cache: pip cache purge",
                    "Install packages manually if needed"
                ],
                recoverable=True
            )
    
    def handle_config_error(self, error: Exception) -> ErrorResponse:
        """Handle configuration errors"""
        error_message = str(error)
        
        if "email" in error_message.lower() and "invalid" in error_message.lower():
            return ErrorResponse(
                error_type=ErrorType.CONFIG_ERROR,
                message="Invalid email address in configuration",
                details=f"Email validation error: {error_message}",
                troubleshooting_steps=[
                    "Verify sender email address format (user@domain.com)",
                    "Check for typos in email address",
                    "Ensure email domain is valid",
                    "Use a different email address if needed"
                ],
                recoverable=True
            )
        elif "port" in error_message.lower():
            return ErrorResponse(
                error_type=ErrorType.CONFIG_ERROR,
                message="Invalid SMTP port configuration",
                details=f"Port configuration error: {error_message}",
                troubleshooting_steps=[
                    "Use standard SMTP ports: 587 (TLS) or 465 (SSL)",
                    "Check provider documentation for correct port",
                    "Verify port is not blocked by firewall",
                    "Try alternative port if available"
                ],
                recoverable=True
            )
        elif "server" in error_message.lower():
            return ErrorResponse(
                error_type=ErrorType.CONFIG_ERROR,
                message="Invalid SMTP server configuration",
                details=f"Server configuration error: {error_message}",
                troubleshooting_steps=[
                    "Verify SMTP server address is correct",
                    "Check provider documentation for server details",
                    "Ensure server address doesn't contain typos",
                    "Try using IP address instead of hostname"
                ],
                recoverable=True
            )
        else:
            return ErrorResponse(
                error_type=ErrorType.CONFIG_ERROR,
                message="Email configuration error",
                details=f"Configuration error: {error_message}",
                troubleshooting_steps=[
                    "Review all configuration settings",
                    "Check provider-specific requirements",
                    "Verify all required fields are filled",
                    "Reset configuration to defaults if needed"
                ],
                recoverable=True
            )
    
    def handle_network_error(self, error: Exception) -> ErrorResponse:
        """Handle network-related errors"""
        error_type = self.get_error_type(error)
        error_message = str(error)
        
        if isinstance(error, smtplib.SMTPConnectError):
            return ErrorResponse(
                error_type=ErrorType.NETWORK_ERROR,
                message="Failed to connect to SMTP server",
                details=f"SMTP connection error: {error_message}",
                troubleshooting_steps=[
                    "Check internet connection",
                    "Verify SMTP server address and port",
                    "Check if firewall is blocking SMTP ports",
                    "Try connecting from a different network",
                    "Contact your ISP if SMTP ports are blocked"
                ],
                recoverable=True
            )
        elif isinstance(error, socket.timeout):
            return ErrorResponse(
                error_type=ErrorType.NETWORK_ERROR,
                message="Connection timeout to SMTP server",
                details=f"Timeout error: {error_message}",
                troubleshooting_steps=[
                    "Check internet connection stability",
                    "Try increasing timeout value in configuration",
                    "Verify SMTP server is responding",
                    "Check for network congestion",
                    "Try connecting at a different time"
                ],
                recoverable=True
            )
        elif isinstance(error, socket.gaierror):
            return ErrorResponse(
                error_type=ErrorType.NETWORK_ERROR,
                message="DNS resolution failed for SMTP server",
                details=f"DNS error: {error_message}",
                troubleshooting_steps=[
                    "Check SMTP server address for typos",
                    "Verify DNS server settings",
                    "Try using a different DNS server (8.8.8.8)",
                    "Check if domain name is correct",
                    "Try using IP address instead of hostname"
                ],
                recoverable=True
            )
        elif isinstance(error, ssl.SSLError):
            return ErrorResponse(
                error_type=ErrorType.NETWORK_ERROR,
                message="SSL/TLS connection error",
                details=f"SSL error: {error_message}",
                troubleshooting_steps=[
                    "Check if SSL/TLS is properly configured",
                    "Verify certificate validity",
                    "Try different SSL/TLS settings",
                    "Check system date and time",
                    "Update system certificates if needed"
                ],
                recoverable=True
            )
        else:
            return ErrorResponse(
                error_type=ErrorType.NETWORK_ERROR,
                message="Network communication error",
                details=f"Network error: {error_message}",
                troubleshooting_steps=[
                    "Check internet connection",
                    "Verify network settings",
                    "Try connecting from different location",
                    "Check for proxy or firewall issues",
                    "Contact network administrator if needed"
                ],
                recoverable=True
            )
    
    def handle_auth_error(self, error: Exception) -> ErrorResponse:
        """Handle authentication errors"""
        error_message = str(error)
        
        if isinstance(error, smtplib.SMTPAuthenticationError):
            smtp_code = getattr(error, 'smtp_code', 0)
            
            if smtp_code == 535:
                # Most common authentication error
                return ErrorResponse(
                    error_type=ErrorType.AUTH_ERROR,
                    message="Authentication failed - Invalid credentials",
                    details=f"SMTP Auth Error (535): {error_message}",
                    troubleshooting_steps=[
                        "Verify email address and password are correct",
                        "For Gmail: Enable 2FA and use App Password",
                        "For Outlook: Check if account supports SMTP",
                        "Ensure 'Less secure app access' is enabled if required",
                        "Try generating a new app-specific password",
                        "Check if account is locked or suspended"
                    ],
                    recoverable=True
                )
            elif smtp_code == 534:
                return ErrorResponse(
                    error_type=ErrorType.AUTH_ERROR,
                    message="Authentication mechanism not supported",
                    details=f"SMTP Auth Error (534): {error_message}",
                    troubleshooting_steps=[
                        "Check if provider supports the authentication method",
                        "Try using App Password instead of regular password",
                        "Enable OAuth2 if supported by provider",
                        "Check provider documentation for auth requirements"
                    ],
                    recoverable=True
                )
            else:
                return ErrorResponse(
                    error_type=ErrorType.AUTH_ERROR,
                    message="SMTP authentication failed",
                    details=f"SMTP Auth Error ({smtp_code}): {error_message}",
                    troubleshooting_steps=[
                        "Check email credentials are correct",
                        "Verify account is active and not locked",
                        "Check provider-specific authentication requirements",
                        "Try logging into email account via web interface"
                    ],
                    recoverable=True
                )
        else:
            return ErrorResponse(
                error_type=ErrorType.AUTH_ERROR,
                message="Authentication error",
                details=f"Auth error: {error_message}",
                troubleshooting_steps=[
                    "Verify login credentials",
                    "Check account status",
                    "Review authentication method",
                    "Contact email provider if issue persists"
                ],
                recoverable=True
            )
    
    def handle_delivery_error(self, error: Exception) -> ErrorResponse:
        """Handle email delivery errors"""
        error_message = str(error)
        
        if isinstance(error, smtplib.SMTPRecipientsRefused):
            return ErrorResponse(
                error_type=ErrorType.DELIVERY_ERROR,
                message="Recipient email address rejected",
                details=f"Recipients refused: {error_message}",
                troubleshooting_steps=[
                    "Verify recipient email address is correct",
                    "Check if recipient domain accepts emails",
                    "Ensure sender reputation is good",
                    "Try sending to a different email address",
                    "Check if recipient mailbox is full"
                ],
                recoverable=True
            )
        elif isinstance(error, smtplib.SMTPDataError):
            return ErrorResponse(
                error_type=ErrorType.DELIVERY_ERROR,
                message="Email content rejected by server",
                details=f"Data error: {error_message}",
                troubleshooting_steps=[
                    "Check email content for spam-like characteristics",
                    "Reduce email size if too large",
                    "Verify email format is correct",
                    "Remove suspicious links or attachments",
                    "Check sender reputation"
                ],
                recoverable=True
            )
        elif isinstance(error, smtplib.SMTPSenderRefused):
            return ErrorResponse(
                error_type=ErrorType.DELIVERY_ERROR,
                message="Sender email address rejected",
                details=f"Sender refused: {error_message}",
                troubleshooting_steps=[
                    "Verify sender email address is correct",
                    "Check if sender domain is valid",
                    "Ensure sender is authorized to send emails",
                    "Check sender reputation and SPF records",
                    "Try using a different sender address"
                ],
                recoverable=True
            )
        else:
            return ErrorResponse(
                error_type=ErrorType.DELIVERY_ERROR,
                message="Email delivery failed",
                details=f"Delivery error: {error_message}",
                troubleshooting_steps=[
                    "Check email content and format",
                    "Verify recipient address",
                    "Check server response for specific error",
                    "Try sending email again later",
                    "Contact email provider support if needed"
                ],
                recoverable=True
            )
    
    def get_error_type(self, error: Exception) -> ErrorType:
        """Determine the type of error"""
        if isinstance(error, (smtplib.SMTPAuthenticationError,)):
            return ErrorType.AUTH_ERROR
        elif isinstance(error, (smtplib.SMTPConnectError, socket.timeout, socket.gaierror, ssl.SSLError)):
            return ErrorType.NETWORK_ERROR
        elif isinstance(error, (smtplib.SMTPRecipientsRefused, smtplib.SMTPDataError, smtplib.SMTPSenderRefused)):
            return ErrorType.DELIVERY_ERROR
        elif "package" in str(error).lower() or "install" in str(error).lower():
            return ErrorType.PACKAGE_ERROR
        elif "config" in str(error).lower() or "validation" in str(error).lower():
            return ErrorType.CONFIG_ERROR
        elif "template" in str(error).lower():
            return ErrorType.TEMPLATE_ERROR
        else:
            return ErrorType.DELIVERY_ERROR  # Default fallback
    
    def get_troubleshooting_steps(self, error_type: ErrorType) -> List[str]:
        """Get troubleshooting steps for an error type"""
        troubleshooting_guide = {
            ErrorType.PACKAGE_ERROR: [
                "Check Python and pip installation",
                "Run application as administrator",
                "Verify internet connection for package downloads",
                "Clear pip cache and try again"
            ],
            ErrorType.CONFIG_ERROR: [
                "Review all configuration settings",
                "Check email address format",
                "Verify SMTP server and port settings",
                "Consult provider documentation"
            ],
            ErrorType.NETWORK_ERROR: [
                "Check internet connection",
                "Verify SMTP server accessibility",
                "Check firewall and proxy settings",
                "Try different network or VPN"
            ],
            ErrorType.AUTH_ERROR: [
                "Verify email credentials",
                "Enable App Passwords for Gmail",
                "Check account security settings",
                "Try logging in via web interface"
            ],
            ErrorType.TEMPLATE_ERROR: [
                "Check template syntax",
                "Verify template file exists",
                "Validate template variables",
                "Use default template as fallback"
            ],
            ErrorType.DELIVERY_ERROR: [
                "Verify recipient email address",
                "Check email content for spam indicators",
                "Ensure sender reputation is good",
                "Try sending to different recipient"
            ]
        }
        
        return troubleshooting_guide.get(error_type, [
            "Check system logs for detailed error information",
            "Verify all configuration settings",
            "Try restarting the application",
            "Contact support if issue persists"
        ])
    
    def _initialize_error_patterns(self) -> Dict[str, ErrorType]:
        """Initialize common error patterns for classification"""
        return {
            # Authentication patterns
            "authentication failed": ErrorType.AUTH_ERROR,
            "login failed": ErrorType.AUTH_ERROR,
            "invalid credentials": ErrorType.AUTH_ERROR,
            "535": ErrorType.AUTH_ERROR,
            "534": ErrorType.AUTH_ERROR,
            
            # Network patterns
            "connection refused": ErrorType.NETWORK_ERROR,
            "timeout": ErrorType.NETWORK_ERROR,
            "network unreachable": ErrorType.NETWORK_ERROR,
            "dns": ErrorType.NETWORK_ERROR,
            "ssl": ErrorType.NETWORK_ERROR,
            
            # Configuration patterns
            "invalid email": ErrorType.CONFIG_ERROR,
            "invalid port": ErrorType.CONFIG_ERROR,
            "invalid server": ErrorType.CONFIG_ERROR,
            "configuration": ErrorType.CONFIG_ERROR,
            
            # Package patterns
            "package": ErrorType.PACKAGE_ERROR,
            "install": ErrorType.PACKAGE_ERROR,
            "pip": ErrorType.PACKAGE_ERROR,
            "permission denied": ErrorType.PACKAGE_ERROR,
            
            # Template patterns
            "template": ErrorType.TEMPLATE_ERROR,
            "render": ErrorType.TEMPLATE_ERROR,
            "variable": ErrorType.TEMPLATE_ERROR,
            
            # Delivery patterns
            "recipients refused": ErrorType.DELIVERY_ERROR,
            "sender refused": ErrorType.DELIVERY_ERROR,
            "data error": ErrorType.DELIVERY_ERROR,
            "mailbox full": ErrorType.DELIVERY_ERROR
        }
    
    def classify_error_by_message(self, error_message: str) -> ErrorType:
        """Classify error by analyzing error message"""
        error_message_lower = error_message.lower()
        
        for pattern, error_type in self.error_patterns.items():
            if pattern in error_message_lower:
                return error_type
        
        return ErrorType.DELIVERY_ERROR  # Default fallback