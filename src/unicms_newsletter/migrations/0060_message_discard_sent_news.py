# Generated by Django 3.2.13 on 2022-06-03 07:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('unicms_newsletter', '0059_auto_20220603_0827'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='discard_sent_news',
            field=models.BooleanField(default=False),
        ),
    ]
