from django.conf import settings
from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import reverse

from cms.contexts.admin import AbstractCreatedModifiedBy

from . settings import *


class AbstractPreviewableAdmin(AbstractCreatedModifiedBy):
    change_form_template = "admin/unicms_newsletter_change_form_preview.html"

    def response_change(self, request, obj):
        if "_preview" in request.POST:
            url = f'/{settings.CMS_PATH_PREFIX}{CMS_NEWSLETTER_VIEW_PREFIX_PATH}/{obj.newsletter.slug}/{CMS_NEWSLETTER_MESSAGE_SUB_PATH}/{obj.pk}/preview/'
            return HttpResponseRedirect(url)

        elif "_send_test" in request.POST or "_send" in request.POST:
            try:
                message = obj.start_sending(test="_send_test" in request.POST)
                self.message_user(request, message)
            except Exception as e:
                self.message_user(request, e)
            url = reverse('admin:unicms_newsletter_message_change',
                          kwargs={'object_id': obj.pk})
            return HttpResponseRedirect(url)

        return super().response_change(request, obj)
