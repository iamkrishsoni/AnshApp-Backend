from flask import Flask, current_app
from .config import Config
from .db import db
from .models import *
from flask_cors import CORS
import logging
from .routes import register_routes
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from .services import update_goal_status_automatically

def create_app():
    app = Flask(__name__)
    CORS(app)

    # Set up logging to file and console
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Load configuration
    app.config.from_object(Config)

    # Initialize the database
    db.init_app(app)

    # Ensure the tables are created at the start (in app context)
    with app.app_context():
        db.create_all()

    # Register routes
    register_routes(app)

    # Initialize the scheduler
    scheduler = BackgroundScheduler()

    # Log the job being added
    app.logger.info("Adding job 'goal_status_updater' to scheduler")
    
    # Wrap job in app context
    def job_wrapper():
        with app.app_context():  # Ensure app context is available
            update_goal_status_automatically()  # Call the actual job function
    
    scheduler.add_job(
        func=job_wrapper,  # Use the wrapper to ensure context is available
        trigger=IntervalTrigger(minutes=1),  # Run every minute
        id='goal_status_updater',
        name='Update goal statuses automatically',
        replace_existing=True
    )

    # Start the scheduler
    try:
        scheduler.start()
        app.logger.info("Scheduler started successfully.")
    except Exception as e:
        app.logger.error(f"Error starting scheduler: {str(e)}")

    # Store the scheduler in the app context for global access
    app.scheduler = scheduler

    # Ensure the scheduler stays running and is not prematurely stopped
    @app.before_request
    def ensure_scheduler_running():
        if not app.scheduler.running:
            app.scheduler.start()
            app.logger.info("Scheduler started before first request.")

    return app
