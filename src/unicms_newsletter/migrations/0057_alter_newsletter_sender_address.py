# Generated by Django 3.2.5 on 2022-05-16 20:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('unicms_newsletter', '0056_newsletter_sender_address'),
    ]

    operations = [
        migrations.AlterField(
            model_name='newsletter',
            name='sender_address',
            field=models.EmailField(blank=True, help_text='Default: wifi.rovito@gmail.com', max_length=254, null=True),
        ),
    ]
