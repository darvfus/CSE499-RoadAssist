"""
Email Delivery Manager Implementation

This module provides email delivery management with retry logic, exponential backoff,
and queuing system for offline scenarios.
"""

import time
import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from threading import Lock
from queue import Queue, Empty
import json

from .interfaces import EmailDeliveryManager, EmailProvider
from .models import EmailData, DeliveryResult, DeliveryStatus, EmailResult
from .enums import DeliveryStatusType


class EmailDeliveryManagerImpl(EmailDeliveryManager):
    """
    Implementation of email delivery manager with retry logic and queuing.
    
    Features:
    - Exponential backoff retry strategy
    - Email queuing for offline scenarios
    - Delivery status tracking with unique IDs
    - Comprehensive logging
    """
    
    def __init__(self, email_provider: Optional[EmailProvider] = None, max_retries: int = 3):
        """
        Initialize the delivery manager.
        
        Args:
            email_provider: The email provider to use for sending (optional)
            max_retries: Maximum number of retry attempts (default: 3)
        """
        self.email_provider = email_provider
        self.max_retries = max_retries
        self.email_queue: Queue = Queue()
        self.delivery_status: Dict[str, DeliveryStatus] = {}
        self.delivery_lock = Lock()
        
        # Configure logging
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def send_with_retry(self, email_data: EmailData) -> DeliveryResult:
        """
        Send email with retry logic and exponential backoff.
        
        Args:
            email_data: Email data to send
            
        Returns:
            DeliveryResult with success status and details
        """
        email_id = str(uuid.uuid4())
        start_time = time.time()
        
        # Check if provider is available
        if not self.email_provider:
            return DeliveryResult(
                success=False,
                email_id=email_id,
                timestamp=datetime.now(),
                attempts=0,
                error_message="No email provider configured",
                delivery_time=0.0
            )
        
        # Initialize delivery status
        with self.delivery_lock:
            self.delivery_status[email_id] = DeliveryStatus(
                email_id=email_id,
                status=DeliveryStatusType.SENDING,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                attempts=0
            )
        
        self.logger.info(f"Starting email delivery for ID: {email_id}")
        
        last_error = None
        
        for attempt in range(1, self.max_retries + 1):
            try:
                # Update status for retry attempts
                if attempt > 1:
                    with self.delivery_lock:
                        self.delivery_status[email_id].status = DeliveryStatusType.RETRYING
                        self.delivery_status[email_id].attempts = attempt
                        self.delivery_status[email_id].updated_at = datetime.now()
                
                self.logger.info(f"Attempt {attempt}/{self.max_retries} for email ID: {email_id}")
                
                # Try to send the email
                result = self.email_provider.send_email(email_data)
                
                if result.success:
                    # Success - update status and return
                    delivery_time = time.time() - start_time
                    
                    with self.delivery_lock:
                        self.delivery_status[email_id].status = DeliveryStatusType.SENT
                        self.delivery_status[email_id].updated_at = datetime.now()
                    
                    self.logger.info(f"Email sent successfully. ID: {email_id}, Time: {delivery_time:.2f}s")
                    
                    return DeliveryResult(
                        success=True,
                        email_id=email_id,
                        timestamp=datetime.now(),
                        attempts=attempt,
                        delivery_time=delivery_time,
                        provider_used=self.email_provider.__class__.__name__
                    )
                else:
                    # Provider returned failure
                    last_error = result.message
                    self.logger.warning(f"Email send failed on attempt {attempt}: {last_error}")
                    
            except Exception as e:
                last_error = str(e)
                self.logger.error(f"Exception on attempt {attempt} for email ID {email_id}: {last_error}")
            
            # Apply exponential backoff if not the last attempt
            if attempt < self.max_retries:
                backoff_time = 2 ** (attempt - 1)  # 1s, 2s, 4s
                self.logger.info(f"Waiting {backoff_time}s before retry...")
                time.sleep(backoff_time)
        
        # All attempts failed
        delivery_time = time.time() - start_time
        
        with self.delivery_lock:
            self.delivery_status[email_id].status = DeliveryStatusType.FAILED
            self.delivery_status[email_id].last_error = last_error
            self.delivery_status[email_id].updated_at = datetime.now()
        
        self.logger.error(f"Email delivery failed after {self.max_retries} attempts. ID: {email_id}")
        
        return DeliveryResult(
            success=False,
            email_id=email_id,
            timestamp=datetime.now(),
            attempts=self.max_retries,
            error_message=last_error,
            delivery_time=delivery_time,
            provider_used=self.email_provider.__class__.__name__
        )
    
    def queue_email(self, email_data: EmailData) -> str:
        """
        Queue email for later delivery.
        
        Args:
            email_data: Email data to queue
            
        Returns:
            Unique email ID for tracking
        """
        email_id = str(uuid.uuid4())
        
        # Create queued email entry
        queued_email = {
            'email_id': email_id,
            'email_data': email_data,
            'queued_at': datetime.now().isoformat()
        }
        
        # Add to queue
        self.email_queue.put(queued_email)
        
        # Update delivery status
        with self.delivery_lock:
            self.delivery_status[email_id] = DeliveryStatus(
                email_id=email_id,
                status=DeliveryStatusType.QUEUED,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                attempts=0
            )
        
        self.logger.info(f"Email queued for delivery. ID: {email_id}")
        return email_id
    
    def process_queue(self) -> List[DeliveryResult]:
        """
        Process all queued emails.
        
        Returns:
            List of delivery results for processed emails
        """
        results = []
        processed_count = 0
        
        self.logger.info("Starting queue processing...")
        
        while not self.email_queue.empty():
            try:
                # Get queued email with timeout
                queued_email = self.email_queue.get(timeout=1)
                processed_count += 1
                
                email_id = queued_email['email_id']
                email_data = queued_email['email_data']
                
                self.logger.info(f"Processing queued email ID: {email_id}")
                
                # Update status to sending
                with self.delivery_lock:
                    if email_id in self.delivery_status:
                        self.delivery_status[email_id].status = DeliveryStatusType.SENDING
                        self.delivery_status[email_id].updated_at = datetime.now()
                
                # Send the email
                result = self.send_with_retry(email_data)
                results.append(result)
                
                # Mark task as done
                self.email_queue.task_done()
                
            except Empty:
                # Queue is empty
                break
            except Exception as e:
                self.logger.error(f"Error processing queued email: {str(e)}")
                # Mark task as done even on error to prevent hanging
                self.email_queue.task_done()
        
        self.logger.info(f"Queue processing completed. Processed {processed_count} emails.")
        return results
    
    def get_delivery_status(self, email_id: str) -> Optional[DeliveryStatus]:
        """
        Get current delivery status of an email.
        
        Args:
            email_id: Unique email identifier
            
        Returns:
            DeliveryStatus if found, None otherwise
        """
        with self.delivery_lock:
            return self.delivery_status.get(email_id)
    
    def cancel_delivery(self, email_id: str) -> bool:
        """
        Cancel a queued email delivery.
        
        Args:
            email_id: Unique email identifier
            
        Returns:
            True if cancelled successfully, False otherwise
        """
        with self.delivery_lock:
            status = self.delivery_status.get(email_id)
            
            if not status:
                self.logger.warning(f"Cannot cancel email {email_id}: not found")
                return False
            
            if status.status not in [DeliveryStatusType.QUEUED, DeliveryStatusType.PENDING]:
                self.logger.warning(f"Cannot cancel email {email_id}: status is {status.status}")
                return False
            
            # Mark as cancelled (we'll use FAILED status with specific message)
            status.status = DeliveryStatusType.FAILED
            status.last_error = "Cancelled by user"
            status.updated_at = datetime.now()
            
            self.logger.info(f"Email delivery cancelled. ID: {email_id}")
            return True
    
    def get_queue_size(self) -> int:
        """
        Get the current size of the email queue.
        
        Returns:
            Number of emails in queue
        """
        return self.email_queue.qsize()
    
    def get_all_delivery_statuses(self) -> Dict[str, DeliveryStatus]:
        """
        Get all delivery statuses.
        
        Returns:
            Dictionary of email_id -> DeliveryStatus
        """
        with self.delivery_lock:
            return self.delivery_status.copy()
    
    def cleanup_old_statuses(self, max_age_hours: int = 24) -> int:
        """
        Clean up old delivery statuses to prevent memory leaks.
        
        Args:
            max_age_hours: Maximum age in hours for keeping statuses
            
        Returns:
            Number of statuses cleaned up
        """
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        cleaned_count = 0
        
        with self.delivery_lock:
            email_ids_to_remove = []
            
            for email_id, status in self.delivery_status.items():
                if status.updated_at < cutoff_time:
                    email_ids_to_remove.append(email_id)
            
            for email_id in email_ids_to_remove:
                del self.delivery_status[email_id]
                cleaned_count += 1
        
        if cleaned_count > 0:
            self.logger.info(f"Cleaned up {cleaned_count} old delivery statuses")
        
        return cleaned_count
    
    def set_provider(self, email_provider: EmailProvider) -> None:
        """
        Set or update the email provider.
        
        Args:
            email_provider: The email provider to use for sending
        """
        self.email_provider = email_provider
        self.logger.info(f"Email provider updated to: {email_provider.__class__.__name__}")