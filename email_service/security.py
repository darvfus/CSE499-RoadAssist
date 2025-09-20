"""
Security and Credential Management for Email Service
"""

import os
import json
import base64
import hashlib
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from .models import EmailConfig
from .enums import ProviderType, AuthMethod


logger = logging.getLogger(__name__)


@dataclass
class SecureCredentials:
    """Secure storage for email credentials"""
    encrypted_password: str
    salt: str
    provider: str
    sender_email: str
    auth_method: str
    created_at: str
    last_updated: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'encrypted_password': self.encrypted_password,
            'salt': self.salt,
            'provider': self.provider,
            'sender_email': self.sender_email,
            'auth_method': self.auth_method,
            'created_at': self.created_at,
            'last_updated': self.last_updated
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SecureCredentials':
        """Create from dictionary"""
        return cls(**data)


@dataclass
class CredentialValidationResult:
    """Result of credential validation"""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    security_score: int = 0  # 0-100 security score


class SecureCredentialManager:
    """Manages secure storage and retrieval of email credentials"""
    
    def __init__(self, config_dir: str = ".kiro/email_config"):
        self.config_dir = config_dir
        self.credentials_file = os.path.join(config_dir, "credentials.enc")
        self.master_key_file = os.path.join(config_dir, "master.key")
        self._ensure_config_directory()
        
    def _ensure_config_directory(self) -> None:
        """Ensure configuration directory exists"""
        os.makedirs(self.config_dir, exist_ok=True)
        
        # Set restrictive permissions on config directory (Unix-like systems)
        if os.name != 'nt':  # Not Windows
            os.chmod(self.config_dir, 0o700)
    
    def _generate_key_from_password(self, password: str, salt: bytes) -> bytes:
        """Generate encryption key from password using PBKDF2"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))
    
    def _get_or_create_master_key(self) -> bytes:
        """Get or create master encryption key"""
        if os.path.exists(self.master_key_file):
            with open(self.master_key_file, 'rb') as f:
                return f.read()
        else:
            # Generate new master key
            key = Fernet.generate_key()
            with open(self.master_key_file, 'wb') as f:
                f.write(key)
            
            # Set restrictive permissions (Unix-like systems)
            if os.name != 'nt':
                os.chmod(self.master_key_file, 0o600)
            
            logger.info("Generated new master encryption key")
            return key
    
    def encrypt_credentials(self, config: EmailConfig, master_password: Optional[str] = None) -> SecureCredentials:
        """Encrypt email credentials for secure storage"""
        from datetime import datetime
        
        # Use master key or password-derived key
        if master_password:
            salt = os.urandom(16)
            key = self._generate_key_from_password(master_password, salt)
            salt_b64 = base64.b64encode(salt).decode()
        else:
            key = self._get_or_create_master_key()
            salt_b64 = ""
        
        # Encrypt the password
        fernet = Fernet(key)
        encrypted_password = fernet.encrypt(config.sender_password.encode()).decode()
        
        # Create secure credentials object
        now = datetime.now().isoformat()
        return SecureCredentials(
            encrypted_password=encrypted_password,
            salt=salt_b64,
            provider=config.provider.value,
            sender_email=config.sender_email,
            auth_method=config.auth_method.value,
            created_at=now,
            last_updated=now
        )
    
    def decrypt_credentials(self, secure_creds: SecureCredentials, master_password: Optional[str] = None) -> str:
        """Decrypt stored credentials"""
        # Use master key or password-derived key
        if master_password and secure_creds.salt:
            salt = base64.b64decode(secure_creds.salt.encode())
            key = self._generate_key_from_password(master_password, salt)
        else:
            key = self._get_or_create_master_key()
        
        # Decrypt the password
        fernet = Fernet(key)
        decrypted_password = fernet.decrypt(secure_creds.encrypted_password.encode()).decode()
        
        return decrypted_password
    
    def save_credentials(self, secure_creds: SecureCredentials) -> bool:
        """Save encrypted credentials to file"""
        try:
            with open(self.credentials_file, 'w') as f:
                json.dump(secure_creds.to_dict(), f, indent=2)
            
            # Set restrictive permissions (Unix-like systems)
            if os.name != 'nt':
                os.chmod(self.credentials_file, 0o600)
            
            logger.info("Credentials saved successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to save credentials: {e}")
            return False
    
    def load_credentials(self) -> Optional[SecureCredentials]:
        """Load encrypted credentials from file"""
        try:
            if not os.path.exists(self.credentials_file):
                return None
            
            with open(self.credentials_file, 'r') as f:
                data = json.load(f)
            
            return SecureCredentials.from_dict(data)
        except Exception as e:
            logger.error(f"Failed to load credentials: {e}")
            return None
    
    def validate_credentials(self, config: EmailConfig) -> CredentialValidationResult:
        """Validate email credentials for security and correctness"""
        result = CredentialValidationResult(is_valid=True)
        
        # Validate email format
        if not config.sender_email or "@" not in config.sender_email:
            result.errors.append("Invalid email address format")
            result.is_valid = False
        
        # Validate password strength
        password = config.sender_password
        if not password:
            result.errors.append("Password cannot be empty")
            result.is_valid = False
        else:
            score = self._calculate_password_strength(password)
            result.security_score = score
            
            if score < 30:
                result.errors.append("Password is too weak")
                result.is_valid = False
            elif score < 60:
                result.warnings.append("Password could be stronger")
        
        # Validate provider-specific requirements
        if config.provider == ProviderType.GMAIL:
            if config.auth_method == AuthMethod.APP_PASSWORD:
                if len(password) != 16 or not password.replace(' ', '').isalnum():
                    result.warnings.append("Gmail App Password should be 16 characters")
        
        # Check for common security issues
        if config.sender_email.lower() in password.lower():
            result.warnings.append("Password should not contain email address")
        
        return result
    
    def _calculate_password_strength(self, password: str) -> int:
        """Calculate password strength score (0-100)"""
        score = 0
        
        # Length bonus
        if len(password) >= 8:
            score += 20
        if len(password) >= 12:
            score += 10
        if len(password) >= 16:
            score += 10
        
        # Character variety
        if any(c.islower() for c in password):
            score += 10
        if any(c.isupper() for c in password):
            score += 10
        if any(c.isdigit() for c in password):
            score += 15
        if any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            score += 15
        
        # Penalty for common patterns
        if password.lower() in ['password', '123456', 'qwerty']:
            score -= 50
        
        return max(0, min(100, score))
    
    def sanitize_credentials(self, config: EmailConfig) -> EmailConfig:
        """Sanitize credentials by removing potentially harmful content"""
        # Create a copy to avoid modifying the original
        sanitized_config = EmailConfig(
            provider=config.provider,
            smtp_server=config.smtp_server.strip(),
            smtp_port=config.smtp_port,
            use_tls=config.use_tls,
            sender_email=config.sender_email.strip().lower(),
            sender_password=config.sender_password.strip(),
            auth_method=config.auth_method,
            timeout=config.timeout,
            max_retries=config.max_retries
        )
        
        # Remove any potential script injection attempts
        sanitized_config.sender_email = self._sanitize_string(sanitized_config.sender_email)
        sanitized_config.smtp_server = self._sanitize_string(sanitized_config.smtp_server)
        
        return sanitized_config
    
    def _sanitize_string(self, value: str) -> str:
        """Remove potentially harmful characters from string"""
        # Remove common script injection patterns
        dangerous_chars = ['<', '>', '"', "'", '&', ';', '|', '`', '$']
        for char in dangerous_chars:
            value = value.replace(char, '')
        
        return value.strip()
    
    def clear_credentials_from_memory(self, config: EmailConfig) -> None:
        """Clear sensitive data from memory (best effort)"""
        # Overwrite password in memory
        if hasattr(config, 'sender_password'):
            # This is a best-effort approach; Python's garbage collector
            # may still have references to the original string
            config.sender_password = '0' * len(config.sender_password)


class EnvironmentCredentialProvider:
    """Provides credentials from environment variables"""
    
    ENV_PREFIX = "EMAIL_SERVICE_"
    
    @classmethod
    def get_config_from_env(cls) -> Optional[EmailConfig]:
        """Create EmailConfig from environment variables"""
        try:
            provider_str = os.getenv(f"{cls.ENV_PREFIX}PROVIDER")
            if not provider_str:
                return None
            
            config = EmailConfig(
                provider=ProviderType(provider_str.lower()),
                smtp_server=os.getenv(f"{cls.ENV_PREFIX}SMTP_SERVER", ""),
                smtp_port=int(os.getenv(f"{cls.ENV_PREFIX}SMTP_PORT", "587")),
                use_tls=os.getenv(f"{cls.ENV_PREFIX}USE_TLS", "true").lower() == "true",
                sender_email=os.getenv(f"{cls.ENV_PREFIX}SENDER_EMAIL", ""),
                sender_password=os.getenv(f"{cls.ENV_PREFIX}SENDER_PASSWORD", ""),
                auth_method=AuthMethod(os.getenv(f"{cls.ENV_PREFIX}AUTH_METHOD", "password")),
                timeout=int(os.getenv(f"{cls.ENV_PREFIX}TIMEOUT", "30")),
                max_retries=int(os.getenv(f"{cls.ENV_PREFIX}MAX_RETRIES", "3"))
            )
            
            return config
        except (ValueError, TypeError) as e:
            logger.error(f"Failed to load config from environment: {e}")
            return None
    
    @classmethod
    def get_required_env_vars(cls) -> List[str]:
        """Get list of required environment variables"""
        return [
            f"{cls.ENV_PREFIX}PROVIDER",
            f"{cls.ENV_PREFIX}SMTP_SERVER",
            f"{cls.ENV_PREFIX}SENDER_EMAIL",
            f"{cls.ENV_PREFIX}SENDER_PASSWORD"
        ]
    
    @classmethod
    def validate_env_config(cls) -> List[str]:
        """Validate environment configuration and return missing variables"""
        missing = []
        for var in cls.get_required_env_vars():
            if not os.getenv(var):
                missing.append(var)
        return missing
    
    @classmethod
    def create_env_template(cls) -> str:
        """Create environment variable template"""
        template = "# Email Service Environment Variables\n"
        template += f"{cls.ENV_PREFIX}PROVIDER=gmail  # gmail, outlook, yahoo, custom\n"
        template += f"{cls.ENV_PREFIX}SMTP_SERVER=smtp.gmail.com\n"
        template += f"{cls.ENV_PREFIX}SMTP_PORT=587\n"
        template += f"{cls.ENV_PREFIX}USE_TLS=true\n"
        template += f"{cls.ENV_PREFIX}SENDER_EMAIL=your-email@gmail.com\n"
        template += f"{cls.ENV_PREFIX}SENDER_PASSWORD=your-app-password\n"
        template += f"{cls.ENV_PREFIX}AUTH_METHOD=app_password  # password, app_password, oauth2\n"
        template += f"{cls.ENV_PREFIX}TIMEOUT=30\n"
        template += f"{cls.ENV_PREFIX}MAX_RETRIES=3\n"
        
        return template