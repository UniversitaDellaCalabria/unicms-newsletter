import calendar
import datetime
import pytz

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from cms.api.utils import check_user_permission_on_object
from cms.contexts.models import WebPath, WebSite
from cms.contexts.models_abstract import AbstractLockable
from cms.contexts.utils import sanitize_path
from cms.publications.models import Category, Publication, PublicationContext
from cms.templates.models import (ActivableModel,
                                  CreatedModifiedBy,
                                  SectionAbstractModel,
                                  SortableModel,
                                  TimeStampedModel)


def message_attachment_path(instance, filename): # pragma: no cover
    # file will be uploaded to MEDIA_ROOT
    return 'newsletter_attachments/{}/{}/{}'.format(instance.message.newsletter.slug,
                                                    instance.message.pk,
                                                    filename)


class Newsletter(ActivableModel, TimeStampedModel, CreatedModifiedBy):
    name = models.CharField(max_length=256)
    slug = models.SlugField(unique=True, blank=True, default='')
    description = models.TextField(max_length=2048,
                                   blank=True,
                                   default='')
    site = models.ForeignKey(WebSite, on_delete=models.CASCADE)

    class Meta:
        ordering = ['name']
        verbose_name = _("Newsletter")
        verbose_name_plural = _("Newsletters")

    def name2slug(self):
        return slugify(self.name)

    def save(self, *args, **kwargs):
        self.slug = self.name2slug()
        super(self.__class__, self).save(*args, **kwargs)

    def get_valid_subscribers(self):
        subscriptions = NewsletterSubscription.objects\
                                              .filter(newsletter=self,
                                                      is_active=True)
        to_exclude = []
        for subscription in subscriptions:
            if not subscription.date_unsubscription: continue
            if subscription.date_subscription <= subscription.date_unsubscription:
                to_exclude.append(subscription.pk)
        return subscriptions.exclude(pk__in=to_exclude)

    def __str__(self):
        return self.name


class NewsletterSubscription(ActivableModel, TimeStampedModel, CreatedModifiedBy):
    newsletter = models.ForeignKey(Newsletter, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=256)
    last_name = models.CharField(max_length=256)
    email = models.EmailField()
    html = models.BooleanField(default=True)
    date_subscription = models.DateTimeField()
    date_unsubscription = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['last_name', 'first_name']
        unique_together = ('newsletter', 'email')

    def __str__(self):
        return f'{self.newsletter} - {self.last_name} {self.first_name} - {self.email}'


class Message(ActivableModel, TimeStampedModel, CreatedModifiedBy):
    name = models.CharField(max_length=256)
    newsletter = models.ForeignKey(Newsletter, on_delete=models.CASCADE)
    group_by_categories = models.BooleanField(default=True)
    date_start = models.DateTimeField()
    date_end = models.DateTimeField()
    intro_text = models.TextField(default='', blank=True)
    repeat_each = models.IntegerField(default=0, help_text=_("in days"))
    template = models.CharField(max_length=256)

    def get_last_sending(self):
        return MessageSending.objects.filter(message=self).first()

    def is_in_progress(self):
        now = timezone.localtime()
        return self.date_start <= now and self.date_end > now

    def is_ready(self):
        if not self.is_active: return False
        if not self.is_in_progress(): return False
        last_sending = self.get_last_sending()
        if not last_sending: return True
        if not self.repeat_each: return False
        now = timezone.localtime()
        next_sending = last_sending.date + datetime.timedelta(self.repeat_each)
        return now >= next_sending

    def __str__(self):
        return f'{self.newsletter} - {self.name}'


class MessageWebpath(ActivableModel, TimeStampedModel, CreatedModifiedBy):
    message = models.ForeignKey(Message, on_delete=models.CASCADE)
    webpath = models.ForeignKey(WebPath, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('message', 'webpath')

    def __str__(self):
        return f'{self.message} - {self.webpath}'


class MessagePublicationCategories(ActivableModel, TimeStampedModel, CreatedModifiedBy):
    message = models.ForeignKey(Message, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('message', 'category')

    def __str__(self):
        return f'{self.message} - {self.category}'


class MessagePublication(ActivableModel, TimeStampedModel, CreatedModifiedBy):
    message = models.ForeignKey(Message, on_delete=models.CASCADE)
    publication = models.ForeignKey(PublicationContext, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('message', 'publication')

    def __str__(self):
        return f'{self.message} - {self.publication}'


class MessageAttachment(ActivableModel, TimeStampedModel, CreatedModifiedBy):
    message = models.ForeignKey(Message, on_delete=models.CASCADE)
    attachment = models.FileField(upload_to=message_attachment_path,
                                  blank=False, null=False)

    def __str__(self):
        return f'{self.message} - {self.attachment}'


class MessageSending(TimeStampedModel, CreatedModifiedBy):
    message = models.ForeignKey(Message, on_delete=models.CASCADE)
    date = models.DateTimeField()
    html_content = models.TextField(default='')
    text_content = models.TextField(default='')
    recipients = models.IntegerField(default=0)
    success = models.IntegerField(default=0)
    failed = models.IntegerField(default=0)

    class Meta:
        ordering = ['-date',]

    def __str__(self):
        return f'{self.message} - {self.date}'
