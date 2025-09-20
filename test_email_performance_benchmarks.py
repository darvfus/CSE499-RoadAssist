"""
Performance Benchmarks for Email Service

This module provides comprehensive performance testing and benchmarking
for all email service operations including sending, template rendering,
configuration validation, and provider switching.
"""

import unittest
import time
import threading
import statistics
import psutil
import os
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from typing import List, Dict, Any

from email_service.testing_utils import (
    EmailTestingUtils, MockEmailProvider, create_test_config,
    create_test_email_data, create_test_user_data, create_test_alert_data
)
from email_service.service_manager import EmailServiceManagerImpl
from email_service.delivery import EmailDeliveryManagerImpl
from email_service.templates import EmailTemplateEngineImpl
from email_service.package_manager import EmailPackageManagerImpl
from email_service.providers import EmailProviderFactory
from email_service.models import EmailConfig, EmailData, UserData, AlertData
from email_service.enums import ProviderType, AuthMethod, AlertType, Priority


class PerformanceBenchmark:
    """Base class for performance benchmarks"""
    
    def __init__(self, name: str):
        self.name = name
        self.results = []
        self.start_time = None
        self.end_time = None
        self.memory_start = None
        self.memory_end = None
    
    def start_measurement(self):
        """Start performance measurement"""
        self.start_time = time.perf_counter()
        process = psutil.Process(os.getpid())
        self.memory_start = process.memory_info().rss / 1024 / 1024  # MB
    
    def end_measurement(self):
        """End performance measurement"""
        self.end_time = time.perf_counter()
        process = psutil.Process(os.getpid())
        self.memory_end = process.memory_info().rss / 1024 / 1024  # MB
    
    def get_duration(self) -> float:
        """Get measurement duration in seconds"""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0.0
    
    def get_memory_usage(self) -> float:
        """Get memory usage increase in MB"""
        if self.memory_start and self.memory_end:
            return self.memory_end - self.memory_start
        return 0.0
    
    def add_result(self, duration: float, success: bool = True, **kwargs):
        """Add a benchmark result"""
        self.results.append({
            'duration': duration,
            'success': success,
            'timestamp': datetime.now(),
            **kwargs
        })
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get performance statistics"""
        if not self.results:
            return {}
        
        durations = [r['duration'] for r in self.results if r['success']]
        success_count = sum(1 for r in self.results if r['success'])
        
        if not durations:
            return {'success_rate': 0.0}
        
        return {
            'total_operations': len(self.results),
            'successful_operations': success_count,
            'success_rate': success_count / len(self.results) * 100,
            'avg_duration': statistics.mean(durations),
            'min_duration': min(durations),
            'max_duration': max(durations),
            'median_duration': statistics.median(durations),
            'std_deviation': statistics.stdev(durations) if len(durations) > 1 else 0.0,
            'operations_per_second': success_count / sum(durations) if sum(durations) > 0 else 0.0
        }


class EmailSendingBenchmark(unittest.TestCase):
    """Benchmark email sending performance"""
    
    def setUp(self):
        """Set up benchmark environment"""
        self.service_manager = EmailServiceManagerImpl()
        self.benchmark = PerformanceBenchmark("Email Sending")
        self.mock_provider = MockEmailProvider()
        
        # Configure service with mock provider
        config = create_test_config(ProviderType.GMAIL)
        
        with patch('email_service.providers.EmailProviderFactory.create_provider') as mock_create:
            mock_create.return_value = self.mock_provider
            self.service_manager.initialize(config)
    
    def test_single_email_sending_performance(self):
        """Benchmark single email sending performance"""
        print("\n--- Single Email Sending Performance ---")
        
        user_data = create_test_user_data()
        alert_data = create_test_alert_data()
        
        # Warm up
        for _ in range(5):
            self.service_manager.send_alert_email(user_data, alert_data)
        
        # Benchmark
        num_tests = 100
        self.benchmark.start_measurement()
        
        for i in range(num_tests):
            start_time = time.perf_counter()
            result = self.service_manager.send_alert_email(user_data, alert_data)
            end_time = time.perf_counter()
            
            self.benchmark.add_result(
                duration=end_time - start_time,
                success=result.success,
                email_id=result.email_id
            )
        
        self.benchmark.end_measurement()
        
        # Analyze results
        stats = self.benchmark.get_statistics()
        total_time = self.benchmark.get_duration()
        memory_usage = self.benchmark.get_memory_usage()
        
        print(f"Total operations: {stats['total_operations']}")
        print(f"Success rate: {stats['success_rate']:.1f}%")
        print(f"Average duration: {stats['avg_duration']*1000:.2f}ms")
        print(f"Min duration: {stats['min_duration']*1000:.2f}ms")
        print(f"Max duration: {stats['max_duration']*1000:.2f}ms")
        print(f"Operations per second: {stats['operations_per_second']:.1f}")
        print(f"Total time: {total_time:.2f}s")
        print(f"Memory usage: {memory_usage:.2f}MB")
        
        # Performance assertions
        self.assertGreater(stats['success_rate'], 95.0)
        self.assertLess(stats['avg_duration'], 0.1)  # Less than 100ms average
        self.assertGreater(stats['operations_per_second'], 10)  # At least 10 ops/sec
        self.assertLess(memory_usage, 10)  # Less than 10MB memory increase
    
    def test_bulk_email_sending_performance(self):
        """Benchmark bulk email sending performance"""
        print("\n--- Bulk Email Sending Performance ---")
        
        num_emails = 500
        users = [create_test_user_data() for _ in range(num_emails)]
        alert_data = create_test_alert_data()
        
        self.benchmark.start_measurement()
        
        successful_sends = 0
        for i, user in enumerate(users):
            user.email = f"bulk_test_{i}@example.com"
            
            start_time = time.perf_counter()
            result = self.service_manager.send_alert_email(user, alert_data)
            end_time = time.perf_counter()
            
            if result.success:
                successful_sends += 1
            
            self.benchmark.add_result(
                duration=end_time - start_time,
                success=result.success
            )
        
        self.benchmark.end_measurement()
        
        # Analyze results
        stats = self.benchmark.get_statistics()
        total_time = self.benchmark.get_duration()
        memory_usage = self.benchmark.get_memory_usage()
        
        print(f"Bulk emails sent: {num_emails}")
        print(f"Successful sends: {successful_sends}")
        print(f"Success rate: {stats['success_rate']:.1f}%")
        print(f"Total time: {total_time:.2f}s")
        print(f"Emails per second: {successful_sends/total_time:.1f}")
        print(f"Average per email: {stats['avg_duration']*1000:.2f}ms")
        print(f"Memory usage: {memory_usage:.2f}MB")
        
        # Performance assertions
        self.assertGreater(stats['success_rate'], 95.0)
        self.assertGreater(successful_sends/total_time, 50)  # At least 50 emails/sec
        self.assertLess(memory_usage, 50)  # Less than 50MB for bulk operation
    
    def test_concurrent_email_sending_performance(self):
        """Benchmark concurrent email sending performance"""
        print("\n--- Concurrent Email Sending Performance ---")
        
        num_threads = 10
        emails_per_thread = 20
        results = []
        errors = []
        
        def send_emails_worker(thread_id: int):
            """Worker function for concurrent email sending"""
            thread_results = []
            for i in range(emails_per_thread):
                user = create_test_user_data()
                user.email = f"concurrent_{thread_id}_{i}@example.com"
                alert = create_test_alert_data()
                
                start_time = time.perf_counter()
                try:
                    result = self.service_manager.send_alert_email(user, alert)
                    end_time = time.perf_counter()
                    
                    thread_results.append({
                        'duration': end_time - start_time,
                        'success': result.success,
                        'thread_id': thread_id,
                        'email_index': i
                    })
                except Exception as e:
                    errors.append(f"Thread {thread_id}, Email {i}: {str(e)}")
            
            results.extend(thread_results)
        
        # Start concurrent sending
        self.benchmark.start_measurement()
        
        threads = []
        for thread_id in range(num_threads):
            thread = threading.Thread(target=send_emails_worker, args=(thread_id,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        self.benchmark.end_measurement()
        
        # Analyze results
        total_emails = num_threads * emails_per_thread
        successful_emails = sum(1 for r in results if r['success'])
        total_time = self.benchmark.get_duration()
        avg_duration = statistics.mean([r['duration'] for r in results if r['success']])
        
        print(f"Concurrent threads: {num_threads}")
        print(f"Emails per thread: {emails_per_thread}")
        print(f"Total emails: {total_emails}")
        print(f"Successful emails: {successful_emails}")
        print(f"Success rate: {successful_emails/total_emails*100:.1f}%")
        print(f"Total time: {total_time:.2f}s")
        print(f"Emails per second: {successful_emails/total_time:.1f}")
        print(f"Average per email: {avg_duration*1000:.2f}ms")
        print(f"Errors: {len(errors)}")
        
        # Performance assertions
        self.assertGreater(successful_emails/total_emails, 0.95)  # 95% success rate
        self.assertGreater(successful_emails/total_time, 80)  # At least 80 emails/sec
        self.assertLess(len(errors), total_emails * 0.05)  # Less than 5% errors


class TemplateRenderingBenchmark(unittest.TestCase):
    """Benchmark template rendering performance"""
    
    def setUp(self):
        """Set up benchmark environment"""
        self.template_engine = EmailTemplateEngineImpl()
        self.benchmark = PerformanceBenchmark("Template Rendering")
        
        # Load templates
        self.template_engine.load_templates()
    
    def test_template_rendering_performance(self):
        """Benchmark template rendering performance"""
        print("\n--- Template Rendering Performance ---")
        
        template_name = "drowsiness_alert"
        template_data = {
            "user_name": "Performance Test User",
            "timestamp": datetime.now().isoformat(),
            "heart_rate": 75,
            "oxygen_saturation": 98.5,
            "alert_type": "Drowsiness",
            "system_name": "Driver Assistant"
        }
        
        # Warm up
        for _ in range(10):
            self.template_engine.render_template(template_name, template_data)
        
        # Benchmark
        num_renders = 1000
        self.benchmark.start_measurement()
        
        for i in range(num_renders):
            start_time = time.perf_counter()
            try:
                content = self.template_engine.render_template(template_name, template_data)
                end_time = time.perf_counter()
                
                self.benchmark.add_result(
                    duration=end_time - start_time,
                    success=content is not None,
                    subject_length=len(content.subject) if content else 0,
                    body_length=len(content.body) if content else 0
                )
            except Exception as e:
                end_time = time.perf_counter()
                self.benchmark.add_result(
                    duration=end_time - start_time,
                    success=False,
                    error=str(e)
                )
        
        self.benchmark.end_measurement()
        
        # Analyze results
        stats = self.benchmark.get_statistics()
        total_time = self.benchmark.get_duration()
        memory_usage = self.benchmark.get_memory_usage()
        
        print(f"Template renders: {num_renders}")
        print(f"Success rate: {stats['success_rate']:.1f}%")
        print(f"Average duration: {stats['avg_duration']*1000:.3f}ms")
        print(f"Min duration: {stats['min_duration']*1000:.3f}ms")
        print(f"Max duration: {stats['max_duration']*1000:.3f}ms")
        print(f"Renders per second: {stats['operations_per_second']:.1f}")
        print(f"Total time: {total_time:.2f}s")
        print(f"Memory usage: {memory_usage:.2f}MB")
        
        # Performance assertions
        self.assertGreater(stats['success_rate'], 99.0)
        self.assertLess(stats['avg_duration'], 0.01)  # Less than 10ms average
        self.assertGreater(stats['operations_per_second'], 100)  # At least 100 renders/sec
        self.assertLess(memory_usage, 5)  # Less than 5MB memory increase
    
    def test_template_loading_performance(self):
        """Benchmark template loading performance"""
        print("\n--- Template Loading Performance ---")
        
        num_loads = 50
        self.benchmark.start_measurement()
        
        for i in range(num_loads):
            # Create new template engine instance
            engine = EmailTemplateEngineImpl()
            
            start_time = time.perf_counter()
            try:
                templates = engine.load_templates()
                end_time = time.perf_counter()
                
                self.benchmark.add_result(
                    duration=end_time - start_time,
                    success=len(templates) > 0,
                    template_count=len(templates)
                )
            except Exception as e:
                end_time = time.perf_counter()
                self.benchmark.add_result(
                    duration=end_time - start_time,
                    success=False,
                    error=str(e)
                )
        
        self.benchmark.end_measurement()
        
        # Analyze results
        stats = self.benchmark.get_statistics()
        total_time = self.benchmark.get_duration()
        
        print(f"Template loads: {num_loads}")
        print(f"Success rate: {stats['success_rate']:.1f}%")
        print(f"Average duration: {stats['avg_duration']*1000:.2f}ms")
        print(f"Loads per second: {stats['operations_per_second']:.1f}")
        print(f"Total time: {total_time:.2f}s")
        
        # Performance assertions
        self.assertGreater(stats['success_rate'], 95.0)
        self.assertLess(stats['avg_duration'], 0.5)  # Less than 500ms average
        self.assertGreater(stats['operations_per_second'], 2)  # At least 2 loads/sec


class ConfigurationBenchmark(unittest.TestCase):
    """Benchmark configuration operations performance"""
    
    def setUp(self):
        """Set up benchmark environment"""
        self.service_manager = EmailServiceManagerImpl()
        self.benchmark = PerformanceBenchmark("Configuration")
        self.testing_utils = EmailTestingUtils()
    
    def test_configuration_validation_performance(self):
        """Benchmark configuration validation performance"""
        print("\n--- Configuration Validation Performance ---")
        
        # Create test configurations
        configs = []
        providers = [ProviderType.GMAIL, ProviderType.OUTLOOK, ProviderType.YAHOO, ProviderType.CUSTOM]
        
        for i in range(100):
            provider = providers[i % len(providers)]
            config = create_test_config(provider)
            config.sender_email = f"test{i}@{provider.value}.com"
            configs.append(config)
        
        # Benchmark validation
        self.benchmark.start_measurement()
        
        for i, config in enumerate(configs):
            start_time = time.perf_counter()
            try:
                result = self.testing_utils.validate_email_config(config)
                end_time = time.perf_counter()
                
                self.benchmark.add_result(
                    duration=end_time - start_time,
                    success=result.valid,
                    provider=config.provider.value,
                    error_count=len(result.errors)
                )
            except Exception as e:
                end_time = time.perf_counter()
                self.benchmark.add_result(
                    duration=end_time - start_time,
                    success=False,
                    error=str(e)
                )
        
        self.benchmark.end_measurement()
        
        # Analyze results
        stats = self.benchmark.get_statistics()
        total_time = self.benchmark.get_duration()
        
        print(f"Configurations validated: {len(configs)}")
        print(f"Success rate: {stats['success_rate']:.1f}%")
        print(f"Average duration: {stats['avg_duration']*1000:.2f}ms")
        print(f"Validations per second: {stats['operations_per_second']:.1f}")
        print(f"Total time: {total_time:.2f}s")
        
        # Performance assertions
        self.assertGreater(stats['success_rate'], 90.0)
        self.assertLess(stats['avg_duration'], 0.05)  # Less than 50ms average
        self.assertGreater(stats['operations_per_second'], 20)  # At least 20 validations/sec
    
    def test_provider_switching_performance(self):
        """Benchmark provider switching performance"""
        print("\n--- Provider Switching Performance ---")
        
        providers = [ProviderType.GMAIL, ProviderType.OUTLOOK, ProviderType.YAHOO]
        num_switches = 30
        
        self.benchmark.start_measurement()
        
        for i in range(num_switches):
            provider = providers[i % len(providers)]
            config = create_test_config(provider)
            
            with patch('email_service.providers.EmailProviderFactory.create_provider') as mock_create:
                mock_provider = MockEmailProvider()
                mock_create.return_value = mock_provider
                
                start_time = time.perf_counter()
                try:
                    result = self.service_manager.initialize(config)
                    end_time = time.perf_counter()
                    
                    self.benchmark.add_result(
                        duration=end_time - start_time,
                        success=result,
                        provider=provider.value
                    )
                except Exception as e:
                    end_time = time.perf_counter()
                    self.benchmark.add_result(
                        duration=end_time - start_time,
                        success=False,
                        error=str(e)
                    )
        
        self.benchmark.end_measurement()
        
        # Analyze results
        stats = self.benchmark.get_statistics()
        total_time = self.benchmark.get_duration()
        
        print(f"Provider switches: {num_switches}")
        print(f"Success rate: {stats['success_rate']:.1f}%")
        print(f"Average duration: {stats['avg_duration']*1000:.2f}ms")
        print(f"Switches per second: {stats['operations_per_second']:.1f}")
        print(f"Total time: {total_time:.2f}s")
        
        # Performance assertions
        self.assertGreater(stats['success_rate'], 95.0)
        self.assertLess(stats['avg_duration'], 1.0)  # Less than 1 second average
        self.assertGreater(stats['operations_per_second'], 1)  # At least 1 switch/sec


class DeliveryManagerBenchmark(unittest.TestCase):
    """Benchmark delivery manager performance"""
    
    def setUp(self):
        """Set up benchmark environment"""
        self.delivery_manager = EmailDeliveryManagerImpl()
        self.benchmark = PerformanceBenchmark("Delivery Manager")
        self.mock_provider = MockEmailProvider()
        
        # Set provider
        self.delivery_manager.set_provider(self.mock_provider)
    
    def test_retry_mechanism_performance(self):
        """Benchmark retry mechanism performance"""
        print("\n--- Retry Mechanism Performance ---")
        
        # Create failing provider that succeeds on 3rd attempt
        class RetryTestProvider(MockEmailProvider):
            def __init__(self):
                super().__init__()
                self.attempt_counts = {}
            
            def send_email(self, email_data):
                email_key = email_data.recipient
                self.attempt_counts[email_key] = self.attempt_counts.get(email_key, 0) + 1
                
                if self.attempt_counts[email_key] < 3:
                    from email_service.models import EmailResult
                    return EmailResult(
                        success=False,
                        message=f"Mock failure attempt {self.attempt_counts[email_key]}",
                        email_id=None
                    )
                return super().send_email(email_data)
        
        retry_provider = RetryTestProvider()
        self.delivery_manager.set_provider(retry_provider)
        
        num_emails = 50
        self.benchmark.start_measurement()
        
        for i in range(num_emails):
            email_data = create_test_email_data(f"retry_test_{i}@example.com")
            
            start_time = time.perf_counter()
            try:
                result = self.delivery_manager.send_with_retry(email_data)
                end_time = time.perf_counter()
                
                self.benchmark.add_result(
                    duration=end_time - start_time,
                    success=result.success,
                    attempts=result.attempts,
                    email_id=result.email_id
                )
            except Exception as e:
                end_time = time.perf_counter()
                self.benchmark.add_result(
                    duration=end_time - start_time,
                    success=False,
                    error=str(e)
                )
        
        self.benchmark.end_measurement()
        
        # Analyze results
        stats = self.benchmark.get_statistics()
        total_time = self.benchmark.get_duration()
        avg_attempts = statistics.mean([r.get('attempts', 0) for r in self.benchmark.results if r['success']])
        
        print(f"Emails with retry: {num_emails}")
        print(f"Success rate: {stats['success_rate']:.1f}%")
        print(f"Average duration: {stats['avg_duration']*1000:.2f}ms")
        print(f"Average attempts: {avg_attempts:.1f}")
        print(f"Emails per second: {stats['operations_per_second']:.1f}")
        print(f"Total time: {total_time:.2f}s")
        
        # Performance assertions
        self.assertGreater(stats['success_rate'], 95.0)
        self.assertLess(stats['avg_duration'], 2.0)  # Less than 2 seconds with retries
        self.assertAlmostEqual(avg_attempts, 3.0, delta=0.1)  # Should average 3 attempts
    
    def test_queue_processing_performance(self):
        """Benchmark email queue processing performance"""
        print("\n--- Queue Processing Performance ---")
        
        num_emails = 100
        
        # Queue emails
        email_ids = []
        for i in range(num_emails):
            email_data = create_test_email_data(f"queue_test_{i}@example.com")
            email_id = self.delivery_manager.queue_email(email_data)
            email_ids.append(email_id)
        
        # Process queue
        self.benchmark.start_measurement()
        
        start_time = time.perf_counter()
        results = self.delivery_manager.process_queue()
        end_time = time.perf_counter()
        
        self.benchmark.end_measurement()
        
        # Analyze results
        successful_deliveries = sum(1 for r in results if r.success)
        total_time = end_time - start_time
        
        print(f"Queued emails: {num_emails}")
        print(f"Processed emails: {len(results)}")
        print(f"Successful deliveries: {successful_deliveries}")
        print(f"Success rate: {successful_deliveries/len(results)*100:.1f}%")
        print(f"Total processing time: {total_time:.2f}s")
        print(f"Emails per second: {successful_deliveries/total_time:.1f}")
        
        # Performance assertions
        self.assertEqual(len(results), num_emails)
        self.assertGreater(successful_deliveries/len(results), 0.95)  # 95% success rate
        self.assertGreater(successful_deliveries/total_time, 20)  # At least 20 emails/sec


class MemoryUsageBenchmark(unittest.TestCase):
    """Benchmark memory usage patterns"""
    
    def setUp(self):
        """Set up benchmark environment"""
        self.service_manager = EmailServiceManagerImpl()
        self.benchmark = PerformanceBenchmark("Memory Usage")
    
    def test_memory_usage_during_bulk_operations(self):
        """Test memory usage during bulk email operations"""
        print("\n--- Memory Usage During Bulk Operations ---")
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        mock_provider = MockEmailProvider()
        config = create_test_config(ProviderType.GMAIL)
        
        with patch('email_service.providers.EmailProviderFactory.create_provider') as mock_create:
            mock_create.return_value = mock_provider
            self.service_manager.initialize(config)
            
            # Send many emails and track memory
            memory_samples = []
            num_emails = 1000
            
            for i in range(num_emails):
                user_data = create_test_user_data()
                user_data.email = f"memory_test_{i}@example.com"
                alert_data = create_test_alert_data()
                
                result = self.service_manager.send_alert_email(user_data, alert_data)
                
                # Sample memory every 100 emails
                if i % 100 == 0:
                    current_memory = process.memory_info().rss / 1024 / 1024
                    memory_samples.append({
                        'email_count': i + 1,
                        'memory_mb': current_memory,
                        'memory_increase': current_memory - initial_memory
                    })
        
        final_memory = process.memory_info().rss / 1024 / 1024
        total_memory_increase = final_memory - initial_memory
        
        print(f"Initial memory: {initial_memory:.2f} MB")
        print(f"Final memory: {final_memory:.2f} MB")
        print(f"Total memory increase: {total_memory_increase:.2f} MB")
        print(f"Memory per email: {total_memory_increase/num_emails*1024:.2f} KB")
        
        # Print memory progression
        print("\nMemory progression:")
        for sample in memory_samples:
            print(f"  {sample['email_count']:4d} emails: {sample['memory_mb']:6.2f} MB (+{sample['memory_increase']:5.2f} MB)")
        
        # Performance assertions
        self.assertLess(total_memory_increase, 100)  # Less than 100MB total increase
        self.assertLess(total_memory_increase/num_emails*1024, 100)  # Less than 100KB per email
    
    def test_memory_leak_detection(self):
        """Test for memory leaks during repeated operations"""
        print("\n--- Memory Leak Detection ---")
        
        process = psutil.Process(os.getpid())
        
        mock_provider = MockEmailProvider()
        config = create_test_config(ProviderType.GMAIL)
        
        with patch('email_service.providers.EmailProviderFactory.create_provider') as mock_create:
            mock_create.return_value = mock_provider
            
            memory_samples = []
            num_cycles = 10
            emails_per_cycle = 50
            
            for cycle in range(num_cycles):
                # Initialize service
                service_manager = EmailServiceManagerImpl()
                service_manager.initialize(config)
                
                # Send emails
                for i in range(emails_per_cycle):
                    user_data = create_test_user_data()
                    user_data.email = f"leak_test_{cycle}_{i}@example.com"
                    alert_data = create_test_alert_data()
                    
                    service_manager.send_alert_email(user_data, alert_data)
                
                # Sample memory
                current_memory = process.memory_info().rss / 1024 / 1024
                memory_samples.append({
                    'cycle': cycle + 1,
                    'memory_mb': current_memory
                })
                
                # Clean up
                del service_manager
        
        # Analyze memory trend
        memory_values = [s['memory_mb'] for s in memory_samples]
        memory_trend = statistics.linear_regression(range(len(memory_values)), memory_values)
        
        print(f"Memory samples across {num_cycles} cycles:")
        for sample in memory_samples:
            print(f"  Cycle {sample['cycle']:2d}: {sample['memory_mb']:6.2f} MB")
        
        print(f"\nMemory trend slope: {memory_trend.slope:.3f} MB/cycle")
        print(f"Memory trend intercept: {memory_trend.intercept:.2f} MB")
        
        # Performance assertions
        self.assertLess(abs(memory_trend.slope), 2.0)  # Less than 2MB increase per cycle
        
        # Check for significant memory increase
        memory_increase = memory_values[-1] - memory_values[0]
        print(f"Total memory increase: {memory_increase:.2f} MB")
        self.assertLess(memory_increase, 20)  # Less than 20MB total increase


class BenchmarkRunner:
    """Main benchmark runner"""
    
    @staticmethod
    def run_all_benchmarks():
        """Run all performance benchmarks"""
        print("=" * 80)
        print("EMAIL SERVICE PERFORMANCE BENCHMARKS")
        print("=" * 80)
        
        # Create test suite
        suite = unittest.TestSuite()
        
        # Add benchmark classes
        benchmark_classes = [
            EmailSendingBenchmark,
            TemplateRenderingBenchmark,
            ConfigurationBenchmark,
            DeliveryManagerBenchmark,
            MemoryUsageBenchmark
        ]
        
        for benchmark_class in benchmark_classes:
            tests = unittest.TestLoader().loadTestsFromTestCase(benchmark_class)
            suite.addTests(tests)
        
        # Run benchmarks
        runner = unittest.TextTestRunner(verbosity=2)
        start_time = time.time()
        result = runner.run(suite)
        end_time = time.time()
        
        # Print summary
        print("\n" + "=" * 80)
        print("PERFORMANCE BENCHMARK SUMMARY")
        print("=" * 80)
        print(f"Total benchmark time: {end_time - start_time:.2f}s")
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
    # Run individual benchmark classes or the full suite
    import sys
    
    if len(sys.argv) > 1:
        # Run specific benchmark class
        benchmark_class_name = sys.argv[1]
        if benchmark_class_name in globals():
            unittest.main(argv=[''], testRunner=unittest.TextTestRunner(verbosity=2))
    else:
        # Run full benchmark suite
        success = BenchmarkRunner.run_all_benchmarks()
        sys.exit(0 if success else 1)