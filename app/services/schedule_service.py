from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from datetime import datetime, timedelta
from .notification_service import create_notification, send_realtime_notification
from ..db import db
from ..models import User, Professional
from ..redis_config import redis_client  # ✅ Import Redis to check if the user is online

# ✅ Initialize Scheduler
scheduler = BackgroundScheduler()
scheduler.start()

def schedule_session_notifications(schedule):
    """Schedule notifications for a user and professional before and during their session."""
    
    # ✅ Fetch user and professional
    user = User.query.get(schedule.user_id)
    professional = Professional.query.get(schedule.professional_id)

    if not user or not professional:
        print("❌ User or Professional not found!")
        return

    start_time = schedule.start_time
    end_time = schedule.end_time
    professional_avatar = getattr(professional, 'avatar', None)
    user_avatar = getattr(user, 'avatar', None)

    # ✅ Notification timings (30 min before, 10 min before, session start, session end)
    notification_timings = [
        (start_time - timedelta(minutes=30), "30 minutes before"),
        (start_time - timedelta(minutes=10), "10 minutes before"),
        (start_time, "At session start"),
        (end_time, "At session end"),
    ]

    for time, description in notification_timings:
        if time > datetime.utcnow():  # ✅ Ensure only future notifications are scheduled
            try:
                # ✅ Schedule User Notification
                user_notification = create_notification(
                    title=f"Your session with {professional.user_name} is scheduled",
                    description=f"Time remaining: {description}",
                    navigation="/sessions/join",
                    body=f"Your session with {professional.user_name} starts {description}.",
                    image=professional_avatar,
                    user_id=user.id,
                    type="session_reminder",
                    service="ScheduleService",
                    status="pending",
                    live_until=end_time,
                )

                # ✅ Schedule Professional Notification
                professional_notification = create_notification(
                    title=f"Session with {user.user_name} is scheduled",
                    description=f"Time remaining: {description}",
                    navigation="/sessions/details",
                    body=f"Session with {user.user_name} starts {description}.",
                    image=user_avatar,
                    user_id=professional.id,
                    type="session_reminder",
                    service="ScheduleService",
                    status="pending",
                    live_until=end_time,
                )

                # ✅ Check if User is Online & Send Real-Time Notification
                if redis_client.hexists("active_users", str(user.id)):
                    send_realtime_notification(user.id, user_notification.title, user_notification.description)
                    print(f"📢 Sent real-time session reminder to User {user.id} - {description}")

                # ✅ Check if Professional is Online & Send Real-Time Notification
                if redis_client.hexists("active_users", str(professional.id)):
                    send_realtime_notification(professional.id, professional_notification.title, professional_notification.description)
                    print(f"📢 Sent real-time session reminder to Professional {professional.id} - {description}")

                # ✅ Schedule Delayed Notifications for Users Who Are Offline
                scheduler.add_job(
                    send_realtime_notification,
                    trigger=DateTrigger(run_date=time),
                    args=[user.id, user_notification.title, user_notification.description],
                    id=f'user_session_{schedule.id}_{description}',
                    replace_existing=True
                )

                scheduler.add_job(
                    send_realtime_notification,
                    trigger=DateTrigger(run_date=time),
                    args=[professional.id, professional_notification.title, professional_notification.description],
                    id=f'professional_session_{schedule.id}_{description}',
                    replace_existing=True
                )

                print(f"✅ Scheduled Session Reminder: '{description}' for User {user.id} & Professional {professional.id} at {time}")

            except Exception as e:
                print(f"❌ Failed to schedule session notification: {str(e)}")
