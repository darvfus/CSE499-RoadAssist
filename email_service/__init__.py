"""
Email Service Package for Driver Assistant

This package provides enhanced email functionality including:
- Automatic package management
- Multiple email provider support
- Secure authentication
- Template-based email composition
- Delivery management with retry logic
"""

from .models import (
    EmailConfig,
    EmailData,
    DeliveryResult,
    PackageStatus,
    EmailResult,
    TestResult,
    UserData,
    AlertData,
    EmailContent,
    DeliveryStatus,
    ErrorResponse
)

from .interfaces import (
    EmailProvider,
    EmailPackageManager,
    EmailTemplateEngine,
    EmailDeliveryManager,
    EmailServiceManager,
    EmailErrorHandler
)

from .package_manager import EmailPackageManagerImpl
from .templates import EmailTemplateEngineImpl
from .delivery import EmailDeliveryManagerImpl
from .service_manager import EmailServiceManagerImpl
from .error_handler import EmailErrorHandlerImpl

from .enums import (
    ProviderType,
    AuthMethod,
    Priority,
    AlertType,
    DeliveryStatusType,
    ErrorType
)

__version__ = "1.0.0"
__all__ = [
    # Data Models
    "EmailConfig",
    "EmailData", 
    "DeliveryResult",
    "PackageStatus",
    "EmailResult",
    "TestResult",
    "UserData",
    "AlertData",
    "EmailContent",
    "DeliveryStatus",
    "ErrorResponse",
    
    # Interfaces
    "EmailProvider",
    "EmailPackageManager",
    "EmailTemplateEngine", 
    "EmailDeliveryManager",
    "EmailServiceManager",
    "EmailErrorHandler",
    
    # Implementations
    "EmailPackageManagerImpl",
    "EmailTemplateEngineImpl",
    "EmailDeliveryManagerImpl",
    "EmailServiceManagerImpl",
    "EmailErrorHandlerImpl",
    
    # Enums
    "ProviderType",
    "AuthMethod",
    "Priority",
    "AlertType",
    "DeliveryStatusType",
    "ErrorType"
]