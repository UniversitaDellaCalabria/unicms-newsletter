# Generated by Django 3.2.19 on 2023-08-23 07:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('unicms_newsletter', '0062_auto_20220613_1128'),
    ]

    operations = [
        migrations.AlterField(
            model_name='newsletter',
            name='sender_address',
            field=models.EmailField(blank=True, max_length=254, null=True),
        ),
    ]