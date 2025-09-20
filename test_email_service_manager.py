#!/usr/bin/env python3
"""
Unit tests for EmailServiceManager

Tests the main email service orchestrator functionality including:
- Service initialization and configuration
- Alert email sending with different types
- Configuration testing and updates
- Error handling and recovery
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from email_service import (
    EmailServiceManagerImpl, EmailConfig, UserData, AlertData, EmailResult,
    TestResult, DeliveryResult, EmailContent, ProviderType, AuthMethod, 
    AlertType, Priority
)


class TestEmailServiceManager(unittest.TestCase):
    """Test cases for EmailServiceManager"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.service_manager = EmailServiceManagerImpl()
        
        self.test_config = EmailConfig(
            provider=ProviderType.GMAIL,
            smtp_server="smtp.gmail.com",
            smtp_port=587,
            use_tls=True,
            sender_email="test@gmail.com",
            sender_password="test-password",
            auth_method=AuthMethod.APP_PASSWORD
        )
        
        self.test_user = UserData(
            name="Test User",
            email="user@example.com",
            user_id="test123"
        )
        
        self.test_alert = AlertData(
            alert_type=AlertType.DROWSINESS,
            timestamp=datetime.now(),
            heart_rate=75,
            oxygen_saturation=98.5
        )
    
    @patch('email_service.service_manager.EmailProviderFactory')
    @patch('email_service.service_manager.EmailPackageManagerImpl')
    def test_initialize_success(self, mock_package_manager, mock_provider_factory):
        """Test successful service initialization"""
        # Mock package manager
        mock_pm_instance = Mock()
        mock_pm_instance.get_installation_status.return_value = Mock(all_installed=True)
        mock_package_manager.return_value = mock_pm_instance
        
        # Mock provider factory and provider
        mock_provider = Mock()
        mock_provider.configure.return_value = True
        mock_provider.test_connection.return_value = True
        mock_provider_factory.create_provider.return_value = mock_provider
        
        # Mock template engine
        with patch.object(self.service_manager.template_engine, 'load_templates', return_value={}):
            # Test initialization
            result = self.service_manager.initialize(self.test_config)
            
            self.assertTrue(result)
            self.assertEqual(self.service_manager.config, self.test_config)
            self.assertEqual(self.service_manager.provider, mock_provider)
    
    def test_initialize_package_installation_failure(self):
        """Test initialization failure due to package installation"""
        # Mock package manager with failed installation
        mock_pm_instance = Mock()
        mock_pm_instance.get_installation_status.return_value = Mock(all_installed=False)
        mock_pm_instance.install_missing_packages.return_value = {'smtplib': False}
        
        # Replace the service manager's package manager with our mock
        self.service_manager.package_manager = mock_pm_instance
        
        result = self.service_manager.initialize(self.test_config)
        
        self.assertFalse(result)
        self.assertIsNone(self.service_manager.config)
        self.assertIsNone(self.service_manager.provider)
    
    def test_send_alert_email_not_initialized(self):
        """Test sending alert email when service is not initialized"""
        result = self.service_manager.send_alert_email(self.test_user, self.test_alert)
        
        self.assertFalse(result.success)
        self.assertIn("not initialized", result.message)
    
    @patch('email_service.service_manager.EmailProviderFactory')
    @patch('email_service.service_manager.EmailPackageManagerImpl')
    def test_send_alert_email_success(self, mock_package_manager, mock_provider_factory):
        """Test successful alert email sending"""
        # Setup mocks for initialization
        mock_pm_instance = Mock()
        mock_pm_instance.get_installation_status.return_value = Mock(all_installed=True)
        mock_package_manager.return_value = mock_pm_instance
        
        mock_provider = Mock()
        mock_provider.configure.return_value = True
        mock_provider.test_connection.return_value = True
        mock_provider_factory.create_provider.return_value = mock_provider
        
        # Mock template engine
        mock_email_content = EmailContent(
            subject="Test Alert",
            body="Test alert body"
        )
        
        with patch.object(self.service_manager.template_engine, 'load_templates', return_value={}):
            with patch.object(self.service_manager.template_engine, 'render_template', return_value=mock_email_content):
                # Mock delivery manager
                mock_delivery_result = DeliveryResult(
                    success=True,
                    email_id="test-123",
                    timestamp=datetime.now(),
                    attempts=1,
                    delivery_time=1.5
                )
                
                with patch.object(self.service_manager.delivery_manager, 'send_with_retry', return_value=mock_delivery_result):
                    # Initialize service
                    self.service_manager.initialize(self.test_config)
                    
                    # Send alert email
                    result = self.service_manager.send_alert_email(self.test_user, self.test_alert)
                    
                    self.assertTrue(result.success)
                    self.assertEqual(result.email_id, "test-123")
                    self.assertIn("successfully", result.message)
    
    @patch('email_service.service_manager.EmailProviderFactory')
    @patch('email_service.service_manager.EmailPackageManagerImpl')
    def test_send_alert_email_template_fallback(self, mock_package_manager, mock_provider_factory):
        """Test alert email sending with template rendering failure (fallback to default)"""
        # Setup mocks for initialization
        mock_pm_instance = Mock()
        mock_pm_instance.get_installation_status.return_value = Mock(all_installed=True)
        mock_package_manager.return_value = mock_pm_instance
        
        mock_provider = Mock()
        mock_provider.configure.return_value = True
        mock_provider.test_connection.return_value = True
        mock_provider_factory.create_provider.return_value = mock_provider
        
        with patch.object(self.service_manager.template_engine, 'load_templates', return_value={}):
            # Mock template engine to raise exception
            with patch.object(self.service_manager.template_engine, 'render_template', side_effect=Exception("Template error")):
                # Mock delivery manager
                mock_delivery_result = DeliveryResult(
                    success=True,
                    email_id="test-456",
                    timestamp=datetime.now(),
                    attempts=1,
                    delivery_time=1.0
                )
                
                with patch.object(self.service_manager.delivery_manager, 'send_with_retry', return_value=mock_delivery_result):
                    # Initialize service
                    self.service_manager.initialize(self.test_config)
                    
                    # Send alert email
                    result = self.service_manager.send_alert_email(self.test_user, self.test_alert)
                    
                    self.assertTrue(result.success)
                    self.assertEqual(result.email_id, "test-456")
    
    def test_test_email_configuration_not_initialized(self):
        """Test email configuration testing when service is not initialized"""
        result = self.service_manager.test_email_configuration()
        
        self.assertFalse(result.success)
        self.assertEqual(result.provider, "None")
        self.assertFalse(result.connection_test)
        self.assertFalse(result.auth_test)
        self.assertFalse(result.send_test)
        self.assertIn("not initialized", result.error_messages[0])
    
    @patch('email_service.service_manager.EmailProviderFactory')
    @patch('email_service.service_manager.EmailPackageManagerImpl')
    def test_test_email_configuration_success(self, mock_package_manager, mock_provider_factory):
        """Test successful email configuration testing"""
        # Setup mocks for initialization
        mock_pm_instance = Mock()
        mock_pm_instance.get_installation_status.return_value = Mock(all_installed=True)
        mock_package_manager.return_value = mock_pm_instance
        
        mock_provider = Mock()
        mock_provider.configure.return_value = True
        mock_provider.test_connection.return_value = True
        mock_provider.send_email.return_value = Mock(success=True, message="Test email sent")
        mock_provider_factory.create_provider.return_value = mock_provider
        
        with patch.object(self.service_manager.template_engine, 'load_templates', return_value={}):
            # Initialize service
            self.service_manager.initialize(self.test_config)
            
            # Test configuration
            result = self.service_manager.test_email_configuration()
            
            self.assertTrue(result.success)
            self.assertEqual(result.provider, "gmail")
            self.assertTrue(result.connection_test)
            self.assertTrue(result.auth_test)
            self.assertTrue(result.send_test)
            self.assertEqual(len(result.error_messages), 0)
    
    @patch('email_service.service_manager.EmailProviderFactory')
    @patch('email_service.service_manager.EmailPackageManagerImpl')
    def test_update_configuration_success(self, mock_package_manager, mock_provider_factory):
        """Test successful configuration update"""
        # Setup mocks for initialization
        mock_pm_instance = Mock()
        mock_pm_instance.get_installation_status.return_value = Mock(all_installed=True)
        mock_package_manager.return_value = mock_pm_instance
        
        mock_provider = Mock()
        mock_provider.configure.return_value = True
        mock_provider.test_connection.return_value = True
        mock_provider_factory.create_provider.return_value = mock_provider
        
        with patch.object(self.service_manager.template_engine, 'load_templates', return_value={}):
            # Initialize service
            self.service_manager.initialize(self.test_config)
            
            # Create updated configuration
            updated_config = EmailConfig(
                provider=ProviderType.GMAIL,
                smtp_server="smtp.gmail.com",
                smtp_port=587,
                use_tls=True,
                sender_email="updated@gmail.com",
                sender_password="updated-password",
                auth_method=AuthMethod.APP_PASSWORD,
                timeout=60
            )
            
            # Update configuration
            result = self.service_manager.update_configuration(updated_config)
            
            self.assertTrue(result)
            self.assertEqual(self.service_manager.config, updated_config)
    
    def test_get_supported_providers(self):
        """Test getting supported providers"""
        with patch('email_service.service_manager.EmailProviderFactory.get_supported_providers') as mock_get_providers:
            mock_get_providers.return_value = [ProviderType.GMAIL, ProviderType.OUTLOOK]
            
            providers = self.service_manager.get_supported_providers()
            
            self.assertEqual(providers, ["gmail", "outlook"])
    
    @patch('email_service.service_manager.EmailPackageManagerImpl')
    def test_get_service_status(self, mock_package_manager):
        """Test getting service status"""
        # Mock package manager
        mock_pm_instance = Mock()
        mock_pm_instance.get_installation_status.return_value = Mock(all_installed=True)
        mock_package_manager.return_value = mock_pm_instance
        
        with patch.object(self.service_manager.template_engine, 'load_templates', return_value={'template1': {}}):
            status = self.service_manager.get_service_status()
            
            self.assertIn('initialized', status)
            self.assertIn('packages_installed', status)
            self.assertIn('templates_loaded', status)
            self.assertIn('supported_providers', status)
            self.assertIn('service_version', status)
            
            self.assertFalse(status['initialized'])  # Not initialized yet
            self.assertTrue(status['packages_installed'])
            self.assertTrue(status['templates_loaded'])
    
    def test_get_template_name(self):
        """Test template name mapping for different alert types"""
        # Test private method through reflection
        self.assertEqual(
            self.service_manager._get_template_name(AlertType.DROWSINESS),
            "drowsiness_alert"
        )
        self.assertEqual(
            self.service_manager._get_template_name(AlertType.VITAL_SIGNS),
            "vital_signs_alert"
        )
        self.assertEqual(
            self.service_manager._get_template_name(AlertType.SYSTEM_ERROR),
            "system_error"
        )
        self.assertEqual(
            self.service_manager._get_template_name(AlertType.TEST_EMAIL),
            "system_test"
        )
    
    def test_prepare_template_data(self):
        """Test template data preparation"""
        template_data = self.service_manager._prepare_template_data(self.test_user, self.test_alert)
        
        self.assertEqual(template_data['user_name'], self.test_user.name)
        self.assertEqual(template_data['user_email'], self.test_user.email)
        self.assertEqual(template_data['alert_type'], self.test_alert.alert_type.value)
        self.assertEqual(template_data['heart_rate'], self.test_alert.heart_rate)
        self.assertEqual(template_data['oxygen_saturation'], self.test_alert.oxygen_saturation)
        self.assertIn('timestamp', template_data)
    
    def test_create_default_email_content(self):
        """Test default email content creation"""
        # Test drowsiness alert
        content = self.service_manager._create_default_email_content(self.test_user, self.test_alert)
        
        self.assertIn("Drowsiness Alert", content.subject)
        self.assertIn(self.test_user.name, content.body)
        self.assertIn("75 BPM", content.body)  # Heart rate
        self.assertIn("98.5%", content.body)   # Oxygen saturation
        
        # Test system error alert
        system_alert = AlertData(
            alert_type=AlertType.SYSTEM_ERROR,
            timestamp=datetime.now()
        )
        
        content = self.service_manager._create_default_email_content(self.test_user, system_alert)
        
        self.assertIn("System Error", content.subject)
        self.assertIn(self.test_user.name, content.body)
    
    def test_get_email_priority(self):
        """Test email priority mapping"""
        self.assertEqual(
            self.service_manager._get_email_priority(AlertType.DROWSINESS),
            Priority.HIGH
        )
        self.assertEqual(
            self.service_manager._get_email_priority(AlertType.VITAL_SIGNS),
            Priority.HIGH
        )
        self.assertEqual(
            self.service_manager._get_email_priority(AlertType.SYSTEM_ERROR),
            Priority.NORMAL
        )
        self.assertEqual(
            self.service_manager._get_email_priority(AlertType.TEST_EMAIL),
            Priority.LOW
        )
    
    def test_create_test_email_data(self):
        """Test test email data creation"""
        # Set up service with config
        self.service_manager.config = self.test_config
        
        test_email = self.service_manager._create_test_email_data()
        
        self.assertEqual(test_email.recipient, self.test_config.sender_email)
        self.assertIn("Test", test_email.subject)
        self.assertIn("test email", test_email.body)
        self.assertEqual(test_email.template_name, "system_test")
        self.assertEqual(test_email.priority, Priority.LOW)


class TestEmailServiceManagerIntegration(unittest.TestCase):
    """Integration tests for EmailServiceManager"""
    
    def setUp(self):
        """Set up integration test fixtures"""
        self.service_manager = EmailServiceManagerImpl()
    
    def test_full_workflow_with_mocks(self):
        """Test complete workflow from initialization to email sending"""
        # This test uses mocks but tests the full integration flow
        
        config = EmailConfig(
            provider=ProviderType.GMAIL,
            smtp_server="smtp.gmail.com",
            smtp_port=587,
            use_tls=True,
            sender_email="test@gmail.com",
            sender_password="test-password",
            auth_method=AuthMethod.APP_PASSWORD
        )
        
        user_data = UserData(name="Integration Test", email="test@example.com")
        alert_data = AlertData(alert_type=AlertType.DROWSINESS, timestamp=datetime.now())
        
        with patch('email_service.service_manager.EmailPackageManagerImpl') as mock_pm:
            with patch('email_service.service_manager.EmailProviderFactory') as mock_pf:
                # Setup mocks
                mock_pm_instance = Mock()
                mock_pm_instance.get_installation_status.return_value = Mock(all_installed=True)
                mock_pm.return_value = mock_pm_instance
                
                mock_provider = Mock()
                mock_provider.configure.return_value = True
                mock_provider.test_connection.return_value = True
                mock_provider.send_email.return_value = Mock(success=True, message="Sent")
                mock_pf.create_provider.return_value = mock_provider
                
                with patch.object(self.service_manager.template_engine, 'load_templates', return_value={}):
                    with patch.object(self.service_manager.template_engine, 'render_template') as mock_render:
                        mock_render.return_value = EmailContent(subject="Test", body="Test body")
                        
                        with patch.object(self.service_manager.delivery_manager, 'send_with_retry') as mock_send:
                            mock_send.return_value = DeliveryResult(
                                success=True, email_id="test-123", timestamp=datetime.now(), attempts=1
                            )
                            
                            # Execute full workflow
                            init_result = self.service_manager.initialize(config)
                            self.assertTrue(init_result)
                            
                            test_result = self.service_manager.test_email_configuration()
                            self.assertTrue(test_result.success)
                            
                            email_result = self.service_manager.send_alert_email(user_data, alert_data)
                            self.assertTrue(email_result.success)
                            
                            status = self.service_manager.get_service_status()
                            self.assertTrue(status['initialized'])


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)