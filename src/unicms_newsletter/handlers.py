from django.conf import settings
from django.contrib import messages
from django.http import HttpResponse, HttpResponseForbidden, Http404
from django.middleware import csrf
from django.shortcuts import get_object_or_404, render
from django.template import Template, Context
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from cms.api.utils import check_user_permission_on_object
from cms.contexts.handlers import BaseContentHandler
from cms.contexts.utils import contextualize_template, sanitize_path
from cms.pages.models import Page

from . forms import *
from . models import *
from . settings import *


class NewsletterListHandler(BaseContentHandler):
    template = "unicms_newsletters.html"

    @property
    def breadcrumbs(self):
        path = self.path
        leaf = (path, _('Newsletter'))
        return (leaf,)

    def as_view(self):
        match_dict = self.match.groupdict()
        page = Page.objects.filter(is_active=True,
                                   webpath__site=self.website,
                                   webpath__fullpath='/').first()

        if not page:  # pragma: no cover
            raise Http404('Unknown Web Page')

        newsletters = Newsletter.objects.filter(site=self.website,
                                                is_active=True,
                                                is_public=True)

        if not newsletters:
            raise Http404('Unknown Web Page')

        data = {'request': self.request,
                'webpath': page.webpath,
                'website': self.website,
                'page': page,
                'path': match_dict.get('webpath', '/'),
                'handler': self,
                'newsletters': newsletters,
                }

        ext_template_sources = contextualize_template(self.template, page)
        template = Template(ext_template_sources)
        context = Context(data)
        return HttpResponse(template.render(context), status=200)


class NewsletterViewHandler(BaseContentHandler):
    template = "unicms_newsletter.html"

    def __init__(self, **kwargs):
        super(NewsletterViewHandler, self).__init__(**kwargs)
        self.match_dict = self.match.groupdict()
        self.page = Page.objects.filter(is_active=True,
                                        webpath__site=self.website,
                                        webpath__fullpath='/').first()

        if not self.page:  # pragma: no cover
            raise Http404('Unknown Web Page')

        self.newsletter = get_object_or_404(Newsletter,
                                            site=self.website,
                                            slug=self.match_dict.get('slug', ''),
                                            is_active=True,
                                            is_public=True)

        # self.messages = MessageSending.objects.filter(message__newsletter=self.newsletter)

    def as_view(self):
        # i18n
        # lang = getattr(self.request, 'LANGUAGE_CODE', None)
        # if lang:
            # self.cal_context.translate_as(lang=lang)

        url = reverse('unicms_newsletter:newsletter-sendings',
                      kwargs = {'newsletter_id': self.newsletter.pk })

        form = SubscribeForm(newsletter=self.newsletter)

        csrft = csrf.get_token(self.request)

        data = {'request': self.request,
                # 'lang': lang,
                'csrfmiddlewaretoken': csrft,
                'webpath': self.page.webpath,
                'website': self.website,
                'page': self.page,
                'path': self.match_dict.get('webpath', '/'),
                'custom_messages': messages.get_messages(self.request),
                'newsletter': self.newsletter,
                'handler': self,
                'form': form,
                # 'newsletter_messages': self.messages,
                'url': url}

        ext_template_sources = contextualize_template(self.template,
                                                      self.page)
        template = Template(ext_template_sources)
        context = Context(data)

        return HttpResponse(template.render(context), status=200)
        # return render(self.request, template)

    @property
    def parent_path_prefix(self):
        return getattr(settings, 'CMS_NEWSLETTER_LIST_PREFIX_PATH',
                       CMS_NEWSLETTER_LIST_PREFIX_PATH)

    @property
    def parent_url(self):
        url = f'{self.page.webpath.get_full_path()}/{self.parent_path_prefix}/'
        return sanitize_path(url)

    @property
    def breadcrumbs(self):
        leaf = ('', self.newsletter.name)
        parent = (self.parent_url, _('Newsletter'))
        return (parent, leaf)


class NewsletterMessageViewHandler(BaseContentHandler):

    def __init__(self, **kwargs):
        super(NewsletterMessageViewHandler, self).__init__(**kwargs)
        self.match_dict = self.match.groupdict()
        self.page = Page.objects.filter(is_active=True,
                                        webpath__site=self.website,
                                        webpath__fullpath='/').first()

        if not self.page:  # pragma: no cover
            raise Http404('Unknown Web Page')

        self.newsletter = Newsletter.objects.filter(site=self.website,
                                                    slug=self.match_dict.get('newsletter_id', '')).first()
        if not self.newsletter:
            raise Http404('Unknown newsletter')

        self.message = Message.objects.filter(newsletter=self.newsletter,
                                              pk=self.match_dict.get('code', '')).first()
        if not self.message:
            raise Http404('Unknown message')

    def as_view(self):
        permission = check_user_permission_on_object(self.request.user,
                                                     self.newsletter)
        if permission['granted']:
            return HttpResponse(self.message.prepare_html())
        return HttpResponseForbidden('Permission denied')


class NewsletterMessageSendingViewHandler(BaseContentHandler):

    def __init__(self, **kwargs):
        super(NewsletterMessageSendingViewHandler, self).__init__(**kwargs)
        self.match_dict = self.match.groupdict()
        self.page = Page.objects.filter(is_active=True,
                                        webpath__site=self.website,
                                        webpath__fullpath='/').first()

        if not self.page:  # pragma: no cover
            raise Http404('Unknown Web Page')

        self.newsletter = Newsletter.objects.filter(site=self.website,
                                                    slug=self.match_dict.get('newsletter_id', '')).first()
        if not self.newsletter:
            raise Http404('Unknown newsletter')

        message = Message.objects.filter(newsletter=self.newsletter,
                                         pk=self.match_dict.get('message_id', '')).first()
        if not message:
            raise Http404('Unknown message')

        self.message_sending = MessageSending.objects.filter(message=message,
                                                             pk=self.match_dict.get('code', '')).first()
        if not self.message_sending:
            raise Http404('Unknown message sending')

    def as_view(self):
        permission = check_user_permission_on_object(self.request.user,
                                                     self.newsletter)
        if permission['granted']:
            return HttpResponse(self.message_sending.html_file)
        if self.newsletter.is_public and self.newsletter.is_active and self.message.is_active:
            return HttpResponse(self.message_sending.html_file)
        raise Http404('Permission denied')
