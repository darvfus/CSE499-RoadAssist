"""
Unit Tests for Email Template Engine
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

from email_service.templates import EmailTemplateEngineImpl
from email_service.models import EmailContent


class TestEmailTemplateEngine(unittest.TestCase):
    """Test cases for EmailTemplateEngine implementation"""
    
    def setUp(self):
        """Set up test environment"""
        # Create temporary directory for test templates
        self.temp_dir = tempfile.mkdtemp()
        self.template_engine = EmailTemplateEngineImpl(template_dir=self.temp_dir)
        
        # Create test template
        self.test_template_content = """Subject: Test Alert - ${user_name}

Hello ${user_name},

This is a test alert at ${timestamp}.

Alert Type: ${alert_type}
Heart Rate: ${heart_rate} BPM
Oxygen Saturation: ${oxygen_saturation}%

Best regards,
${system_name}"""
        
        # Write test template to file
        template_path = Path(self.temp_dir) / "test_alert.txt"
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(self.test_template_content)
        
        # Create test template metadata
        metadata_content = """{
  "name": "Test Alert",
  "description": "Test template for unit testing",
  "category": "test",
  "priority": "normal",
  "required_variables": ["user_name", "timestamp"],
  "optional_variables": ["heart_rate", "oxygen_saturation"]
}"""
        metadata_path = Path(self.temp_dir) / "test_alert.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            f.write(metadata_content)
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir)
    
    def test_load_templates(self):
        """Test template loading functionality"""
        templates = self.template_engine.load_templates()
        
        self.assertIn('test_alert', templates)
        self.assertIn('template', templates['test_alert'])
        self.assertIn('metadata', templates['test_alert'])
        self.assertIn('variables', templates['test_alert'])
        
        # Check metadata
        metadata = templates['test_alert']['metadata']
        self.assertEqual(metadata['name'], 'Test Alert')
        self.assertEqual(metadata['category'], 'test')
    
    def test_render_template_success(self):
        """Test successful template rendering"""
        # Load templates first
        self.template_engine.load_templates()
        
        # Test data
        test_data = {
            'user_name': 'John Doe',
            'timestamp': '2024-01-15 10:30:00',
            'alert_type': 'Drowsiness',
            'heart_rate': '75',
            'oxygen_saturation': '98',
            'system_name': 'Driver Assistant'
        }
        
        # Render template
        result = self.template_engine.render_template('test_alert', test_data)
        
        # Verify result
        self.assertIsInstance(result, EmailContent)
        self.assertEqual(result.subject, 'Test Alert - John Doe')
        self.assertIn('John Doe', result.body)
        self.assertIn('2024-01-15 10:30:00', result.body)
        self.assertIn('75 BPM', result.body)
        self.assertIn('98%', result.body)
    
    def test_render_template_missing_variables(self):
        """Test template rendering with missing variables"""
        self.template_engine.load_templates()
        
        # Test data with missing variables
        test_data = {
            'user_name': 'Jane Doe',
            'timestamp': '2024-01-15 10:30:00'
            # Missing: alert_type, heart_rate, oxygen_saturation, system_name
        }
        
        # Should still render with default values
        result = self.template_engine.render_template('test_alert', test_data)
        
        self.assertIsInstance(result, EmailContent)
        self.assertEqual(result.subject, 'Test Alert - Jane Doe')
        self.assertIn('Jane Doe', result.body)
        self.assertIn('N/A', result.body)  # Default value for missing variables
    
    def test_render_template_not_found(self):
        """Test rendering non-existent template"""
        with self.assertRaises(ValueError) as context:
            self.template_engine.render_template('nonexistent', {})
        
        self.assertIn('not found', str(context.exception))
    
    def test_validate_template_valid(self):
        """Test validation of valid template"""
        valid_template = "Subject: Test\n\nHello ${user_name}, this is a test at ${timestamp}."
        
        result = self.template_engine.validate_template(valid_template)
        self.assertTrue(result)
    
    def test_validate_template_invalid_empty(self):
        """Test validation of empty template"""
        result = self.template_engine.validate_template("")
        self.assertFalse(result)
    
    def test_validate_template_dangerous_content(self):
        """Test validation rejects dangerous content"""
        dangerous_template = "Subject: Test\n\n<script>alert('xss')</script>Hello ${user_name}"
        
        result = self.template_engine.validate_template(dangerous_template)
        self.assertFalse(result)
    
    def test_get_template_variables(self):
        """Test extraction of template variables"""
        self.template_engine.load_templates()
        
        variables = self.template_engine.get_template_variables('test_alert')
        
        expected_variables = ['alert_type', 'heart_rate', 'oxygen_saturation', 'system_name', 'timestamp', 'user_name']
        self.assertEqual(sorted(variables), sorted(expected_variables))
    
    def test_get_template_variables_not_found(self):
        """Test getting variables for non-existent template"""
        variables = self.template_engine.get_template_variables('nonexistent')
        self.assertEqual(variables, [])
    
    def test_sanitize_template_data(self):
        """Test data sanitization"""
        dangerous_data = {
            'user_name': 'John<script>alert("xss")</script>Doe',
            'message': 'Hello "world"',
            'number': 42,
            'boolean': True,
            'none_value': None,
            'long_string': 'x' * 2000  # Very long string
        }
        
        sanitized = self.template_engine._sanitize_template_data(dangerous_data)
        
        # Check sanitization
        self.assertNotIn('<script>', sanitized['user_name'])
        self.assertNotIn('"', sanitized['message'])
        self.assertEqual(sanitized['number'], '42')
        self.assertEqual(sanitized['boolean'], 'True')
        self.assertEqual(sanitized['none_value'], 'N/A')
        self.assertEqual(len(sanitized['long_string']), 1000)  # Truncated
    
    def test_extract_template_variables(self):
        """Test variable extraction from template content"""
        template_content = """
        Hello ${user_name}, this is $alert_type.
        Your heart rate is ${heart_rate} and oxygen is $oxygen_saturation.
        """
        
        variables = self.template_engine._extract_template_variables(template_content)
        expected = ['alert_type', 'heart_rate', 'oxygen_saturation', 'user_name']
        
        self.assertEqual(sorted(variables), sorted(expected))
    
    def test_parse_rendered_content(self):
        """Test parsing of rendered content"""
        content = """Subject: Test Subject

This is the email body.
It has multiple lines.
"""
        
        subject, body = self.template_engine._parse_rendered_content(content)
        
        self.assertEqual(subject, 'Test Subject')
        self.assertEqual(body, 'This is the email body.\nIt has multiple lines.')
    
    def test_parse_rendered_content_no_subject(self):
        """Test parsing content without explicit subject"""
        content = """This is just body content.
No subject line here."""
        
        subject, body = self.template_engine._parse_rendered_content(content)
        
        self.assertEqual(subject, 'Driver Alert Notification')  # Default subject
        self.assertEqual(body, 'This is just body content.\nNo subject line here.')
    
    def test_default_template_data(self):
        """Test default template data generation"""
        defaults = self.template_engine._get_default_template_data()
        
        self.assertIn('timestamp', defaults)
        self.assertIn('user_name', defaults)
        self.assertIn('alert_type', defaults)
        self.assertIn('heart_rate', defaults)
        self.assertIn('oxygen_saturation', defaults)
        self.assertIn('system_name', defaults)
        
        # Check default values
        self.assertEqual(defaults['user_name'], 'User')
        self.assertEqual(defaults['heart_rate'], 'N/A')
        self.assertEqual(defaults['oxygen_saturation'], 'N/A')


class TestTemplateValidation(unittest.TestCase):
    """Test cases for template validation"""
    
    def setUp(self):
        """Set up test environment"""
        self.template_engine = EmailTemplateEngineImpl()
    
    def test_has_required_sections_valid(self):
        """Test valid template sections"""
        template = "Hello ${user_name}, this is a test."
        result = self.template_engine._has_required_sections(template)
        self.assertTrue(result)
    
    def test_has_required_sections_empty(self):
        """Test empty template"""
        result = self.template_engine._has_required_sections("")
        self.assertFalse(result)
    
    def test_has_required_sections_no_variables(self):
        """Test template without variables"""
        template = "This is just plain text."
        result = self.template_engine._has_required_sections(template)
        self.assertFalse(result)
    
    def test_has_dangerous_content_safe(self):
        """Test safe template content"""
        template = "Hello ${user_name}, your alert is ${alert_type}."
        result = self.template_engine._has_dangerous_content(template)
        self.assertFalse(result)
    
    def test_has_dangerous_content_script(self):
        """Test template with script tag"""
        template = "Hello ${user_name} <script>alert('xss')</script>"
        result = self.template_engine._has_dangerous_content(template)
        self.assertTrue(result)
    
    def test_has_dangerous_content_javascript(self):
        """Test template with javascript"""
        template = "Hello ${user_name} javascript:alert('xss')"
        result = self.template_engine._has_dangerous_content(template)
        self.assertTrue(result)
    
    def test_validate_template_variables_valid(self):
        """Test valid variable names"""
        variables = ['user_name', 'alert_type', 'heart_rate', '_private_var']
        result = self.template_engine._validate_template_variables(variables)
        self.assertTrue(result)
    
    def test_validate_template_variables_invalid(self):
        """Test invalid variable names"""
        variables = ['user-name', '123invalid', 'alert.type']
        result = self.template_engine._validate_template_variables(variables)
        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()