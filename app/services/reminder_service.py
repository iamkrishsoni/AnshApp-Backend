from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from datetime import datetime, timedelta
from .notification_service import send_notification

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
            scheduler.add_job(
                send_notification,
                trigger=DateTrigger(run_date=time),
                args=[reminder.reminder_text, reminder.user_id],
                id=f'reminder_{reminder.id}_{description}'
            )
