import calendar
import datetime
import logging
import os
import sys
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

from unicms_calendar.models import *

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
NEWSLETTER_MAX_ITEMS_FOR_MANUAL_SENDING = getattr(settings,'NEWSLETTER_MAX_ITEMS_FOR_MANUAL_SENDING',
                                                  NEWSLETTER_MAX_ITEMS_FOR_MANUAL_SENDING)
TOKEN_EXPIRATION = getattr(settings, 'TOKEN_EXPIRATION', TOKEN_EXPIRATION)

CMS_NEWSLETTER_LIST_PREFIX_PATH =  getattr(settings, 'CMS_NEWSLETTER_VIEW_PREFIX_PATH',
                                           CMS_NEWSLETTER_VIEW_PREFIX_PATH)
CMS_NEWSLETTER_MESSAGE_SUB_PATH =  getattr(settings, 'CMS_NEWSLETTER_MESSAGE_SUB_PATH',
                                           CMS_NEWSLETTER_MESSAGE_SUB_PATH)
CMS_NEWSLETTER_MESSAGE_SENDING_SUB_PATH =  getattr(settings, 'CMS_NEWSLETTER_MESSAGE_SENDING_SUB_PATH',
                                                   CMS_NEWSLETTER_MESSAGE_SENDING_SUB_PATH)


def message_attachment_path(instance, filename): # pragma: no cover
    # file will be uploaded to MEDIA_ROOT
    return 'newsletter/{}/{}/attachments/{}'.format(instance.message.newsletter.pk,
                                                    instance.message.pk,
                                                    filename)

def message_html_path(newsletter_pk, message_pk): # pragma: no cover
    # file will be uploaded to MEDIA_ROOT
    return 'newsletter/{}/{}/sendings'.format(newsletter_pk,
                                              message_pk)

def message_banner_path(instance, filename): # pragma: no cover
    # file will be uploaded to MEDIA_ROOT
    return 'newsletter/{}/{}/banners/{}'.format(instance.newsletter.pk,
                                                instance.pk,
                                                filename)


class Newsletter(ActivableModel, TimeStampedModel, CreatedModifiedBy,
                 AbstractLockable):
    name = models.CharField(max_length=255)
    slug = models.SlugField()
    description = models.TextField(max_length=2048,
                                   blank=True,
                                   default='')
    conditions = models.TextField(max_length=2048,
                                  blank=True,
                                  default='')
    site = models.ForeignKey(WebSite, on_delete=models.CASCADE)
    sender_address = models.EmailField(blank=True, null=True)
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
    first_name = models.CharField(default='', blank=True, max_length=255)
    last_name = models.CharField(default='', blank=True, max_length=255)
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
    name = models.CharField(max_length=255)
    newsletter = models.ForeignKey(Newsletter, on_delete=models.CASCADE)
    group_by_categories = models.BooleanField(default=True)
    date_start = models.DateTimeField(null=True, blank=True)
    date_end = models.DateTimeField(null=True, blank=True)
    repeat_each = models.PositiveIntegerField(null=True,
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
    template = models.CharField(max_length=255,
                                blank=True,
                                default='',
                                help_text=DEFAULT_TEMPLATE)
    queued_test = models.BooleanField(default=False)
    sending_test = models.BooleanField(default=False)
    queued = models.BooleanField(default=False)
    sending = models.BooleanField(default=False)
    week_day = models.CharField(max_length=255, default='', blank=True)
    discard_sent_news = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if '[' in self.week_day:
            self.week_day = self.week_day[1:-1].replace("'","").replace(" ","")

        if self.pk is None and self.banner:
            saved_banner = self.banner
            self.banner = None
            super(Message, self).save(*args, **kwargs)
            self.banner = saved_banner
            self.save(update_fields=['banner'])
        else:
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

    def is_ready(self, test=False):
        # if test message, check only test params
        if test:
            if self.sending_test: return False
            if self.queued_test: return True
            return False

        # the message is being sent
        if self.sending: return False
        # manual sending
        if self.queued: return True
        # check conditions
        if not self.is_active: return False
        if not self.is_in_progress(): return False
        now = timezone.localtime()
        # check week day
        if self.week_day and str(now.weekday()) not in self.week_day.split(','):
            return False
        # check hour: to work properly cronjob must be executed every hour
        if self.hour is not None and now.hour != self.hour: return False
        # repeat_each rule
        # None: ignore it
        # 0: only 1 send
        # n: every n days
        if self.repeat_each is None: return True
        last_sending = self.get_last_sending()
        if not last_sending: return True
        if self.repeat_each == 0: return False
        next_sending = last_sending.date + datetime.timedelta(self.repeat_each)
        return now >= next_sending

    def get_categories(self):
        categories = MessagePublicationCategory.objects\
                                          .filter(message=self, is_active=True)\
                                          .select_related('category')
        if not categories.exists():
            return Category.objects.all()
        cat_list = []
        for cat in categories:
            if cat.category not in cat_list:
                cat_list.append(cat.category)
        return cat_list

    def get_calendar_contexts(self):
        return MessageCalendarContext.objects\
                                     .filter(message=self, is_active=True)\
                                     .select_related('calendar_context')

    def get_webpaths(self):
        return MessageWebpath.objects\
                             .filter(message=self, is_active=True)\
                             .select_related('webpath')

    def get_webpath_news(self, message_webpath):
        if not message_webpath or not message_webpath.webpath.is_active:
            return PublicationContext.objects.none()
        now = timezone.localtime()
        news_from = message_webpath.news_from
        news_to = message_webpath.news_to
        news_from_query = Q()
        news_to_query = Q()
        discard_sent_news_query = Q()
        webpath_news_query = Q(webpath=message_webpath.webpath,
                               date_start__lte=now,
                               date_end__gt=now,
                               is_active=True,
                               publication__is_active=True)
        if news_from:
            news_from_query = Q(date_start__gte=news_from)
        if news_to:
            news_to_query = Q(date_start__lte=news_to)
        if self.discard_sent_news:
            # get most recent sending
            last_sending = MessageSending.objects.filter(message=self).first()
            if last_sending:
                discard_sent_news_query = Q(date_start__gt=last_sending.date)
        return PublicationContext.objects.filter(webpath_news_query,
                                                 news_from_query,
                                                 news_to_query,
                                                 discard_sent_news_query)

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
        return mpub

    def get_calendar_events(self, calendar_context):
        q_empty = MessageCalendarContext.objects.none()
        if not calendar_context: return q_empty
        if not calendar_context.is_active: return q_empty
        if not calendar_context.calendar_context.is_active: return q_empty
        if not calendar_context.calendar_context.webpath.is_active: return q_empty
        if not calendar_context.calendar_context.calendar.is_active: return q_empty

        now = timezone.localtime()
        events_from = calendar_context.events_from
        events_to = calendar_context.events_to
        events_from_query = Q()
        events_to_query = Q()

        # discard_sent_events_query = Q()

        events_query = Q(calendar=calendar_context.calendar_context.calendar,
                         # event__date_start__lte=now,
                         event__date_end__gt=now,
                         is_active=True,
                         event__publication__is_active=True)
        if events_from:
            events_from_query = Q(event__date_end__gte=events_from)
        if events_to:
            events_to_query = Q(event__date_start__lte=events_to)
        # if self.discard_sent_news:
            # get most recent sending
            # last_sending = MessageSending.objects.filter(message=self).first()
            # if last_sending:
                # discard_sent_news_query = Q(date_start__gt=last_sending.date)
        return CalendarEvent.objects.filter(events_query,
                                            events_from_query,
                                            events_to_query)
                                            # discard_sent_news_query)

    def get_attachments(self):
        return MessageAttachment.objects.filter(message=self, is_active=True)

    @staticmethod
    def build_news_dict(d, news, category, taken_news=[]):
        n = news.filter(publication__publication__category=category).exclude(publication__publication__pk__in=taken_news)
        if n.exists():
            for pub in n:
                if pub.publication.pk not in taken_news:
                    taken_news.append(pub.publication.publication.pk)
            d[category] = n

    def prepare_data(self, test=False):
        now = timezone.localtime()

        categories = self.get_categories()
        message_calendar_contexts = self.get_calendar_contexts()
        message_webpaths = self.get_webpaths()
        publications = self.get_publications()
        single_news = self.get_publicationcontexts()
        evidence_news = self.get_publicationcontexts(in_evidence=True)
        webpath_news = PublicationContext.objects.none()
        calendar_events = {}

        for message_webpath in message_webpaths:
            webpath_news = webpath_news | self.get_webpath_news(message_webpath)

        for calendar in message_calendar_contexts:
            calendar_events[calendar] = self.get_calendar_events(calendar)

        # list of single publications id, to exclude from webpath news
        # publications_id = list(map(lambda pub: pub.pk, single_news))
        # webpath_news = webpath_news.exclude(pk__in=publications_id)

        if self.group_by_categories:
            news_webpath = {}
            news_in_evidence = {}
            news_single = {}

            taken_news = []
            for category in categories:
                pubs = webpath_news.filter(publication__category=category)\
                                   [0:NEWSLETTER_MAX_ITEMS_IN_CATEGORY]
                if pubs.exists():
                    news_webpath[category] = pubs

                Message.build_news_dict(news_in_evidence, evidence_news, category, taken_news)
                Message.build_news_dict(news_single, single_news, category, taken_news)

            # if categories are chosen manually
            # get other categories
            if isinstance(categories, list):
                categories_id = [c.pk for c in categories]
                for category in Category.objects.all().exclude(pk__in=categories_id):
                    Message.build_news_dict(news_in_evidence, evidence_news, category, taken_news)
                    Message.build_news_dict(news_single, single_news, category, taken_news)
        else:
            news_webpath = webpath_news[0:NEWSLETTER_MAX_FREE_ITEMS]
            news_in_evidence = evidence_news
            news_single = single_news

        data = {'banner': self.banner.url if self.banner else '',
                'banner_url': self.banner_url,
                'calendar_events': calendar_events,
                'content': self.content,
                'intro_text': self.intro_text,
                'footer_text': self.footer_text,
                'group_by_categories': self.group_by_categories,
                'news_in_evidence': news_in_evidence,
                'newsletter': self.newsletter,
                'publications': publications,
                'single_news': news_single,
                'test': test,
                'webpath_news': news_webpath,
                }
        return data

    def check_data(self, test=False):
        keys = ['content', 'intro_text', 'news_in_evidence',
                'publications', 'single_news', 'webpath_news',
                'calendar_events']
        data = self.prepare_data(test=test)
        for key in keys:
            if data[key]: return data
        return {}

    def prepare_plain_text(self, test=False, data={}):
        data = data or self.prepare_data(test=test)
        return 'plain text {}'.format(data)

    def prepare_html(self, test=False, data={}):
        data = data or self.prepare_data(test=test)
        html_content = get_template(self.template or DEFAULT_TEMPLATE)
        return html_content.render(data)

    def register_sending(self, recipients, html_text):
        # create newsletter sending html file
        relative_path = message_html_path(self.newsletter.pk,
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
                                      recipients=len(recipients))

    def send_message(self, recipient,
                     html_text='', plain_text='',
                     attachments=[],
                     test=False):
        # build message
        message = mail.EmailMessage(
            subject=self.name,
            # html_text if recipient.html else plain_text,
            body=html_text,
            to=[recipient],
            from_email=f'{self.newsletter.name} <{self.newsletter.sender_address or settings.DEFAULT_FROM_EMAIL}>',
        )
        message.content_subtype = "html"

        for attachment in attachments:
            message.attach_file(attachment)

        # end build message
        message.send()


    def send(self, test=False, data={}):
        if test:
            # the message is being sent
            if self.sending_test:
                raise Exception(_('The test message is being sent, try later'))
            self.sending_test = True
        else:
            # the message is being sent
            if self.sending:
                raise Exception(_('The message is being sent, try later'))
            self.sending = True

        self.save()

        logger.debug('[{}] sending message {} '
                'for newsletter {}'.format(timezone.localtime(),
                                           self.name,
                                           self.newsletter))

        data = data or self.prepare_data(test=test)
        html_text = self.prepare_html(test=test, data=data)
        plain_text = self.prepare_plain_text(test=test, data=data)

        recipients = self.newsletter.get_valid_subscribers(test=test)
        attachments = self.get_attachments()
        message_attachments = []
        for attachment in attachments:
            file_path = attachment.attachment.path
            if os.path.exists(file_path):
                message_attachments.append(file_path)
            else:
                logger.debug('[{}] newsletter attachment "{}"'
                            'not found'.format(timezone.localtime(),
                                               file_path))
        # send message to recipients
        for index, recipient in enumerate(recipients, start=1):

            try:
                logger.debug(f'Try to send newsletter {self.newsletter} email to {recipient.email}')

                if NEWSLETTER_SEND_EMAIL_DELAY:
                    logger.debug(f'Start sleeping {self.newsletter} - SEND EMAIL DELAY')
                    time.sleep(NEWSLETTER_SEND_EMAIL_DELAY)
                    logger.debug(f'End sleeping {self.newsletter} - SEND EMAIL DELAY')
                if NEWSLETTER_SEND_EMAIL_GROUP:
                    if index % NEWSLETTER_SEND_EMAIL_GROUP == 0:
                        logger.debug(f'Start sleeping {self.newsletter} - SEND EMAIL GROUP')
                        time.sleep(NEWSLETTER_SEND_EMAIL_GROUP_DELAY)
                        logger.debug(f'End sleeping {self.newsletter} - SEND EMAIL GROUP')

                self.send_message(test=test,
                                  recipient=recipient.email,
                                  html_text=html_text,
                                  plain_text=plain_text,
                                  attachments=message_attachments)

                logger.debug(f'Sent newsletter {self.newsletter} email to {recipient.email}')

            except Exception as e:
                logger.debug(f'Newsletter {self.newsletter} exception {e} while sending to {recipient.email}')

        logger.debug('[{}] sent {} message {} '
                'for newsletter {}'.format(timezone.localtime(),
                                           'test-' if test else '',
                                           self.name,
                                           self.newsletter))

        if test:
            self.sending_test = False
            self.queued_test = False
        else:
            self.queued = False
            self.sending = False
            self.register_sending(recipients, html_text)
        self.save()

    def start_sending(self, test=False):
        # Start sending process
        # It decides whether the message should be sent instantly
        # or if it should be queued
        subscribers = self.newsletter.get_valid_subscribers(test=test)
        if len(subscribers) <= NEWSLETTER_MAX_ITEMS_FOR_MANUAL_SENDING:
            self.send(test=test)
            return _("Test message sent") if test else _("Message sent")
        else:
            if test: self.queued_test = True
            else: self.queued = True
            self.save()
            return _("Test message queued for the next submission") \
                     if test \
                     else _("Message queued for the next submission")

    def __str__(self):
        return f'{self.newsletter} - {self.name}'


class MessageWebpath(ActivableModel, TimeStampedModel, CreatedModifiedBy):
    message = models.ForeignKey(Message, on_delete=models.CASCADE)
    webpath = models.ForeignKey(WebPath, on_delete=models.CASCADE)
    news_from = models.DateTimeField(blank=True, null=True)
    news_to = models.DateTimeField(blank=True, null=True)

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


class MessageCalendarContext(ActivableModel, TimeStampedModel, CreatedModifiedBy):
    message = models.ForeignKey(Message, on_delete=models.CASCADE)
    calendar_context = models.ForeignKey(CalendarContext, on_delete=models.CASCADE)
    events_from = models.DateTimeField(blank=True, null=True)
    events_to = models.DateTimeField(blank=True, null=True)

    class Meta:
        unique_together = ('message', 'calendar_context')
        ordering = ('calendar_context',)

    def is_lockable_by(self, user):
        item = self.message.newsletter
        permission = check_user_permission_on_object(user=user, obj=item)
        return permission['granted']

    def __str__(self):
        return f'{self.message} - {self.calendar_context}'


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
