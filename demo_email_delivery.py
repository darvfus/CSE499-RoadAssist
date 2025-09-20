"""
Demo script for Email Delivery Manager

This script demonstrates the key features of the EmailDeliveryManager:
- Retry logic with exponential backoff
- Email queuing system
- Delivery status tracking
- Comprehensive logging
"""

import time
from datetime import datetime

from email_service.delivery import EmailDeliveryManagerImpl
from email_service.models import EmailData, EmailResult
from email_service.enums import Priority


class DemoEmailProvider:
    """Demo email provider that simulates different scenarios"""
    
    def __init__(self, scenario="success"):
        self.scenario = scenario
        self.call_count = 0
    
    def send_email(self, email_data):
        self.call_count += 1
        print(f"  📧 Provider attempting to send email (attempt {self.call_count})")
        
        if self.scenario == "success":
            return EmailResult(
                success=True,
                message="Email sent successfully",
                email_id=f"demo-{self.call_count}"
            )
        elif self.scenario == "retry_then_success":
            if self.call_count <= 2:
                return EmailResult(
                    success=False,
                    message=f"Temporary failure {self.call_count}",
                    email_id=None
                )
            else:
                return EmailResult(
                    success=True,
                    message="Email sent successfully after retries",
                    email_id=f"demo-{self.call_count}"
                )
        elif self.scenario == "always_fail":
            return EmailResult(
                success=False,
                message="Permanent failure",
                email_id=None
            )
        else:
            raise Exception("Simulated provider exception")


def demo_successful_delivery():
    """Demo successful email delivery"""
    print("\n🟢 Demo 1: Successful Email Delivery")
    print("=" * 50)
    
    provider = DemoEmailProvider("success")
    delivery_manager = EmailDeliveryManagerImpl(provider, max_retries=3)
    
    email_data = EmailData(
        recipient="user@example.com",
        subject="Welcome Email",
        body="Welcome to our service!",
        template_name="welcome_template",
        template_data={"name": "John Doe"},
        priority=Priority.HIGH
    )
    
    result = delivery_manager.send_with_retry(email_data)
    
    print(f"✅ Result: {'Success' if result.success else 'Failed'}")
    print(f"📧 Email ID: {result.email_id}")
    print(f"🔄 Attempts: {result.attempts}")
    print(f"⏱️  Delivery Time: {result.delivery_time:.3f}s")
    
    # Check delivery status
    status = delivery_manager.get_delivery_status(result.email_id)
    print(f"📊 Status: {status.status.name}")


def demo_retry_logic():
    """Demo retry logic with exponential backoff"""
    print("\n🟡 Demo 2: Retry Logic with Exponential Backoff")
    print("=" * 50)
    
    provider = DemoEmailProvider("retry_then_success")
    delivery_manager = EmailDeliveryManagerImpl(provider, max_retries=3)
    
    email_data = EmailData(
        recipient="user@example.com",
        subject="Important Alert",
        body="This is an important alert message",
        template_name="alert_template",
        template_data={"alert_type": "system_warning"},
        priority=Priority.HIGH
    )
    
    print("⏳ Sending email with retry logic...")
    start_time = time.time()
    result = delivery_manager.send_with_retry(email_data)
    total_time = time.time() - start_time
    
    print(f"✅ Result: {'Success' if result.success else 'Failed'}")
    print(f"📧 Email ID: {result.email_id}")
    print(f"🔄 Attempts: {result.attempts}")
    print(f"⏱️  Total Time: {total_time:.3f}s")
    print(f"📊 Final Status: {delivery_manager.get_delivery_status(result.email_id).status.name}")


def demo_failure_scenario():
    """Demo failure after all retry attempts"""
    print("\n🔴 Demo 3: Failure After All Retry Attempts")
    print("=" * 50)
    
    provider = DemoEmailProvider("always_fail")
    delivery_manager = EmailDeliveryManagerImpl(provider, max_retries=3)
    
    email_data = EmailData(
        recipient="user@example.com",
        subject="Test Email",
        body="This email will fail to send",
        template_name="test_template",
        template_data={"test": True},
        priority=Priority.NORMAL
    )
    
    print("⏳ Attempting to send email (will fail)...")
    result = delivery_manager.send_with_retry(email_data)
    
    print(f"❌ Result: {'Success' if result.success else 'Failed'}")
    print(f"📧 Email ID: {result.email_id}")
    print(f"🔄 Attempts: {result.attempts}")
    print(f"❗ Error: {result.error_message}")
    
    status = delivery_manager.get_delivery_status(result.email_id)
    print(f"📊 Status: {status.status.name}")
    print(f"🔍 Last Error: {status.last_error}")


def demo_email_queuing():
    """Demo email queuing system"""
    print("\n🟦 Demo 4: Email Queuing System")
    print("=" * 50)
    
    provider = DemoEmailProvider("success")
    delivery_manager = EmailDeliveryManagerImpl(provider, max_retries=3)
    
    # Queue multiple emails
    email_ids = []
    for i in range(3):
        email_data = EmailData(
            recipient=f"user{i}@example.com",
            subject=f"Queued Email {i+1}",
            body=f"This is queued email number {i+1}",
            template_name="queued_template",
            template_data={"number": i+1},
            priority=Priority.NORMAL
        )
        
        email_id = delivery_manager.queue_email(email_data)
        email_ids.append(email_id)
        print(f"📥 Queued email {i+1} with ID: {email_id}")
    
    print(f"📊 Queue size: {delivery_manager.get_queue_size()}")
    
    # Check status of queued emails
    print("\n📋 Queued email statuses:")
    for email_id in email_ids:
        status = delivery_manager.get_delivery_status(email_id)
        print(f"  📧 {email_id}: {status.status.name}")
    
    # Process the queue
    print("\n⚡ Processing queue...")
    results = delivery_manager.process_queue()
    
    print(f"✅ Processed {len(results)} emails")
    print(f"📊 Queue size after processing: {delivery_manager.get_queue_size()}")
    
    # Check final statuses
    print("\n📋 Final email statuses:")
    for email_id in email_ids:
        status = delivery_manager.get_delivery_status(email_id)
        print(f"  📧 {email_id}: {status.status.name}")


def demo_delivery_tracking():
    """Demo delivery status tracking"""
    print("\n🟣 Demo 5: Delivery Status Tracking")
    print("=" * 50)
    
    provider = DemoEmailProvider("success")
    delivery_manager = EmailDeliveryManagerImpl(provider, max_retries=3)
    
    # Send multiple emails
    email_ids = []
    for i in range(3):
        email_data = EmailData(
            recipient=f"tracking{i}@example.com",
            subject=f"Tracking Test {i+1}",
            body=f"Email for tracking test {i+1}",
            template_name="tracking_template",
            template_data={"test_id": i+1},
            priority=Priority.NORMAL
        )
        
        result = delivery_manager.send_with_retry(email_data)
        email_ids.append(result.email_id)
        print(f"📧 Sent email {i+1} with ID: {result.email_id}")
    
    # Get all delivery statuses
    print("\n📊 All delivery statuses:")
    all_statuses = delivery_manager.get_all_delivery_statuses()
    
    for email_id, status in all_statuses.items():
        if email_id in email_ids:  # Only show our test emails
            print(f"  📧 {email_id}")
            print(f"     Status: {status.status.name}")
            print(f"     Created: {status.created_at.strftime('%H:%M:%S')}")
            print(f"     Updated: {status.updated_at.strftime('%H:%M:%S')}")
            print(f"     Attempts: {status.attempts}")


def demo_cancellation():
    """Demo email delivery cancellation"""
    print("\n🟠 Demo 6: Email Delivery Cancellation")
    print("=" * 50)
    
    provider = DemoEmailProvider("success")
    delivery_manager = EmailDeliveryManagerImpl(provider, max_retries=3)
    
    # Queue an email
    email_data = EmailData(
        recipient="cancel@example.com",
        subject="Email to Cancel",
        body="This email will be cancelled",
        template_name="cancel_template",
        template_data={"action": "cancel"},
        priority=Priority.LOW
    )
    
    email_id = delivery_manager.queue_email(email_data)
    print(f"📥 Queued email with ID: {email_id}")
    
    # Check initial status
    status = delivery_manager.get_delivery_status(email_id)
    print(f"📊 Initial status: {status.status.name}")
    
    # Cancel the email
    cancelled = delivery_manager.cancel_delivery(email_id)
    print(f"🚫 Cancellation {'successful' if cancelled else 'failed'}")
    
    # Check final status
    status = delivery_manager.get_delivery_status(email_id)
    print(f"📊 Final status: {status.status.name}")
    print(f"❗ Last error: {status.last_error}")


def main():
    """Run all demos"""
    print("🚀 Email Delivery Manager Demo")
    print("=" * 50)
    print("This demo showcases the key features of the EmailDeliveryManager:")
    print("• Retry logic with exponential backoff")
    print("• Email queuing for offline scenarios")
    print("• Delivery status tracking with unique IDs")
    print("• Comprehensive logging")
    print("• Email delivery cancellation")
    
    try:
        demo_successful_delivery()
        demo_retry_logic()
        demo_failure_scenario()
        demo_email_queuing()
        demo_delivery_tracking()
        demo_cancellation()
        
        print("\n🎉 All demos completed successfully!")
        print("\nKey Features Demonstrated:")
        print("✅ Successful email delivery")
        print("✅ Retry logic with exponential backoff")
        print("✅ Failure handling after max retries")
        print("✅ Email queuing and batch processing")
        print("✅ Delivery status tracking")
        print("✅ Email delivery cancellation")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {str(e)}")
        raise


if __name__ == "__main__":
    main()