from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from datetime import datetime, timedelta
from .notification_service import send_realtime_notification, create_notification
from ..redis_config import redis_client  

# ✅ Initialize Scheduler
scheduler = BackgroundScheduler()
scheduler.start()

def schedule_reminder_notifications(reminder):
    """Schedule notifications at different intervals before a reminder time."""
    
    reminder_time = reminder.reminder_time
    user_id = reminder.user_id

    notifications = [
        (reminder_time - timedelta(minutes=10), "10 minutes before"),
        (reminder_time - timedelta(seconds=30), "30 seconds before"),
        (reminder_time, "At reminder time")
    ]

    for time, description in notifications:
        if time > datetime.now():  # ✅ Ensure the time is in the future
            try:
                # ✅ Create a notification in the database
                notification = create_notification(
                    title=f"Reminder: {description}",
                    description=f"This is a reminder scheduled for {reminder_time}.",
                    navigation="/reminders",  
                    body=reminder.reminder_text,
                    image=None,  
                    user_id=user_id,
                    type="reminder",
                    service="ReminderService",
                    status="pending",
                    live_until=reminder_time + timedelta(hours=1)
                )

                # ✅ Check if the user is online and send a real-time notification
                if redis_client.hexists("active_users", str(user_id)):
                    send_realtime_notification(user_id, notification)
                    print(f"📢 Sent real-time reminder to User {user_id} - {description}")
                else:
                    print(f"⚠️ User {user_id} is offline. Reminder saved for later.")

                # ✅ Schedule a delayed notification
                scheduler.add_job(
                    send_realtime_notification,  # ✅ Send notification when scheduled time arrives
                    trigger=DateTrigger(run_date=time),
                    args=[user_id, notification.title, notification.description],
                    id=f'reminder_{reminder.id}_{description}',
                    replace_existing=True
                )
                
                print(f"✅ Scheduled Reminder: '{description}' for User {user_id} at {time}")

            except Exception as e:
                print(f"❌ Failed to schedule notification: {str(e)}")
