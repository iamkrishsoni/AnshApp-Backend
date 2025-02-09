from ..db import db
from flask import current_app
from ..models import Notifications, User  # Import user model
from datetime import datetime, timedelta
from ..socketio import send_realtime_notification
from ..redis_config import redis_client
from random import choice

def create_notification(
    title,
    description,
    navigation="",
    body="",
    image="",
    user_id=None,  
    type="info",
    service="Anshap",
    status="pending",
    live_until=None,
    all_users=False  # ✅ Flag for common notifications
):
    try:
        notifications = []

        if all_users:
            # ✅ Fetch all user IDs
            users = User.query.with_entities(User.id).all()
            user_ids = [user.id for user in users]

            for uid in user_ids:
                new_notification = Notifications(
                    title=title,
                    description=description,
                    navigation=navigation,
                    body=body,
                    image=image,
                    user_id=uid,
                    type=type,
                    service=service,
                    status=status,
                    live_until=live_until
                )
                db.session.add(new_notification)
                notifications.append(new_notification)
        else:
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
            db.session.add(new_notification)
            notifications.append(new_notification)

        db.session.commit()

        return notifications
    except Exception as e:
        db.session.rollback()
        raise ValueError(f"Error creating notification: {str(e)}")

def send_scheduled_notifications():
    """Send pending scheduled notifications to users."""
    with current_app.app_context(): 
        try:
            # ✅ Fetch pending notifications
            pending_notifications = Notifications.query.filter(
                Notifications.status == "pending",
                Notifications.live_until <= datetime.utcnow()
            ).all()

            for notification in pending_notifications:
                user_id = notification.user_id

                # ✅ Send real-time notification if the user is online
                if redis_client.hexists("active_users", str(user_id)):
                    send_realtime_notification(user_id, notification.title, notification.description)
                    print(f"📢 Sent real-time scheduled notification to User {user_id}")

                # ✅ Mark notification as sent
                notification.status = "sent"

            db.session.commit()
            print(f"✅ Sent {len(pending_notifications)} scheduled notifications.")

        except Exception as e:
            db.session.rollback()
            print(f"❌ Error sending scheduled notifications: {str(e)}")
                 
def generate_morning_notifications():
    messages = [
        "Start your day strong—your mental fitness journey awaits! 💪",
        "New day, new opportunities! Stay positive and keep moving forward. ☀️",
        "Good morning! Today is a fresh start—embrace it with positivity. 😊",
        "Rise and shine! Your mental fitness journey continues today. ✨",
        "Make today amazing! Keep working on becoming the best version of yourself. 🚀",
    ]

    # ✅ Select a random message
    message = choice(messages)

    # ✅ Create notifications for all users using the existing create_notification function
    create_notification(
        title="Morning Motivation 🌞",
        description=message,
        all_users=True,  # Flag to send to all users
        type="info",
        service="Daily Motivation",
        status="pending",
        live_until=datetime.utcnow(),
        navigation="",  # Default value for navigation
        body="",        # Default value for body
        image=""        # Default value for image
    )

    print(f"📢 Morning notifications sent to all users.")

def generate_afternoon_notifications():
    """Generate and send midday motivation notifications (Mon, Wed, Fri at 12:00 PM - 1:30 PM)"""

    # ✅ List of midday motivation messages
    messages = [
        "Take a mindful break—explore Anshap to recharge! 🌿",
        "Your well-being matters! Take a moment to breathe and refresh. 😌",
        "Midday reset: Pause, reflect, and continue your day with positivity! ☀️",
        "Anshap Tip: A quick meditation can boost your focus. Try one now! 🧘‍♂️",
        "Small breaks = Big energy! Recharge with a moment of mindfulness. 🚀",
    ]

    # ✅ Select a random message
    message = choice(messages)

    # ✅ Fetch all users
    create_notification(
        title="Midday Motivation ☀️",
        description=message,
        all_users=True,  # Flag to send to all users
        type="motivation",
        service="Daily Motivation",
        status="pending",
        live_until=datetime.utcnow(),
        navigation="",  # Default value for navigation
        body="",        # Default value for body
        image=""        # Default value for image
    )

def generate_evening_notifications():
    """Generate and send wind-down encouragement notifications (Tue, Thu, Sat, Sun at 7:00 PM - 9:00 PM)"""

    # ✅ List of evening encouragement messages
    messages = [
        "Reflect on your day—your journey continues with Anshap! 🌙",
        "Take a deep breath—end your day with gratitude and positivity. ✨",
        "Unwind and recharge—tomorrow is a new opportunity! 🌟",
        "Spend a moment in mindfulness—peace comes from within. 🧘‍♂️",
        "Good night! You’ve made progress today—keep going! 🚀",
    ]

    # ✅ Select a random message
    message = choice(messages)

    create_notification(
        title="Evening Reflection 🌙",
        description=message,
        all_users=True,  # Flag to send to all users
        type="motivation",
        service="Daily Motivation",
        status="pending",
        live_until=datetime.utcnow(),
        navigation="",  # Default value for navigation
        body="",        # Default value for body
        image=""        # Default value for image
    )

    print(f"📢 Evening motivation notifications sent to all users.")

def generate_inactivity_nudges():
    """Generate and send inactivity nudges to users who have been inactive for a week."""
    messages = [
        "It’s been a while! Let’s reconnect with your mental fitness goals today. 💪",
        "We miss you! Come back and check out what's new on Anshap. 🚀",
        "A little progress each day adds up to big results—let's start today! ✨",
        "Your journey to mental fitness continues! Let’s take the next step. 😊",
        "Your well-being is important—come back and take time for yourself. 🌱",
    ]

    message = choice(messages)
    last_active_threshold = datetime.utcnow() - timedelta(days=7)
    inactive_users = User.query.filter(User.last_active < last_active_threshold).all()
    user_ids = [user.id for user in inactive_users]

    if not user_ids:
        print("✅ No inactive users found this week. Skipping inactivity nudges.")
        return

    for user_id in user_ids:
        create_notification(
            title="Time to Reconnect! 🔄",
            description=message,
            user_id=user_id,
            type="inactivity_nudge",
            service="Weekly Nudge",
            status="pending",
            live_until=datetime.utcnow()
        )

        if redis_client.hexists("active_users", str(user_id)):
            send_realtime_notification(user_id, "Time to Reconnect! 🔄", message)
            print(f"📢 Sent real-time inactivity nudge to User {user_id}")

    print(f"📢 Weekly inactivity nudges sent to {len(user_ids)} users.")
    return user_ids

def generate_monthly_recheck_reminders():
    """Generate and send a mental fitness recheck reminder on the 1st of every month."""
    message = "Time for a mental fitness check-up! Reassess your journey today. 💪"
    users = User.query.with_entities(User.id).all()
    user_ids = [user.id for user in users]

    for user_id in user_ids:
        create_notification(
            title="Monthly Recheck Reminder 📅",
            description=message,
            user_id=user_id,
            type="recheck_reminder",
            service="Monthly Checkup",
            status="pending",
            live_until=datetime.utcnow()
        )

        if redis_client.hexists("active_users", str(user_id)):
            send_realtime_notification(user_id, "Monthly Recheck Reminder 📅", message)
            print(f"📢 Sent real-time monthly recheck reminder to User {user_id}")

    print(f"📢 Monthly recheck reminders sent to {len(user_ids)} users.")
    return user_ids

def generate_fun_nudges():
    """Generate and send fun nudges on Saturday OR Sunday at 2:00 PM."""
    messages = [
        "It’s vibe check time! Discover something new about yourself today. 🎭",
        "Weekend energy! Try a new activity on Anshap and refresh your mind. 🚀",
        "Let’s make today fun! Explore mindfulness exercises on Anshap. 🎉",
        "Take a moment for yourself—do something that makes you happy today! 😊",
        "Self-discovery starts with a single step—what will you explore today? 🔍",
    ]

    message = choice(messages)
    users = User.query.with_entities(User.id).all()
    user_ids = [user.id for user in users]

    for user_id in user_ids:
        create_notification(
            title="Weekly Fun Nudge 🎭",
            description=message,
            user_id=user_id,
            type="fun_nudge",
            service="Weekly Engagement",
            status="pending",
            live_until=datetime.utcnow()
        )

        if redis_client.hexists("active_users", str(user_id)):
            send_realtime_notification(user_id, "Weekly Fun Nudge 🎭", message)
            print(f"📢 Sent real-time fun nudge to User {user_id}")

    print(f"📢 Weekly fun nudges sent to {len(user_ids)} users.")
    return user_ids

def generate_checkin_nudges(time_of_day):
    """Generate and send check-in nudges (Morning at 9:30 AM, Evening at 8:30 PM)."""
    morning_messages = [
        "How are you feeling today? Connect with a Comfort Buddy now. ☀️",
        "Start your day strong! Set a positive intention for today. 🌟",
        "Check in with yourself: What’s your mood this morning? 😊",
        "A fresh start awaits! Let’s begin the day with self-awareness. 💙",
        "Take a deep breath and set a goal for your mental well-being today. 🧘‍♂️",
    ]

    evening_messages = [
        "Reflect on your day—how did you feel? Share with a Comfort Buddy. 🌙",
        "End your day with a moment of gratitude. What went well today? ✨",
        "How did today make you feel? Let’s check in and process it. 😊",
        "Unwind and relax—your well-being matters. Take time for yourself. 🌿",
        "Self-reflection helps growth. How would you describe today in one word? 🔄",
    ]

    messages = morning_messages if time_of_day == "morning" else evening_messages
    message = choice(messages)
    users = User.query.with_entities(User.id).all()
    user_ids = [user.id for user in users]

    for user_id in user_ids:
        create_notification(
            title=f"Daily Check-In: {time_of_day.capitalize()} ☀️" if time_of_day == "morning" else "Daily Check-In: Evening 🌙",
            description=message,
            user_id=user_id,
            type="checkin_nudge",
            service="Daily Check-In",
            status="pending",
            live_until=datetime.utcnow()
        )

        if redis_client.hexists("active_users", str(user_id)):
            send_realtime_notification(user_id, f"Daily Check-In: {time_of_day.capitalize()} ☀️", message)
            print(f"📢 Sent real-time {time_of_day} check-in nudge to User {user_id}")

    print(f"📢 {time_of_day.capitalize()} check-in nudges sent to {len(user_ids)} users.")
    return user_ids

def affirmationdaily(time_of_day):
    """Generate and send affirmations (Morning at 7:00 AM, Afternoon at 3:00 PM)."""
    morning_affirmations = [
        "Start your day strong—look in the mirror and repeat today’s affirmation. ☀️",
        "I am ready to take on the challenges of today with confidence and grace. 💪",
        "Today is a new beginning filled with endless possibilities. 🌟",
        "I am strong, capable, and worthy of success. 💙",
        "I choose to embrace positivity and kindness today. 😊",
    ]

    afternoon_affirmations = [
        "You are doing amazing—keep pushing forward! 🚀",
        "Take a deep breath, reset, and remind yourself: You got this! 😌",
        "Every small step counts—celebrate your progress! 🎉",
        "I am filled with energy and motivation to finish the day strong. ⚡",
        "I am resilient, and I overcome challenges with ease. 🔥",
    ]

    affirmations = morning_affirmations if time_of_day == "morning" else afternoon_affirmations
    message = choice(affirmations)
    users = User.query.with_entities(User.id).all()
    user_ids = [user.id for user in users]

    for user_id in user_ids:
        create_notification(
            title=f"Morning Affirmation ☀️" if time_of_day == "morning" else "Afternoon Affirmation ⚡",
            description=message,
            user_id=user_id,
            type="affirmation",
            service="Daily Affirmation",
            status="pending",
            live_until=datetime.utcnow()
        )

        if redis_client.hexists("active_users", str(user_id)):
            send_realtime_notification(user_id, f"Morning Affirmation ☀️" if time_of_day == "morning" else "Afternoon Affirmation ⚡", message)
            print(f"📢 Sent real-time {time_of_day} affirmation to User {user_id}")

    print(f"📢 {time_of_day.capitalize()} affirmations sent to {len(user_ids)} users.")
    return user_ids

def generate_goal_setting_nudge():
    """Generate and send a goal-setting reminder every Sunday at 6:00 PM."""
    message = "Set your goals for the week—small steps, big wins! 🎯"
    users = User.query.with_entities(User.id).all()
    notifications = []

    for user in users:
        create_notification(
            title="Weekly Goal Setting 📝",
            description=message,
            user_id=user.id,
            type="goal_setting",
            service="Weekly Planning",
            status="pending",
            live_until=datetime.utcnow()
        )

        if redis_client.hexists("active_users", str(user.id)):
            send_realtime_notification(user.id, "Weekly Goal Setting 📝", message)

    print(f"📢 Goal-setting reminders sent to {len(users)} users.")
    return notifications

def generate_journaling_nudge(time_of_day):
    """Generate and send journaling reminders (Morning Gratitude, End-of-Day Reflection)."""
    morning_messages = [
        "What’s one thing you’re grateful for today? Let’s journal it now. ☀️",
        "Gratitude fuels happiness! Start your day with a positive thought. 💛",
        "Write down one thing that made you smile today. 😊",
    ]
    evening_messages = [
        "Unwind your thoughts—end your day with reflection in your journal. 🌙",
        "Write down a lesson you learned today. Growth starts with reflection. ✍️",
        "What was the best moment of your day? Capture it in your journal! 📖",
    ]

    message = choice(morning_messages) if time_of_day == "morning" else choice(evening_messages)
    users = User.query.with_entities(User.id).all()
    notifications = []

    for user in users:
        create_notification(
            title="Morning Gratitude ✨" if time_of_day == "morning" else "End-of-Day Reflection 🌙",
            description=message,
            user_id=user.id,
            type="journaling",
            service="Journaling",
            status="pending",
            live_until=datetime.utcnow()
        )

        if redis_client.hexists("active_users", str(user.id)):
            send_realtime_notification(user.id, f"Morning Gratitude ✨" if time_of_day == "morning" else "End-of-Day Reflection 🌙", message)

    print(f"📢 {time_of_day.capitalize()} journaling reminders sent to {len(users)} users.")
    return notifications


def generate_vision_board_nudge():
    """Generate and send a Vision Board reminder every Saturday at 11:00 AM."""
    message = "Update your Vision Board and stay inspired for the week ahead! 🎨"
    users = User.query.with_entities(User.id).all()

    for user in users:
        create_notification(
            title="Vision Board Update 🎨",
            description=message,
            user_id=user.id,
            type="vision_board",
            service="Weekly Inspiration",
            status="pending",
            live_until=datetime.utcnow()
        )

        if redis_client.hexists("active_users", str(user.id)):
            send_realtime_notification(user.id, "Vision Board Update 🎨", message)

    print(f"📢 Vision board reminders sent to {len(users)} users.")

def generate_mindfulness_nudge(time_of_day):
    """Generate and send mindfulness reminders (Morning & Afternoon)."""
    
    messages = [
        "Pause. Breathe. Recharge. Open Mindfulness now for peace. 🌿",
        "Take a moment to reset your mind—tap into mindfulness now. 🧘‍♂️",
        "A calm mind is a productive mind—relax and take a deep breath. ☁️",
    ]
    
    message = choice(messages)

    users = User.query.with_entities(User.id).all()
    notifications = []

    for user in users:
        create_notification(
            title="Morning Mindfulness 🌞" if time_of_day == "morning" else "Afternoon Mindfulness ☀️",
            description=message,
            user_id=user.id,
            type="mindfulness",
            service="Daily Mindfulness",
            status="pending",
            live_until=datetime.utcnow()
        )

        if redis_client.hexists("active_users", str(user.id)):
            send_realtime_notification(user.id, f"Morning Mindfulness 🌞" if time_of_day == "morning" else "Afternoon Mindfulness ☀️", message)

    print(f"📢 {time_of_day.capitalize()} mindfulness reminders sent to {len(users)} users.")
    return notifications

def delete_old_notifications():
    """Delete notifications older than 24 hours."""
    # Calculate 24 hours ago
    threshold_time = datetime.utcnow() - timedelta(days=1)
    
    # Query to find notifications older than 24 hours
    old_notifications = db.session.query(Notifications).filter(Notifications.created_at <= threshold_time).all()
    
    # Delete notifications older than 24 hours
    for notification in old_notifications:
        db.session.delete(notification)

    # Commit the changes to the database
    db.session.commit()

    print(f"📅 Deleted {len(old_notifications)} notifications older than 24 hours.")
    
    