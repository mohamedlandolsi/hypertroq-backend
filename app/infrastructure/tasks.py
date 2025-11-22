"""Example Celery tasks."""
from typing import Any
from app.core.celery_app import celery_app
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


@celery_app.task(name="send_email_task")
def send_email_task(to: str, subject: str, body: str) -> dict[str, str]:
    """
    Background task to send email.
    
    Args:
        to: Recipient email address
        subject: Email subject
        body: Email body content
    
    Returns:
        Status dictionary
    """
    logger.info(f"Sending email to {to} with subject: {subject}")
    # TODO: Implement actual email sending logic
    return {"status": "success", "to": to, "subject": subject}


@celery_app.task(name="process_ai_request")
def process_ai_request(prompt: str, user_id: str) -> dict[str, Any]:
    """
    Background task to process AI requests with Google Gemini.
    
    Args:
        prompt: User prompt for AI
        user_id: User ID making the request
    
    Returns:
        AI response dictionary
    """
    logger.info(f"Processing AI request for user {user_id}")
    # TODO: Implement Gemini AI integration
    return {"status": "success", "user_id": user_id, "response": "AI response here"}


@celery_app.task(name="cleanup_expired_tokens")
def cleanup_expired_tokens() -> dict[str, int]:
    """
    Periodic task to clean up expired tokens from database.
    
    Returns:
        Number of tokens cleaned up
    """
    logger.info("Cleaning up expired tokens")
    # TODO: Implement token cleanup logic
    return {"status": "success", "cleaned": 0}
