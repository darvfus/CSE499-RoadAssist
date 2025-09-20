"""
Unit Tests for Email Security and Credential Management
"""

import os
import json
import tempfile
import shutil
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from email_service.security import (
    SecureCredentialManager, EnvironmentCredentialProvider,
    SecureCredentials, CredentialValidationResult
)
from email_service.models import EmailConfig
from email_service.enums import ProviderType, AuthMethod


class TestSecureCredentialManager:
    """Test cases for SecureCredentialManager"""
    
    def setup_method(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.credential_manager = SecureCredentialManager(self.temp_dir)
        
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
    
    def test_encrypt_decrypt_credentials(self):
        """Test credential encryption and decryption"""
        # Encrypt credentials
        secure_creds = self.credential_manager.encrypt_credentials(self.sample_config)
        
        assert secure_creds.provider == "gmail"
        assert secure_creds.sender_email == "test@gmail.com"
        assert secure_creds.auth_method == "app_password"
        assert secure_creds.encrypted_password != self.sample_config.sender_password
        
        # Decrypt credentials
        decrypted_password = self.credential_manager.decrypt_credentials(secure_creds)
        assert decrypted_password == self.sample_config.sender_password
    
    def test_validate_credentials_valid(self):
        """Test credential validation with valid credentials"""
        result = self.credential_manager.validate_credentials(self.sample_config)
        
        assert result.is_valid
        assert len(result.errors) == 0
        assert result.security_score > 0


class TestEnvironmentCredentialProvider:
    """Test cases for EnvironmentCredentialProvider"""
    
    def setup_method(self):
        """Set up test environment"""
        # Store original environment
        self.original_env = dict(os.environ)
    
    def teardown_method(self):
        """Restore original environment"""
        os.environ.clear()
        os.environ.update(self.original_env)
    
    def test_create_env_template(self):
        """Test creating environment variable template"""
        template = EnvironmentCredentialProvider.create_env_template()
        
        assert 'EMAIL_SERVICE_PROVIDER=' in template
        assert 'EMAIL_SERVICE_SMTP_SERVER=' in template
        assert 'EMAIL_SERVICE_SENDER_EMAIL=' in template
        assert 'EMAIL_SERVICE_SENDER_PASSWORD=' in template
        assert '# Email Service Environment Variables' in template


if __name__ == '__main__':
    pytest.main([__file__])