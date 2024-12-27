def register_routes(app):
    from .auth import auth_bp
    from .users import user_bp
    from .schedules import schedule_bp
    from .professionals import professional_bp
    from .bountypoints import bounty_bp
    from .chats import chat_bp
    from .affirmations import affirmation_bp
    from .reminder_routes import reminder_routes
    from .feedback import feedback_bp
    from .journaling import journaling_bp
    from .visionboard import vision_board_bp
    from .goals import goal_bp
    from .mindfulness import mindfulness_bp
    from .extras import extras_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(user_bp, url_prefix='/user')
    app.register_blueprint(professional_bp, url_prefix='/professional')
    app.register_blueprint(schedule_bp, url_prefix='/schedules')
    app.register_blueprint(bounty_bp, url_prefix='/bounty')
    app.register_blueprint(chat_bp, url_prefix='/api/v1')
    app.register_blueprint(affirmation_bp, url_prefix = '/affirmation')
    app.register_blueprint(feedback_bp, url_prefix = '/feedback')
    app.register_blueprint(journaling_bp, url_prefix = '/journaling')
    app.register_blueprint(vision_board_bp, url_prefix = '/visionboard')
    app.register_blueprint(goal_bp, url_prefix = '/goals')
    app.register_blueprint(mindfulness_bp, url_prefix = '/mindfulness')
    app.register_blueprint(extras_bp, url_prefix = '/new')
    

