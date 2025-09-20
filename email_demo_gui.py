#!/usr/bin/env python3
"""
Email Service GUI Demo

A simple GUI demonstration of the enhanced email functionality
for the Driver Assistant system.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
from datetime import datetime
import json
import os

# Import email service components
try:
    from email_service import (
        EmailServiceManagerImpl, EmailConfig, UserData, AlertData,
        ProviderType, AuthMethod, AlertType, TestResult
    )
    EMAIL_SERVICE_AVAILABLE = True
except ImportError:
    messagebox.showerror("Error", "Email service not available")
    EMAIL_SERVICE_AVAILABLE = False
    exit(1)


class EmailDemoGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Driver Assistant - Email Service Demo")
        self.root.geometry("800x600")
        self.root.configure(bg='#f0f0f0')
        
        # Email service manager
        self.email_service = EmailServiceManagerImpl()
        self.current_config = None
        
        # Create GUI
        self.create_widgets()
        
    def create_widgets(self):
        """Create the GUI widgets"""
        # Title
        title_label = tk.Label(
            self.root, 
            text="Driver Assistant Email Service Demo", 
            font=('Arial', 16, 'bold'),
            bg='#f0f0f0'
        )
        title_label.pack(pady=10)
        
        # Create notebook for tabs
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Log tab (create first so log_text exists)
        log_frame = ttk.Frame(notebook)
        notebook.add(log_frame, text="Activity Log")
        self.create_log_tab(log_frame)
        
        # Configuration tab
        config_frame = ttk.Frame(notebook)
        notebook.add(config_frame, text="Email Configuration")
        self.create_config_tab(config_frame)
        
        # Testing tab
        test_frame = ttk.Frame(notebook)
        notebook.add(test_frame, text="Send Test Emails")
        self.create_test_tab(test_frame)
        
        # Status tab
        status_frame = ttk.Frame(notebook)
        notebook.add(status_frame, text="Service Status")
        self.create_status_tab(status_frame)
        
    def create_config_tab(self, parent):
        """Create email configuration tab"""
        # Provider selection
        provider_frame = ttk.LabelFrame(parent, text="Email Provider", padding=10)
        provider_frame.pack(fill='x', padx=10, pady=5)
        
        self.provider_var = tk.StringVar(value="gmail")
        providers = [("Gmail", "gmail"), ("Outlook", "outlook"), ("Yahoo", "yahoo"), ("Custom SMTP", "custom")]
        
        for text, value in providers:
            ttk.Radiobutton(
                provider_frame, 
                text=text, 
                variable=self.provider_var, 
                value=value,
                command=self.on_provider_change
            ).pack(side='left', padx=10)
        
        # Configuration fields
        config_frame = ttk.LabelFrame(parent, text="Configuration", padding=10)
        config_frame.pack(fill='x', padx=10, pady=5)
        
        # Email address
        ttk.Label(config_frame, text="Email Address:").grid(row=0, column=0, sticky='w', pady=2)
        self.email_entry = ttk.Entry(config_frame, width=40)
        self.email_entry.grid(row=0, column=1, sticky='ew', pady=2, padx=(10, 0))
        
        # Password
        ttk.Label(config_frame, text="Password/App Password:").grid(row=1, column=0, sticky='w', pady=2)
        self.password_entry = ttk.Entry(config_frame, width=40, show="*")
        self.password_entry.grid(row=1, column=1, sticky='ew', pady=2, padx=(10, 0))
        
        # SMTP Server
        ttk.Label(config_frame, text="SMTP Server:").grid(row=2, column=0, sticky='w', pady=2)
        self.smtp_server_entry = ttk.Entry(config_frame, width=40)
        self.smtp_server_entry.grid(row=2, column=1, sticky='ew', pady=2, padx=(10, 0))
        
        # SMTP Port
        ttk.Label(config_frame, text="SMTP Port:").grid(row=3, column=0, sticky='w', pady=2)
        self.smtp_port_entry = ttk.Entry(config_frame, width=40)
        self.smtp_port_entry.grid(row=3, column=1, sticky='ew', pady=2, padx=(10, 0))
        
        # TLS checkbox
        self.use_tls_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            config_frame, 
            text="Use TLS Encryption", 
            variable=self.use_tls_var
        ).grid(row=4, column=0, columnspan=2, sticky='w', pady=5)
        
        config_frame.columnconfigure(1, weight=1)
        
        # Buttons
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Button(
            button_frame, 
            text="Load Defaults", 
            command=self.load_defaults
        ).pack(side='left', padx=5)
        
        ttk.Button(
            button_frame, 
            text="Test Configuration", 
            command=self.test_configuration
        ).pack(side='left', padx=5)
        
        ttk.Button(
            button_frame, 
            text="Save Configuration", 
            command=self.save_configuration
        ).pack(side='left', padx=5)
        
        # Load defaults initially
        self.load_defaults()
        
    def create_test_tab(self, parent):
        """Create test email tab"""
        # Recipient
        recipient_frame = ttk.LabelFrame(parent, text="Test Email Recipient", padding=10)
        recipient_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(recipient_frame, text="Recipient Email:").pack(side='left')
        self.recipient_entry = ttk.Entry(recipient_frame, width=40)
        self.recipient_entry.pack(side='left', padx=10, fill='x', expand=True)
        
        # Alert type selection
        alert_frame = ttk.LabelFrame(parent, text="Alert Type", padding=10)
        alert_frame.pack(fill='x', padx=10, pady=5)
        
        self.alert_type_var = tk.StringVar(value="drowsiness")
        alert_types = [
            ("Drowsiness Alert", "drowsiness"),
            ("Vital Signs Alert", "vital_signs"),
            ("System Test", "test_email")
        ]
        
        for text, value in alert_types:
            ttk.Radiobutton(
                alert_frame, 
                text=text, 
                variable=self.alert_type_var, 
                value=value
            ).pack(side='left', padx=10)
        
        # User info
        user_frame = ttk.LabelFrame(parent, text="User Information", padding=10)
        user_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(user_frame, text="User Name:").grid(row=0, column=0, sticky='w', pady=2)
        self.user_name_entry = ttk.Entry(user_frame, width=30)
        self.user_name_entry.grid(row=0, column=1, sticky='ew', pady=2, padx=(10, 0))
        self.user_name_entry.insert(0, "Demo User")
        
        ttk.Label(user_frame, text="Heart Rate (BPM):").grid(row=1, column=0, sticky='w', pady=2)
        self.heart_rate_entry = ttk.Entry(user_frame, width=30)
        self.heart_rate_entry.grid(row=1, column=1, sticky='ew', pady=2, padx=(10, 0))
        self.heart_rate_entry.insert(0, "75")
        
        ttk.Label(user_frame, text="Oxygen Saturation (%):").grid(row=2, column=0, sticky='w', pady=2)
        self.oxygen_entry = ttk.Entry(user_frame, width=30)
        self.oxygen_entry.grid(row=2, column=1, sticky='ew', pady=2, padx=(10, 0))
        self.oxygen_entry.insert(0, "98.5")
        
        user_frame.columnconfigure(1, weight=1)
        
        # Send button
        send_frame = ttk.Frame(parent)
        send_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Button(
            send_frame, 
            text="Send Test Email", 
            command=self.send_test_email,
            style='Accent.TButton'
        ).pack(pady=10)
        
    def create_status_tab(self, parent):
        """Create service status tab"""
        self.status_text = scrolledtext.ScrolledText(
            parent, 
            height=20, 
            width=80,
            font=('Consolas', 10)
        )
        self.status_text.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Refresh button
        ttk.Button(
            parent, 
            text="Refresh Status", 
            command=self.refresh_status
        ).pack(pady=5)
        
        # Initial status
        self.refresh_status()
        
    def create_log_tab(self, parent):
        """Create activity log tab"""
        self.log_text = scrolledtext.ScrolledText(
            parent, 
            height=20, 
            width=80,
            font=('Consolas', 9)
        )
        self.log_text.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Clear button
        ttk.Button(
            parent, 
            text="Clear Log", 
            command=self.clear_log
        ).pack(pady=5)
        
        self.log("Email Service Demo Started")
        
    def on_provider_change(self):
        """Handle provider selection change"""
        self.load_defaults()
        
    def load_defaults(self):
        """Load default configuration for selected provider"""
        provider = self.provider_var.get()
        
        defaults = {
            "gmail": {
                "smtp_server": "smtp.gmail.com",
                "smtp_port": "587",
                "use_tls": True
            },
            "outlook": {
                "smtp_server": "smtp-mail.outlook.com", 
                "smtp_port": "587",
                "use_tls": True
            },
            "yahoo": {
                "smtp_server": "smtp.mail.yahoo.com",
                "smtp_port": "587", 
                "use_tls": True
            },
            "custom": {
                "smtp_server": "mail.example.com",
                "smtp_port": "587",
                "use_tls": True
            }
        }
        
        if provider in defaults:
            config = defaults[provider]
            self.smtp_server_entry.delete(0, tk.END)
            self.smtp_server_entry.insert(0, config["smtp_server"])
            
            self.smtp_port_entry.delete(0, tk.END)
            self.smtp_port_entry.insert(0, config["smtp_port"])
            
            self.use_tls_var.set(config["use_tls"])
            
        self.log(f"Loaded defaults for {provider}")
        
    def test_configuration(self):
        """Test the email configuration"""
        if not self.validate_config_fields():
            return
            
        def test_thread():
            try:
                config = self.create_email_config()
                self.log("Testing email configuration...")
                
                # Initialize service
                result = self.email_service.initialize(config)
                if result:
                    self.log("✓ Email service initialized successfully")
                    
                    # Test configuration
                    test_result = self.email_service.test_email_configuration()
                    
                    if test_result.success:
                        self.log("✓ Email configuration test passed!")
                        messagebox.showinfo("Success", "Email configuration is working correctly!")
                    else:
                        error_msg = "\\n".join(test_result.error_messages)
                        self.log(f"✗ Configuration test failed: {error_msg}")
                        messagebox.showwarning("Test Failed", f"Configuration test failed:\\n{error_msg}")
                else:
                    self.log("✗ Failed to initialize email service")
                    messagebox.showerror("Error", "Failed to initialize email service")
                    
            except Exception as e:
                self.log(f"✗ Configuration test error: {str(e)}")
                messagebox.showerror("Error", f"Configuration test failed:\\n{str(e)}")
        
        threading.Thread(target=test_thread, daemon=True).start()
        
    def save_configuration(self):
        """Save the current configuration"""
        if not self.validate_config_fields():
            return
            
        try:
            config = self.create_email_config()
            
            # Initialize service
            result = self.email_service.initialize(config)
            if result:
                self.current_config = config
                self.log("✓ Configuration saved and applied")
                messagebox.showinfo("Success", "Email configuration saved successfully!")
            else:
                self.log("✗ Failed to save configuration")
                messagebox.showerror("Error", "Failed to save configuration")
                
        except Exception as e:
            self.log(f"✗ Save configuration error: {str(e)}")
            messagebox.showerror("Error", f"Failed to save configuration:\\n{str(e)}")
            
    def send_test_email(self):
        """Send a test email"""
        if not self.current_config:
            messagebox.showwarning("Warning", "Please save a valid configuration first")
            return
            
        recipient = self.recipient_entry.get().strip()
        if not recipient:
            messagebox.showwarning("Warning", "Please enter a recipient email address")
            return
            
        def send_thread():
            try:
                # Create user data
                user_data = UserData(
                    name=self.user_name_entry.get() or "Demo User",
                    email=recipient,
                    user_id="demo_user"
                )
                
                # Create alert data
                alert_type = AlertType(self.alert_type_var.get())
                alert_data = AlertData(
                    alert_type=alert_type,
                    timestamp=datetime.now(),
                    heart_rate=int(self.heart_rate_entry.get() or 75),
                    oxygen_saturation=float(self.oxygen_entry.get() or 98.5)
                )
                
                self.log(f"Sending {alert_type.value} email to {recipient}...")
                
                # Send email
                result = self.email_service.send_alert_email(user_data, alert_data)
                
                if result.success:
                    self.log(f"✓ Email sent successfully! ID: {result.email_id}")
                    messagebox.showinfo("Success", "Test email sent successfully!")
                else:
                    self.log(f"✗ Email sending failed: {result.message}")
                    messagebox.showerror("Error", f"Failed to send email:\\n{result.message}")
                    
            except Exception as e:
                self.log(f"✗ Send email error: {str(e)}")
                messagebox.showerror("Error", f"Failed to send email:\\n{str(e)}")
        
        threading.Thread(target=send_thread, daemon=True).start()
        
    def refresh_status(self):
        """Refresh service status display"""
        self.status_text.delete(1.0, tk.END)
        
        try:
            status = self.email_service.get_service_status()
            
            self.status_text.insert(tk.END, "=== EMAIL SERVICE STATUS ===\\n\\n")
            
            for key, value in status.items():
                if isinstance(value, list):
                    self.status_text.insert(tk.END, f"{key.replace('_', ' ').title()}:\\n")
                    for item in value:
                        self.status_text.insert(tk.END, f"  - {item}\\n")
                else:
                    self.status_text.insert(tk.END, f"{key.replace('_', ' ').title()}: {value}\\n")
            
            self.status_text.insert(tk.END, "\\n=== CONFIGURATION ===\\n\\n")
            if self.current_config:
                self.status_text.insert(tk.END, f"Provider: {self.current_config.provider.value}\\n")
                self.status_text.insert(tk.END, f"SMTP Server: {self.current_config.smtp_server}\\n")
                self.status_text.insert(tk.END, f"SMTP Port: {self.current_config.smtp_port}\\n")
                self.status_text.insert(tk.END, f"Use TLS: {self.current_config.use_tls}\\n")
                self.status_text.insert(tk.END, f"Sender Email: {self.current_config.sender_email}\\n")
            else:
                self.status_text.insert(tk.END, "No configuration loaded\\n")
                
        except Exception as e:
            self.status_text.insert(tk.END, f"Error getting status: {str(e)}\\n")
            
    def validate_config_fields(self):
        """Validate configuration fields"""
        if not self.email_entry.get().strip():
            messagebox.showwarning("Warning", "Please enter an email address")
            return False
            
        if not self.password_entry.get().strip():
            messagebox.showwarning("Warning", "Please enter a password")
            return False
            
        if not self.smtp_server_entry.get().strip():
            messagebox.showwarning("Warning", "Please enter an SMTP server")
            return False
            
        try:
            port = int(self.smtp_port_entry.get())
            if not (1 <= port <= 65535):
                raise ValueError()
        except ValueError:
            messagebox.showwarning("Warning", "Please enter a valid SMTP port (1-65535)")
            return False
            
        return True
        
    def create_email_config(self):
        """Create EmailConfig from form fields"""
        return EmailConfig(
            provider=ProviderType(self.provider_var.get()),
            smtp_server=self.smtp_server_entry.get().strip(),
            smtp_port=int(self.smtp_port_entry.get()),
            use_tls=self.use_tls_var.get(),
            sender_email=self.email_entry.get().strip(),
            sender_password=self.password_entry.get().strip(),
            auth_method=AuthMethod.APP_PASSWORD
        )
        
    def log(self, message):
        """Add message to activity log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\\n")
        self.log_text.see(tk.END)
        
    def clear_log(self):
        """Clear the activity log"""
        self.log_text.delete(1.0, tk.END)
        self.log("Log cleared")


def main():
    """Main function"""
    if not EMAIL_SERVICE_AVAILABLE:
        return
        
    root = tk.Tk()
    app = EmailDemoGUI(root)
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("\\nDemo interrupted by user")


if __name__ == "__main__":
    main()