"""
Demo script for Email Security and Configuration Management
"""

import os
import tempfile
from email_service.models import EmailConfig
from email_service.enums import ProviderType, AuthMethod
from email_service.security import SecureCredentialManager, EnvironmentCredentialProvider
from email_service.config_manager import EmailConfigManager


def demo_secure_credential_management():
    """Demonstrate secure credential management features"""
    print("=== Secure Credential Management Demo ===\n")
    
    # Create temporary directory for demo
    temp_dir = tempfile.mkdtemp()
    credential_manager = SecureCredentialManager(temp_dir)
    
    # Sample email configuration
    config = EmailConfig(
        provider=ProviderType.GMAIL,
        smtp_server="smtp.gmail.com",
        smtp_port=587,
        use_tls=True,
        sender_email="demo@gmail.com",
        sender_password="MySecurePassword123!",
        auth_method=AuthMethod.APP_PASSWORD
    )
    
    print("1. Original Configuration:")
    print(f"   Email: {config.sender_email}")
    print(f"   Password: {config.sender_password}")
    print(f"   Provider: {config.provider.value}")
    
    # Encrypt credentials
    print("\n2. Encrypting credentials...")
    secure_creds = credential_manager.encrypt_credentials(config)
    print(f"   Encrypted password: {secure_creds.encrypted_password[:50]}...")
    print(f"   Provider: {secure_creds.provider}")
    print(f"   Email: {secure_creds.sender_email}")
    
    # Save encrypted credentials
    print("\n3. Saving encrypted credentials...")
    success = credential_manager.save_credentials(secure_creds)
    print(f"   Save successful: {success}")
    
    # Load and decrypt credentials
    print("\n4. Loading and decrypting credentials...")
    loaded_creds = credential_manager.load_credentials()
    if loaded_creds:
        decrypted_password = credential_manager.decrypt_credentials(loaded_creds)
        print(f"   Decrypted password: {decrypted_password}")
        print(f"   Passwords match: {decrypted_password == config.sender_password}")
    
    # Validate credentials
    print("\n5. Validating credentials...")
    validation = credential_manager.validate_credentials(config)
    print(f"   Valid: {validation.is_valid}")
    print(f"   Security score: {validation.security_score}/100")
    if validation.warnings:
        print(f"   Warnings: {validation.warnings}")
    
    # Sanitize credentials
    print("\n6. Sanitizing credentials...")
    malicious_config = EmailConfig(
        provider=ProviderType.GMAIL,
        smtp_server="smtp.gmail.com<script>alert('xss')</script>",
        smtp_port=587,
        use_tls=True,
        sender_email="DEMO@GMAIL.COM  ",
        sender_password="password123",
        auth_method=AuthMethod.APP_PASSWORD
    )
    
    print(f"   Before sanitization: {malicious_config.sender_email}")
    print(f"   Before sanitization: {malicious_config.smtp_server}")
    
    sanitized = credential_manager.sanitize_credentials(malicious_config)
    print(f"   After sanitization: {sanitized.sender_email}")
    print(f"   After sanitization: {sanitized.smtp_server}")
    
    # Clean up
    import shutil
    shutil.rmtree(temp_dir)
    print("\n✓ Secure credential management demo completed!")


def demo_environment_credentials():
    """Demonstrate environment variable credential management"""
    print("\n=== Environment Credential Management Demo ===\n")
    
    # Set environment variables for demo
    os.environ.update({
        'EMAIL_SERVICE_PROVIDER': 'gmail',
        'EMAIL_SERVICE_SMTP_SERVER': 'smtp.gmail.com',
        'EMAIL_SERVICE_SMTP_PORT': '587',
        'EMAIL_SERVICE_USE_TLS': 'true',
        'EMAIL_SERVICE_SENDER_EMAIL': 'env-demo@gmail.com',
        'EMAIL_SERVICE_SENDER_PASSWORD': 'env_password_123',
        'EMAIL_SERVICE_AUTH_METHOD': 'app_password'
    })
    
    print("1. Environment variables set:")
    for key, value in os.environ.items():
        if key.startswith('EMAIL_SERVICE_'):
            display_value = value if 'PASSWORD' not in key else '*' * len(value)
            print(f"   {key}: {display_value}")
    
    # Load configuration from environment
    print("\n2. Loading configuration from environment...")
    config = EnvironmentCredentialProvider.get_config_from_env()
    if config:
        print(f"   Provider: {config.provider.value}")
        print(f"   SMTP Server: {config.smtp_server}")
        print(f"   Email: {config.sender_email}")
        print(f"   Password: {'*' * len(config.sender_password)}")
    
    # Validate environment configuration
    print("\n3. Validating environment configuration...")
    missing = EnvironmentCredentialProvider.validate_env_config()
    if missing:
        print(f"   Missing variables: {missing}")
    else:
        print("   ✓ All required environment variables are set")
    
    # Show environment template
    print("\n4. Environment variable template:")
    template = EnvironmentCredentialProvider.create_env_template()
    print(template)
    
    # Clean up environment variables
    for key in list(os.environ.keys()):
        if key.startswith('EMAIL_SERVICE_'):
            del os.environ[key]
    
    print("✓ Environment credential management demo completed!")


def demo_configuration_management():
    """Demonstrate configuration management features"""
    print("\n=== Configuration Management Demo ===\n")
    
    # Create temporary directory for demo
    temp_dir = tempfile.mkdtemp()
    config_manager = EmailConfigManager(temp_dir)
    
    # Sample configurations
    gmail_config = EmailConfig(
        provider=ProviderType.GMAIL,
        smtp_server="smtp.gmail.com",
        smtp_port=587,
        use_tls=True,
        sender_email="demo@gmail.com",
        sender_password="gmail_password_123",
        auth_method=AuthMethod.APP_PASSWORD
    )
    
    outlook_config = EmailConfig(
        provider=ProviderType.OUTLOOK,
        smtp_server="smtp-mail.outlook.com",
        smtp_port=587,
        use_tls=True,
        sender_email="demo@outlook.com",
        sender_password="outlook_password_123",
        auth_method=AuthMethod.PASSWORD
    )
    
    print("1. Saving Gmail configuration...")
    success = config_manager.save_config(gmail_config, "Initial Gmail setup")
    print(f"   Save successful: {success}")
    
    # Create backup
    print("\n2. Creating backup...")
    backup_id = config_manager.create_backup("Before switching to Outlook")
    print(f"   Backup ID: {backup_id}")
    
    # Save different configuration
    print("\n3. Switching to Outlook configuration...")
    config_manager.save_config(outlook_config, "Switch to Outlook")
    
    # List backups
    print("\n4. Listing backups...")
    backups = config_manager.list_backups()
    for backup in backups:
        print(f"   ID: {backup.backup_id}")
        print(f"   Description: {backup.description}")
        print(f"   Timestamp: {backup.timestamp}")
    
    # Load current configuration
    print("\n5. Current configuration:")
    current_config = config_manager.load_config(use_env_fallback=False)
    if current_config:
        print(f"   Provider: {current_config.provider.value}")
        print(f"   Email: {current_config.sender_email}")
    
    # Restore from backup
    print(f"\n6. Restoring from backup {backup_id}...")
    success = config_manager.restore_backup(backup_id)
    print(f"   Restore successful: {success}")
    
    # Verify restored configuration
    print("\n7. Restored configuration:")
    restored_config = config_manager.load_config(use_env_fallback=False)
    if restored_config:
        print(f"   Provider: {restored_config.provider.value}")
        print(f"   Email: {restored_config.sender_email}")
    
    # Export configuration
    print("\n8. Exporting configuration...")
    export_path = os.path.join(temp_dir, "exported_config.json")
    success = config_manager.export_config(export_path, include_credentials=False)
    print(f"   Export successful: {success}")
    
    if success and os.path.exists(export_path):
        with open(export_path, 'r') as f:
            import json
            exported_data = json.load(f)
        print(f"   Exported data keys: {list(exported_data.keys())}")
    
    # Validate configuration
    print("\n9. Validating configuration...")
    validation = config_manager.validate_config(gmail_config)
    print(f"   Valid: {validation.is_valid}")
    if validation.warnings:
        print(f"   Warnings: {validation.warnings}")
    
    # Get configuration template
    print("\n10. Configuration template:")
    template = config_manager.get_config_template()
    for key, value in template.items():
        print(f"    {key}: {value}")
    
    # Clean up
    import shutil
    shutil.rmtree(temp_dir)
    print("\n✓ Configuration management demo completed!")


def main():
    """Run all security and configuration demos"""
    print("Email Security and Configuration Management Demo")
    print("=" * 50)
    
    try:
        demo_secure_credential_management()
        demo_environment_credentials()
        demo_configuration_management()
        
        print("\n" + "=" * 50)
        print("All demos completed successfully! 🎉")
        print("\nKey features demonstrated:")
        print("• Secure credential encryption/decryption")
        print("• Password strength validation")
        print("• Credential sanitization")
        print("• Environment variable configuration")
        print("• Configuration backup and restore")
        print("• Configuration validation")
        print("• Import/export functionality")
        
    except Exception as e:
        print(f"\nDemo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()