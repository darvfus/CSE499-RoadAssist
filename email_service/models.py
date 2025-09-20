"""
Data Models for Email Service
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional, List
from .enums import ProviderType, AuthMethod, Priority, AlertType, DeliveryStatusType, ErrorType


@dataclass
class EmailConfig:
    """Configuration for email provider settings"""
    provider: ProviderType
    smtp_server: str
    smtp_port: int
    use_tls: bool
    sender_email: str
    sender_password: str
    auth_method: AuthMethod
    timeout: int = 30
    max_retries: int = 3
    
    def __post_init__(self):
        """Validate configuration after initialization"""
        if not self.sender_email or "@" not in self.sender_email:
            raise ValueError("Invalid sender email address")
        if not self.smtp_server:
            raise ValueError("SMTP server cannot be empty")
        if not (1 <= self.smtp_port <= 65535):
            raise ValueError("SMTP port must be between 1 and 65535")


@dataclass
class UserData:
    """User information for email personalization"""
    name: str
    email: str
    user_id: Optional[str] = None
    preferences: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AlertData:
    """Alert information for email content"""
    alert_type: AlertType
    timestamp: datetime
    heart_rate: Optional[int] = None
    oxygen_saturation: Optional[float] = None
    additional_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EmailContent:
    """Rendered email content"""
    subject: str
    body: str
    html_body: Optional[str] = None
    attachments: List[str] = field(default_factory=list)


@dataclass
class EmailData:
    """Complete email data for sending"""
    recipient: str
    subject: str
    body: str
    template_name: str
    template_data: Dict[str, Any]
    priority: Priority = Priority.NORMAL
    html_body: Optional[str] = None
    attachments: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate email data after initialization"""
        if not self.recipient or "@" not in self.recipient:
            raise ValueError("Invalid recipient email address")
        if not self.subject.strip():
            raise ValueError("Email subject cannot be empty")


@dataclass
class DeliveryResult:
    """Result of email delivery attempt"""
    success: bool
    email_id: str
    timestamp: datetime
    attempts: int
    error_message: Optional[str] = None
    delivery_time: float = 0.0
    provider_used: Optional[str] = None


@dataclass
class DeliveryStatus:
    """Current status of email delivery"""
    email_id: str
    status: DeliveryStatusType
    created_at: datetime
    updated_at: datetime
    attempts: int = 0
    last_error: Optional[str] = None


@dataclass
class PackageStatus:
    """Status of email package installation"""
    required_packages: Dict[str, bool]
    installation_log: List[str] = field(default_factory=list)
    all_installed: bool = False
    
    def __post_init__(self):
        """Update all_installed status"""
        self.all_installed = all(self.required_packages.values())


@dataclass
class EmailResult:
    """Result of email operation"""
    success: bool
    message: str
    email_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TestResult:
    """Result of email configuration test"""
    success: bool
    provider: str
    connection_test: bool
    auth_test: bool
    send_test: bool
    error_messages: List[str] = field(default_factory=list)
    test_duration: float = 0.0


@dataclass
class ErrorResponse:
    """Structured error response"""
    error_type: ErrorType
    message: str
    details: str
    troubleshooting_steps: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    recoverable: bool = True