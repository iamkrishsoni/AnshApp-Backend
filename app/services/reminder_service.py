from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from datetime import datetime, timedelta
from .notification_service import send_notification,create_notification

scheduler = BackgroundScheduler()
scheduler.start()

def schedule_reminder_notifications(reminder):
    reminder_time = reminder.reminder_time
    notifications = [
        (reminder_time - timedelta(minutes=10), "10 minutes before"),
        (reminder_time - timedelta(seconds=30), "30 seconds before"),
        (reminder_time, "At reminder time")
    ]

    for time, description in notifications:
        if time > datetime.now():
            try:
                notification = create_notification(
                    title=f"Reminder: {description}",
                    description=f"This is a reminder scheduled for {reminder_time}.",
                    navigation="/reminders",  
                    body=reminder.reminder_text,
                    image=None,  
                    user_id=reminder.user_id,
                    type="reminder",
                    service="ReminderService",
                    status="pending",
                    live_until=reminder_time + timedelta(hours=1)  
                )

                scheduler.add_job(
                    send_notification,
                    trigger=DateTrigger(run_date=time),
                    args=[notification.body, notification.user_id],
                    id=f'reminder_{reminder.id}_{description}'
                )
            except Exception as e:
                print(f"Failed to schedule notification: {str(e)}")
