"""
Demo script for Email Template Engine
"""

from datetime import datetime
from email_service.templates import EmailTemplateEngineImpl


def main():
    """Demonstrate email template engine functionality"""
    print("=== Email Template Engine Demo ===\n")
    
    # Initialize template engine
    template_engine = EmailTemplateEngineImpl()
    
    # Load templates
    print("Loading templates...")
    templates = template_engine.load_templates()
    print(f"Loaded {len(templates)} templates:")
    for name, info in templates.items():
        metadata = info.get('metadata', {})
        print(f"  - {name}: {metadata.get('description', 'No description')}")
    print()
    
    # Test data for rendering
    test_data = {
        'user_name': 'John Doe',
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'alert_type': 'Drowsiness Detection',
        'heart_rate': '78',
        'oxygen_saturation': '97.5',
        'system_name': 'Driver Assistant System'
    }
    
    # Test each template
    for template_name in templates.keys():
        if template_name.endswith('_html'):
            continue  # Skip HTML templates for this demo
            
        print(f"=== Testing Template: {template_name} ===")
        
        try:
            # Get template variables
            variables = template_engine.get_template_variables(template_name)
            print(f"Template variables: {', '.join(variables)}")
            
            # Render template
            result = template_engine.render_template(template_name, test_data)
            
            print(f"Subject: {result.subject}")
            print("Body:")
            print("-" * 50)
            print(result.body)
            print("-" * 50)
            
            if result.html_body:
                print("HTML version available: Yes")
            else:
                print("HTML version available: No")
            
        except Exception as e:
            print(f"Error rendering template: {e}")
        
        print()
    
    # Test template validation
    print("=== Template Validation Tests ===")
    
    valid_template = "Subject: Test\n\nHello ${user_name}, this is a test at ${timestamp}."
    invalid_template = "Subject: Dangerous\n\n<script>alert('xss')</script>Hello ${user_name}"
    
    print(f"Valid template validation: {template_engine.validate_template(valid_template)}")
    print(f"Invalid template validation: {template_engine.validate_template(invalid_template)}")
    
    # Test with missing data
    print("\n=== Testing with Missing Data ===")
    incomplete_data = {
        'user_name': 'Jane Smith',
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        # Missing other variables
    }
    
    try:
        result = template_engine.render_template('drowsiness_alert', incomplete_data)
        print("Successfully rendered template with missing data")
        print(f"Subject: {result.subject}")
        print("Body preview:")
        print(result.body[:200] + "..." if len(result.body) > 200 else result.body)
    except Exception as e:
        print(f"Error with missing data: {e}")
    
    print("\n=== Demo Complete ===")


if __name__ == "__main__":
    main()