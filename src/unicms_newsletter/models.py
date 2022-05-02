import calendar
import datetime
import logging
import os
import time

from django import template
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core import mail
# from django.core.mail import EmailMessage, send_mail
from django.db import models
from django.db.models import Q
from django.template.loader import get_template
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from cms.api.utils import check_user_permission_on_object
from cms.contexts.models import WebPath, WebSite
from cms.contexts.models_abstract import AbstractLockable
from cms.contexts.utils import sanitize_path
from cms.medias.models import Media
from cms.medias.validators import *
from cms.publications.models import Category, Publication, PublicationContext
from cms.templates.models import (ActivableModel,
                                  CreatedModifiedBy,
                                  SectionAbstractModel,
                                  SortableModel,
                                  TimeStampedModel)

from . settings import *


logger = logging.getLogger(__name__)
register = template.Library()


NEWSLETTER_MAX_ITEMS_IN_CATEGORY = getattr(settings, 'NEWSLETTER_MAX_ITEMS_IN_CATEGORY',
                                           NEWSLETTER_MAX_ITEMS_IN_CATEGORY)
NEWSLETTER_MAX_FREE_ITEMS = getattr(settings, 'NEWSLETTER_MAX_FREE_ITEMS',
                                    NEWSLETTER_MAX_FREE_ITEMS)
NEWSLETTER_SEND_EMAIL_DELAY = getattr(settings, 'NEWSLETTER_SEND_EMAIL_DELAY',
                                      NEWSLETTER_SEND_EMAIL_DELAY)
NEWSLETTER_SEND_EMAIL_GROUP = getattr(settings, 'NEWSLETTER_SEND_EMAIL_GROUP',
                                      NEWSLETTER_SEND_EMAIL_GROUP)


def message_attachment_path(instance, filename): # pragma: no cover
    # file will be uploaded to MEDIA_ROOT
    return 'newsletter/attachments/{}/{}/{}'.format(instance.message.newsletter.slug,
                                                    instance.message.pk,
                                                    filename)

def message_html_path(newsletter_slug, message_pk): # pragma: no cover
    # file will be uploaded to MEDIA_ROOT
    return 'newsletter/sendings/{}/{}'.format(newsletter_slug,
                                                 message_pk)


class Newsletter(ActivableModel, TimeStampedModel, CreatedModifiedBy,
                 AbstractLockable):
    name = models.CharField(max_length=254)
    slug = models.SlugField()
    description = models.TextField(max_length=2048,
                                   blank=True,
                                   default='')
    site = models.ForeignKey(WebSite, on_delete=models.CASCADE)

    class Meta:
        ordering = ['name']
        unique_together = ('slug', 'site')
        verbose_name = _("Newsletter")
        verbose_name_plural = _("Newsletters")

    def get_valid_subscribers(self, test=False):
        if test:
            return NewsletterTestSubscription.objects\
                                             .filter(newsletter=self,
                                                     is_active=True)

        subscriptions = NewsletterSubscription.objects\
                                              .filter(newsletter=self,
                                                      is_active=True)
        to_exclude = []
        for subscription in subscriptions:
            if not subscription.date_unsubscription: continue
            if subscription.date_subscription <= subscription.date_unsubscription:
                to_exclude.append(subscription.pk)
        return subscriptions.exclude(pk__in=to_exclude)

    def serialize(self):
        return {'name': self.name,
                'slug': self.slug,
                'site': self.site.domain}

    def __str__(self):
        return self.name


class AbstractNewsletterSubscription(ActivableModel, CreatedModifiedBy):
    newsletter = models.ForeignKey(Newsletter, on_delete=models.CASCADE)
    first_name = models.CharField(default='', blank=True, max_length=254)
    last_name = models.CharField(default='', blank=True, max_length=254)
    email = models.EmailField()
    html = models.BooleanField(default=True)

    class Meta:
        abstract = True
        ordering = ['last_name', 'first_name']
        unique_together = ('newsletter', 'email')

    def is_lockable_by(self, user):
        item = self.newsletter
        permission = check_user_permission_on_object(user=user, obj=item)
        return permission['granted']

    def __str__(self):
        return f'{self.newsletter} - {self.email}'


class NewsletterSubscription(AbstractNewsletterSubscription):
    date_subscription = models.DateTimeField()
    date_unsubscription = models.DateTimeField(blank=True, null=True)

    def token_is_valid(self, token):
        if not token: return False
        last_timestamp = self.date_subscription.timestamp()
        if self.date_unsubscription:
            if self.date_unsubscription > self.date_subscription:
                last_timestamp = self.date_unsubscription.timestamp()
        return token > last_timestamp


class NewsletterTestSubscription(AbstractNewsletterSubscription):
    pass


class Message(ActivableModel, TimeStampedModel, CreatedModifiedBy):
    name = models.CharField(max_length=254)
    newsletter = models.ForeignKey(Newsletter, on_delete=models.CASCADE)
    group_by_categories = models.BooleanField(default=True)
    date_start = models.DateTimeField()
    date_end = models.DateTimeField()
    repeat_each = models.PositiveIntegerField(default=0, help_text=_("in days"))
    banner = models.ForeignKey(Media,
                               on_delete=models.SET_NULL,
                               blank=True,
                               null=True)
    banner_url = models.URLField(max_length=200, default='', blank=True)
    intro_text = models.TextField(default='', blank=True)
    content = models.TextField(default='', blank=True)
    footer_text = models.TextField(default='', blank=True)
    template = models.CharField(max_length=254,
                                blank=True,
                                default='',
                                help_text=DEFAULT_TEMPLATE)

    def is_lockable_by(self, user):
        item = self.newsletter
        permission = check_user_permission_on_object(user=user, obj=item)
        return permission['granted']

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

    def get_categories(self):
        mcat = MessagePublicationCategory.objects\
                                          .filter(message=self, is_active=True)\
                                          .select_related('category')
        categories = []
        for item in mcat:
            categories.append(item.category)
        return categories

    def get_webpaths(self):
        return MessageWebpath.objects\
                             .filter(message=self, is_active=True)\
                             .values_list('webpath__pk', flat=True)

    def get_publications(self):
        mpub = MessagePublication.objects\
                                 .filter(message=self,
                                         is_active=True)\
                                 .select_related('publication')
        publications = []
        for item in mpub:
            publications.append(item.publication)
        return publications

    def get_publicationcontexts(self, in_evidence=False):
        mpub = MessagePublicationContext.objects\
                                        .filter(message=self,
                                                is_active=True,
                                                in_evidence=in_evidence)\
                                        .select_related('publication')
        publications = []
        for item in mpub:
            publications.append(item.publication)
        return publications

    def get_publicationcontexts_in_evidence(self):
        return self.get_publicationcontexts(in_evidence=True)

    def get_attachments(self):
        return MessageAttachment.objects.filter(message=self, is_active=True)

    def prepare_data(self, test=False):
        now = timezone.localtime()

        categories = self.get_categories()
        webpaths = self.get_webpaths()
        publications = self.get_publications()
        single_news = self.get_publicationcontexts()
        news_in_evidence = self.get_publicationcontexts_in_evidence()

        # list of single publications id, to exclude from webpath news
        publications_id = list(map(lambda pub: pub.pk, single_news))

        news = {}

        webpath_news_query = Q(webpath__pk__in=webpaths,
                               date_start__lte=now,
                               date_end__gt=now,
                               is_active=True,
                               publication__is_active=True)

        if self.group_by_categories:
            for category in categories:
                pubs = PublicationContext.objects\
                                         .filter(webpath_news_query,
                                                 publication__category=category)\
                                         .exclude(pk__in=publications_id)\
                                         [0:NEWSLETTER_MAX_ITEMS_IN_CATEGORY]
                if pubs: news[category] = pubs
        else:
            news = PublicationContext.objects\
                                     .filter(webpath_news_query,
                                             publication__category__in=categories)\
                                     .exclude(pk__in=publications_id)\
                                     [0:NEWSLETTER_MAX_FREE_ITEMS]

        data = {'banner': self.banner,
                'banner_url': self.banner_url,
                'content': self.content,
                'intro_text': self.intro_text,
                'footer_text': self.footer_text,
                'group_by_categories': self.group_by_categories,
                'news_in_evidence': news_in_evidence,
                'newsletter': self.newsletter,
                'publications': publications,
                'single_news': single_news,
                'test': test,
                'webpath_news': news,
                }
        return data

    def prepare_plain_text(self, test=False, data={}):
        data = data or self.prepare_data()
        return 'plain text {}'.format(data)

    def prepare_html(self, test=False, data={}):
        data = data or self.prepare_data()
        html_content = get_template(self.template or DEFAULT_TEMPLATE)
        return html_content.render(data)

    def send(self, test=False):
        logger.info('[{}] sending message {} '
                    'for newsletter {}'.format(timezone.localtime(),
                                               self.name,
                                               self.newsletter))

        data = self.prepare_data(test=test)

        html_text = self.prepare_html(test=test, data=data)
        plain_text = self.prepare_plain_text(test=test, data=data)

        recipients = self.newsletter.get_valid_subscribers(test=test)

        messages = []
        recipients_email = []

        # for index, recipient in enumerate(recipients):
        for recipient in recipients:
            recipients_email.append(recipient.email)

        message = mail.EmailMessage(
            self.name,
            # html_text if recipient.html else plain_text,
            html_text,
            settings.DEFAULT_FROM_EMAIL,
            recipients_email,
        )
        message.content_subtype = "html"

        attachments = self.get_attachments()
        for attachment in attachments:
            file_path = attachment.attachment.path
            if os.path.exists(file_path):
                message.attach_file(file_path)
            else:
                logger.info('[{}] newsletter attachment "{}"'
                            'not found'.format(timezone.localtime(),
                                               file_path))

        message.send()

        logger.info('[{}] sent {}message {} '
                    'for newsletter {}'.format(timezone.localtime(),
                                               'test-' if test else '',
                                               self.name,
                                               self.newsletter))

        if not test:
            relative_path = message_html_path(self.newsletter.slug,
                                              self.pk)

            now = timezone.localtime()
            file_name = f'newsletter_{self.newsletter.slug}_{now.strftime("%Y-%m-%d_%H-%M")}.html'
            isExist = os.path.exists(f'{settings.MEDIA_ROOT}/{relative_path}')
            if not isExist:
              # Create a new directory because it does not exist
              os.makedirs(f'{settings.MEDIA_ROOT}/{relative_path}')

            html_file = open(f'{settings.MEDIA_ROOT}/{relative_path}/{file_name}', "w", encoding='utf-8')
            html_file.write(html_text)
            html_file.close()

            MessageSending.objects.create(message=self,
                                          date=now,
                                          html_file=f'{relative_path}/{file_name}',
                                          recipients=recipients.count())

        return True

    def __str__(self):
        return f'{self.newsletter} - {self.name}'


class MessageWebpath(ActivableModel, TimeStampedModel, CreatedModifiedBy):
    message = models.ForeignKey(Message, on_delete=models.CASCADE)
    webpath = models.ForeignKey(WebPath, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('message', 'webpath')
        ordering = ('webpath__name',)

    def is_lockable_by(self, user):
        item = self.message.newsletter
        permission = check_user_permission_on_object(user=user, obj=item)
        return permission['granted']

    def __str__(self):
        return f'{self.message} - {self.webpath}'


class MessagePublicationCategory(ActivableModel, TimeStampedModel,
                                   CreatedModifiedBy, SortableModel):
    message = models.ForeignKey(Message, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('message', 'category')
        ordering = ('order', 'category__name')

    def is_lockable_by(self, user):
        item = self.message.newsletter
        permission = check_user_permission_on_object(user=user, obj=item)
        return permission['granted']

    def __str__(self):
        return f'{self.message} - {self.category}'


class MessagePublicationContext(ActivableModel, TimeStampedModel,
                                CreatedModifiedBy, SortableModel):
    message = models.ForeignKey(Message, on_delete=models.CASCADE)
    publication = models.ForeignKey(PublicationContext, on_delete=models.CASCADE)
    in_evidence = models.BooleanField(default=False)

    class Meta:
        unique_together = ('message', 'publication')
        ordering = ('order', 'publication__publication__title')

    def is_lockable_by(self, user):
        item = self.message.newsletter
        permission = check_user_permission_on_object(user=user, obj=item)
        return permission['granted']

    def __str__(self):
        return f'{self.message} - {self.publication}'


class MessagePublication(ActivableModel, TimeStampedModel,
                         CreatedModifiedBy, SortableModel):
    message = models.ForeignKey(Message, on_delete=models.CASCADE)
    publication = models.ForeignKey(Publication, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('message', 'publication')
        ordering = ('order', 'publication__title')

    def is_lockable_by(self, user):
        item = self.message.newsletter
        permission = check_user_permission_on_object(user=user, obj=item)
        return permission['granted']

    def __str__(self):
        return f'{self.message} - {self.publication}'


class MessageAttachment(ActivableModel, TimeStampedModel,
                        CreatedModifiedBy, SortableModel):
    message = models.ForeignKey(Message, on_delete=models.CASCADE)
    attachment = models.FileField(upload_to=message_attachment_path,
                                  validators=[validate_file_extension,
                                              validate_file_size])

    class Meta:
        ordering = ('order',)

    def is_lockable_by(self, user):
        item = self.message.newsletter
        permission = check_user_permission_on_object(user=user, obj=item)
        return permission['granted']

    def __str__(self):
        return f'{self.message} - {self.attachment}'


class MessageSending(TimeStampedModel):
    message = models.ForeignKey(Message, on_delete=models.CASCADE)
    date = models.DateTimeField()
    html_file = models.FileField(blank=True, null=True)
    recipients = models.IntegerField(default=0)
    # success = models.IntegerField(default=0)
    # failed = models.IntegerField(default=0)

    class Meta:
        ordering = ['-date',]

    def __str__(self):
        return f'{self.message} - {self.date}'
