from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from datetime import datetime, timedelta
from .notification_service import create_notification, send_notification
from ..db import db
from ..models import User, Professional

scheduler = BackgroundScheduler()
scheduler.start()

def schedule_session_notifications(schedule):
    # Fetch user and professional based on user_id and professional_id
    user = User.query.get(schedule.user_id)
    professional = Professional.query.get(schedule.professional_id)

    if not user or not professional:
        # If user or professional is not found, log or return early
        print("User or Professional not found!")
        return

    start_time = schedule.start_time
    end_time = schedule.end_time
    professional_avatar = getattr(professional, 'avatar', None)
    user_avatar = getattr(user, 'avatar', None)

    # Notification timings
    notification_timings = [
        (start_time - timedelta(minutes=30), "30 minutes before"),
        (start_time - timedelta(minutes=10), "10 minutes before"),
        (start_time, "At session start"),
        (end_time, "At session end"),
    ]

    for time, description in notification_timings:
        if time > datetime.now():
            # Schedule user notifications
            if user:
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
                scheduler.add_job(
                    send_notification,
                    trigger=DateTrigger(run_date=time),
                    args=[user_notification.body, user_notification.user_id],
                    id=f'user_session_{schedule.id}_{description}',
                )

            if professional:
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
                scheduler.add_job(
                    send_notification,
                    trigger=DateTrigger(run_date=time),
                    args=[professional_notification.body, professional_notification.user_id],
                    id=f'professional_session_{schedule.id}_{description}',
                )
