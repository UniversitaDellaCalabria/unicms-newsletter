# Generated by Django 3.2.13 on 2022-06-13 06:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('unicms_newsletter', '0060_message_discard_sent_news'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='queued',
            field=models.BooleanField(default=False),
        ),
    ]