# Generated by Django 3.2.5 on 2022-04-21 11:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('unicms_newsletter', '0020_alter_messagesending_html_file'),
    ]

    operations = [
        migrations.AddField(
            model_name='messagepublication',
            name='in_evidence',
            field=models.BooleanField(default=False),
        ),
    ]
