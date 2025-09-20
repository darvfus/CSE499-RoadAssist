"""
Email Package Manager Implementation

Handles automatic detection and installation of required email packages.
"""

import subprocess
import sys
import logging
import importlib
from typing import Dict, List
from .interfaces import EmailPackageManager
from .models import PackageStatus
from .enums import ErrorType


class EmailPackageManagerImpl(EmailPackageManager):
    """Implementation of email package management functionality"""
    
    # Required packages for email functionality
    REQUIRED_PACKAGES = [
        'smtplib',  # Built-in, should always be available
        'email',    # Built-in, should always be available
        'ssl',      # Built-in, should always be available
    ]
    
    # Optional packages that enhance functionality
    OPTIONAL_PACKAGES = [
        'cryptography',  # For secure credential storage
        'keyring',       # For credential management
        'requests',      # For OAuth2 authentication
    ]
    
    def __init__(self):
        """Initialize the package manager"""
        self.logger = logging.getLogger(__name__)
        self._installation_log = []
        
    def check_required_packages(self) -> Dict[str, bool]:
        """
        Check which required packages are installed
        
        Returns:
            Dict mapping package names to installation status
        """
        package_status = {}
        
        for package in self.REQUIRED_PACKAGES:
            try:
                importlib.import_module(package)
                package_status[package] = True
                self.logger.debug(f"Package {package} is available")
            except ImportError:
                package_status[package] = False
                self.logger.warning(f"Package {package} is not available")
                
        # Check optional packages
        for package in self.OPTIONAL_PACKAGES:
            try:
                importlib.import_module(package)
                package_status[package] = True
                self.logger.debug(f"Optional package {package} is available")
            except ImportError:
                package_status[package] = False
                self.logger.info(f"Optional package {package} is not available")
                
        return package_status
    
    def install_missing_packages(self) -> Dict[str, bool]:
        """
        Install missing packages using pip
        
        Returns:
            Dict mapping package names to installation success status
        """
        installation_results = {}
        package_status = self.check_required_packages()
        
        # Only install optional packages that are missing
        missing_packages = [
            pkg for pkg in self.OPTIONAL_PACKAGES 
            if not package_status.get(pkg, False)
        ]
        
        if not missing_packages:
            self.logger.info("All required packages are already installed")
            # Return current status for all packages
            return package_status
        
        for package in missing_packages:
            try:
                self.logger.info(f"Installing package: {package}")
                self._installation_log.append(f"Starting installation of {package}")
                
                # Use subprocess to install package
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "install", package],
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minute timeout
                )
                
                if result.returncode == 0:
                    installation_results[package] = True
                    self.logger.info(f"Successfully installed {package}")
                    self._installation_log.append(f"Successfully installed {package}")
                else:
                    installation_results[package] = False
                    error_msg = f"Failed to install {package}: {result.stderr}"
                    self.logger.error(error_msg)
                    self._installation_log.append(error_msg)
                    
            except subprocess.TimeoutExpired:
                installation_results[package] = False
                error_msg = f"Installation of {package} timed out"
                self.logger.error(error_msg)
                self._installation_log.append(error_msg)
                
            except Exception as e:
                installation_results[package] = False
                error_msg = f"Error installing {package}: {str(e)}"
                self.logger.error(error_msg)
                self._installation_log.append(error_msg)
        
        # Combine initial status with installation results
        final_results = package_status.copy()
        final_results.update(installation_results)
            
        return final_results
    
    def get_installation_status(self) -> PackageStatus:
        """
        Get detailed status of package installations
        
        Returns:
            PackageStatus object with current status
        """
        package_status = self.check_required_packages()
        
        return PackageStatus(
            required_packages=package_status,
            installation_log=self._installation_log.copy(),
            all_installed=all(package_status.values())
        )
    
    def get_required_packages(self) -> List[str]:
        """
        Get list of required package names
        
        Returns:
            List of required package names
        """
        return self.REQUIRED_PACKAGES + self.OPTIONAL_PACKAGES
    
    def validate_email_functionality(self) -> Dict[str, bool]:
        """
        Validate that email functionality is working
        
        Returns:
            Dict mapping functionality to availability status
        """
        functionality_status = {}
        
        # Test SMTP functionality
        try:
            import smtplib
            functionality_status['smtp'] = True
        except ImportError:
            functionality_status['smtp'] = False
            
        # Test email composition
        try:
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            functionality_status['email_composition'] = True
        except ImportError:
            functionality_status['email_composition'] = False
            
        # Test SSL functionality
        try:
            import ssl
            functionality_status['ssl'] = True
        except ImportError:
            functionality_status['ssl'] = False
            
        # Test optional secure storage
        try:
            import cryptography
            functionality_status['secure_storage'] = True
        except ImportError:
            functionality_status['secure_storage'] = False
            
        return functionality_status
    
    def get_package_info(self, package_name: str) -> Dict[str, str]:
        """
        Get information about a specific package
        
        Args:
            package_name: Name of the package to get info for
            
        Returns:
            Dict with package information
        """
        try:
            module = importlib.import_module(package_name)
            return {
                'name': package_name,
                'version': getattr(module, '__version__', 'Unknown'),
                'file': getattr(module, '__file__', 'Unknown'),
                'installed': True
            }
        except ImportError:
            return {
                'name': package_name,
                'version': 'Not installed',
                'file': 'Not available',
                'installed': False
            }
    
    def clear_installation_log(self) -> None:
        """Clear the installation log"""
        self._installation_log.clear()
        self.logger.debug("Installation log cleared")