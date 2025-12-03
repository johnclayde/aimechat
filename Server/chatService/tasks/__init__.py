"""
Celery background tasks
"""
from chatService.tasks.message_tasks import register_celery_tasks

__all__ = ['register_celery_tasks']

