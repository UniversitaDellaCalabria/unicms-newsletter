# Generated by Django 3.2.5 on 2022-04-22 09:07

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('unicms_newsletter', '0026_auto_20220422_1106'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='messagewebpath',
            options={'ordering': ('webpath__name',)},
        ),
    ]
