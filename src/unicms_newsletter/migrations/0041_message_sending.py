# Generated by Django 3.2.5 on 2022-05-05 11:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('unicms_newsletter', '0040_newsletter_conditions'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='sending',
            field=models.BooleanField(default=False),
        ),
    ]