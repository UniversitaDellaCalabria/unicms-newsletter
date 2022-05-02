import django
import os
import sys
sys.path.append('project_path')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings_path')
django.setup()

from unicms_newsletter.models import Message

messages = Message.objects.filter(newsletter__is_active=True)
for message in messages:
    if message.is_ready(): message.send()
