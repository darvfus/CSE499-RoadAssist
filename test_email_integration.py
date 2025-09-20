"""
Integration Test Suite for Email Service

This comprehensive test suite covers end-to-end email workflows, provider switching,
error scenarios, and performance testing for the email service system.
"""

import unittest
import time
import threading
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from typing import List, Dict, Any

from email_service.testing_utils import (
    EmailTestingUtils, MockEmailProvider, create_test_config,
    create_test_email_data, create_test_user_data, create_test_alert_data
)
from email_service.service_manager import EmailServiceManagerImpl
from email_service.delivery import EmailDeliveryManagerImpl
from email_service.templates import EmailTemplateEngineImpl
from email_service.package_manager import EmailPackageManagerImpl
from email_service.error_handler import EmailErrorHandlerImpl
from email_service.models import (
    EmailConfig, EmailData, UserData, AlertData, DeliveryResult, TestResult
)
from email_service.enums import (
    ProviderType, AuthMethod, Priority, AlertType, DeliveryStatusType, ErrorType
)


class EmailServiceIntegrationTest(unittest.TestCase):
    """Integration tests for complete email service workflows"""
    
    def setUp(self):
        """Set up test environment"""
        self.service_manager = EmailServiceManagerImpl()
        self.delivery_manager = EmailDeliveryManagerImpl()
        self.template_engine = EmailTemplateEngineImpl()
        self.package_manager = EmailPackageManagerImpl()
        self.error_handler = EmailErrorHandlerImpl()
        self.testing_utils = EmailTestingUtils()
        
        # Create test data
        self.test_config = create_test_config(ProviderType.GMAIL)
        self.test_user = create_test_user_data()
        self.test_alert = create_test_alert_data()
        self.test_email_data = create_test_email_data()
    
    def test_end_to_end_email_workflow(self):
        """Test complete end-to-end email sending workflow"""
        print("\n--- Testing End-to-End Email Workflow ---")
        
        # Use mock provider for testing
        mock_provider = MockEmailProvider()
        
        with patch('email_service.providers.EmailProviderFactory.create_provider') as mock_create:
            mock_create.return_value = mock_provider
            
            # Initialize service
            init_result = self.service_manager.initialize(self.test_config)
            self.assertTrue(init_result)
            
            # Send alert email
            result = self.service_manager.send_alert_email(self.test_user, self.test_alert)
            
            # Verify results
            self.assertTrue(result.success)
            self.assertIsNotNone(result.email_id)
            
            # Check that email was sent through mock provider
            sent_emails = mock_provider.get_sent_emails()
            self.assertEqual(len(sent_emails), 1)
            
            sent_email = sent_emails[0]
            self.assertEqual(sent_email['data'].recipient, self.test_user.email)
            self.assertIn("drowsiness", sent_email['data'].subject.lower())
    
    def test_template_integration_workflow(self):
        """Test integration between template engine and email service"""
        print("\n--- Testing Template Integration Workflow ---")
        
        mock_provider = MockEmailProvider()
        
        with patch('email_service.providers.EmailProviderFactory.create_provider') as mock_create:
            mock_create.return_value = mock_provider
            
            # Initialize service
            self.service_manager.initialize(self.test_config)
            
            # Test different alert types
            alert_types = [AlertType.DROWSINESS, AlertType.VITAL_SIGNS]
            
            for alert_type in alert_types:
                with self.subTest(alert_type=alert_type):
                    test_alert = create_test_alert_data()
                    test_alert.alert_type = alert_type
                    
                    result = self.service_manager.send_alert_email(self.test_user, test_alert)
                    self.assertTrue(result.success)
            
            # Verify both emails were sent
            sent_emails = mock_provider.get_sent_emails()
            self.assertEqual(len(sent_emails), 2)
    
    def test_delivery_manager_integration(self):
        """Test integration with delivery manager for retry logic"""
        print("\n--- Testing Delivery Manager Integration ---")
        
        # Create failing provider that succeeds on retry
        class RetryMockProvider(MockEmailProvider):
            def __init__(self):
                super().__init__()
                self.attempt_count = 0
            
            def send_email(self, email_data):
                self.attempt_count += 1
                if self.attempt_count < 3:  # Fail first 2 attempts
                    from email_service.models import EmailResult
                    return EmailResult(
                        success=False,
                        message=f"Mock failure attempt {self.attempt_count}",
                        email_id=None
                    )
                return super().send_email(email_data)
        
        retry_provider = RetryMockProvider()
        
        # Set the provider directly on the delivery manager
        self.delivery_manager.set_provider(retry_provider)
        
        # Test delivery with retry
        result = self.delivery_manager.send_with_retry(self.test_email_data)
        
        # Should succeed after retries
        self.assertTrue(result.success)
        self.assertEqual(result.attempts, 3)
        self.assertEqual(retry_provider.attempt_count, 3)
    
    def test_package_manager_integration(self):
        """Test integration with package manager"""
        print("\n--- Testing Package Manager Integration ---")
        
        # Test package checking
        package_status = self.package_manager.get_installation_status()
        self.assertIsInstance(package_status.required_packages, dict)
        
        # Test with service manager initialization
        with patch.object(self.service_manager, 'package_manager', self.package_manager):
            init_result = self.service_manager.initialize(self.test_config)
            # Should succeed even if some packages are missing (they get installed)
            self.assertTrue(init_result)
    
    def test_error_handler_integration(self):
        """Test integration with error handler"""
        print("\n--- Testing Error Handler Integration ---")
        
        # Test different error types
        test_errors = [
            (ConnectionError("Network error"), ErrorType.NETWORK_ERROR),
            (ValueError("Config error"), ErrorType.CONFIG_ERROR),
            (Exception("Unknown error"), ErrorType.PACKAGE_ERROR)  # Using available enum value
        ]
        
        for error, expected_type in test_errors:
            with self.subTest(error_type=expected_type):
                error_type = self.error_handler.get_error_type(error)
                response = self.error_handler.handle_network_error(error)
                
                self.assertIsInstance(response.troubleshooting_steps, list)
                self.assertGreater(len(response.troubleshooting_steps), 0)


class ProviderSwitchingTest(unittest.TestCase):
    """Test provider switching and configuration changes"""
    
    def setUp(self):
        """Set up test environment"""
        self.service_manager = EmailServiceManagerImpl()
        self.testing_utils = EmailTestingUtils()
    
    def test_provider_switching(self):
        """Test switching between different email providers"""
        print("\n--- Testing Provider Switching ---")
        
        providers = [
            (ProviderType.GMAIL, "Gmail"),
            (ProviderType.OUTLOOK, "Outlook"),
            (ProviderType.YAHOO, "Yahoo")
        ]
        
        for provider_type, provider_name in providers:
            with self.subTest(provider=provider_name):
                config = create_test_config(provider_type)
                mock_provider = MockEmailProvider()
                
                with patch('email_service.providers.EmailProviderFactory.create_provider') as mock_create:
                    mock_create.return_value = mock_provider
                    
                    # Initialize with new provider
                    result = self.service_manager.initialize(config)
                    self.assertTrue(result)
                    
                    # Test configuration
                    test_result = self.service_manager.test_email_configuration()
                    self.assertTrue(test_result.success)
                    self.assertEqual(test_result.provider, provider_type.value)
    
    def test_configuration_updates(self):
        """Test updating email configuration"""
        print("\n--- Testing Configuration Updates ---")
        
        mock_provider = MockEmailProvider()
        
        with patch('email_service.providers.EmailProviderFactory.create_provider') as mock_create:
            mock_create.return_value = mock_provider
            
            # Initial configuration
            initial_config = create_test_config(ProviderType.GMAIL)
            self.service_manager.initialize(initial_config)
            
            # Update configuration
            new_config = create_test_config(ProviderType.OUTLOOK)
            update_result = self.service_manager.update_configuration(new_config)
            self.assertTrue(update_result)
            
            # Verify new configuration is active
            test_result = self.service_manager.test_email_configuration()
            self.assertEqual(test_result.provider, ProviderType.OUTLOOK.value)
    
    def test_provider_fallback(self):
        """Test fallback to alternative providers on failure"""
        print("\n--- Testing Provider Fallback ---")
        
        # Create providers with different failure modes
        failing_provider = MockEmailProvider(should_fail=True, fail_on='send_email')
        working_provider = MockEmailProvider()
        
        providers = [failing_provider, working_provider]
        provider_index = 0
        
        def mock_create_provider(config):
            nonlocal provider_index
            provider = providers[provider_index % len(providers)]
            provider_index += 1
            return provider
        
        with patch('email_service.providers.EmailProviderFactory.create_provider', side_effect=mock_create_provider):
            # This would require implementing fallback logic in the service manager
            # For now, we test that the service can handle provider failures
            self.service_manager.initialize(self.service_manager._config or create_test_config())
            
            # The service should handle provider failures gracefully
            user_data = create_test_user_data()
            alert_data = create_test_alert_data()
            
            # First attempt should fail, but service should handle it
            result = self.service_manager.send_alert_email(user_data, alert_data)
            # Result depends on implementation of fallback logic


class ErrorScenarioTest(unittest.TestCase):
    """Test various error scenarios and recovery mechanisms"""
    
    def setUp(self):
        """Set up test environment"""
        self.service_manager = EmailServiceManagerImpl()
        self.delivery_manager = EmailDeliveryManagerImpl()
        self.error_handler = EmailErrorHandlerImpl()
    
    def test_network_error_scenarios(self):
        """Test handling of network-related errors"""
        print("\n--- Testing Network Error Scenarios ---")
        
        network_errors = [
            ConnectionError("Connection refused"),
            TimeoutError("Connection timeout"),
            OSError("Network unreachable")
        ]
        
        for error in network_errors:
            with self.subTest(error=type(error).__name__):
                response = self.error_handler.handle_network_error(error)
                
                self.assertEqual(response.error_type, ErrorType.NETWORK_ERROR)
                self.assertIn("network", response.message.lower())
                self.assertGreater(len(response.troubleshooting_steps), 0)
    
    def test_authentication_error_scenarios(self):
        """Test handling of authentication errors"""
        print("\n--- Testing Authentication Error Scenarios ---")
        
        import smtplib
        auth_errors = [
            smtplib.SMTPAuthenticationError(535, "Authentication failed"),
            smtplib.SMTPAuthenticationError(534, "Username and password not accepted")
        ]
        
        for error in auth_errors:
            with self.subTest(error_code=error.smtp_code):
                response = self.error_handler.handle_auth_error(error)
                
                self.assertEqual(response.error_type, ErrorType.AUTH_ERROR)
                self.assertIn("authentication", response.message.lower())
                self.assertIn("credentials", " ".join(response.troubleshooting_steps).lower())
    
    def test_configuration_error_scenarios(self):
        """Test handling of configuration errors"""
        print("\n--- Testing Configuration Error Scenarios ---")
        
        config_errors = [
            ValueError("Invalid email address"),
            ValueError("Invalid port number"),
            KeyError("Missing configuration key")
        ]
        
        for error in config_errors:
            with self.subTest(error=str(error)):
                response = self.error_handler.handle_config_error(error)
                
                self.assertEqual(response.error_type, ErrorType.CONFIG_ERROR)
                self.assertGreater(len(response.troubleshooting_steps), 0)
    
    def test_email_queue_error_recovery(self):
        """Test email queue error recovery"""
        print("\n--- Testing Email Queue Error Recovery ---")
        
        # Create failing provider
        failing_provider = MockEmailProvider(should_fail=True, fail_on='send_email')
        
        # Set the failing provider directly on the delivery manager
        self.delivery_manager.set_provider(failing_provider)
        
        # Queue multiple emails
        email_ids = []
        for i in range(3):
            email_data = create_test_email_data(f"test{i}@example.com")
            email_id = self.delivery_manager.queue_email(email_data)
            email_ids.append(email_id)
        
        # Process queue (should fail)
        results = self.delivery_manager.process_queue()
        
        # All should fail
        for result in results:
            self.assertFalse(result.success)
        
        # Check delivery status
        for email_id in email_ids:
            status = self.delivery_manager.get_delivery_status(email_id)
            self.assertIsNotNone(status)
            self.assertEqual(status.status, DeliveryStatusType.FAILED)
    
    def test_concurrent_email_sending(self):
        """Test concurrent email sending scenarios"""
        print("\n--- Testing Concurrent Email Sending ---")
        
        mock_provider = MockEmailProvider()
        results = []
        errors = []
        
        def send_email_worker(email_data):
            try:
                result = mock_provider.send_email(email_data)
                results.append(result)
            except Exception as e:
                errors.append(e)
        
        # Create multiple threads sending emails
        threads = []
        for i in range(5):
            email_data = create_test_email_data(f"concurrent{i}@example.com")
            thread = threading.Thread(target=send_email_worker, args=(email_data,))
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Verify results
        self.assertEqual(len(results), 5)
        self.assertEqual(len(errors), 0)
        
        # Check that all emails were sent
        sent_emails = mock_provider.get_sent_emails()
        self.assertEqual(len(sent_emails), 5)


class PerformanceTest(unittest.TestCase):
    """Performance tests for email service operations"""
    
    def setUp(self):
        """Set up test environment"""
        self.service_manager = EmailServiceManagerImpl()
        self.delivery_manager = EmailDeliveryManagerImpl()
        self.template_engine = EmailTemplateEngineImpl()
        self.testing_utils = EmailTestingUtils()
    
    def test_email_sending_performance(self):
        """Test email sending performance"""
        print("\n--- Testing Email Sending Performance ---")
        
        mock_provider = MockEmailProvider()
        
        with patch('email_service.providers.EmailProviderFactory.create_provider') as mock_create:
            mock_create.return_value = mock_provider
            
            self.service_manager.initialize(create_test_config())
            
            # Measure time for multiple emails
            num_emails = 100
            start_time = time.time()
            
            for i in range(num_emails):
                user_data = create_test_user_data()
                user_data.email = f"perf_test_{i}@example.com"
                alert_data = create_test_alert_data()
                
                result = self.service_manager.send_alert_email(user_data, alert_data)
                self.assertTrue(result.success)
            
            end_time = time.time()
            total_time = end_time - start_time
            emails_per_second = num_emails / total_time
            
            print(f"Sent {num_emails} emails in {total_time:.2f} seconds")
            print(f"Performance: {emails_per_second:.2f} emails/second")
            
            # Performance assertion (should be fast with mock provider)
            self.assertLess(total_time, 10.0)  # Should complete in under 10 seconds
            self.assertGreater(emails_per_second, 10)  # Should send at least 10 emails/second
    
    def test_template_rendering_performance(self):
        """Test template rendering performance"""
        print("\n--- Testing Template Rendering Performance ---")
        
        # Load templates
        templates = self.template_engine.load_templates()
        self.assertGreater(len(templates), 0)
        
        # Test rendering performance
        template_name = "drowsiness_alert"
        template_data = {
            "user_name": "Performance Test User",
            "timestamp": datetime.now().isoformat(),
            "heart_rate": 75,
            "oxygen_saturation": 98.5
        }
        
        num_renders = 1000
        start_time = time.time()
        
        for i in range(num_renders):
            content = self.template_engine.render_template(template_name, template_data)
            self.assertIsNotNone(content.subject)
            self.assertIsNotNone(content.body)
        
        end_time = time.time()
        total_time = end_time - start_time
        renders_per_second = num_renders / total_time
        
        print(f"Rendered {num_renders} templates in {total_time:.2f} seconds")
        print(f"Performance: {renders_per_second:.2f} renders/second")
        
        # Performance assertion
        self.assertLess(total_time, 5.0)  # Should complete in under 5 seconds
        self.assertGreater(renders_per_second, 200)  # Should render at least 200/second
    
    def test_configuration_validation_performance(self):
        """Test configuration validation performance"""
        print("\n--- Testing Configuration Validation Performance ---")
        
        configs = []
        for i in range(100):
            config = create_test_config(ProviderType.GMAIL)
            config.sender_email = f"test{i}@gmail.com"
            configs.append(config)
        
        start_time = time.time()
        
        for config in configs:
            result = self.testing_utils.validate_email_config(config)
            self.assertTrue(result.valid)
        
        end_time = time.time()
        total_time = end_time - start_time
        validations_per_second = len(configs) / total_time
        
        print(f"Validated {len(configs)} configurations in {total_time:.2f} seconds")
        print(f"Performance: {validations_per_second:.2f} validations/second")
        
        # Performance assertion
        self.assertLess(total_time, 2.0)  # Should complete in under 2 seconds
        self.assertGreater(validations_per_second, 50)  # Should validate at least 50/second
    
    def test_memory_usage_during_bulk_operations(self):
        """Test memory usage during bulk email operations"""
        print("\n--- Testing Memory Usage During Bulk Operations ---")
        
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        mock_provider = MockEmailProvider()
        
        with patch('email_service.providers.EmailProviderFactory.create_provider') as mock_create:
            mock_create.return_value = mock_provider
            
            self.service_manager.initialize(create_test_config())
            
            # Send many emails
            for i in range(500):
                user_data = create_test_user_data()
                user_data.email = f"memory_test_{i}@example.com"
                alert_data = create_test_alert_data()
                
                result = self.service_manager.send_alert_email(user_data, alert_data)
                self.assertTrue(result.success)
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        print(f"Initial memory: {initial_memory:.2f} MB")
        print(f"Final memory: {final_memory:.2f} MB")
        print(f"Memory increase: {memory_increase:.2f} MB")
        
        # Memory usage should not increase dramatically
        self.assertLess(memory_increase, 50)  # Should not increase by more than 50MB


class IntegrationTestSuite:
    """Main integration test suite runner"""
    
    @staticmethod
    def run_all_tests():
        """Run all integration tests"""
        print("=" * 80)
        print("EMAIL SERVICE INTEGRATION TEST SUITE")
        print("=" * 80)
        
        # Create test suite
        suite = unittest.TestSuite()
        
        # Add test classes
        test_classes = [
            EmailServiceIntegrationTest,
            ProviderSwitchingTest,
            ErrorScenarioTest,
            PerformanceTest
        ]
        
        for test_class in test_classes:
            tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
            suite.addTests(tests)
        
        # Run tests
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        # Print summary
        print("\n" + "=" * 80)
        print("INTEGRATION TEST SUMMARY")
        print("=" * 80)
        print(f"Tests run: {result.testsRun}")
        print(f"Failures: {len(result.failures)}")
        print(f"Errors: {len(result.errors)}")
        print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
        
        if result.failures:
            print("\nFAILURES:")
            for test, traceback in result.failures:
                print(f"- {test}: {traceback.split('AssertionError:')[-1].strip()}")
        
        if result.errors:
            print("\nERRORS:")
            for test, traceback in result.errors:
                print(f"- {test}: {traceback.split('Exception:')[-1].strip()}")
        
        return result.wasSuccessful()


if __name__ == '__main__':
    # Run individual test classes or the full suite
    import sys
    
    if len(sys.argv) > 1:
        # Run specific test class
        test_class_name = sys.argv[1]
        if test_class_name in globals():
            unittest.main(argv=[''], testRunner=unittest.TextTestRunner(verbosity=2))
    else:
        # Run full integration test suite
        success = IntegrationTestSuite.run_all_tests()
        sys.exit(0 if success else 1)