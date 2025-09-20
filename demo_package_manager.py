#!/usr/bin/env python3
"""
Demonstration script for Email Package Manager

Shows how to use the EmailPackageManagerImpl to check and install packages.
"""

import logging
from email_service import EmailPackageManagerImpl

def main():
    """Demonstrate package manager functionality"""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("🔧 Email Package Manager Demo")
    print("=" * 50)
    
    # Create package manager instance
    package_manager = EmailPackageManagerImpl()
    
    # Check required packages
    print("\n📦 Checking required packages...")
    package_status = package_manager.check_required_packages()
    
    for package, installed in package_status.items():
        status = "✅ Installed" if installed else "❌ Missing"
        print(f"  {package:20} {status}")
    
    # Get installation status
    print("\n📊 Installation Status:")
    status = package_manager.get_installation_status()
    print(f"  All packages installed: {'✅ Yes' if status.all_installed else '❌ No'}")
    print(f"  Installation log entries: {len(status.installation_log)}")
    
    # Validate email functionality
    print("\n🔍 Validating email functionality...")
    functionality = package_manager.validate_email_functionality()
    
    for func, available in functionality.items():
        status = "✅ Available" if available else "❌ Not available"
        print(f"  {func:20} {status}")
    
    # Show package information
    print("\n📋 Package Information:")
    for package in package_manager.get_required_packages():
        info = package_manager.get_package_info(package)
        print(f"  {package}:")
        print(f"    Version: {info['version']}")
        print(f"    Installed: {'✅ Yes' if info['installed'] else '❌ No'}")
    
    # Test installation (only if there are missing packages)
    missing_packages = [pkg for pkg, installed in package_status.items() if not installed]
    
    if missing_packages:
        print(f"\n🔧 Found {len(missing_packages)} missing packages")
        print("Would you like to install them? (y/n): ", end="")
        
        try:
            response = input().lower().strip()
            if response in ['y', 'yes']:
                print("Installing missing packages...")
                results = package_manager.install_missing_packages()
                
                print("\n📥 Installation Results:")
                for package, success in results.items():
                    if package in missing_packages:
                        status = "✅ Success" if success else "❌ Failed"
                        print(f"  {package:20} {status}")
                
                # Show installation log
                final_status = package_manager.get_installation_status()
                if final_status.installation_log:
                    print("\n📝 Installation Log:")
                    for entry in final_status.installation_log:
                        print(f"  {entry}")
            else:
                print("Skipping installation.")
        except KeyboardInterrupt:
            print("\nOperation cancelled.")
    else:
        print("\n✅ All required packages are already installed!")
    
    print("\n🎉 Demo completed!")

if __name__ == "__main__":
    main()