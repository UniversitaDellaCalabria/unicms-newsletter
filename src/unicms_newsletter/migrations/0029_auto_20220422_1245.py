# Generated by Django 3.2.5 on 2022-04-22 10:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('unicms_newsletter', '0028_newslettertestsubscription'),
    ]

    operations = [
        migrations.AlterField(
            model_name='newslettersubscription',
            name='first_name',
            field=models.CharField(blank=True, default='', max_length=254),
        ),
        migrations.AlterField(
            model_name='newslettersubscription',
            name='last_name',
            field=models.CharField(blank=True, default='', max_length=254),
        ),
        migrations.AlterField(
            model_name='newslettertestsubscription',
            name='first_name',
            field=models.CharField(blank=True, default='', max_length=254),
        ),
        migrations.AlterField(
            model_name='newslettertestsubscription',
            name='last_name',
            field=models.CharField(blank=True, default='', max_length=254),
        ),
    ]
