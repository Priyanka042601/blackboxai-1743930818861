import os
import json
import logging
from firebase_admin import credentials, initialize_app, messaging
from django.conf import settings

logger = logging.getLogger(__name__)

# Initialize Firebase
try:
    cred = credentials.Certificate(json.loads(settings.FIREBASE_CREDENTIALS))
    firebase_app = initialize_app(cred)
except Exception as e:
    logger.error(f"Firebase initialization failed: {str(e)}")
    raise

def send_push_notification(tokens, title, body, data=None):
    """
    Send push notification to multiple devices
    Args:
        tokens: List of device tokens
        title: Notification title
        body: Notification body
        data: Additional data payload (dict)
    """
    if not tokens:
        return 0
        
    try:
        message = messaging.MulticastMessage(
            notification=messaging.Notification(
                title=title,
                body=body
            ),
            tokens=tokens,
            data=data or {}
        )
        response = messaging.send_multicast(message)
        return response.success_count
    except Exception as e:
        logger.error(f"Error sending Firebase notification: {str(e)}")
        return 0