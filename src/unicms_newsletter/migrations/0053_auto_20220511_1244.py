# Generated by Django 3.2.5 on 2022-05-11 10:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('unicms_newsletter', '0052_auto_20220511_1227'),
    ]

    operations = [
        migrations.AlterField(
            model_name='message',
            name='date_end',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='message',
            name='date_start',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
