def register_routes(app):
    from .auth import auth_bp
    from .users import user_bp
    from .schedules import schedule_bp
    from .professionals import professional_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(user_bp, url_prefix='/user')
    app.register_blueprint(professional_bp, url_prefix='/professional')
    app.register_blueprint(schedule_bp, url_prefix='/schedules')

