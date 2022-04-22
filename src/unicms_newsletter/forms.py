from django import forms
from django.conf import settings
from django.forms.widgets import HiddenInput
from django.utils.translation import gettext_lazy as _

from . models import *


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
