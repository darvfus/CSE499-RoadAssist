"""
Unit Tests for Email Configuration Management
"""

import os
import json
import tempfile
import shutil
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from email_service.config_manager import (
    EmailConfigManager, ConfigValidationResult, ConfigBackup
)
from email_service.models import EmailConfig
from email_service.enums import ProviderType, AuthMethod


class TestEmailConfigManager:
    """Test cases for EmailConfigManager"""
    
    def setup_method(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_manager = EmailConfigManager(self.temp_dir)
        
        # Sample email config for testing
        self.sample_config = EmailConfig(
            provider=ProviderType.GMAIL,
            smtp_server="smtp.gmail.com",
            smtp_port=587,
            use_tls=True,
            sender_email="test@gmail.com",
            sender_password="test_password_123",
            auth_method=AuthMethod.APP_PASSWORD
        )
    
    def teardown_method(self):
        """Clean up test environment"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_save_load_config(self):
        """Test saving and loading configuration"""
        # Save configuration
        success = self.config_manager.save_config(self.sample_config, "Test save")
        assert success
        
        # Load configuration
        loaded_config = self.config_manager.load_config(use_env_fallback=False)
        assert loaded_config is not None
        assert loaded_config.provider == self.sample_config.provider
        assert loaded_config.smtp_server == self.sample_config.smtp_server
        assert loaded_config.smtp_port == self.sample_config.smtp_port
        assert loaded_config.sender_email == self.sample_config.sender_email
        assert loaded_config.sender_password == self.sample_config.sender_password
    
    def test_validate_config_valid(self):
        """Test configuration validation with valid config"""
        result = self.config_manager.validate_config(self.sample_config)
        
        assert result.is_valid
        assert len(result.errors) == 0
    
    def test_validate_config_invalid_email(self):
        """Test configuration validation with invalid email"""
        # Create config with valid email first, then modify it to bypass __post_init__
        invalid_config = EmailConfig(
            provider=ProviderType.GMAIL,
            smtp_server="smtp.gmail.com",
            smtp_port=587,
            use_tls=True,
            sender_email="test@gmail.com",  # Valid email initially
            sender_password="test_password_123",
            auth_method=AuthMethod.APP_PASSWORD
        )
        # Modify email to invalid after creation
        invalid_config.sender_email = "invalid_email"
        
        result = self.config_manager.validate_config(invalid_config)
        
        assert not result.is_valid
        assert any("Invalid sender email address" in error for error in result.errors)
    
    def test_validate_config_invalid_port(self):
        """Test configuration validation with invalid port"""
        # Create config with valid port first, then modify it to bypass __post_init__
        invalid_config = EmailConfig(
            provider=ProviderType.GMAIL,
            smtp_server="smtp.gmail.com",
            smtp_port=587,  # Valid port initially
            use_tls=True,
            sender_email="test@gmail.com",
            sender_password="test_password_123",
            auth_method=AuthMethod.APP_PASSWORD
        )
        # Modify port to invalid after creation
        invalid_config.smtp_port = 99999
        
        result = self.config_manager.validate_config(invalid_config)
        
        assert not result.is_valid
        assert any("SMTP port must be between 1 and 65535" in error for error in result.errors)
    
    def test_create_backup(self):
        """Test creating configuration backup"""
        # Save initial configuration
        self.config_manager.save_config(self.sample_config, "Initial config")
        
        # Create backup
        backup_id = self.config_manager.create_backup("Test backup")
        assert backup_id is not None
        
        # Verify backup exists in list
        backups = self.config_manager.list_backups()
        assert len(backups) == 1
        assert backups[0].backup_id == backup_id
        assert backups[0].description == "Test backup"
    
    def test_restore_backup(self):
        """Test restoring configuration from backup"""
        # Save initial configuration
        self.config_manager.save_config(self.sample_config, "Initial config")
        
        # Create backup
        backup_id = self.config_manager.create_backup("Test backup")
        
        # Modify configuration
        modified_config = EmailConfig(
            provider=ProviderType.OUTLOOK,
            smtp_server="smtp-mail.outlook.com",
            smtp_port=587,
            use_tls=True,
            sender_email="modified@outlook.com",
            sender_password="modified_password",
            auth_method=AuthMethod.PASSWORD
        )
        self.config_manager.save_config(modified_config, "Modified config")
        
        # Restore from backup
        success = self.config_manager.restore_backup(backup_id)
        assert success
        
        # Verify restored configuration
        restored_config = self.config_manager.load_config(use_env_fallback=False)
        assert restored_config.provider == self.sample_config.provider
        assert restored_config.sender_email == self.sample_config.sender_email
    
    def test_delete_backup(self):
        """Test deleting configuration backup"""
        # Save configuration and create backup
        self.config_manager.save_config(self.sample_config, "Initial config")
        backup_id = self.config_manager.create_backup("Test backup")
        
        # Verify backup exists
        backups = self.config_manager.list_backups()
        assert len(backups) == 1
        
        # Delete backup
        success = self.config_manager.delete_backup(backup_id)
        assert success
        
        # Verify backup is deleted
        backups = self.config_manager.list_backups()
        assert len(backups) == 0
    
    def test_export_import_config(self):
        """Test exporting and importing configuration"""
        # Save initial configuration
        self.config_manager.save_config(self.sample_config, "Initial config")
        
        # Export configuration
        export_path = os.path.join(self.temp_dir, "exported_config.json")
        success = self.config_manager.export_config(export_path, include_credentials=True)
        assert success
        assert os.path.exists(export_path)
        
        # Clear current configuration
        if os.path.exists(self.config_manager.config_file):
            os.remove(self.config_manager.config_file)
        
        # Import configuration
        success = self.config_manager.import_config(export_path)
        assert success
        
        # Verify imported configuration
        imported_config = self.config_manager.load_config(use_env_fallback=False)
        assert imported_config.provider == self.sample_config.provider
        assert imported_config.sender_email == self.sample_config.sender_email
    
    def test_get_config_template(self):
        """Test getting configuration template"""
        template = self.config_manager.get_config_template()
        
        assert 'provider' in template
        assert 'smtp_server' in template
        assert 'smtp_port' in template
        assert 'sender_email' in template
        assert template['provider'] == 'gmail'
        assert template['smtp_server'] == 'smtp.gmail.com'
    
    @patch.dict(os.environ, {
        'EMAIL_SERVICE_PROVIDER': 'gmail',
        'EMAIL_SERVICE_SMTP_SERVER': 'smtp.gmail.com',
        'EMAIL_SERVICE_SMTP_PORT': '587',
        'EMAIL_SERVICE_USE_TLS': 'true',
        'EMAIL_SERVICE_SENDER_EMAIL': 'env@gmail.com',
        'EMAIL_SERVICE_SENDER_PASSWORD': 'env_password',
        'EMAIL_SERVICE_AUTH_METHOD': 'app_password'
    })
    def test_load_config_env_fallback(self):
        """Test loading configuration with environment fallback"""
        # Load config with env fallback (no file exists)
        config = self.config_manager.load_config(use_env_fallback=True)
        
        assert config is not None
        assert config.provider == ProviderType.GMAIL
        assert config.sender_email == 'env@gmail.com'
        assert config.sender_password == 'env_password'
    
    def test_provider_specific_validation_gmail(self):
        """Test provider-specific validation for Gmail"""
        gmail_config = EmailConfig(
            provider=ProviderType.GMAIL,
            smtp_server="wrong.server.com",  # Wrong server
            smtp_port=25,  # Wrong port
            use_tls=True,
            sender_email="test@gmail.com",
            sender_password="test_password_123",
            auth_method=AuthMethod.APP_PASSWORD
        )
        
        result = self.config_manager.validate_config(gmail_config)
        
        # Should have warnings about server and port
        assert any("Gmail typically uses smtp.gmail.com" in warning 
                  for warning in result.warnings)
        assert any("Gmail typically uses port 465" in warning or 
                  "Gmail typically uses port 587" in warning
                  for warning in result.warnings)
    
    def test_provider_specific_validation_outlook(self):
        """Test provider-specific validation for Outlook"""
        outlook_config = EmailConfig(
            provider=ProviderType.OUTLOOK,
            smtp_server="wrong.server.com",  # Wrong server
            smtp_port=25,  # Wrong port
            use_tls=True,
            sender_email="test@outlook.com",
            sender_password="test_password_123",
            auth_method=AuthMethod.PASSWORD
        )
        
        result = self.config_manager.validate_config(outlook_config)
        
        # Should have warnings about server and port
        assert any("Outlook typically uses smtp-mail.outlook.com" in warning 
                  for warning in result.warnings)
        assert any("Outlook typically uses port 587" in warning 
                  for warning in result.warnings)


class TestConfigValidationResult:
    """Test cases for ConfigValidationResult"""
    
    def test_add_error(self):
        """Test adding validation error"""
        result = ConfigValidationResult(is_valid=True)
        
        result.add_error("Test error")
        
        assert not result.is_valid
        assert "Test error" in result.errors
    
    def test_add_warning(self):
        """Test adding validation warning"""
        result = ConfigValidationResult(is_valid=True)
        
        result.add_warning("Test warning")
        
        assert result.is_valid  # Warnings don't affect validity
        assert "Test warning" in result.warnings


class TestConfigBackup:
    """Test cases for ConfigBackup"""
    
    def test_to_dict_conversion(self):
        """Test converting ConfigBackup to dictionary"""
        backup = ConfigBackup(
            backup_id="test_backup_123",
            timestamp=datetime(2023, 1, 1, 12, 0, 0),
            description="Test backup",
            file_path="/path/to/backup.json",
            config_hash="abc123"
        )
        
        backup_dict = backup.to_dict()
        
        assert backup_dict['backup_id'] == "test_backup_123"
        assert backup_dict['timestamp'] == "2023-01-01T12:00:00"
        assert backup_dict['description'] == "Test backup"
        assert backup_dict['file_path'] == "/path/to/backup.json"
        assert backup_dict['config_hash'] == "abc123"
    
    def test_from_dict_conversion(self):
        """Test creating ConfigBackup from dictionary"""
        backup_dict = {
            'backup_id': "test_backup_123",
            'timestamp': "2023-01-01T12:00:00",
            'description': "Test backup",
            'file_path': "/path/to/backup.json",
            'config_hash': "abc123"
        }
        
        backup = ConfigBackup.from_dict(backup_dict)
        
        assert backup.backup_id == "test_backup_123"
        assert backup.timestamp == datetime(2023, 1, 1, 12, 0, 0)
        assert backup.description == "Test backup"
        assert backup.file_path == "/path/to/backup.json"
        assert backup.config_hash == "abc123"


if __name__ == '__main__':
    pytest.main([__file__])