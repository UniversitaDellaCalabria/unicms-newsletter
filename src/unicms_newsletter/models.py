import calendar
import datetime
import logging
import os
import time

from django import template
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core import mail
from django.core.validators import MaxValueValidator, MinValueValidator,validate_comma_separated_integer_list
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
NEWSLETTER_SEND_EMAIL_GROUP_DELAY = getattr(settings, 'NEWSLETTER_SEND_EMAIL_GROUP_DELAY',
                                            NEWSLETTER_SEND_EMAIL_GROUP_DELAY)
TOKEN_EXPIRATION = getattr(settings, 'TOKEN_EXPIRATION', TOKEN_EXPIRATION)

CMS_NEWSLETTER_LIST_PREFIX_PATH =  getattr(settings, 'CMS_NEWSLETTER_VIEW_PREFIX_PATH',
                                           CMS_NEWSLETTER_VIEW_PREFIX_PATH)
CMS_NEWSLETTER_MESSAGE_SUB_PATH =  getattr(settings, 'CMS_NEWSLETTER_MESSAGE_SUB_PATH',
                                           CMS_NEWSLETTER_MESSAGE_SUB_PATH)
CMS_NEWSLETTER_MESSAGE_SENDING_SUB_PATH =  getattr(settings, 'CMS_NEWSLETTER_MESSAGE_SENDING_SUB_PATH',
                                                   CMS_NEWSLETTER_MESSAGE_SENDING_SUB_PATH)

def message_attachment_path(instance, filename): # pragma: no cover
    # file will be uploaded to MEDIA_ROOT
    return 'newsletter/{}/{}/attachments/{}'.format(instance.message.newsletter.slug,
                                                    instance.message.pk,
                                                    filename)

def message_html_path(newsletter_slug, message_pk): # pragma: no cover
    # file will be uploaded to MEDIA_ROOT
    return 'newsletter/{}/{}/sendings'.format(newsletter_slug,
                                              message_pk)

def message_banner_path(instance, filename): # pragma: no cover
    # file will be uploaded to MEDIA_ROOT
    return 'newsletter/{}/{}/banners/{}'.format(instance.newsletter.slug,
                                                instance.pk,
                                                filename)


class Newsletter(ActivableModel, TimeStampedModel, CreatedModifiedBy,
                 AbstractLockable):
    name = models.CharField(max_length=254)
    slug = models.SlugField()
    description = models.TextField(max_length=2048,
                                   blank=True,
                                   default='')
    conditions = models.TextField(max_length=2048,
                                  blank=True,
                                  default='')
    site = models.ForeignKey(WebSite, on_delete=models.CASCADE)
    is_subscriptable = models.BooleanField(default=True)
    is_public = models.BooleanField(default=True)

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

        # check token expiration
        token_date = datetime.datetime.fromtimestamp(token)
        now = datetime.datetime.now()
        expiration = token_date + datetime.timedelta(TOKEN_EXPIRATION)
        if now > expiration: return False

        # check if token has never been used
        last_timestamp = self.date_subscription.timestamp()
        if self.date_unsubscription:
            if self.date_unsubscription > self.date_subscription:
                last_timestamp = self.date_unsubscription.timestamp()
        return token > last_timestamp


class NewsletterTestSubscription(AbstractNewsletterSubscription):
    pass


WEEK_DAYS = (
        ('0', _('Monday')),
        ('1', _('Tuesday')),
        ('2', _('Wednesday')),
        ('3', _('Thursday')),
        ('4', _('Friday')),
        ('5', _('Saturday')),
        ('6', _('Sunday')),
    )

class Message(ActivableModel, TimeStampedModel, CreatedModifiedBy):
    name = models.CharField(max_length=254)
    newsletter = models.ForeignKey(Newsletter, on_delete=models.CASCADE)
    group_by_categories = models.BooleanField(default=True)
    date_start = models.DateTimeField(null=True, blank=True)
    date_end = models.DateTimeField(null=True, blank=True)
    repeat_each = models.PositiveIntegerField(default=0,
                                              blank=True,
                                              help_text=_("in days"))
    hour = models.IntegerField(null=True, blank=True,
                               validators=[
                                    MaxValueValidator(23),
                                    MinValueValidator(0)
                               ],
                               help_text=_("The sending time value, 0-23 (depends on the cronjob setting)"))
    # banner = models.ForeignKey(Media,
                               # on_delete=models.SET_NULL,
                               # blank=True,
                               # null=True)
    banner = models.ImageField(upload_to=message_banner_path,
                               validators=[validate_file_size],
                               blank=True, null=True)
    banner_url = models.URLField(max_length=200, default='', blank=True)
    intro_text = models.TextField(default='', blank=True)
    content = models.TextField(default='', blank=True)
    footer_text = models.TextField(default='', blank=True)
    template = models.CharField(max_length=254,
                                blank=True,
                                default='',
                                help_text=DEFAULT_TEMPLATE)
    sending = models.BooleanField(default=False)
    week_day = models.CharField(max_length=254, default='', blank=True)

    def save(self, *args, **kwargs):
        if '[' in self.week_day:
            self.week_day = self.week_day[1:-1].replace("'","").replace(" ","")
        super(Message, self).save(*args, **kwargs)

    def is_lockable_by(self, user):
        item = self.newsletter
        permission = check_user_permission_on_object(user=user, obj=item)
        return permission['granted']

    def get_last_sending(self):
        return MessageSending.objects.filter(message=self).first()

    def is_in_progress(self):
        if not self.date_start or not self.date_end: return False
        now = timezone.localtime()
        return self.date_start <= now and self.date_end > now

    def is_ready(self):
        if not self.is_active: return False
        if not self.is_in_progress(): return False
        now = timezone.localtime()
        # check week day
        if self.week_day and str(now.weekday()) not in self.week_day.split(','):
            return False
        # check hour: to work properly cronjob must be executed every hour
        if self.hour is not None and self.hour < now.hour: return False
        last_sending = self.get_last_sending()
        if not last_sending: return True
        if not self.repeat_each: return False
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

        data = {#'banner': self.banner,
                'banner': self.banner.url if self.banner else '',
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

    def register_sending(self, recipients, html_text):
        # create newsletter sending html file
        relative_path = message_html_path(self.newsletter.slug,
                                          self.pk)

        now = timezone.localtime()
        file_name = f'newsletter_{self.newsletter.slug}_{now.strftime("%Y-%m-%d_%H-%M")}.html'
        esistent = os.path.exists(f'{settings.MEDIA_ROOT}/{relative_path}')
        if not esistent:
          # Create a new directory because it does not exist
          os.makedirs(f'{settings.MEDIA_ROOT}/{relative_path}')

        html_file = open(f'{settings.MEDIA_ROOT}/{relative_path}/{file_name}', "w", encoding='utf-8')
        html_file.write(html_text)
        html_file.close()

        MessageSending.objects.create(message=self,
                                      date=now,
                                      html_file=f'{relative_path}/{file_name}',
                                      recipients=recipients.count())

    def send(self, test=False):
        # the message is being sent
        if self.sending:
            raise Exception(_('The message is being sent, try later'))

        self.sending = True
        self.save()

        try:
            logger.info('[{}] sending message {} '
                    'for newsletter {}'.format(timezone.localtime(),
                                               self.name,
                                               self.newsletter))

            data = self.prepare_data(test=test)

            html_text = self.prepare_html(test=test, data=data)
            plain_text = self.prepare_plain_text(test=test, data=data)

            recipients = self.newsletter.get_valid_subscribers(test=test)

            connection = mail.get_connection()
            connection.open()

            # build message
            message = mail.EmailMessage(
                subject=self.name,
                # html_text if recipient.html else plain_text,
                body=html_text,
                from_email=f'{self.newsletter.name} <ciao@unical.it>',
                connection=connection
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
            # end build message

            # send message to recipients
            for index, recipient in enumerate(recipients, start=1):
                message.to = [recipient.email]
                if NEWSLETTER_SEND_EMAIL_DELAY:
                    time.sleep(NEWSLETTER_SEND_EMAIL_DELAY)
                if NEWSLETTER_SEND_EMAIL_GROUP:
                    if index % NEWSLETTER_SEND_EMAIL_GROUP == 0:
                        time.sleep(NEWSLETTER_SEND_EMAIL_GROUP_DELAY)
                message.send()

            connection.close()

            logger.info('[{}] sent {} message {} '
                    'for newsletter {}'.format(timezone.localtime(),
                                               'test-' if test else '',
                                               self.name,
                                               self.newsletter))

            if not test: self.register_sending(recipients, html_text)

        finally:
            self.sending = False
            self.save()

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

    def view_html(self):
        newsletter = self.message.newsletter
        path = f'//{newsletter.site.domain}/{CMS_NEWSLETTER_VIEW_PREFIX_PATH}/{newsletter.slug}/{CMS_NEWSLETTER_MESSAGE_SUB_PATH}/{self.message.pk}/{CMS_NEWSLETTER_MESSAGE_SENDING_SUB_PATH}/{self.pk}/'
        return path

    def __str__(self):
        return f'{self.message} - {self.date}'
