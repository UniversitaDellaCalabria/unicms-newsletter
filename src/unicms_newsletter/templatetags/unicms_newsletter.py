import logging

from django import template
from django.db.models import Q
from  django.template import RequestContext
from django.utils import timezone
from django.utils.safestring import SafeString

from cms.contexts.utils import handle_faulty_templates

from .. forms import SubscribeForm
from .. models import Newsletter


logger = logging.getLogger(__name__)
register = template.Library()

from django.shortcuts import render
from django.template.loader import get_template

@register.simple_tag(takes_context=True)
def load_newsletter_subscription(context, template, newsletter_id):
    _func_name = 'load_newsletter_subscription'
    _log_msg = f'Template Tag {_func_name}'

    request=context['request']

    newsletter = Newsletter.objects.filter(pk=newsletter_id,
                                           is_active=True).first()

    if not newsletter:
        _msg = '{} cannot find newsletter id {}'.format(_log_msg,
                                                        newsletter_id)
        logger.error(_msg)
        return SafeString('')
    data = {'form': SubscribeForm(newsletter=newsletter)}
    # return handle_faulty_templates(template, data, name=_func_name)

    t = get_template(template)
    return t.render(data, request)
