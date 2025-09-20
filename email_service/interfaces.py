"""
Abstract Base Classes and Interfaces for Email Service
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from .models import (
    EmailConfig, EmailData, EmailResult, DeliveryResult, 
    PackageStatus, TestResult, UserData, AlertData,
    EmailContent, DeliveryStatus, ErrorResponse
)
from .enums import ErrorType


class EmailProvider(ABC):
    """Abstract base class for email providers"""
    
    @abstractmethod
    def configure(self, config: EmailConfig) -> bool:
        """Configure the email provider with given settings"""
        pass
    
    @abstractmethod
    def test_connection(self) -> bool:
        """Test connection to the email server"""
        pass
    
    @abstractmethod
    def send_email(self, email_data: EmailData) -> EmailResult:
        """Send an email using this provider"""
        pass
    
    @abstractmethod
    def validate_config(self, config: EmailConfig) -> List[str]:
        """Validate configuration and return list of errors"""
        pass


class EmailPackageManager(ABC):
    """Abstract base class for package management"""
    
    @abstractmethod
    def check_required_packages(self) -> Dict[str, bool]:
        """Check which required packages are installed"""
        pass
    
    @abstractmethod
    def install_missing_packages(self) -> Dict[str, bool]:
        """Install missing packages and return installation results"""
        pass
    
    @abstractmethod
    def get_installation_status(self) -> PackageStatus:
        """Get detailed status of package installations"""
        pass
    
    @abstractmethod
    def get_required_packages(self) -> List[str]:
        """Get list of required package names"""
        pass


class EmailTemplateEngine(ABC):
    """Abstract base class for email template management"""
    
    @abstractmethod
    def load_templates(self) -> Dict[str, Any]:
        """Load all available email templates"""
        pass
    
    @abstractmethod
    def render_template(self, template_name: str, data: Dict[str, Any]) -> EmailContent:
        """Render a template with provided data"""
        pass
    
    @abstractmethod
    def validate_template(self, template: str) -> bool:
        """Validate template syntax and structure"""
        pass
    
    @abstractmethod
    def get_template_variables(self, template_name: str) -> List[str]:
        """Get list of variables used in a template"""
        pass


class EmailDeliveryManager(ABC):
    """Abstract base class for email delivery management"""
    
    @abstractmethod
    def send_with_retry(self, email_data: EmailData) -> DeliveryResult:
        """Send email with retry logic"""
        pass
    
    @abstractmethod
    def queue_email(self, email_data: EmailData) -> str:
        """Queue email for later delivery and return email ID"""
        pass
    
    @abstractmethod
    def process_queue(self) -> List[DeliveryResult]:
        """Process queued emails and return results"""
        pass
    
    @abstractmethod
    def get_delivery_status(self, email_id: str) -> Optional[DeliveryStatus]:
        """Get current delivery status of an email"""
        pass
    
    @abstractmethod
    def cancel_delivery(self, email_id: str) -> bool:
        """Cancel a queued email delivery"""
        pass


class EmailServiceManager(ABC):
    """Abstract base class for main email service orchestration"""
    
    @abstractmethod
    def initialize(self, config: EmailConfig) -> bool:
        """Initialize the email service with configuration"""
        pass
    
    @abstractmethod
    def send_alert_email(self, user_data: UserData, alert_data: AlertData) -> EmailResult:
        """Send an alert email to the user"""
        pass
    
    @abstractmethod
    def test_email_configuration(self) -> TestResult:
        """Test the current email configuration"""
        pass
    
    @abstractmethod
    def update_configuration(self, new_config: EmailConfig) -> bool:
        """Update email service configuration"""
        pass
    
    @abstractmethod
    def get_supported_providers(self) -> List[str]:
        """Get list of supported email providers"""
        pass


class EmailErrorHandler(ABC):
    """Abstract base class for email error handling"""
    
    @abstractmethod
    def handle_package_error(self, error: Exception) -> ErrorResponse:
        """Handle package installation errors"""
        pass
    
    @abstractmethod
    def handle_config_error(self, error: Exception) -> ErrorResponse:
        """Handle configuration errors"""
        pass
    
    @abstractmethod
    def handle_network_error(self, error: Exception) -> ErrorResponse:
        """Handle network-related errors"""
        pass
    
    @abstractmethod
    def handle_auth_error(self, error: Exception) -> ErrorResponse:
        """Handle authentication errors"""
        pass
    
    @abstractmethod
    def get_error_type(self, error: Exception) -> ErrorType:
        """Determine the type of error"""
        pass
    
    @abstractmethod
    def get_troubleshooting_steps(self, error_type: ErrorType) -> List[str]:
        """Get troubleshooting steps for an error type"""
        pass