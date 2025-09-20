"""
Unit Tests for Email Delivery Manager

Tests the EmailDeliveryManager implementation including:
- Retry logic with exponential backoff
- Email queuing system
- Delivery status tracking
- Logging functionality
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import time
from datetime import datetime, timedelta
from queue import Queue

from email_service.delivery import EmailDeliveryManagerImpl
from email_service.models import EmailData, EmailResult, DeliveryStatus
from email_service.enums import Priority, DeliveryStatusType


class MockEmailProvider:
    """Mock email provider for testing"""
    
    def __init__(self, should_succeed=True, failure_count=0):
        self.should_succeed = should_succeed
        self.failure_count = failure_count
        self.call_count = 0
    
    def send_email(self, email_data):
        self.call_count += 1
        
        if self.failure_count > 0 and self.call_count <= self.failure_count:
            return EmailResult(
                success=False,
                message=f"Mock failure {self.call_count}",
                email_id=None
            )
        
        if self.should_succeed:
            return EmailResult(
                success=True,
                message="Email sent successfully",
                email_id="mock-email-id"
            )
        else:
            return EmailResult(
                success=False,
                message="Mock failure",
                email_id=None
            )


class TestEmailDeliveryManager(unittest.TestCase):
    """Test cases for EmailDeliveryManager"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_provider = MockEmailProvider()
        self.delivery_manager = EmailDeliveryManagerImpl(
            email_provider=self.mock_provider,
            max_retries=3
        )
        
        # Sample email data
        self.sample_email = EmailData(
            recipient="test@example.com",
            subject="Test Email",
            body="This is a test email",
            template_name="test_template",
            template_data={"name": "Test User"},
            priority=Priority.NORMAL
        )
    
    def test_successful_email_delivery(self):
        """Test successful email delivery on first attempt"""
        # Configure mock to succeed
        self.mock_provider.should_succeed = True
        
        # Send email
        result = self.delivery_manager.send_with_retry(self.sample_email)
        
        # Verify success
        self.assertTrue(result.success)
        self.assertEqual(result.attempts, 1)
        self.assertIsNotNone(result.email_id)
        self.assertIsNone(result.error_message)
        self.assertEqual(self.mock_provider.call_count, 1)
        
        # Check delivery status
        status = self.delivery_manager.get_delivery_status(result.email_id)
        self.assertIsNotNone(status)
        self.assertEqual(status.status, DeliveryStatusType.SENT)
    
    def test_email_delivery_with_retries(self):
        """Test email delivery that succeeds after retries"""
        # Configure mock to fail first 2 attempts, then succeed
        self.mock_provider.failure_count = 2
        
        # Mock time.sleep to speed up test
        with patch('time.sleep'):
            result = self.delivery_manager.send_with_retry(self.sample_email)
        
        # Verify success after retries
        self.assertTrue(result.success)
        self.assertEqual(result.attempts, 3)  # Failed twice, succeeded on third
        self.assertEqual(self.mock_provider.call_count, 3)
        
        # Check final delivery status
        status = self.delivery_manager.get_delivery_status(result.email_id)
        self.assertEqual(status.status, DeliveryStatusType.SENT)
    
    def test_email_delivery_failure_after_max_retries(self):
        """Test email delivery that fails after all retry attempts"""
        # Configure mock to always fail
        self.mock_provider.should_succeed = False
        
        # Mock time.sleep to speed up test
        with patch('time.sleep'):
            result = self.delivery_manager.send_with_retry(self.sample_email)
        
        # Verify failure
        self.assertFalse(result.success)
        self.assertEqual(result.attempts, 3)  # Max retries
        self.assertIsNotNone(result.error_message)
        self.assertEqual(self.mock_provider.call_count, 3)
        
        # Check final delivery status
        status = self.delivery_manager.get_delivery_status(result.email_id)
        self.assertEqual(status.status, DeliveryStatusType.FAILED)
        self.assertIsNotNone(status.last_error)
    
    @patch('time.sleep')
    def test_exponential_backoff_timing(self, mock_sleep):
        """Test that exponential backoff is applied correctly"""
        # Configure mock to fail first 2 attempts
        self.mock_provider.failure_count = 2
        
        # Send email
        self.delivery_manager.send_with_retry(self.sample_email)
        
        # Verify sleep was called with correct backoff times
        expected_calls = [unittest.mock.call(1), unittest.mock.call(2)]
        mock_sleep.assert_has_calls(expected_calls)
    
    def test_email_queuing(self):
        """Test email queuing functionality"""
        # Queue an email
        email_id = self.delivery_manager.queue_email(self.sample_email)
        
        # Verify email was queued
        self.assertIsNotNone(email_id)
        self.assertEqual(self.delivery_manager.get_queue_size(), 1)
        
        # Check delivery status
        status = self.delivery_manager.get_delivery_status(email_id)
        self.assertIsNotNone(status)
        self.assertEqual(status.status, DeliveryStatusType.QUEUED)
    
    def test_queue_processing(self):
        """Test processing of queued emails"""
        # Queue multiple emails
        email_ids = []
        for i in range(3):
            email_data = EmailData(
                recipient=f"test{i}@example.com",
                subject=f"Test Email {i}",
                body=f"Test body {i}",
                template_name="test_template",
                template_data={"name": f"User {i}"}
            )
            email_id = self.delivery_manager.queue_email(email_data)
            email_ids.append(email_id)
        
        # Verify queue size
        self.assertEqual(self.delivery_manager.get_queue_size(), 3)
        
        # Process queue
        with patch('time.sleep'):  # Speed up retries
            results = self.delivery_manager.process_queue()
        
        # Verify all emails were processed
        self.assertEqual(len(results), 3)
        self.assertEqual(self.delivery_manager.get_queue_size(), 0)
        
        # Check that all emails were sent successfully
        for result in results:
            self.assertTrue(result.success)
    
    def test_delivery_status_tracking(self):
        """Test delivery status tracking with unique IDs"""
        # Send multiple emails
        results = []
        for i in range(3):
            email_data = EmailData(
                recipient=f"test{i}@example.com",
                subject=f"Test Email {i}",
                body=f"Test body {i}",
                template_name="test_template",
                template_data={"name": f"User {i}"}
            )
            result = self.delivery_manager.send_with_retry(email_data)
            results.append(result)
        
        # Verify each email has unique ID and status
        email_ids = [result.email_id for result in results]
        self.assertEqual(len(set(email_ids)), 3)  # All IDs should be unique
        
        # Check status for each email
        for result in results:
            status = self.delivery_manager.get_delivery_status(result.email_id)
            self.assertIsNotNone(status)
            self.assertEqual(status.email_id, result.email_id)
            self.assertEqual(status.status, DeliveryStatusType.SENT)
    
    def test_cancel_queued_delivery(self):
        """Test cancelling a queued email delivery"""
        # Queue an email
        email_id = self.delivery_manager.queue_email(self.sample_email)
        
        # Verify it's queued
        status = self.delivery_manager.get_delivery_status(email_id)
        self.assertEqual(status.status, DeliveryStatusType.QUEUED)
        
        # Cancel the delivery
        cancelled = self.delivery_manager.cancel_delivery(email_id)
        self.assertTrue(cancelled)
        
        # Verify status is updated
        status = self.delivery_manager.get_delivery_status(email_id)
        self.assertEqual(status.status, DeliveryStatusType.FAILED)
        self.assertEqual(status.last_error, "Cancelled by user")
    
    def test_cancel_non_queued_delivery(self):
        """Test attempting to cancel a non-queued email"""
        # Send an email (not queued)
        result = self.delivery_manager.send_with_retry(self.sample_email)
        
        # Try to cancel it (should fail since it's already sent)
        cancelled = self.delivery_manager.cancel_delivery(result.email_id)
        self.assertFalse(cancelled)
    
    def test_cancel_nonexistent_delivery(self):
        """Test attempting to cancel a non-existent email"""
        # Try to cancel non-existent email
        cancelled = self.delivery_manager.cancel_delivery("non-existent-id")
        self.assertFalse(cancelled)
    
    def test_get_all_delivery_statuses(self):
        """Test retrieving all delivery statuses"""
        # Send multiple emails
        email_ids = []
        for i in range(3):
            email_data = EmailData(
                recipient=f"test{i}@example.com",
                subject=f"Test Email {i}",
                body=f"Test body {i}",
                template_name="test_template",
                template_data={"name": f"User {i}"}
            )
            result = self.delivery_manager.send_with_retry(email_data)
            email_ids.append(result.email_id)
        
        # Get all statuses
        all_statuses = self.delivery_manager.get_all_delivery_statuses()
        
        # Verify all emails are tracked
        self.assertEqual(len(all_statuses), 3)
        for email_id in email_ids:
            self.assertIn(email_id, all_statuses)
            self.assertEqual(all_statuses[email_id].status, DeliveryStatusType.SENT)
    
    def test_cleanup_old_statuses(self):
        """Test cleanup of old delivery statuses"""
        # Send an email
        result = self.delivery_manager.send_with_retry(self.sample_email)
        email_id = result.email_id
        
        # Verify status exists
        status = self.delivery_manager.get_delivery_status(email_id)
        self.assertIsNotNone(status)
        
        # Manually set old timestamp
        with self.delivery_manager.delivery_lock:
            self.delivery_manager.delivery_status[email_id].updated_at = (
                datetime.now() - timedelta(hours=25)
            )
        
        # Run cleanup
        cleaned_count = self.delivery_manager.cleanup_old_statuses(max_age_hours=24)
        
        # Verify status was cleaned up
        self.assertEqual(cleaned_count, 1)
        status = self.delivery_manager.get_delivery_status(email_id)
        self.assertIsNone(status)
    
    @patch('email_service.delivery.logging.getLogger')
    def test_logging_functionality(self, mock_get_logger):
        """Test that logging is properly configured and used"""
        # Create a mock logger
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        # Create new delivery manager to trigger logger setup
        delivery_manager = EmailDeliveryManagerImpl(self.mock_provider)
        
        # Send an email to trigger logging
        delivery_manager.send_with_retry(self.sample_email)
        
        # Verify logger was called
        self.assertTrue(mock_logger.info.called)
    
    def test_provider_exception_handling(self):
        """Test handling of exceptions from email provider"""
        # Create a provider that raises exceptions
        class ExceptionProvider:
            def send_email(self, email_data):
                raise Exception("Provider connection failed")
        
        exception_provider = ExceptionProvider()
        delivery_manager = EmailDeliveryManagerImpl(exception_provider, max_retries=2)
        
        # Mock time.sleep to speed up test
        with patch('time.sleep'):
            result = delivery_manager.send_with_retry(self.sample_email)
        
        # Verify failure is handled properly
        self.assertFalse(result.success)
        self.assertEqual(result.attempts, 2)
        self.assertIn("Provider connection failed", result.error_message)
    
    def test_thread_safety(self):
        """Test thread safety of delivery status operations"""
        import threading
        
        results = []
        
        def send_email_worker():
            email_data = EmailData(
                recipient="worker@example.com",
                subject="Worker Email",
                body="Worker body",
                template_name="test_template",
                template_data={"name": "Worker"}
            )
            result = self.delivery_manager.send_with_retry(email_data)
            results.append(result)
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=send_email_worker)
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all emails were processed
        self.assertEqual(len(results), 5)
        
        # Verify all have unique IDs
        email_ids = [result.email_id for result in results]
        self.assertEqual(len(set(email_ids)), 5)


if __name__ == '__main__':
    unittest.main()