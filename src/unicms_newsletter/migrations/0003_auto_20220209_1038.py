# Generated by Django 3.2.5 on 2022-02-09 09:38

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import unicms_newsletter.models


class Migration(migrations.Migration):

    dependencies = [
        ('cmspublications', '0022_auto_20220128_1536'),
        ('cmscontexts', '0011_alter_webpath_options'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('unicms_newsletter', '0002_newsletterwebpath'),
    ]

    operations = [
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(default=False)),
                ('name', models.CharField(max_length=256)),
                ('group_by_categories', models.BooleanField(default=True)),
                ('date_start', models.DateTimeField()),
                ('date_end', models.DateTimeField()),
                ('intro_text', models.TextField(default='')),
                ('days_interval', models.IntegerField(default=0)),
                ('template', models.CharField(max_length=256)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='message_created_by', to=settings.AUTH_USER_MODEL)),
                ('modified_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='message_modified_by', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='MessageAttachment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(default=False)),
                ('attachment', models.FileField(upload_to=unicms_newsletter.models.message_attachment_path)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='messageattachment_created_by', to=settings.AUTH_USER_MODEL)),
                ('message', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='unicms_newsletter.message')),
                ('modified_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='messageattachment_modified_by', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='MessagePublication',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(default=False)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='messagepublication_created_by', to=settings.AUTH_USER_MODEL)),
                ('message', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='unicms_newsletter.message')),
                ('modified_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='messagepublication_modified_by', to=settings.AUTH_USER_MODEL)),
                ('publication', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='cmspublications.publicationcontext')),
            ],
            options={
                'unique_together': {('message', 'publication')},
            },
        ),
        migrations.CreateModel(
            name='MessagePublicationCategories',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(default=False)),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='cmspublications.category')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='messagepublicationcategories_created_by', to=settings.AUTH_USER_MODEL)),
                ('message', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='unicms_newsletter.message')),
                ('modified_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='messagepublicationcategories_modified_by', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('message', 'category')},
            },
        ),
        migrations.CreateModel(
            name='MessageSending',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('date', models.DateTimeField()),
                ('html_content', models.TextField(default='')),
                ('text_content', models.TextField(default='')),
                ('recipients', models.IntegerField(default=0)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='messagesending_created_by', to=settings.AUTH_USER_MODEL)),
                ('message', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='unicms_newsletter.message')),
                ('modified_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='messagesending_modified_by', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='MessageWebpath',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(default=False)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='messagewebpath_created_by', to=settings.AUTH_USER_MODEL)),
                ('message', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='unicms_newsletter.message')),
                ('modified_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='messagewebpath_modified_by', to=settings.AUTH_USER_MODEL)),
                ('webpath', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='cmscontexts.webpath')),
            ],
            options={
                'unique_together': {('message', 'webpath')},
            },
        ),
        migrations.CreateModel(
            name='NewsletterSubscription',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(default=False)),
                ('first_name', models.CharField(max_length=256)),
                ('last_name', models.CharField(max_length=256)),
                ('email', models.EmailField(max_length=254)),
                ('html', models.BooleanField(default=True)),
                ('date_subscription', models.DateTimeField()),
                ('date_unsubscription', models.DateTimeField(blank=True, null=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='newslettersubscription_created_by', to=settings.AUTH_USER_MODEL)),
                ('modified_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='newslettersubscription_modified_by', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['last_name', 'first_name'],
            },
        ),
        migrations.AlterModelOptions(
            name='newsletter',
            options={'ordering': ['name'], 'verbose_name': 'Newsletter', 'verbose_name_plural': 'Newsletters'},
        ),
        migrations.DeleteModel(
            name='NewsletterWebpath',
        ),
        migrations.AddField(
            model_name='newslettersubscription',
            name='newsletter',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='unicms_newsletter.newsletter'),
        ),
        migrations.AddField(
            model_name='message',
            name='newsletter',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='unicms_newsletter.newsletter'),
        ),
        migrations.AlterUniqueTogether(
            name='newslettersubscription',
            unique_together={('newsletter', 'email')},
        ),
    ]
