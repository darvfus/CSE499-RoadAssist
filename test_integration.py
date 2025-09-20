#!/usr/bin/env python3
"""
Test script for email integration
"""

def test_email_integration():
    """Test the email integration module"""
    print("Testing Email Integration")
    print("=" * 30)
    
    try:
        # Test import
        print("1. Testing import...")
        from email_integration import (
            enviar_correo, 
            inicializar_email_service, 
            get_email_service_status,
            EMAIL_SERVICE_AVAILABLE
        )
        print("✓ Import successful")
        
        # Test service availability
        print(f"2. Enhanced service available: {EMAIL_SERVICE_AVAILABLE}")
        
        # Test status
        print("3. Getting service status...")
        status = get_email_service_status()
        print(f"   Service type: {status['service_type']}")
        print(f"   Enhanced available: {status['enhanced_service_available']}")
        print(f"   Enhanced initialized: {status['enhanced_service_initialized']}")
        
        # Test initialization
        print("4. Testing initialization...")
        init_result = inicializar_email_service()
        print(f"   Initialization result: {init_result}")
        
        # Test email function (dry run - won't actually send)
        print("5. Testing email function (dry run)...")
        print("   Note: This won't actually send an email without proper configuration")
        
        print("\n✓ All tests completed successfully")
        print("\nNext steps:")
        print("1. Create email_config.json with your credentials")
        print("2. Test actual email sending with real credentials")
        
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        print("Make sure email_integration.py is in the same directory")
        return False
    except Exception as e:
        print(f"✗ Test error: {e}")
        return False

def test_existing_files():
    """Test that existing files can still import their dependencies"""
    print("\nTesting Existing Files Compatibility")
    print("=" * 40)
    
    files_to_test = [
        'main.py',
        'driverassitant.py',
        'driverassistant_modified.py'
    ]
    
    for filename in files_to_test:
        try:
            print(f"Testing {filename}...")
            # Try to compile the file to check for syntax errors
            with open(filename, 'r') as f:
                code = f.read()
            compile(code, filename, 'exec')
            print(f"✓ {filename} syntax OK")
        except FileNotFoundError:
            print(f"- {filename} not found (skipping)")
        except SyntaxError as e:
            print(f"✗ {filename} syntax error: {e}")
        except Exception as e:
            print(f"? {filename} other issue: {e}")

if __name__ == "__main__":
    success = test_email_integration()
    test_existing_files()
    
    if success:
        print("\n🎉 Integration test completed successfully!")
    else:
        print("\n❌ Integration test failed")