"""
Email Service Manager - Main orchestrator for email functionality
"""

import logging
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime

from .interfaces import EmailServiceManager, EmailProvider, EmailErrorHandler
from .models import (
    EmailConfig, EmailData, EmailResult, TestResult, UserData, AlertData,
    EmailContent, ErrorResponse
)
from .enums import ProviderType, AlertType, ErrorType
from .providers import EmailProviderFactory
from .package_manager import EmailPackageManagerImpl
from .templates import EmailTemplateEngineImpl
from .delivery import EmailDeliveryManagerImpl
from .error_handler import EmailErrorHandlerImpl


class EmailServiceManagerImpl(EmailServiceManager):
    """
    Main email service orchestrator that coordinates all email functionality.
    
    This class manages:
    - Package installation and validation
    - Email provider configuration and creation
    - Template rendering and email composition
    - Email delivery with retry logic
    - Error handling and troubleshooting
    """
    
    def __init__(self):
        """Initialize the email service manager"""
        self.config: Optional[EmailConfig] = None
        self.provider: Optional[EmailProvider] = None
        self.fallback_providers: List[EmailProvider] = []
        self.package_manager = EmailPackageManagerImpl()
        self.template_engine = EmailTemplateEngineImpl()
        self.delivery_manager = EmailDeliveryManagerImpl()
        self.error_handler = EmailErrorHandlerImpl()
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def initialize(self, config: EmailConfig) -> bool:
        """
        Initialize the email service with configuration.
        
        This method:
        1. Validates and installs required packages
        2. Creates and configures the email provider
        3. Initializes template engine and delivery manager
        4. Performs initial connection test
        
        Args:
            config: Email configuration settings
            
        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            self.logger.info("Initializing email service...")
            
            # Step 1: Check and install required packages
            self.logger.info("Checking required packages...")
            package_status = self.package_manager.get_installation_status()
            
            if not package_status.all_installed:
                self.logger.info("Installing missing packages...")
                install_results = self.package_manager.install_missing_packages()
                
                failed_packages = [pkg for pkg, success in install_results.items() if not success]
                if failed_packages:
                    self.logger.error(f"Failed to install packages: {failed_packages}")
                    return False
                
                # Re-check package status after installation
                updated_status = self.package_manager.get_installation_status()
                if not updated_status.all_installed:
                    self.logger.error("Package installation verification failed")
                    return False
                
                self.logger.info("All required packages installed successfully")
            
            # Step 2: Validate configuration
            self.logger.info("Validating email configuration...")
            if not self._validate_config(config):
                self.logger.error("Configuration validation failed")
                return False
            
            # Step 3: Create and configure email provider
            self.logger.info(f"Creating {config.provider.value} email provider...")
            try:
                self.provider = EmailProviderFactory.create_provider(config.provider)
                if not self.provider.configure(config):
                    self.logger.error("Failed to configure email provider")
                    return False
            except Exception as e:
                self.logger.error(f"Failed to create email provider: {e}")
                return False
            
            # Step 4: Initialize template engine
            self.logger.info("Loading email templates...")
            try:
                templates = self.template_engine.load_templates()
                self.logger.info(f"Loaded {len(templates)} email templates")
            except Exception as e:
                self.logger.warning(f"Failed to load templates: {e}")
                # Continue without templates - use default content
            
            # Step 5: Initialize delivery manager with provider
            self.logger.info("Initializing delivery manager...")
            self.delivery_manager.set_provider(self.provider)
            
            # Step 6: Store configuration
            self.config = config
            
            # Step 7: Test connection (optional but recommended)
            self.logger.info("Testing email configuration...")
            test_result = self.test_email_configuration()
            if not test_result.success:
                self.logger.warning("Email configuration test failed, but service is initialized")
                self.logger.warning(f"Test errors: {test_result.error_messages}")
            else:
                self.logger.info("Email service initialized and tested successfully")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize email service: {e}")
            error_response = self.error_handler.handle_config_error(e)
            self.logger.error(f"Error details: {error_response.details}")
            return False
    
    def send_alert_email(self, user_data: UserData, alert_data: AlertData) -> EmailResult:
        """
        Send an alert email to the user.
        
        This method:
        1. Validates that service is initialized
        2. Renders appropriate email template
        3. Composes email data
        4. Sends email through delivery manager
        
        Args:
            user_data: User information for personalization
            alert_data: Alert details for email content
            
        Returns:
            EmailResult: Result of email sending operation
        """
        try:
            # Validate service is initialized
            if not self.config or not self.provider:
                return EmailResult(
                    success=False,
                    message="Email service not initialized",
                    details={"error": "Service must be initialized before sending emails"}
                )
            
            self.logger.info(f"Sending {alert_data.alert_type.value} alert email to {user_data.email}")
            
            # Step 1: Determine template name based on alert type
            template_name = self._get_template_name(alert_data.alert_type)
            
            # Step 2: Prepare template data
            template_data = self._prepare_template_data(user_data, alert_data)
            
            # Step 3: Render email content
            try:
                email_content = self.template_engine.render_template(template_name, template_data)
            except Exception as e:
                self.logger.warning(f"Failed to render template {template_name}: {e}")
                # Fallback to default content
                email_content = self._create_default_email_content(user_data, alert_data)
            
            # Step 4: Create email data
            email_data = EmailData(
                recipient=user_data.email,
                subject=email_content.subject,
                body=email_content.body,
                html_body=email_content.html_body,
                template_name=template_name,
                template_data=template_data,
                priority=self._get_email_priority(alert_data.alert_type)
            )
            
            # Step 5: Send email with fallback support
            email_result = self.send_with_fallback(email_data)
            
            # Convert email result to delivery result format for compatibility
            if email_result.success:
                delivery_result = type('DeliveryResult', (), {
                    'success': True,
                    'email_id': email_result.email_id or str(uuid.uuid4()),
                    'delivery_time': 0.0,
                    'attempts': 1,
                    'error_message': None
                })()
            else:
                delivery_result = type('DeliveryResult', (), {
                    'success': False,
                    'email_id': email_result.email_id or str(uuid.uuid4()),
                    'delivery_time': 0.0,
                    'attempts': 1,
                    'error_message': email_result.message
                })()
            
            # If direct send failed, try through delivery manager with retry logic
            if not delivery_result.success and self.provider:
                self.logger.info("Trying email delivery through delivery manager with retry logic")
                delivery_result = self.delivery_manager.send_with_retry(email_data)
            
            # Step 6: Convert delivery result to email result
            if delivery_result.success:
                self.logger.info(f"Alert email sent successfully to {user_data.email}")
                return EmailResult(
                    success=True,
                    message="Alert email sent successfully",
                    email_id=delivery_result.email_id,
                    details={
                        "recipient": user_data.email,
                        "alert_type": alert_data.alert_type.value,
                        "template": template_name,
                        "delivery_time": delivery_result.delivery_time,
                        "attempts": delivery_result.attempts
                    }
                )
            else:
                self.logger.error(f"Failed to send alert email: {delivery_result.error_message}")
                return EmailResult(
                    success=False,
                    message="Failed to send alert email",
                    email_id=delivery_result.email_id,
                    details={
                        "error": delivery_result.error_message,
                        "attempts": delivery_result.attempts,
                        "alert_type": alert_data.alert_type.value
                    }
                )
                
        except Exception as e:
            self.logger.error(f"Unexpected error sending alert email: {e}")
            error_response = self.error_handler.handle_delivery_error(e)
            return EmailResult(
                success=False,
                message="Unexpected error sending alert email",
                details={
                    "error": str(e),
                    "error_type": error_response.error_type.name,
                    "troubleshooting": error_response.troubleshooting_steps
                }
            )
    
    def test_email_configuration(self) -> TestResult:
        """
        Test the current email configuration.
        
        This method performs comprehensive testing:
        1. Connection test to SMTP server
        2. Authentication test with credentials
        3. Optional test email sending
        
        Returns:
            TestResult: Detailed test results
        """
        if not self.config or not self.provider:
            return TestResult(
                success=False,
                provider="None",
                connection_test=False,
                auth_test=False,
                send_test=False,
                error_messages=["Email service not initialized"]
            )
        
        start_time = datetime.now()
        test_result = TestResult(
            success=False,
            provider=self.config.provider.value,
            connection_test=False,
            auth_test=False,
            send_test=False,
            error_messages=[]
        )
        
        try:
            self.logger.info("Testing email configuration...")
            
            # Test 1: Connection test
            self.logger.info("Testing SMTP connection...")
            try:
                test_result.connection_test = self.provider.test_connection()
                if test_result.connection_test:
                    self.logger.info("SMTP connection test passed")
                else:
                    test_result.error_messages.append("SMTP connection test failed")
                    self.logger.error("SMTP connection test failed")
            except Exception as e:
                test_result.error_messages.append(f"Connection test error: {str(e)}")
                self.logger.error(f"Connection test error: {e}")
            
            # Test 2: Authentication test (already included in connection test)
            test_result.auth_test = test_result.connection_test
            
            # Test 3: Send test email (optional)
            if test_result.connection_test:
                self.logger.info("Sending test email...")
                try:
                    test_email_data = self._create_test_email_data()
                    send_result = self.provider.send_email(test_email_data)
                    test_result.send_test = send_result.success
                    
                    if send_result.success:
                        self.logger.info("Test email sent successfully")
                    else:
                        test_result.error_messages.append(f"Test email failed: {send_result.message}")
                        self.logger.error(f"Test email failed: {send_result.message}")
                        
                except Exception as e:
                    test_result.error_messages.append(f"Test email error: {str(e)}")
                    self.logger.error(f"Test email error: {e}")
            
            # Overall success
            test_result.success = (
                test_result.connection_test and 
                test_result.auth_test and 
                test_result.send_test
            )
            
            # Calculate test duration
            end_time = datetime.now()
            test_result.test_duration = (end_time - start_time).total_seconds()
            
            if test_result.success:
                self.logger.info("Email configuration test completed successfully")
            else:
                self.logger.warning("Email configuration test completed with issues")
            
            return test_result
            
        except Exception as e:
            self.logger.error(f"Email configuration test failed: {e}")
            test_result.error_messages.append(f"Test failed: {str(e)}")
            test_result.test_duration = (datetime.now() - start_time).total_seconds()
            return test_result
    
    def update_configuration(self, new_config: EmailConfig) -> bool:
        """
        Update email service configuration.
        
        Args:
            new_config: New email configuration
            
        Returns:
            bool: True if update successful, False otherwise
        """
        try:
            self.logger.info("Updating email configuration...")
            
            # Validate new configuration
            if not self._validate_config(new_config):
                self.logger.error("New configuration validation failed")
                return False
            
            # Create new provider if provider type changed
            if not self.config or self.config.provider != new_config.provider:
                self.logger.info(f"Creating new {new_config.provider.value} provider...")
                try:
                    new_provider = EmailProviderFactory.create_provider(new_config.provider)
                    if not new_provider.configure(new_config):
                        self.logger.error("Failed to configure new provider")
                        return False
                    self.provider = new_provider
                except Exception as e:
                    self.logger.error(f"Failed to create new provider: {e}")
                    return False
            else:
                # Reconfigure existing provider
                if not self.provider.configure(new_config):
                    self.logger.error("Failed to reconfigure existing provider")
                    return False
            
            # Update delivery manager with new provider
            self.delivery_manager.set_provider(self.provider)
            
            # Store new configuration
            self.config = new_config
            
            self.logger.info("Email configuration updated successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update configuration: {e}")
            return False
    
    def get_supported_providers(self) -> List[str]:
        """
        Get list of supported email providers.
        
        Returns:
            List[str]: List of supported provider names
        """
        return [provider.value for provider in EmailProviderFactory.get_supported_providers()]
    
    def configure_fallback_providers(self, fallback_configs: List[EmailConfig]) -> bool:
        """
        Configure fallback email providers for redundancy.
        
        Args:
            fallback_configs: List of fallback email configurations
            
        Returns:
            bool: True if fallback providers configured successfully
        """
        try:
            self.fallback_providers = []
            
            for i, config in enumerate(fallback_configs):
                self.logger.info(f"Configuring fallback provider {i+1}: {config.provider.value}")
                
                try:
                    provider = EmailProviderFactory.create_provider(config.provider)
                    if provider.configure(config):
                        self.fallback_providers.append(provider)
                        self.logger.info(f"Fallback provider {i+1} configured successfully")
                    else:
                        self.logger.warning(f"Failed to configure fallback provider {i+1}")
                except Exception as e:
                    self.logger.warning(f"Error configuring fallback provider {i+1}: {e}")
            
            self.logger.info(f"Configured {len(self.fallback_providers)} fallback providers")
            return len(self.fallback_providers) > 0
            
        except Exception as e:
            self.logger.error(f"Failed to configure fallback providers: {e}")
            return False
    
    def send_with_fallback(self, email_data: EmailData) -> EmailResult:
        """
        Send email with fallback provider support.
        
        Args:
            email_data: Email data to send
            
        Returns:
            EmailResult: Result of email sending operation
        """
        # Try primary provider first
        if self.provider:
            try:
                self.logger.info("Attempting to send email with primary provider")
                result = self.provider.send_email(email_data)
                
                if result.success:
                    self.logger.info("Email sent successfully with primary provider")
                    return result
                else:
                    self.logger.warning(f"Primary provider failed: {result.message}")
                    
            except Exception as e:
                self.logger.error(f"Primary provider error: {e}")
        
        # Try fallback providers
        for i, fallback_provider in enumerate(self.fallback_providers):
            try:
                self.logger.info(f"Attempting to send email with fallback provider {i+1}")
                result = fallback_provider.send_email(email_data)
                
                if result.success:
                    self.logger.info(f"Email sent successfully with fallback provider {i+1}")
                    # Add fallback info to result
                    result.details["fallback_used"] = True
                    result.details["fallback_provider"] = i + 1
                    return result
                else:
                    self.logger.warning(f"Fallback provider {i+1} failed: {result.message}")
                    
            except Exception as e:
                self.logger.error(f"Fallback provider {i+1} error: {e}")
        
        # All providers failed
        self.logger.error("All email providers failed")
        return EmailResult(
            success=False,
            message="All email providers failed",
            details={
                "primary_provider_available": self.provider is not None,
                "fallback_providers_count": len(self.fallback_providers),
                "error": "No working email provider available"
            }
        )
    
    def get_service_status(self) -> Dict[str, Any]:
        """
        Get current service status and information.
        
        Returns:
            Dict[str, Any]: Service status information
        """
        package_status = self.package_manager.get_installation_status()
        
        return {
            "initialized": self.config is not None and self.provider is not None,
            "provider": self.config.provider.value if self.config else None,
            "fallback_providers_count": len(self.fallback_providers),
            "packages_installed": package_status.all_installed,
            "templates_loaded": len(self.template_engine.load_templates()) > 0,
            "supported_providers": self.get_supported_providers(),
            "service_version": "1.0.0"
        }
    
    # Private helper methods
    
    def _validate_config(self, config: EmailConfig) -> bool:
        """Validate email configuration"""
        try:
            # Basic validation is done in EmailConfig.__post_init__
            # Additional validation can be added here
            return True
        except Exception as e:
            self.logger.error(f"Configuration validation error: {e}")
            return False
    
    def _get_template_name(self, alert_type: AlertType) -> str:
        """Get template name for alert type"""
        template_mapping = {
            AlertType.DROWSINESS: "drowsiness_alert",
            AlertType.VITAL_SIGNS: "vital_signs_alert",
            AlertType.SYSTEM_ERROR: "system_error",
            AlertType.TEST_EMAIL: "system_test"
        }
        return template_mapping.get(alert_type, "drowsiness_alert")
    
    def _prepare_template_data(self, user_data: UserData, alert_data: AlertData) -> Dict[str, Any]:
        """Prepare data for template rendering"""
        return {
            "user_name": user_data.name,
            "user_email": user_data.email,
            "alert_type": alert_data.alert_type.value,
            "timestamp": alert_data.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "heart_rate": alert_data.heart_rate,
            "oxygen_saturation": alert_data.oxygen_saturation,
            "additional_data": alert_data.additional_data
        }
    
    def _create_default_email_content(self, user_data: UserData, alert_data: AlertData) -> EmailContent:
        """Create default email content when template rendering fails"""
        if alert_data.alert_type == AlertType.DROWSINESS:
            subject = "Driver Drowsiness Alert"
            body = f"""
Dear {user_data.name},

This is an automated alert from your Driver Drowsiness Detection System.

Alert Details:
- Type: Drowsiness Detection
- Time: {alert_data.timestamp.strftime("%Y-%m-%d %H:%M:%S")}
- User: {user_data.name}
"""
            if alert_data.heart_rate:
                body += f"- Heart Rate: {alert_data.heart_rate} BPM\n"
            if alert_data.oxygen_saturation:
                body += f"- Oxygen Saturation: {alert_data.oxygen_saturation}%\n"
            
            body += """
Please take immediate action to ensure your safety:
1. Pull over safely if possible
2. Take a break and rest
3. Consider switching drivers if available

Stay safe!

Driver Assistant System
"""
        else:
            subject = f"Driver Assistant Alert - {alert_data.alert_type.value.replace('_', ' ').title()}"
            body = f"""
Dear {user_data.name},

This is an automated alert from your Driver Assistant System.

Alert Type: {alert_data.alert_type.value.title()}
Time: {alert_data.timestamp.strftime("%Y-%m-%d %H:%M:%S")}

Please check your system for more details.

Driver Assistant System
"""
        
        return EmailContent(subject=subject, body=body)
    
    def _get_email_priority(self, alert_type: AlertType):
        """Get email priority based on alert type"""
        from .enums import Priority
        
        priority_mapping = {
            AlertType.DROWSINESS: Priority.HIGH,
            AlertType.VITAL_SIGNS: Priority.HIGH,
            AlertType.SYSTEM_ERROR: Priority.NORMAL,
            AlertType.TEST_EMAIL: Priority.LOW
        }
        return priority_mapping.get(alert_type, Priority.NORMAL)
    
    def _create_test_email_data(self) -> EmailData:
        """Create test email data"""
        from .enums import Priority
        
        return EmailData(
            recipient=self.config.sender_email,  # Send test email to sender
            subject="Email Configuration Test",
            body="This is a test email to verify your email configuration is working correctly.",
            template_name="system_test",
            template_data={"test_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
            priority=Priority.LOW
        )