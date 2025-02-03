from flask import current_app
from datetime import datetime
from ..models import Goals
from ..db import db

def update_goal_status_automatically():
    try:
        # Ensure the function runs within the app context
        with current_app.app_context():
            current_time = datetime.now()

            # Fetch goals where the status is not 'Cancelled'
            goals = Goals.query.filter(Goals.status != 'Cancelled').all()

            for goal in goals:
                print(f"Checking goal {goal.id}, current status: {goal.status}")

                if goal.end_date and goal.end_time:
                    goal_end_datetime = datetime.combine(goal.end_date, goal.end_time)

                    print(f"Goal end datetime: {goal_end_datetime}, current time: {current_time}")

                    if goal_end_datetime <= current_time:
                        if goal.status != 'Completed':
                            print(f"Updating goal {goal.id} to 'Completed'.")
                            goal.status = 'Completed'
                            db.session.commit()  # Commit changes to the database
                            print(f"Goal {goal.id} status updated to Completed.")
                        else:
                            print(f"Goal {goal.id} already marked as 'Completed'.")
                else:
                    print(f"Goal {goal.id} doesn't have valid end date/time.")

                # Only attempt to update the status to "Started" if it's not "Completed"
                if goal.status != 'Completed' and goal.status != 'Started' and goal.start_time:
                    if goal.start_date:
                        goal_start_datetime = datetime.combine(goal.start_date, goal.start_time)

                        print(f"Goal start datetime: {goal_start_datetime}, current time: {current_time}")

                        if goal_start_datetime <= current_time:
                            print(f"Updating goal {goal.id} to 'Started'.")
                            goal.status = 'Started'
                            db.session.commit()  # Commit changes to the database
                            print(f"Goal {goal.id} status updated to Started.")
                        else:
                            print(f"Goal {goal.id} is not yet started.")

    except Exception as e:
        print(f"Error updating goal statuses: {str(e)}")
