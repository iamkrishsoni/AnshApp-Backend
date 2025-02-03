# gunicorn.conf.py
workers = 4  # Number of workers
bind = "0.0.0.0:4000"  # Address and port to bind to
accesslog = '-'  # Log requests to stdout
errorlog = '-'   # Log errors to stderr
loglevel = 'info'  # Logging level
