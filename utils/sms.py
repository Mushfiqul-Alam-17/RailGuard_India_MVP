import os
import logging
from twilio.rest import Client

logger = logging.getLogger(__name__)

# Twilio configuration
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.environ.get("TWILIO_PHONE_NUMBER")

def send_sms_notification(to_phone_number, message):
    """
    Send SMS notification using Twilio
    
    Args:
        to_phone_number (str): Recipient's phone number
        message (str): SMS content
        
    Returns:
        bool: True if successful, False otherwise
    """
    # Check if Twilio credentials are available
    if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER]):
        logger.warning("Twilio credentials not configured. SMS notification skipped.")
        raise ValueError("Twilio credentials not configured")
    
    try:
        # Initialize Twilio client
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        # Send SMS
        sms = client.messages.create(
            body=message,
            from_=TWILIO_PHONE_NUMBER,
            to=to_phone_number
        )
        
        logger.info(f"SMS sent successfully to {to_phone_number}, SID: {sms.sid}")
        return True
    except Exception as e:
        logger.error(f"Failed to send SMS: {str(e)}")
        raise
