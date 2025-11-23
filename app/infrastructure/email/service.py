"""
Email Service for sending notifications.

Handles email sending via SMTP with support for HTML templates.
"""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending email notifications.
    
    Uses SMTP configuration from settings to send emails.
    Falls back gracefully if SMTP is not configured.
    """
    
    def __init__(self):
        """Initialize email service with SMTP settings."""
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_email = settings.EMAILS_FROM_EMAIL or self.smtp_user
        self.from_name = settings.EMAILS_FROM_NAME or "HypertroQ"
        
        # Check if SMTP is configured
        self.is_configured = all([
            self.smtp_host,
            self.smtp_port,
            self.smtp_user,
            self.smtp_password,
        ])
        
        if not self.is_configured:
            logger.warning(
                "Email service not fully configured. Emails will not be sent. "
                "Set SMTP_HOST, SMTP_PORT, SMTP_USER, and SMTP_PASSWORD in .env"
            )
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
    ) -> bool:
        """Send an email.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML email body
            text_content: Optional plain text fallback
            
        Returns:
            bool: True if sent successfully, False otherwise
        """
        if not self.is_configured:
            logger.warning(
                f"Skipping email to {to_email} - SMTP not configured. "
                f"Subject: {subject}"
            )
            return False
        
        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["From"] = f"{self.from_name} <{self.from_email}>"
            msg["To"] = to_email
            msg["Subject"] = subject
            
            # Add text/plain part if provided
            if text_content:
                text_part = MIMEText(text_content, "plain")
                msg.attach(text_part)
            
            # Add text/html part
            html_part = MIMEText(html_content, "html")
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {to_email}: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False
    
    async def send_password_change_email(
        self,
        to_email: str,
        user_name: str,
    ) -> bool:
        """Send password change confirmation email.
        
        Args:
            to_email: User's email address
            user_name: User's full name
            
        Returns:
            bool: True if sent successfully
        """
        subject = "Password Changed - HypertroQ"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .container {{
                    background-color: #ffffff;
                    border: 1px solid #e0e0e0;
                    border-radius: 8px;
                    padding: 30px;
                    margin: 20px 0;
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 30px;
                }}
                .logo {{
                    font-size: 32px;
                    font-weight: bold;
                    color: #6366f1;
                    margin-bottom: 10px;
                }}
                .content {{
                    margin: 20px 0;
                }}
                .alert {{
                    background-color: #fef3c7;
                    border-left: 4px solid #f59e0b;
                    padding: 15px;
                    margin: 20px 0;
                    border-radius: 4px;
                }}
                .footer {{
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #e0e0e0;
                    font-size: 12px;
                    color: #666;
                    text-align: center;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">HypertroQ</div>
                </div>
                
                <div class="content">
                    <p>Hi {user_name},</p>
                    
                    <p>This email confirms that your password was successfully changed.</p>
                    
                    <div class="alert">
                        <strong>⚠️ Did not make this change?</strong><br>
                        If you did not change your password, please contact our support team immediately 
                        at support@hypertroq.com or reset your password right away.
                    </div>
                    
                    <p>For your security:</p>
                    <ul>
                        <li>Never share your password with anyone</li>
                        <li>Use a unique password for each service</li>
                        <li>Consider using a password manager</li>
                    </ul>
                    
                    <p>Stay strong,<br>
                    The HypertroQ Team</p>
                </div>
                
                <div class="footer">
                    <p>© 2025 HypertroQ. All rights reserved.</p>
                    <p>This is an automated notification. Please do not reply to this email.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Hi {user_name},

        This email confirms that your password was successfully changed.

        ⚠️ DID NOT MAKE THIS CHANGE?
        If you did not change your password, please contact our support team immediately 
        at support@hypertroq.com or reset your password right away.

        For your security:
        - Never share your password with anyone
        - Use a unique password for each service
        - Consider using a password manager

        Stay strong,
        The HypertroQ Team

        ---
        © 2025 HypertroQ. All rights reserved.
        This is an automated notification. Please do not reply to this email.
        """
        
        return await self.send_email(
            to_email=to_email,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
        )
    
    async def send_deletion_request_email(
        self,
        to_email: str,
        user_name: str,
        deletion_date: str,
        cancellation_link: str,
    ) -> bool:
        """Send account deletion request confirmation email.
        
        Args:
            to_email: User's email address
            user_name: User's full name
            deletion_date: Date when account will be deleted (formatted)
            cancellation_link: Link to cancel deletion
            
        Returns:
            bool: True if sent successfully
        """
        subject = "Account Deletion Requested - HypertroQ"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .container {{
                    background-color: #ffffff;
                    border: 1px solid #e0e0e0;
                    border-radius: 8px;
                    padding: 30px;
                    margin: 20px 0;
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 30px;
                }}
                .logo {{
                    font-size: 32px;
                    font-weight: bold;
                    color: #6366f1;
                    margin-bottom: 10px;
                }}
                .content {{
                    margin: 20px 0;
                }}
                .alert {{
                    background-color: #fee2e2;
                    border-left: 4px solid #ef4444;
                    padding: 15px;
                    margin: 20px 0;
                    border-radius: 4px;
                }}
                .button {{
                    display: inline-block;
                    padding: 12px 24px;
                    background-color: #6366f1;
                    color: #ffffff;
                    text-decoration: none;
                    border-radius: 6px;
                    margin: 20px 0;
                    font-weight: 600;
                }}
                .button:hover {{
                    background-color: #4f46e5;
                }}
                .footer {{
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #e0e0e0;
                    font-size: 12px;
                    color: #666;
                    text-align: center;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">HypertroQ</div>
                </div>
                
                <div class="content">
                    <p>Hi {user_name},</p>
                    
                    <p>We received a request to delete your HypertroQ account.</p>
                    
                    <div class="alert">
                        <strong>⏰ Grace Period Active</strong><br>
                        Your account will be permanently deleted on <strong>{deletion_date}</strong> (30 days from now).
                        You can cancel this deletion at any time before that date.
                    </div>
                    
                    <p>What happens during the grace period:</p>
                    <ul>
                        <li>Your account remains accessible</li>
                        <li>You can cancel deletion at any time</li>
                        <li>Your data is safe until the deletion date</li>
                        <li>After 30 days, all data will be permanently deleted</li>
                    </ul>
                    
                    <p><strong>Did not request this?</strong></p>
                    <p>If you did not request account deletion, please cancel immediately and change your password.</p>
                    
                    <div style="text-align: center;">
                        <a href="{cancellation_link}" class="button">Cancel Account Deletion</a>
                    </div>
                    
                    <p>Or copy this link: {cancellation_link}</p>
                    
                    <p>We're sorry to see you go. If there's anything we can do to improve, 
                    please let us know at feedback@hypertroq.com</p>
                    
                    <p>Stay strong,<br>
                    The HypertroQ Team</p>
                </div>
                
                <div class="footer">
                    <p>© 2025 HypertroQ. All rights reserved.</p>
                    <p>This is an automated notification. Please do not reply to this email.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Hi {user_name},

        We received a request to delete your HypertroQ account.

        ⏰ GRACE PERIOD ACTIVE
        Your account will be permanently deleted on {deletion_date} (30 days from now).
        You can cancel this deletion at any time before that date.

        What happens during the grace period:
        - Your account remains accessible
        - You can cancel deletion at any time
        - Your data is safe until the deletion date
        - After 30 days, all data will be permanently deleted

        DID NOT REQUEST THIS?
        If you did not request account deletion, please cancel immediately and change your password.

        Cancel Account Deletion:
        {cancellation_link}

        We're sorry to see you go. If there's anything we can do to improve, 
        please let us know at feedback@hypertroq.com

        Stay strong,
        The HypertroQ Team

        ---
        © 2025 HypertroQ. All rights reserved.
        This is an automated notification. Please do not reply to this email.
        """
        
        return await self.send_email(
            to_email=to_email,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
        )
    
    async def send_deletion_cancelled_email(
        self,
        to_email: str,
        user_name: str,
    ) -> bool:
        """Send account deletion cancellation confirmation email.
        
        Args:
            to_email: User's email address
            user_name: User's full name
            
        Returns:
            bool: True if sent successfully
        """
        subject = "Account Deletion Cancelled - HypertroQ"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .container {{
                    background-color: #ffffff;
                    border: 1px solid #e0e0e0;
                    border-radius: 8px;
                    padding: 30px;
                    margin: 20px 0;
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 30px;
                }}
                .logo {{
                    font-size: 32px;
                    font-weight: bold;
                    color: #6366f1;
                    margin-bottom: 10px;
                }}
                .content {{
                    margin: 20px 0;
                }}
                .success {{
                    background-color: #d1fae5;
                    border-left: 4px solid #10b981;
                    padding: 15px;
                    margin: 20px 0;
                    border-radius: 4px;
                }}
                .footer {{
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #e0e0e0;
                    font-size: 12px;
                    color: #666;
                    text-align: center;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">HypertroQ</div>
                </div>
                
                <div class="content">
                    <p>Hi {user_name},</p>
                    
                    <div class="success">
                        <strong>✓ Account Deletion Cancelled</strong><br>
                        Your account deletion request has been cancelled. Your account and all data are safe.
                    </div>
                    
                    <p>Welcome back! We're glad you're staying with us.</p>
                    
                    <p>Your account is now fully active and you can continue using HypertroQ as normal.</p>
                    
                    <p>Keep crushing your goals,<br>
                    The HypertroQ Team</p>
                </div>
                
                <div class="footer">
                    <p>© 2025 HypertroQ. All rights reserved.</p>
                    <p>This is an automated notification. Please do not reply to this email.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Hi {user_name},

        ✓ ACCOUNT DELETION CANCELLED
        Your account deletion request has been cancelled. Your account and all data are safe.

        Welcome back! We're glad you're staying with us.

        Your account is now fully active and you can continue using HypertroQ as normal.

        Keep crushing your goals,
        The HypertroQ Team

        ---
        © 2025 HypertroQ. All rights reserved.
        This is an automated notification. Please do not reply to this email.
        """
        
        return await self.send_email(
            to_email=to_email,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
        )
