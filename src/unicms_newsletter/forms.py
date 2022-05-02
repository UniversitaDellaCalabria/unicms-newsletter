from django import forms
from django.conf import settings
from django.forms.widgets import HiddenInput
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from cms.api.settings import FORM_SOURCE_LABEL

from . models import *


class NewsletterForm(forms.ModelForm):

    class Meta:
        model = Newsletter
        fields = ['name', 'slug', 'description', 'site', 'is_active']


class NewsletterSubscriptionForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        newsletter_id = kwargs.pop('newsletter_id', None)
        super().__init__(*args, **kwargs)
        if newsletter_id:
            self.fields['newsletter'].queryset = Newsletter.objects.filter(pk=newsletter_id)

    class Meta:
        model = NewsletterSubscription
        fields = ['newsletter', 'first_name', 'last_name',
                  'email', 'html', 'date_subscription']


class NewsletterTestSubscriptionForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        newsletter_id = kwargs.pop('newsletter_id', None)
        super().__init__(*args, **kwargs)
        if newsletter_id:
            self.fields['newsletter'].queryset = Newsletter.objects.filter(pk=newsletter_id)

    class Meta:
        model = NewsletterSubscription
        fields = ['newsletter', 'first_name', 'last_name', 'email', 'html']


class MessageForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        newsletter_id = kwargs.pop('newsletter_id', None)
        super().__init__(*args, **kwargs)
        if newsletter_id:
            self.fields['newsletter'].queryset = Newsletter.objects.filter(pk=newsletter_id)
        setattr(self.fields['banner'],
                FORM_SOURCE_LABEL,
                # only images
                reverse('unicms_api:media-options') + '?file_type=image%2Fwebp')

    class Meta:
        model = Message
        fields = ['newsletter', 'name', 'group_by_categories', 'date_start',
                  'date_end', 'repeat_each', 'banner', 'banner_url',
                  'intro_text', 'content', 'footer_text',
                  'template', 'is_active',]


class MessageAttachmentForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        message_id = kwargs.pop('message_id', None)
        super().__init__(*args, **kwargs)
        if message_id:
            self.fields['message'].queryset = Message.objects.filter(pk=message_id)

    class Meta:
        model = MessageAttachment
        fields = ['message', 'attachment', 'order', 'is_active']


class MessagePublicationForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        message_id = kwargs.pop('message_id', None)
        super().__init__(*args, **kwargs)
        if message_id:
            self.fields['message'].queryset = Message.objects.filter(pk=message_id)
        setattr(self.fields['publication'],
                FORM_SOURCE_LABEL,
                # only images
                reverse('unicms_api:editorial-board-publications-options'))

    class Meta:
        model = MessagePublication
        fields = ['message', 'publication', 'order', 'is_active']


class MessagePublicationCategoryForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        message_id = kwargs.pop('message_id', None)
        super().__init__(*args, **kwargs)
        if message_id:
            self.fields['message'].queryset = Message.objects.filter(pk=message_id)

    class Meta:
        model = MessagePublicationCategory
        fields = ['message', 'category', 'order', 'is_active']


class MessageWebpathForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        message_id = kwargs.pop('message_id', None)
        super().__init__(*args, **kwargs)
        if message_id:
            self.fields['message'].queryset = Message.objects.filter(pk=message_id)
        setattr(self.fields['webpath'],
                FORM_SOURCE_LABEL,
                reverse('unicms_api:webpath-all-options'))

    class Meta:
        model = MessageWebpath
        fields = ['message', 'webpath', 'is_active'] #'order', 'is_active']


class MessagePublicationContextForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        message_id = kwargs.pop('message_id', None)
        super().__init__(*args, **kwargs)
        if message_id:
            self.fields['message'].queryset = Message.objects.filter(pk=message_id)
        setattr(self.fields['publication'],
                FORM_SOURCE_LABEL,
                reverse('unicms_api:editorial-board-all-publication-contexts-options'))

    class Meta:
        model = MessagePublicationContext
        fields = ['message', 'publication', 'in_evidence',
                  'order', 'is_active']


class SubscribeForm(forms.Form):
    """
    """
    first_name = forms.CharField(label=_('Name'), required=True)
    last_name = forms.CharField(label=_('Surname'), required=True)
    email = forms.EmailField(label=_('Email'), required=True)
    html = forms.BooleanField(initial=True, required=False)
    newsletter = forms.SlugField(label=_('HTML version'),
                                 widget=HiddenInput,
                                 required=True)

    def __init__(self, *args, **kwargs):
        newsletter_slug = kwargs.pop('newsletter', None)
        super().__init__(*args, **kwargs)
        self.fields['newsletter'].initial = newsletter_slug


class UnsubscribeForm(forms.Form):
    """
    """
    email = forms.EmailField(label=_('Email'), required=True)
    newsletter = forms.SlugField(label=_('HTML version'),
                                 widget=HiddenInput,
                                 required=True)

    def __init__(self, *args, **kwargs):
        newsletter_slug = kwargs.pop('newsletter', None)
        super().__init__(*args, **kwargs)
        self.fields['newsletter'].initial = newsletter_slug
