from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
import random
from flask import Flask

from .notification_service import (
    affirmationdaily,
    generate_checkin_nudges,
    send_scheduled_notifications,
    generate_morning_notifications,
    generate_afternoon_notifications,
    generate_evening_notifications,
    generate_inactivity_nudges,
    generate_monthly_recheck_reminders,
    generate_fun_nudges,
    generate_goal_setting_nudge,
    generate_journaling_nudge,
    generate_vision_board_nudge,
    generate_mindfulness_nudge,
    delete_old_notifications
)
from .goal_service import update_goal_status_automatically

# ✅ Initialize Scheduler
scheduler = BackgroundScheduler()

def start_scheduler(app: Flask):
    """Start the scheduler and ensure jobs run inside Flask app context."""

    def job_wrapper(func):
        """Wrap job functions to ensure they run inside `app.app_context()`"""
        def wrapped_func():
            with app.app_context():
                func()
        return wrapped_func

    # ✅ Job: Update Goal Status (Every 1 Minute)
    scheduler.add_job(
        func=job_wrapper(update_goal_status_automatically),
        trigger=IntervalTrigger(minutes=5),
        id='goal_status_updater',
        name='Update goal statuses automatically',
        replace_existing=True
    )

    # ✅ Job: Send Scheduled Notifications (Every 1 Minute)
    scheduler.add_job(
        func=job_wrapper(send_scheduled_notifications),
        trigger=IntervalTrigger(minutes=5),
        id="scheduled_notifications",
        name="Send Scheduled Notifications",
        replace_existing=True
    )

    # ✅ Job: Daily Morning Motivation (7:30 AM)
    scheduler.add_job(
        func=job_wrapper(generate_morning_notifications),
        trigger=CronTrigger(hour=7, minute=30),
        id="morning_notifications",
        name="Send Morning Motivation Notifications",
        replace_existing=True
    )

    # ✅ Job: Afternoon Motivation (Mon, Wed, Fri at 12:00 PM)
    scheduler.add_job(
        func=job_wrapper(generate_afternoon_notifications),
        trigger=CronTrigger(day_of_week="mon,wed,fri", hour=14, minute=0),
        id="afternoon_notifications",
        name="Send Afternoon Motivation Notifications",
        replace_existing=True
    )

    # ✅ Job: Evening Motivation (Tue, Thu, Sat, Sun at 7:00 PM)
    scheduler.add_job(
        func=job_wrapper(generate_evening_notifications),
        trigger=CronTrigger(day_of_week="tue,thu,sat,sun", hour=14, minute=20),
        id="evening_notifications",
        name="Send Evening Motivation Notifications",
        replace_existing=True
    )

    # ✅ Job: Weekly Inactivity Nudge (Randomly on Tue or Thu at 6:00 PM)
    random_day = random.choice(["tue", "thu"])
    scheduler.add_job(
        func=job_wrapper(generate_inactivity_nudges),
        trigger=CronTrigger(day_of_week=random_day, hour=18, minute=0),
        id="inactivity_nudges",
        name="Send Weekly Inactivity Nudges",
        replace_existing=True
    )

    # ✅ Job: Monthly Recheck Reminder (1st Day of Month at 7:30 PM)
    scheduler.add_job(
        func=job_wrapper(generate_monthly_recheck_reminders),
        trigger=CronTrigger(day=1, hour=19, minute=30),
        id="monthly_recheck_reminder",
        name="Send Monthly Recheck Reminder",
        replace_existing=True
    )

    # ✅ Job: Weekly Fun Nudge (Randomly on Sat or Sun at 2:00 PM)
    random_day = random.choice(["sat", "sun"])
    scheduler.add_job(
        func=job_wrapper(generate_fun_nudges),
        trigger=CronTrigger(day_of_week=random_day, hour=14, minute=15),
        id="fun_nudges",
        name="Send Weekly Fun Nudges",
        replace_existing=True
    )

    # ✅ Job: Morning Check-In (Daily at 9:30 AM)
    scheduler.add_job(
        func=job_wrapper(lambda: generate_checkin_nudges("morning")),
        trigger=CronTrigger(hour=9, minute=30),
        id="morning_checkin",
        name="Send Morning Check-In Nudges",
        replace_existing=True
    )

    # ✅ Job: Evening Check-In (Daily at 8:30 PM)
    scheduler.add_job(
        func=job_wrapper(lambda: generate_checkin_nudges("evening")),
        trigger=CronTrigger(hour=20, minute=30),
        id="evening_checkin",
        name="Send Evening Check-In Nudges",
        replace_existing=True
    )

    # ✅ Job: Morning Affirmation (Daily at 7:00 AM)
    scheduler.add_job(
        func=job_wrapper(lambda: affirmationdaily("morning")),
        trigger=CronTrigger(hour=7, minute=0),
        id="morning_affirmation",
        name="Send Morning Affirmations",
        replace_existing=True
    )

    # ✅ Job: Afternoon Affirmation (Daily at 3:00 PM)
    scheduler.add_job(
        func=job_wrapper(lambda: affirmationdaily("afternoon")),
        trigger=CronTrigger(hour=15, minute=0),
        id="afternoon_affirmation",
        name="Send Afternoon Affirmations",
        replace_existing=True
    )

    # ✅ Job: Weekly Goal Setting (Sunday at 6:00 PM)
    scheduler.add_job(
        func=job_wrapper(generate_goal_setting_nudge),
        trigger=CronTrigger(day_of_week="sun", hour=18, minute=0),
        id="goal_setting",
        name="Send Weekly Goal-Setting Reminder",
        replace_existing=True
    )

    # ✅ Job: Morning Gratitude (Every other day at 7:15 AM)
    scheduler.add_job(
        func=job_wrapper(lambda: generate_journaling_nudge("morning")),
        trigger=CronTrigger(day="*/2", hour=7, minute=15),
        id="morning_journaling",
        name="Send Morning Gratitude Journaling Reminder",
        replace_existing=True
    )

    # ✅ Job: End-of-Day Reflection (Every other day at 9:00 PM)
    scheduler.add_job(
        func=job_wrapper(lambda: generate_journaling_nudge("evening")),
        trigger=CronTrigger(day="*/2", hour=21, minute=0),
        id="evening_journaling",
        name="Send End-of-Day Reflection Reminder",
        replace_existing=True
    )

    # ✅ Job: Vision Board Update (Saturday at 11:00 AM)
    scheduler.add_job(
        func=job_wrapper(generate_vision_board_nudge),
        trigger=CronTrigger(day_of_week="sat", hour=11, minute=0),
        id="vision_board",
        name="Send Weekly Vision Board Reminder",
        replace_existing=True
    )

    # ✅ Job: Morning Mindfulness (Daily at 8:30 AM)
    scheduler.add_job(
        func=job_wrapper(lambda: generate_mindfulness_nudge("morning")),
        trigger=CronTrigger(hour=8, minute=30),
        id="morning_mindfulness",
        name="Send Morning Mindfulness Reminder",
        replace_existing=True
    )

    # ✅ Job: Afternoon Mindfulness (Daily at 2:30 PM)
    scheduler.add_job(
        func=job_wrapper(lambda: generate_mindfulness_nudge("afternoon")),
        trigger=CronTrigger(hour=14, minute=30),
        id="afternoon_mindfulness",
        name="Send Afternoon Mindfulness Reminder",
        replace_existing=True
    )
    scheduler.add_job(
        func=job_wrapper(delete_old_notifications),
        trigger=CronTrigger(minute=0),  # This will run every hour, at minute 0
        id="delete_old_notifications",
        name="Delete Old Notifications",
        replace_existing=True
    )

    scheduler.start()
    print(f"Scheduler running: {scheduler.running}")
    print(f"Scheduled Jobs: {scheduler.get_jobs()}")

