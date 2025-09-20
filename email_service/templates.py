"""
Email Template Engine Implementation
"""

import os
import re
import json
import logging
from typing import Dict, List, Any, Optional
from string import Template
from pathlib import Path
from datetime import datetime

from .interfaces import EmailTemplateEngine
from .models import EmailContent, ErrorResponse
from .enums import ErrorType


class EmailTemplateEngineImpl(EmailTemplateEngine):
    """Implementation of email template engine with template loading and rendering"""
    
    def __init__(self, template_dir: Optional[str] = None):
        """
        Initialize template engine
        
        Args:
            template_dir: Directory containing template files. If None, uses default.
        """
        self.logger = logging.getLogger(__name__)
        self.template_dir = Path(template_dir) if template_dir else Path(__file__).parent / "templates"
        self.templates: Dict[str, Template] = {}
        self.template_metadata: Dict[str, Dict[str, Any]] = {}
        self._ensure_template_directory()
        
    def _ensure_template_directory(self) -> None:
        """Ensure template directory exists"""
        try:
            self.template_dir.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"Template directory ensured: {self.template_dir}")
        except Exception as e:
            self.logger.error(f"Failed to create template directory: {e}")
            raise
    
    def load_templates(self) -> Dict[str, Any]:
        """
        Load all available email templates from the template directory
        
        Returns:
            Dictionary of loaded templates with metadata
        """
        loaded_templates = {}
        
        try:
            if not self.template_dir.exists():
                self.logger.warning(f"Template directory does not exist: {self.template_dir}")
                return loaded_templates
            
            # Load template files
            for template_file in self.template_dir.glob("*.txt"):
                template_name = template_file.stem
                
                try:
                    with open(template_file, 'r', encoding='utf-8') as f:
                        template_content = f.read()
                    
                    # Create Template object
                    template = Template(template_content)
                    self.templates[template_name] = template
                    
                    # Load metadata if exists
                    metadata_file = template_file.with_suffix('.json')
                    metadata = {}
                    if metadata_file.exists():
                        with open(metadata_file, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                    
                    self.template_metadata[template_name] = metadata
                    loaded_templates[template_name] = {
                        'template': template,
                        'metadata': metadata,
                        'variables': self._extract_template_variables(template_content)
                    }
                    
                    self.logger.info(f"Loaded template: {template_name}")
                    
                except Exception as e:
                    self.logger.error(f"Failed to load template {template_file}: {e}")
                    continue
            
            self.logger.info(f"Successfully loaded {len(loaded_templates)} templates")
            return loaded_templates
            
        except Exception as e:
            self.logger.error(f"Failed to load templates: {e}")
            raise
    
    def render_template(self, template_name: str, data: Dict[str, Any]) -> EmailContent:
        """
        Render a template with provided data
        
        Args:
            template_name: Name of the template to render
            data: Data dictionary for template substitution
            
        Returns:
            EmailContent object with rendered subject and body
            
        Raises:
            ValueError: If template not found or rendering fails
        """
        try:
            # Load templates if not already loaded
            if not self.templates:
                self.load_templates()
            
            if template_name not in self.templates:
                raise ValueError(f"Template '{template_name}' not found")
            
            template = self.templates[template_name]
            
            # Sanitize and validate data
            sanitized_data = self._sanitize_template_data(data)
            
            # Add default values for common variables
            default_data = self._get_default_template_data()
            render_data = {**default_data, **sanitized_data}
            
            # Render template
            try:
                rendered_content = template.safe_substitute(render_data)
            except KeyError as e:
                # Try with partial substitution for missing variables
                self.logger.warning(f"Missing template variable: {e}")
                rendered_content = template.safe_substitute(render_data)
            
            # Parse rendered content to extract subject and body
            subject, body = self._parse_rendered_content(rendered_content)
            
            # Check if HTML version exists
            html_body = None
            html_template_name = f"{template_name}_html"
            if html_template_name in self.templates:
                html_template = self.templates[html_template_name]
                html_content = html_template.safe_substitute(render_data)
                _, html_body = self._parse_rendered_content(html_content)
            
            self.logger.info(f"Successfully rendered template: {template_name}")
            
            return EmailContent(
                subject=subject,
                body=body,
                html_body=html_body
            )
            
        except Exception as e:
            self.logger.error(f"Failed to render template '{template_name}': {e}")
            raise ValueError(f"Template rendering failed: {e}")
    
    def validate_template(self, template: str) -> bool:
        """
        Validate template syntax and structure
        
        Args:
            template: Template string to validate
            
        Returns:
            True if template is valid, False otherwise
        """
        try:
            # Check if template can be parsed
            Template(template)
            
            # Check for required sections (subject and body)
            if not self._has_required_sections(template):
                return False
            
            # Check for potentially dangerous content
            if self._has_dangerous_content(template):
                return False
            
            # Validate template variables
            variables = self._extract_template_variables(template)
            if not self._validate_template_variables(variables):
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Template validation failed: {e}")
            return False
    
    def get_template_variables(self, template_name: str) -> List[str]:
        """
        Get list of variables used in a template
        
        Args:
            template_name: Name of the template
            
        Returns:
            List of variable names used in the template
        """
        try:
            if template_name not in self.templates:
                if not self.templates:
                    self.load_templates()
                
                if template_name not in self.templates:
                    raise ValueError(f"Template '{template_name}' not found")
            
            template = self.templates[template_name]
            return self._extract_template_variables(template.template)
            
        except Exception as e:
            self.logger.error(f"Failed to get template variables for '{template_name}': {e}")
            return []
    
    def _extract_template_variables(self, template_content: str) -> List[str]:
        """Extract variable names from template content"""
        # Find all ${variable} patterns
        pattern = r'\$\{([^}]+)\}'
        variables = re.findall(pattern, template_content)
        
        # Also find $variable patterns (without braces)
        pattern2 = r'\$([a-zA-Z_][a-zA-Z0-9_]*)'
        variables.extend(re.findall(pattern2, template_content))
        
        # Remove duplicates and return sorted list
        return sorted(list(set(variables)))
    
    def _sanitize_template_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize template data to prevent injection attacks"""
        sanitized = {}
        
        for key, value in data.items():
            if isinstance(value, str):
                # Remove potentially dangerous characters
                sanitized_value = re.sub(r'[<>"\']', '', str(value))
                # Limit length to prevent abuse
                sanitized_value = sanitized_value[:1000]
                sanitized[key] = sanitized_value
            elif isinstance(value, (int, float, bool)):
                sanitized[key] = str(value)
            elif value is None:
                sanitized[key] = "N/A"
            else:
                sanitized[key] = str(value)[:1000]
        
        return sanitized
    
    def _get_default_template_data(self) -> Dict[str, Any]:
        """Get default data for template rendering"""
        return {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'user_name': 'User',
            'alert_type': 'Alert',
            'heart_rate': 'N/A',
            'oxygen_saturation': 'N/A',
            'system_name': 'Driver Assistant System'
        }
    
    def _parse_rendered_content(self, content: str) -> tuple[str, str]:
        """Parse rendered content to extract subject and body"""
        lines = content.strip().split('\n')
        
        # Look for Subject: line
        subject = "Driver Alert Notification"
        body_lines = []
        
        for i, line in enumerate(lines):
            if line.startswith('Subject:'):
                subject = line[8:].strip()
                body_lines = lines[i+1:]
                break
        else:
            # No subject line found, use entire content as body
            body_lines = lines
        
        body = '\n'.join(body_lines).strip()
        
        return subject, body
    
    def _has_required_sections(self, template: str) -> bool:
        """Check if template has required sections"""
        # Template should have some content
        if not template.strip():
            return False
        
        # Should have at least one template variable
        variables = self._extract_template_variables(template)
        return len(variables) > 0
    
    def _has_dangerous_content(self, template: str) -> bool:
        """Check for potentially dangerous content in template"""
        dangerous_patterns = [
            r'<script',
            r'javascript:',
            r'eval\(',
            r'exec\(',
            r'import\s+',
            r'__import__'
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, template, re.IGNORECASE):
                return True
        
        return False
    
    def _validate_template_variables(self, variables: List[str]) -> bool:
        """Validate template variable names"""
        valid_pattern = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')
        
        for var in variables:
            if not valid_pattern.match(var):
                return False
        
        return True