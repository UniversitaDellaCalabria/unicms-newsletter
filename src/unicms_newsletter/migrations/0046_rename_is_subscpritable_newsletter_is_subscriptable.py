# Generated by Django 3.2.5 on 2022-05-09 09:16

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('unicms_newsletter', '0045_rename_is_subscritable_newsletter_is_subscpritable'),
    ]

    operations = [
        migrations.RenameField(
            model_name='newsletter',
            old_name='is_subscpritable',
            new_name='is_subscriptable',
        ),
    ]
