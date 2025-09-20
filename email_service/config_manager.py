"""
Configuration Management System for Email Service
"""

import os
import json
import shutil
import logging
import hashlib
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from .models import EmailConfig
from .enums import ProviderType, AuthMethod
from .security import SecureCredentialManager, EnvironmentCredentialProvider


logger = logging.getLogger(__name__)


@dataclass
class ConfigValidationResult:
    """Result of configuration validation"""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def add_error(self, message: str) -> None:
        """Add validation error"""
        self.errors.append(message)
        self.is_valid = False
    
    def add_warning(self, message: str) -> None:
        """Add validation warning"""
        self.warnings.append(message)


@dataclass
class ConfigBackup:
    """Configuration backup metadata"""
    backup_id: str
    timestamp: datetime
    description: str
    file_path: str
    config_hash: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'backup_id': self.backup_id,
            'timestamp': self.timestamp.isoformat(),
            'description': self.description,
            'file_path': self.file_path,
            'config_hash': self.config_hash
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConfigBackup':
        """Create from dictionary"""
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


class EmailConfigManager:
    """Manages email service configuration with validation, backup, and restore"""
    
    def __init__(self, config_dir: str = ".kiro/email_config"):
        self.config_dir = Path(config_dir)
        self.config_file = self.config_dir / "email_config.json"
        self.backup_dir = self.config_dir / "backups"
        self.backup_index_file = self.backup_dir / "backup_index.json"
        self.credential_manager = SecureCredentialManager(str(self.config_dir))
        self._ensure_directories()
    
    def _ensure_directories(self) -> None:
        """Ensure all required directories exist"""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Set restrictive permissions (Unix-like systems)
        if os.name != 'nt':
            os.chmod(self.config_dir, 0o700)
            os.chmod(self.backup_dir, 0o700)
    
    def save_config(self, config: EmailConfig, description: str = "Configuration update") -> bool:
        """Save configuration with automatic backup"""
        try:
            # Create backup before saving new config
            if self.config_file.exists():
                self.create_backup(description)
            
            # Prepare config data (excluding sensitive information)
            config_data = {
                'provider': config.provider.value,
                'smtp_server': config.smtp_server,
                'smtp_port': config.smtp_port,
                'use_tls': config.use_tls,
                'sender_email': config.sender_email,
                'auth_method': config.auth_method.value,
                'timeout': config.timeout,
                'max_retries': config.max_retries,
                'last_updated': datetime.now().isoformat(),
                'version': '1.0'
            }
            
            # Save configuration file
            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            # Save encrypted credentials separately
            secure_creds = self.credential_manager.encrypt_credentials(config)
            self.credential_manager.save_credentials(secure_creds)
            
            # Set restrictive permissions
            if os.name != 'nt':
                os.chmod(self.config_file, 0o600)
            
            logger.info("Configuration saved successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            return False
    
    def load_config(self, use_env_fallback: bool = True) -> Optional[EmailConfig]:
        """Load configuration from file or environment variables"""
        try:
            # Try to load from file first
            config = self._load_config_from_file()
            if config:
                return config
            
            # Fallback to environment variables if enabled
            if use_env_fallback:
                env_config = EnvironmentCredentialProvider.get_config_from_env()
                if env_config:
                    logger.info("Loaded configuration from environment variables")
                    return env_config
            
            logger.warning("No configuration found")
            return None
            
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            return None
    
    def _load_config_from_file(self) -> Optional[EmailConfig]:
        """Load configuration from JSON file"""
        if not self.config_file.exists():
            return None
        
        with open(self.config_file, 'r') as f:
            config_data = json.load(f)
        
        # Load encrypted credentials
        secure_creds = self.credential_manager.load_credentials()
        if not secure_creds:
            logger.error("Could not load encrypted credentials")
            return None
        
        # Decrypt password
        password = self.credential_manager.decrypt_credentials(secure_creds)
        
        # Create EmailConfig object
        config = EmailConfig(
            provider=ProviderType(config_data['provider']),
            smtp_server=config_data['smtp_server'],
            smtp_port=config_data['smtp_port'],
            use_tls=config_data['use_tls'],
            sender_email=config_data['sender_email'],
            sender_password=password,
            auth_method=AuthMethod(config_data['auth_method']),
            timeout=config_data.get('timeout', 30),
            max_retries=config_data.get('max_retries', 3)
        )
        
        return config
    
    def validate_config(self, config: EmailConfig) -> ConfigValidationResult:
        """Validate email configuration"""
        result = ConfigValidationResult(is_valid=True)
        
        # Validate provider
        if not isinstance(config.provider, ProviderType):
            result.add_error("Invalid provider type")
        
        # Validate SMTP settings
        if not config.smtp_server:
            result.add_error("SMTP server cannot be empty")
        
        if not (1 <= config.smtp_port <= 65535):
            result.add_error("SMTP port must be between 1 and 65535")
        
        # Validate email address
        if not config.sender_email or "@" not in config.sender_email:
            result.add_error("Invalid sender email address")
        
        # Validate password
        if not config.sender_password:
            result.add_error("Sender password cannot be empty")
        
        # Validate auth method
        if not isinstance(config.auth_method, AuthMethod):
            result.add_error("Invalid authentication method")
        
        # Provider-specific validations
        self._validate_provider_specific(config, result)
        
        # Validate timeout and retries
        if config.timeout <= 0:
            result.add_error("Timeout must be positive")
        
        if config.max_retries < 0:
            result.add_error("Max retries cannot be negative")
        
        # Security validations
        cred_validation = self.credential_manager.validate_credentials(config)
        result.errors.extend(cred_validation.errors)
        result.warnings.extend(cred_validation.warnings)
        
        if cred_validation.errors:
            result.is_valid = False
        
        return result
    
    def _validate_provider_specific(self, config: EmailConfig, result: ConfigValidationResult) -> None:
        """Validate provider-specific configuration"""
        if config.provider == ProviderType.GMAIL:
            if config.smtp_server != "smtp.gmail.com":
                result.add_warning("Gmail typically uses smtp.gmail.com")
            if config.smtp_port not in [465, 587]:
                result.add_warning("Gmail typically uses port 465 (SSL) or 587 (TLS)")
        
        elif config.provider == ProviderType.OUTLOOK:
            if config.smtp_server != "smtp-mail.outlook.com":
                result.add_warning("Outlook typically uses smtp-mail.outlook.com")
            if config.smtp_port != 587:
                result.add_warning("Outlook typically uses port 587")
        
        elif config.provider == ProviderType.YAHOO:
            if config.smtp_server != "smtp.mail.yahoo.com":
                result.add_warning("Yahoo typically uses smtp.mail.yahoo.com")
            if config.smtp_port != 587:
                result.add_warning("Yahoo typically uses port 587")
    
    def create_backup(self, description: str = "Manual backup") -> Optional[str]:
        """Create a backup of current configuration"""
        try:
            if not self.config_file.exists():
                logger.warning("No configuration file to backup")
                return None
            
            # Generate backup ID and file path
            timestamp = datetime.now()
            backup_id = timestamp.strftime("%Y%m%d_%H%M%S")
            backup_file = self.backup_dir / f"config_backup_{backup_id}.json"
            
            # Copy configuration file
            shutil.copy2(self.config_file, backup_file)
            
            # Calculate config hash for integrity checking
            with open(self.config_file, 'rb') as f:
                config_hash = hashlib.sha256(f.read()).hexdigest()
            
            # Create backup metadata
            backup = ConfigBackup(
                backup_id=backup_id,
                timestamp=timestamp,
                description=description,
                file_path=str(backup_file),
                config_hash=config_hash
            )
            
            # Update backup index
            self._update_backup_index(backup)
            
            logger.info(f"Configuration backup created: {backup_id}")
            return backup_id
            
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return None
    
    def restore_backup(self, backup_id: str) -> bool:
        """Restore configuration from backup"""
        try:
            # Find backup in index
            backup = self._find_backup(backup_id)
            if not backup:
                logger.error(f"Backup not found: {backup_id}")
                return False
            
            # Verify backup file exists
            backup_file = Path(backup.file_path)
            if not backup_file.exists():
                logger.error(f"Backup file not found: {backup.file_path}")
                return False
            
            # Verify backup integrity
            with open(backup_file, 'rb') as f:
                current_hash = hashlib.sha256(f.read()).hexdigest()
            
            if current_hash != backup.config_hash:
                logger.error(f"Backup integrity check failed for: {backup_id}")
                return False
            
            # Create backup of current config before restore
            self.create_backup(f"Pre-restore backup before restoring {backup_id}")
            
            # Restore configuration
            shutil.copy2(backup_file, self.config_file)
            
            logger.info(f"Configuration restored from backup: {backup_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to restore backup: {e}")
            return False
    
    def list_backups(self) -> List[ConfigBackup]:
        """List all available configuration backups"""
        try:
            if not self.backup_index_file.exists():
                return []
            
            with open(self.backup_index_file, 'r') as f:
                index_data = json.load(f)
            
            backups = [ConfigBackup.from_dict(backup_data) 
                      for backup_data in index_data.get('backups', [])]
            
            # Sort by timestamp (newest first)
            backups.sort(key=lambda x: x.timestamp, reverse=True)
            
            return backups
            
        except Exception as e:
            logger.error(f"Failed to list backups: {e}")
            return []
    
    def delete_backup(self, backup_id: str) -> bool:
        """Delete a configuration backup"""
        try:
            backup = self._find_backup(backup_id)
            if not backup:
                logger.error(f"Backup not found: {backup_id}")
                return False
            
            # Delete backup file
            backup_file = Path(backup.file_path)
            if backup_file.exists():
                backup_file.unlink()
            
            # Remove from index
            self._remove_from_backup_index(backup_id)
            
            logger.info(f"Backup deleted: {backup_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete backup: {e}")
            return False
    
    def _update_backup_index(self, backup: ConfigBackup) -> None:
        """Update backup index with new backup"""
        index_data = {'backups': []}
        
        if self.backup_index_file.exists():
            with open(self.backup_index_file, 'r') as f:
                index_data = json.load(f)
        
        # Add new backup to index
        index_data['backups'].append(backup.to_dict())
        
        # Keep only last 10 backups
        index_data['backups'] = index_data['backups'][-10:]
        
        # Save updated index
        with open(self.backup_index_file, 'w') as f:
            json.dump(index_data, f, indent=2)
    
    def _remove_from_backup_index(self, backup_id: str) -> None:
        """Remove backup from index"""
        if not self.backup_index_file.exists():
            return
        
        with open(self.backup_index_file, 'r') as f:
            index_data = json.load(f)
        
        # Remove backup from list
        index_data['backups'] = [
            backup for backup in index_data['backups']
            if backup['backup_id'] != backup_id
        ]
        
        # Save updated index
        with open(self.backup_index_file, 'w') as f:
            json.dump(index_data, f, indent=2)
    
    def _find_backup(self, backup_id: str) -> Optional[ConfigBackup]:
        """Find backup by ID"""
        backups = self.list_backups()
        for backup in backups:
            if backup.backup_id == backup_id:
                return backup
        return None
    
    def get_config_template(self) -> Dict[str, Any]:
        """Get configuration template with default values"""
        return {
            'provider': 'gmail',
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'use_tls': True,
            'sender_email': 'your-email@gmail.com',
            'auth_method': 'app_password',
            'timeout': 30,
            'max_retries': 3
        }
    
    def export_config(self, export_path: str, include_credentials: bool = False) -> bool:
        """Export configuration to external file"""
        try:
            config = self.load_config(use_env_fallback=False)
            if not config:
                logger.error("No configuration to export")
                return False
            
            export_data = {
                'provider': config.provider.value,
                'smtp_server': config.smtp_server,
                'smtp_port': config.smtp_port,
                'use_tls': config.use_tls,
                'sender_email': config.sender_email,
                'auth_method': config.auth_method.value,
                'timeout': config.timeout,
                'max_retries': config.max_retries,
                'exported_at': datetime.now().isoformat()
            }
            
            if include_credentials:
                export_data['sender_password'] = config.sender_password
                logger.warning("Exporting configuration with credentials - ensure secure handling")
            
            with open(export_path, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            logger.info(f"Configuration exported to: {export_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export configuration: {e}")
            return False
    
    def import_config(self, import_path: str) -> bool:
        """Import configuration from external file"""
        try:
            with open(import_path, 'r') as f:
                import_data = json.load(f)
            
            # Create EmailConfig from imported data
            config = EmailConfig(
                provider=ProviderType(import_data['provider']),
                smtp_server=import_data['smtp_server'],
                smtp_port=import_data['smtp_port'],
                use_tls=import_data['use_tls'],
                sender_email=import_data['sender_email'],
                sender_password=import_data.get('sender_password', ''),
                auth_method=AuthMethod(import_data['auth_method']),
                timeout=import_data.get('timeout', 30),
                max_retries=import_data.get('max_retries', 3)
            )
            
            # Validate imported configuration
            validation = self.validate_config(config)
            if not validation.is_valid:
                logger.error(f"Invalid imported configuration: {validation.errors}")
                return False
            
            # Save imported configuration
            return self.save_config(config, f"Imported from {import_path}")
            
        except Exception as e:
            logger.error(f"Failed to import configuration: {e}")
            return False