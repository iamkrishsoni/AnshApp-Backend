from datetime import datetime
from ..models import Goals
from ..db import db

def update_goal_status_automatically():
    try:
        # Get the current time
        current_time = datetime.now()

        # Fetch goals where the status is not 'Cancelled'
        goals = Goals.query.filter(Goals.status != 'Cancelled').all()

        for goal in goals:
            # If the goal is not started and the start_time is now or in the past
            if goal.status != 'Started' and goal.start_time:
                start_time = datetime.combine(datetime.today(), goal.start_time)
                if start_time <= current_time:
                    # Update the goal's status to 'Started' if it's the right time
                    goal.status = 'Started'
                    db.session.commit()
                    print(f"Goal {goal.id} status updated to Started.")

            # If the goal has started and the end_time is now or in the past
            if goal.status == 'Started' and goal.end_time:
                end_time = datetime.combine(datetime.today(), goal.end_time)
                if end_time <= current_time:
                    # Update the goal's status to 'Completed' if it's the right time
                    goal.status = 'Completed'
                    db.session.commit()
                    print(f"Goal {goal.id} status updated to Completed.")

    except Exception as e:
        print(f"Error updating goal statuses: {str(e)}")
