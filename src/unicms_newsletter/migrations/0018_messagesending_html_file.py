# Generated by Django 3.2.5 on 2022-02-18 08:24

from django.db import migrations, models
import unicms_newsletter.models


class Migration(migrations.Migration):

    dependencies = [
        ('unicms_newsletter', '0017_messagepublicationcategories_order'),
    ]

    operations = [
        migrations.AddField(
            model_name='messagesending',
            name='html_file',
            field=models.FileField(blank=True, null=True, upload_to=unicms_newsletter.models.message_html_path),
        ),
    ]
