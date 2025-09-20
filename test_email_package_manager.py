#!/usr/bin/env python3
"""
Unit tests for Email Package Manager

Tests package detection, installation, and validation functionality.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import subprocess
import sys
from email_service.package_manager import EmailPackageManagerImpl
from email_service.models import PackageStatus


class TestEmailPackageManager(unittest.TestCase):
    """Test cases for EmailPackageManagerImpl"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.package_manager = EmailPackageManagerImpl()
        
    def test_initialization(self):
        """Test package manager initialization"""
        self.assertIsInstance(self.package_manager, EmailPackageManagerImpl)
        self.assertEqual(len(self.package_manager._installation_log), 0)
        self.assertIsNotNone(self.package_manager.logger)
        
    def test_get_required_packages(self):
        """Test getting list of required packages"""
        packages = self.package_manager.get_required_packages()
        
        # Should include both required and optional packages
        expected_required = ['smtplib', 'email', 'ssl']
        expected_optional = ['cryptography', 'keyring', 'requests']
        
        for pkg in expected_required:
            self.assertIn(pkg, packages)
        for pkg in expected_optional:
            self.assertIn(pkg, packages)
            
    @patch('email_service.package_manager.importlib.import_module')
    def test_check_required_packages_all_available(self, mock_import):
        """Test checking packages when all are available"""
        # Mock successful imports
        mock_import.return_value = Mock()
        
        result = self.package_manager.check_required_packages()
        
        # All packages should be marked as available
        for package in self.package_manager.REQUIRED_PACKAGES + self.package_manager.OPTIONAL_PACKAGES:
            self.assertTrue(result[package], f"Package {package} should be available")
            
    @patch('email_service.package_manager.importlib.import_module')
    def test_check_required_packages_some_missing(self, mock_import):
        """Test checking packages when some are missing"""
        # Mock import to fail for specific packages
        def mock_import_side_effect(package):
            if package in ['cryptography', 'keyring']:
                raise ImportError(f"No module named '{package}'")
            return Mock()
            
        mock_import.side_effect = mock_import_side_effect
        
        result = self.package_manager.check_required_packages()
        
        # Built-in packages should be available
        for package in self.package_manager.REQUIRED_PACKAGES:
            self.assertTrue(result[package], f"Required package {package} should be available")
            
        # Some optional packages should be missing
        self.assertFalse(result['cryptography'])
        self.assertFalse(result['keyring'])
        self.assertTrue(result['requests'])  # This one should be available
        
    @patch('email_service.package_manager.subprocess.run')
    def test_install_missing_packages_success(self, mock_subprocess):
        """Test successful installation of missing packages"""
        # Temporarily add a fake package to test installation
        original_optional = self.package_manager.OPTIONAL_PACKAGES.copy()
        self.package_manager.OPTIONAL_PACKAGES = ['fake_nonexistent_package']
        
        try:
            # Mock successful subprocess call
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stderr = ""
            mock_subprocess.return_value = mock_result
            
            result = self.package_manager.install_missing_packages()
            
            # Should attempt to install missing package
            mock_subprocess.assert_called_with(
                [sys.executable, "-m", "pip", "install", "fake_nonexistent_package"],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            # Installation should be marked as successful
            self.assertTrue(result['fake_nonexistent_package'])
            
        finally:
            # Restore original packages
            self.package_manager.OPTIONAL_PACKAGES = original_optional
        
    @patch('email_service.package_manager.subprocess.run')
    def test_install_missing_packages_failure(self, mock_subprocess):
        """Test failed installation of missing packages"""
        # Temporarily add a fake package to test installation failure
        original_optional = self.package_manager.OPTIONAL_PACKAGES.copy()
        self.package_manager.OPTIONAL_PACKAGES = ['fake_nonexistent_package']
        
        try:
            # Mock failed subprocess call
            mock_result = Mock()
            mock_result.returncode = 1
            mock_result.stderr = "Installation failed"
            mock_subprocess.return_value = mock_result
            
            result = self.package_manager.install_missing_packages()
            
            # Installation should be marked as failed
            self.assertFalse(result['fake_nonexistent_package'])
            
            # Should have logged the error
            self.assertGreater(len(self.package_manager._installation_log), 0)
            self.assertIn("Failed to install fake_nonexistent_package", 
                         ' '.join(self.package_manager._installation_log))
                         
        finally:
            # Restore original packages
            self.package_manager.OPTIONAL_PACKAGES = original_optional
        
    @patch('email_service.package_manager.subprocess.run')
    def test_install_missing_packages_timeout(self, mock_subprocess):
        """Test installation timeout handling"""
        # Temporarily add a fake package to test timeout
        original_optional = self.package_manager.OPTIONAL_PACKAGES.copy()
        self.package_manager.OPTIONAL_PACKAGES = ['fake_nonexistent_package']
        
        try:
            # Mock subprocess timeout
            mock_subprocess.side_effect = subprocess.TimeoutExpired(
                cmd=['pip', 'install', 'fake_nonexistent_package'], 
                timeout=300
            )
            
            result = self.package_manager.install_missing_packages()
            
            # Installation should be marked as failed
            self.assertFalse(result['fake_nonexistent_package'])
            
            # Should have logged the timeout
            self.assertIn("timed out", ' '.join(self.package_manager._installation_log))
            
        finally:
            # Restore original packages
            self.package_manager.OPTIONAL_PACKAGES = original_optional
        
    @patch('email_service.package_manager.importlib.import_module')
    def test_get_installation_status(self, mock_import):
        """Test getting installation status"""
        # Mock some packages as missing
        def mock_import_side_effect(package):
            if package == 'cryptography':
                raise ImportError(f"No module named '{package}'")
            return Mock()
            
        mock_import.side_effect = mock_import_side_effect
        
        # Add some log entries
        self.package_manager._installation_log = ["Test log entry"]
        
        status = self.package_manager.get_installation_status()
        
        self.assertIsInstance(status, PackageStatus)
        self.assertFalse(status.all_installed)  # cryptography is missing
        self.assertEqual(len(status.installation_log), 1)
        self.assertFalse(status.required_packages['cryptography'])
        
    @patch('email_service.package_manager.importlib.import_module')
    def test_validate_email_functionality(self, mock_import):
        """Test email functionality validation"""
        # Mock successful imports
        mock_import.return_value = Mock()
        
        result = self.package_manager.validate_email_functionality()
        
        expected_functions = ['smtp', 'email_composition', 'ssl', 'secure_storage']
        for func in expected_functions:
            self.assertIn(func, result)
            
    @patch('email_service.package_manager.importlib.import_module')
    def test_get_package_info_installed(self, mock_import):
        """Test getting info for installed package"""
        # Mock module with version
        mock_module = Mock()
        mock_module.__version__ = "1.0.0"
        mock_module.__file__ = "/path/to/module.py"
        mock_import.return_value = mock_module
        
        info = self.package_manager.get_package_info('test_package')
        
        self.assertEqual(info['name'], 'test_package')
        self.assertEqual(info['version'], '1.0.0')
        self.assertEqual(info['file'], '/path/to/module.py')
        self.assertTrue(info['installed'])
        
    @patch('email_service.package_manager.importlib.import_module')
    def test_get_package_info_not_installed(self, mock_import):
        """Test getting info for non-installed package"""
        # Mock import error
        mock_import.side_effect = ImportError("No module named 'test_package'")
        
        info = self.package_manager.get_package_info('test_package')
        
        self.assertEqual(info['name'], 'test_package')
        self.assertEqual(info['version'], 'Not installed')
        self.assertEqual(info['file'], 'Not available')
        self.assertFalse(info['installed'])
        
    def test_clear_installation_log(self):
        """Test clearing installation log"""
        # Add some log entries
        self.package_manager._installation_log = ["Entry 1", "Entry 2"]
        
        self.package_manager.clear_installation_log()
        
        self.assertEqual(len(self.package_manager._installation_log), 0)


class TestPackageManagerIntegration(unittest.TestCase):
    """Integration tests for package manager"""
    
    def setUp(self):
        """Set up integration test fixtures"""
        self.package_manager = EmailPackageManagerImpl()
        
    def test_real_package_detection(self):
        """Test real package detection (no mocking)"""
        # This tests actual package detection
        result = self.package_manager.check_required_packages()
        
        # Built-in packages should always be available
        self.assertTrue(result['smtplib'])
        self.assertTrue(result['email'])
        self.assertTrue(result['ssl'])
        
        # Optional packages may or may not be available
        # Just check that we get a boolean result
        for package in self.package_manager.OPTIONAL_PACKAGES:
            self.assertIsInstance(result[package], bool)
            
    def test_functionality_validation(self):
        """Test actual functionality validation"""
        result = self.package_manager.validate_email_functionality()
        
        # Core email functionality should work
        self.assertTrue(result['smtp'])
        self.assertTrue(result['email_composition'])
        self.assertTrue(result['ssl'])
        
        # Secure storage depends on cryptography being installed
        self.assertIsInstance(result['secure_storage'], bool)


if __name__ == '__main__':
    # Configure logging for tests
    import logging
    logging.basicConfig(level=logging.DEBUG)
    
    # Run tests
    unittest.main(verbosity=2)