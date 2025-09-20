#!/usr/bin/env python3
"""
Script to update existing driver assistant files to use the new email service.
This script provides backward compatibility while enabling enhanced email functionality.
"""

import os
import shutil
from datetime import datetime

def backup_file(filepath):
    """Create a backup of the original file"""
    if os.path.exists(filepath):
        backup_path = f"{filepath}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2(filepath, backup_path)
        print(f"Backup created: {backup_path}")
        return backup_path
    return None

def create_email_config_template():
    """Create an email configuration template file"""
    config_template = {
        "provider": "gmail",
        "smtp_server": "smtp.gmail.com", 
        "smtp_port": 587,
        "use_tls": True,
        "sender_email": "your_email@gmail.com",
        "sender_password": "your_app_password",
        "auth_method": "app_password",
        "timeout": 30,
        "max_retries": 3
    }
    
    try:
        import json
        with open("email_config_template.json", "w") as f:
            json.dump(config_template, f, indent=4)
        print("Created email_config_template.json")
        return True
    except Exception as e:
        print(f"Error creating config template: {e}")
        return False

def update_file_for_integration(filepath):
    """Update a file to use email integration"""
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return False
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if already updated
        if 'email_integration' in content:
            print(f"File {filepath} already updated")
            return True
        
        # Create backup
        backup_file(filepath)
        
        # Simple approach: Add integration import and modify enviar_correo calls
        lines = content.split('\n')
        updated_lines = []
        
        # Add import after existing imports
        import_added = False
        for i, line in enumerate(lines):
            updated_lines.append(line)
            
            # Add import after the last import line
            if (line.strip().startswith('import ') or line.strip().startswith('from ')) and not import_added:
                # Look ahead to see if there are more imports
                has_more_imports = False
                for j in range(i + 1, min(i + 10, len(lines))):
                    if lines[j].strip().startswith('import ') or lines[j].strip().startswith('from '):
                        has_more_imports = True
                        break
                    elif lines[j].strip() and not lines[j].strip().startswith('#'):
                        break
                
                if not has_more_imports:
                    updated_lines.append('')
                    updated_lines.append('# Enhanced email integration')
                    updated_lines.append('try:')
                    updated_lines.append('    from email_integration import enviar_correo as enviar_correo_integrado')
                    updated_lines.append('    EMAIL_INTEGRATION_AVAILABLE = True')
                    updated_lines.append('except ImportError:')
                    updated_lines.append('    EMAIL_INTEGRATION_AVAILABLE = False')
                    updated_lines.append('    print("Email integration not available, using original functionality")')
                    updated_lines.append('')
                    import_added = True
        
        # Update enviar_correo function definition or calls
        final_lines = []
        for line in updated_lines:
            if 'def enviar_correo(' in line and 'enviar_correo_integrado' not in line:
                # Replace function definition with wrapper
                final_lines.append('def enviar_correo(nombre_usuario, correo_usuario):')
                final_lines.append('    """Enhanced email function with backward compatibility"""')
                final_lines.append('    if EMAIL_INTEGRATION_AVAILABLE:')
                final_lines.append('        try:')
                final_lines.append('            return enviar_correo_integrado(nombre_usuario, correo_usuario)')
                final_lines.append('        except Exception as e:')
                final_lines.append('            print(f"Error with integrated email, using fallback: {e}")')
                final_lines.append('    ')
                final_lines.append('    # Original email functionality as fallback')
                final_lines.append('    return enviar_correo_original(nombre_usuario, correo_usuario)')
                final_lines.append('')
                final_lines.append('def enviar_correo_original(nombre_usuario, correo_usuario):')
                # Skip the original function definition line
            else:
                final_lines.append(line)
        
        # Write updated content
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(final_lines))
        
        print(f"✓ Successfully updated {filepath}")
        return True
        
    except Exception as e:
        print(f"✗ Error updating {filepath}: {e}")
        return False

def create_simple_integration_example():
    """Create a simple example of how to use the email integration"""
    example_code = '''#!/usr/bin/env python3
"""
Simple example of using the email integration module
"""

from email_integration import enviar_correo, inicializar_email_service, get_email_service_status

def main():
    print("Email Integration Example")
    print("=" * 30)
    
    # Initialize email service (optional - will auto-initialize)
    print("Initializing email service...")
    success = inicializar_email_service()
    
    if success:
        print("✓ Enhanced email service initialized")
    else:
        print("⚠ Using basic email functionality")
    
    # Get service status
    status = get_email_service_status()
    print(f"Service type: {status['service_type']}")
    
    # Send test email (replace with actual user data)
    print("\\nSending test email...")
    result = enviar_correo("Test User", "test@example.com")
    
    if result:
        print("✓ Email sent successfully")
    else:
        print("✗ Failed to send email")

if __name__ == "__main__":
    main()
'''
    
    try:
        with open("email_integration_example.py", "w") as f:
            f.write(example_code)
        print("Created email_integration_example.py")
        return True
    except Exception as e:
        print(f"Error creating example: {e}")
        return False

def main():
    """Main update function"""
    print("Driver Assistant Email Integration Update Script")
    print("=" * 50)
    
    # Create configuration template
    print("Creating email configuration template...")
    create_email_config_template()
    
    # Create integration example
    print("Creating integration example...")
    create_simple_integration_example()
    
    # Files to update (only update files that exist)
    potential_files = [
        'main.py',
        'driverassitant.py', 
        'driverassistant_modified.py',
        'interfaz.py'
    ]
    
    files_to_update = [f for f in potential_files if os.path.exists(f)]
    
    if not files_to_update:
        print("No driver assistant files found to update")
        return
    
    print(f"\nFound {len(files_to_update)} files to update:")
    for f in files_to_update:
        print(f"  - {f}")
    
    # Ask for confirmation
    response = input("\nProceed with updates? (y/n): ").lower().strip()
    if response != 'y':
        print("Update cancelled")
        return
    
    updated_files = []
    failed_files = []
    
    for filepath in files_to_update:
        print(f"\nUpdating {filepath}...")
        
        if update_file_for_integration(filepath):
            updated_files.append(filepath)
        else:
            failed_files.append(filepath)
    
    # Summary
    print("\n" + "=" * 50)
    print("Update Summary:")
    print(f"Successfully updated: {len(updated_files)} files")
    for f in updated_files:
        print(f"  ✓ {f}")
    
    if failed_files:
        print(f"Failed to update: {len(failed_files)} files")
        for f in failed_files:
            print(f"  ✗ {f}")
    
    print("\nFiles created:")
    print("  ✓ email_integration.py - Main integration module")
    print("  ✓ email_config_template.json - Configuration template")
    print("  ✓ email_integration_example.py - Usage example")
    
    print("\nNext steps:")
    print("1. Copy email_config_template.json to email_config.json")
    print("2. Edit email_config.json with your email credentials")
    print("3. Test the updated files to ensure they work correctly")
    print("4. The system will automatically use enhanced email when available")
    print("5. Backup files have been created for safety")

if __name__ == "__main__":
    main()