# Generated by Django 3.2.5 on 2022-04-22 11:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('unicms_newsletter', '0030_auto_20220422_1302'),
    ]

    operations = [
        migrations.AlterField(
            model_name='message',
            name='template',
            field=models.CharField(blank=True, default='', help_text='newsletter/body.html', max_length=254),
        ),
    ]
