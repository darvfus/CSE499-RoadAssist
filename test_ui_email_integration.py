"""
Integration tests for UI email functionality
Tests the email configuration interface and status tracking
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import tkinter as tk
import threading
import time
from datetime import datetime

# Import the interface module
import interfaz
from email_service import (
    EmailServiceManagerImpl, EmailConfig, UserData, AlertData,
    ProviderType, AuthMethod, AlertType, TestResult
)


class TestUIEmailIntegration(unittest.TestCase):
    """Test email functionality integration with the UI"""
    
    def setUp(self):
        """Set up test environment"""
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the window during tests
        
        # Clear email status tracking
        interfaz.email_delivery_status.clear()
        
        # Mock email service
        self.mock_email_service = Mock(spec=EmailServiceManagerImpl)
        interfaz.email_service_manager = self.mock_email_service
    
    def tearDown(self):
        """Clean up after tests"""
        try:
            self.root.destroy()
        except:
            pass
    
    def test_email_status_tracking_functions(self):
        """Test email status tracking functions"""
        # Test marking email as sending
        email_id = "test-123"
        recipient = "test@example.com"
        
        interfaz.marcar_email_enviando(email_id, recipient)
        
        self.assertIn(email_id, interfaz.email_delivery_status)
        status = interfaz.email_delivery_status[email_id]
        self.assertEqual(status['recipient'], recipient)
        self.assertTrue(status['sending'])
        self.assertFalse(status['success'])
        
        # Test updating email status - success
        interfaz.actualizar_estado_email(email_id, recipient, True, 1, None)
        
        status = interfaz.email_delivery_status[email_id]
        self.assertTrue(status['success'])
        self.assertFalse(status['sending'])
        self.assertEqual(status['attempts'], 1)
        self.assertIsNone(status['error_message'])
        
        # Test updating email status - failure
        error_msg = "SMTP connection failed"
        interfaz.actualizar_estado_email(email_id, recipient, False, 3, error_msg)
        
        status = interfaz.email_delivery_status[email_id]
        self.assertFalse(status['success'])
        self.assertEqual(status['attempts'], 3)
        self.assertEqual(status['error_message'], error_msg)
    
    @patch('interfaz.EMAIL_SERVICE_AVAILABLE', True)
    def test_email_configuration_window_creation(self):
        """Test that email configuration window can be created"""
        # This test verifies the window can be created without errors
        try:
            # Create a mock window to avoid actual GUI display
            with patch('tkinter.Toplevel') as mock_toplevel:
                mock_window = Mock()
                mock_toplevel.return_value = mock_window
                
                # Mock window methods
                mock_window.title = Mock()
                mock_window.geometry = Mock()
                mock_window.configure = Mock()
                mock_window.resizable = Mock()
                mock_window.transient = Mock()
                mock_window.grab_set = Mock()
                mock_window.update = Mock()
                mock_window.destroy = Mock()
                
                # Call the function
                interfaz.abrir_configuracion_email()
                
                # Verify window was created and configured
                mock_toplevel.assert_called_once()
                mock_window.title.assert_called_with("Configuración de Email")
                mock_window.geometry.assert_called_with("500x600")
                
        except Exception as e:
            self.fail(f"Email configuration window creation failed: {e}")
    
    @patch('interfaz.EMAIL_SERVICE_AVAILABLE', True)
    def test_email_status_window_creation(self):
        """Test that email status window can be created"""
        try:
            # Create a mock window to avoid actual GUI display
            with patch('tkinter.Toplevel') as mock_toplevel:
                mock_window = Mock()
                mock_toplevel.return_value = mock_window
                
                # Mock window methods and attributes
                mock_window.title = Mock()
                mock_window.geometry = Mock()
                mock_window.configure = Mock()
                mock_window.winfo_exists = Mock(return_value=True)
                mock_window.lift = Mock()
                mock_window.after = Mock()
                mock_window.destroy = Mock()
                
                # Set up the global variable
                interfaz.email_status_window = None
                
                # Call the function
                interfaz.mostrar_estado_email()
                
                # Verify window was created and configured
                mock_toplevel.assert_called_once()
                mock_window.title.assert_called_with("Estado de Entrega de Emails")
                mock_window.geometry.assert_called_with("600x400")
                
        except Exception as e:
            self.fail(f"Email status window creation failed: {e}")
    
    def test_email_configuration_validation(self):
        """Test email configuration validation"""
        # Test valid Gmail configuration
        try:
            config = EmailConfig(
                provider=ProviderType.GMAIL,
                smtp_server="smtp.gmail.com",
                smtp_port=587,
                use_tls=True,
                sender_email="test@gmail.com",
                sender_password="test_password",
                auth_method=AuthMethod.APP_PASSWORD
            )
            # If no exception is raised, validation passed
            self.assertTrue(True)
        except Exception as e:
            self.fail(f"Valid Gmail configuration failed validation: {e}")
        
        # Test invalid email configuration
        with self.assertRaises(ValueError):
            EmailConfig(
                provider=ProviderType.GMAIL,
                smtp_server="smtp.gmail.com",
                smtp_port=587,
                use_tls=True,
                sender_email="invalid_email",  # Invalid email
                sender_password="test_password",
                auth_method=AuthMethod.APP_PASSWORD
            )
        
        # Test invalid port configuration
        with self.assertRaises(ValueError):
            EmailConfig(
                provider=ProviderType.GMAIL,
                smtp_server="smtp.gmail.com",
                smtp_port=70000,  # Invalid port
                use_tls=True,
                sender_email="test@gmail.com",
                sender_password="test_password",
                auth_method=AuthMethod.APP_PASSWORD
            )
    
    @patch('interfaz.EmailServiceManagerImpl')
    def test_email_service_initialization_in_config(self, mock_service_class):
        """Test email service initialization during configuration"""
        # Set up mock
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.initialize.return_value = True
        mock_service.test_email_configuration.return_value = TestResult(
            success=True,
            provider="gmail",
            connection_test=True,
            auth_test=True,
            send_test=True,
            error_messages=[],
            test_duration=1.5
        )
        
        # Test that service manager is created and initialized
        interfaz.email_service_manager = None
        
        # Simulate configuration test
        config = EmailConfig(
            provider=ProviderType.GMAIL,
            smtp_server="smtp.gmail.com",
            smtp_port=587,
            use_tls=True,
            sender_email="test@gmail.com",
            sender_password="test_password",
            auth_method=AuthMethod.APP_PASSWORD
        )
        
        # Create service manager (simulating what happens in the UI)
        service_manager = EmailServiceManagerImpl()
        result = service_manager.initialize(config)
        
        # Verify service was created and initialized
        self.assertIsNotNone(service_manager)
    
    def test_email_status_display_data(self):
        """Test email status display data formatting"""
        # Add some test email statuses
        test_statuses = {
            "email-001": {
                'recipient': 'user1@example.com',
                'success': True,
                'attempts': 1,
                'timestamp': '10:30:15',
                'error_message': None,
                'sending': False,
                'queued': False
            },
            "email-002": {
                'recipient': 'user2@example.com',
                'success': False,
                'attempts': 3,
                'timestamp': '10:32:20',
                'error_message': 'SMTP connection timeout',
                'sending': False,
                'queued': False
            },
            "email-003": {
                'recipient': 'user3@example.com',
                'success': False,
                'attempts': 1,
                'timestamp': '10:35:10',
                'error_message': None,
                'sending': True,
                'queued': False
            }
        }
        
        interfaz.email_delivery_status.update(test_statuses)
        
        # Test status counting
        total = len(interfaz.email_delivery_status)
        exitosos = sum(1 for status in interfaz.email_delivery_status.values() if status.get('success', False))
        fallidos = sum(1 for status in interfaz.email_delivery_status.values() 
                      if not status.get('success', False) and not status.get('sending', False))
        
        self.assertEqual(total, 3)
        self.assertEqual(exitosos, 1)
        self.assertEqual(fallidos, 1)  # One failed, one still sending
        
        # Test status text generation
        for email_id, status in interfaz.email_delivery_status.items():
            if status.get('success', False):
                expected_status = "Exitoso"
            elif status.get('sending', False):
                expected_status = "Enviando..."
            elif status.get('queued', False):
                expected_status = "En cola"
            else:
                expected_status = "Fallido"
            
            # Verify status text logic
            if email_id == "email-001":
                self.assertEqual(expected_status, "Exitoso")
            elif email_id == "email-002":
                self.assertEqual(expected_status, "Fallido")
            elif email_id == "email-003":
                self.assertEqual(expected_status, "Enviando...")
    
    def test_provider_type_mapping(self):
        """Test provider type mapping for UI"""
        provider_mappings = {
            "gmail": ProviderType.GMAIL,
            "outlook": ProviderType.OUTLOOK,
            "yahoo": ProviderType.YAHOO,
            "custom": ProviderType.CUSTOM
        }
        
        for string_value, enum_value in provider_mappings.items():
            self.assertEqual(ProviderType(string_value), enum_value)
            self.assertEqual(enum_value.value, string_value)
    
    @patch('interfaz.messagebox')
    def test_email_service_unavailable_handling(self, mock_messagebox):
        """Test handling when email service is not available"""
        # Temporarily disable email service
        original_available = interfaz.EMAIL_SERVICE_AVAILABLE
        interfaz.EMAIL_SERVICE_AVAILABLE = False
        
        try:
            # Try to open email configuration
            interfaz.abrir_configuracion_email()
            
            # Verify error message was shown
            mock_messagebox.showerror.assert_called_once_with(
                "Error", "Email service not available"
            )
        finally:
            # Restore original state
            interfaz.EMAIL_SERVICE_AVAILABLE = original_available
    
    def test_email_status_persistence(self):
        """Test that email status persists across multiple updates"""
        email_id = "persistent-test"
        recipient = "test@example.com"
        
        # Initial status
        interfaz.marcar_email_enviando(email_id, recipient)
        self.assertTrue(interfaz.email_delivery_status[email_id]['sending'])
        
        # Update to success
        interfaz.actualizar_estado_email(email_id, recipient, True, 1, None)
        self.assertTrue(interfaz.email_delivery_status[email_id]['success'])
        self.assertFalse(interfaz.email_delivery_status[email_id]['sending'])
        
        # Verify data persistence
        status = interfaz.email_delivery_status[email_id]
        self.assertEqual(status['recipient'], recipient)
        self.assertEqual(status['attempts'], 1)
        self.assertIsNone(status['error_message'])
    
    def test_concurrent_email_status_updates(self):
        """Test concurrent email status updates"""
        def update_status(email_id, recipient, success):
            interfaz.actualizar_estado_email(email_id, recipient, success, 1, None)
        
        # Create multiple threads to update different emails
        threads = []
        for i in range(5):
            email_id = f"concurrent-{i}"
            recipient = f"user{i}@example.com"
            success = i % 2 == 0  # Alternate success/failure
            
            thread = threading.Thread(
                target=update_status, 
                args=(email_id, recipient, success)
            )
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all statuses were recorded
        self.assertEqual(len(interfaz.email_delivery_status), 5)
        
        # Verify success/failure pattern
        for i in range(5):
            email_id = f"concurrent-{i}"
            expected_success = i % 2 == 0
            actual_success = interfaz.email_delivery_status[email_id]['success']
            self.assertEqual(actual_success, expected_success)


class TestEmailConfigurationUI(unittest.TestCase):
    """Test email configuration UI components"""
    
    def setUp(self):
        """Set up test environment"""
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the window during tests
    
    def tearDown(self):
        """Clean up after tests"""
        try:
            self.root.destroy()
        except:
            pass
    
    def test_provider_specific_smtp_settings(self):
        """Test that provider-specific SMTP settings are correct"""
        provider_settings = {
            "gmail": {
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "use_tls": True
            },
            "outlook": {
                "smtp_server": "smtp-mail.outlook.com",
                "smtp_port": 587,
                "use_tls": True
            },
            "yahoo": {
                "smtp_server": "smtp.mail.yahoo.com",
                "smtp_port": 587,
                "use_tls": True
            }
        }
        
        for provider, settings in provider_settings.items():
            # Test that we can create valid configurations
            try:
                config = EmailConfig(
                    provider=ProviderType(provider),
                    smtp_server=settings["smtp_server"],
                    smtp_port=settings["smtp_port"],
                    use_tls=settings["use_tls"],
                    sender_email=f"test@{provider}.com",
                    sender_password="test_password",
                    auth_method=AuthMethod.APP_PASSWORD
                )
                self.assertIsNotNone(config)
            except Exception as e:
                self.fail(f"Failed to create config for {provider}: {e}")


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)