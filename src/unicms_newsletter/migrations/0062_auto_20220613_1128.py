# Generated by Django 3.2.13 on 2022-06-13 09:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('unicms_newsletter', '0061_message_queued'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='queued_test',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='message',
            name='sending_test',
            field=models.BooleanField(default=False),
        ),
    ]
