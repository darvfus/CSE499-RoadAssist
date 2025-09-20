"""
Enums for Email Service Configuration and Status
"""

from enum import Enum, auto


class ProviderType(Enum):
    """Email provider types supported by the system"""
    GMAIL = "gmail"
    OUTLOOK = "outlook"
    YAHOO = "yahoo"
    CUSTOM = "custom"


class AuthMethod(Enum):
    """Authentication methods for email providers"""
    PASSWORD = "password"
    APP_PASSWORD = "app_password"
    OAUTH2 = "oauth2"


class Priority(Enum):
    """Email priority levels"""
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


class AlertType(Enum):
    """Types of alerts that can be sent"""
    DROWSINESS = "drowsiness"
    VITAL_SIGNS = "vital_signs"
    SYSTEM_ERROR = "system_error"
    TEST_EMAIL = "test_email"


class DeliveryStatusType(Enum):
    """Email delivery status types"""
    PENDING = auto()
    SENDING = auto()
    SENT = auto()
    FAILED = auto()
    QUEUED = auto()
    RETRYING = auto()


class ErrorType(Enum):
    """Categories of errors that can occur"""
    PACKAGE_ERROR = auto()
    CONFIG_ERROR = auto()
    NETWORK_ERROR = auto()
    AUTH_ERROR = auto()
    TEMPLATE_ERROR = auto()
    DELIVERY_ERROR = auto()