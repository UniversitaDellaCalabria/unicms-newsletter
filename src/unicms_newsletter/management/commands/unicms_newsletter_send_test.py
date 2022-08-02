import os
import shutil

from django.conf import settings
from django.core.management.base import BaseCommand

from ... models import Message


def confirm():
    """
    Ask user to enter Y or N (case-insensitive).
    :return: True if the answer is Y.
    :rtype: bool
    """
    answer = ""
    while answer not in ["y", "n"]:
        answer = input("OK to push to continue [Y/N]? ").lower()
    return answer == "y"


class Command(BaseCommand):
    help = 'uniCMS newsletter send all ready TEST messages'

    def add_arguments(self, parser):
        parser.epilog = 'Example: ./manage.py unicms_newsletter_send_test'
        parser.add_argument('-y', required=False, action="store_true",
                            help="send all ready test messages")

    def handle(self, *args, **options):
        if options['y'] or confirm():
            messages = Message.objects.filter(newsletter__is_active=True)
            for message in messages:
                if not message.is_ready(test=True):
                    print(f'[{message.newsletter}] - Message {message.name} is not ready')
                else:
                    data = message.check_data(test=True)
                    if not data:
                        print(f'[{message.newsletter}] - {message.name} is empty')
                    else:
                        print(f'[{message.newsletter}] - Sending message {message.name}')
                        message.send(test=True, data=data)
                        print(f'[{message.newsletter}] - Sent message {message.name}')
