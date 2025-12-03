"""
Celery worker entry point

Run with: celery -A celery_worker.celery worker --loglevel=info
Or: python celery_worker.py
"""
from chatService import create_app, get_celery
from config import Config

# Create Flask app context for Celery
app = create_app(Config)
celery = get_celery()

# Make celery available for command line
# This allows: celery -A celery_worker.celery worker --loglevel=info
if __name__ == '__main__':
    import sys
    from celery.__main__ import main
    sys.argv = ['celery', 'worker', '--loglevel=info']
    main()

