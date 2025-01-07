from ..db import db
from ..models import Notifications
from datetime import datetime

def create_notification(
    title,
    description,
    navigation,
    body,
    image,
    user_id,
    type,
    service,
    status='pending',
    live_until=None
):
    try:
        # Create a new Notification object
        new_notification = Notifications(
            title=title,
            description=description,
            navigation=navigation,
            body=body,
            image=image,
            user_id=user_id,
            type=type,
            service=service,
            status=status,
            live_until=live_until
        )

        # Add to the session and commit
        db.session.add(new_notification)
        db.session.commit()

        return new_notification
    except Exception as e:
        db.session.rollback()  # Rollback if there's an error
        raise ValueError(f"Error creating notification: {str(e)}")

def send_notification(reminder_text, user_id):
    print(f"Notification for User {user_id}: {reminder_text}")
    
