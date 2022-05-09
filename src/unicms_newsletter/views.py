import datetime
import json
import logging

from django import template
from django.conf import settings
from django.contrib import messages
from django.core.mail import EmailMessage, send_mail
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import get_template
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from . forms import *
from . jwts import *
from . models import *
from . settings import DEFAULT_TEMPLATE

logger = logging.getLogger(__name__)
register = template.Library()


def _check_subscription(request, subscription, unsubscribe=False):
    # no existent subscription
    if not subscription:
        if not unsubscribe: return True
        messages.add_message(request, messages.ERROR,
                             (_("This email address is not registered")))
        return False

    # subscription has been disabled from admin
    if not subscription.is_active:
        messages.add_message(request, messages.ERROR,
                             (_("This subscription is invalid. Contact our support")))
        return False

    # unsubscription request
    if unsubscribe:
        if not subscription.date_unsubscription: return True
        if subscription.date_unsubscription < subscription.date_subscription:
            return True
        messages.add_message(request, messages.WARNING,
                             (_("You're already unsubscripted to this newsletter")))
        return False

    # subscription request
    if subscription.date_unsubscription and subscription.date_subscription < subscription.date_unsubscription:
        return True
    messages.add_message(request, messages.WARNING,
                         (_("You're already subscripted to this newsletter")))
    return False

def subscribe_unsubscribe(request):
    """
    """
    if request.method == 'POST':
        form = SubscribeForm(request.POST)
        if form.is_valid():
            first_name = form.cleaned_data.get('first_name', '')
            last_name = form.cleaned_data.get('last_name', '')
            email = form.cleaned_data['email']
            html = form.cleaned_data.get('html', True)
            newsletter_slug = form.cleaned_data['newsletter']

            # get newsletter
            newsletter = get_object_or_404(Newsletter,
                                           is_active=True,
                                           slug=newsletter_slug)

            # check if newsletter is subscriptable
            if not newsletter.is_subscriptable:
                # log action
                logger.info(_("This newsletter isn't subscriptable"))
                raise Exception(_("This newsletter isn't subscriptable"))

            # get action (subscription or unsubscription?)
            unsubscribe = request.POST.get('unsubscribe', False)

            # get existent user subscription
            subscription = NewsletterSubscription.objects.filter(newsletter=newsletter,
                                                                 email=email).first()
            # check
            check = _check_subscription(request=request,
                                        subscription=subscription,
                                        unsubscribe=unsubscribe)

            if check:
                if unsubscribe:
                    sub_url = reverse('unicms_newsletter:newsletter_unsubscription_confirm')
                    mail_message = 'Unsubscription to newsletter {}'.format(newsletter)
                    log_message = '[{}] {} unsubscription request for {}'
                else:
                    sub_url = reverse('unicms_newsletter:newsletter_subscription_confirm')
                    mail_message = 'Subscription to newsletter {}'.format(newsletter)
                    log_message = '[{}] {} subscription request for {}'

                data = {'first_name': first_name,
                        'last_name': last_name,
                        'email': email,
                        'html': html,
                        'newsletter': newsletter.pk,
                        'timestamp': timezone.now().timestamp() }
                encrypted_data = encrypt_to_jwe(json.dumps(data).encode())

                url =  request.build_absolute_uri(f'{sub_url}?d={encrypted_data}')

                # send email with token to confirm action
                mail = EmailMessage(
                    mail_message,
                    url,
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                )
                mail.send(fail_silently=True)

                # log action
                logger.info(log_message.format(timezone.localtime(),
                                               email,
                                               newsletter))

                messages.add_message(request, messages.SUCCESS,
                                     _("Email sent to {}!").format(email))

        else: # pragma: no cover
            for k,v in form.errors.items():
                messages.add_message(request, messages.ERROR,
                                     "{}: {}".format(k, v))
        return redirect(request.headers['Referer'])
    raise Exception(_("Can't access to this URL"))


def subscription_confirm(request):
    data = request.GET.get('d', '')

    # if no data
    if not data:
        logger.info('[{}] subscription attempt '
                    'with empty data'.format(timezone.localtime()))
        raise Exception(_("No data submitted"))

    data_dict = json.loads(decrypt_from_jwe(data))
    newsletter = get_object_or_404(Newsletter,
                                   is_active=True,
                                   pk=data_dict['newsletter'])

    # check if newsletter is subscriptable
    if not newsletter.is_subscriptable:
        # log action
        logger.info(_("This newsletter isn't subscriptable"))
        raise Exception(_("This newsletter isn't subscriptable"))

    subscription = NewsletterSubscription.objects\
                                         .filter(newsletter=newsletter,
                                                 email=data_dict['email'])\
                                         .first()
    # check
    check = _check_subscription(request=request, subscription=subscription)

    if check:
        # if there is an existent email subscription for the newsletter
        if subscription:

            # if the token is old
            if not subscription.token_is_valid(data_dict['timestamp']):
                logger.info('[{}] {} tried to use '
                            'an old token for '
                            'newsletter {}'.format(timezone.localtime(),
                                                   data_dict['email'],
                                                   data_dict['newsletter']))
                raise Exception(_("Token is expired"))

            subscription.first_name = data_dict['first_name']
            subscription.last_name = data_dict['last_name']
            subscription.email = data_dict['email']
            subscription.html = data_dict['html']
            subscription.date_subscription = timezone.localtime()
            subscription.save()

        else:
            subscription = NewsletterSubscription.objects\
                                                 .create(newsletter=newsletter,
                                                         first_name=data_dict['first_name'],
                                                         last_name=data_dict['last_name'],
                                                         email=data_dict['email'],
                                                         html=data_dict['html'],
                                                         is_active=True,
                                                         date_subscription=timezone.localtime())

        # log action
        logger.info('[{}] {} subscription confirmed/edited'
                    'for {}'.format(timezone.localtime(),
                                    data_dict['email'],
                                    newsletter))

    messages.add_message(request, messages.SUCCESS,
                         _("{} subscription confirmed").format(data_dict['email']))
    redirect = f'/{settings.CMS_PATH_PREFIX}{settings.CMS_NEWSLETTER_VIEW_PREFIX_PATH}/{newsletter.slug}/'
    return HttpResponseRedirect(redirect)


def unsubscription_confirm(request):
    data = request.GET.get('d', '')

    # if no data
    if not data:
        logger.info('[{}] unsubscription attempt '
                    'with empty data'.format(timezone.localtime()))
        raise Exception(_("No data submitted"))

    data_dict = json.loads(decrypt_from_jwe(data))
    newsletter = get_object_or_404(Newsletter,
                                   is_active=True,
                                   pk=data_dict['newsletter'])

    # check if newsletter is subscriptable
    if not newsletter.is_subscriptable:
        # log action
        logger.info(_("This newsletter isn't subscriptable"))
        raise Exception(_("This newsletter isn't subscriptable"))

    subscription = NewsletterSubscription.objects\
                                         .filter(newsletter=newsletter,
                                                 email=data_dict['email'])\
                                         .first()

    # if there isn't an existent email subscription for the newsletter
    if not subscription:
        raise Exception(_("No subscription for this email"))

    # check
    check = _check_subscription(request=request,
                                subscription=subscription,
                                unsubscribe=True)

    if check:

        # if the token is old
        if not subscription.token_is_valid(data_dict['timestamp']):
            logger.info('[{}] {} tried to use '
                        'an old token for '
                        'newsletter {}'.format(timezone.localtime(),
                                               data_dict['email'],
                                               data_dict['newsletter']))
            raise Exception(_("Token is expired"))

        subscription.date_unsubscription = timezone.localtime()
        subscription.save()

        # log action
        logger.info('[{}] {} unsubscription confirmed'
                    'for {}'.format(timezone.localtime(),
                                    data_dict['email'],
                                    newsletter))

    messages.add_message(request, messages.SUCCESS,
                         _("{} unsubscription confirmed").format(data_dict['email']))
    redirect = f'/{settings.CMS_PATH_PREFIX}{settings.CMS_NEWSLETTER_VIEW_PREFIX_PATH}/{newsletter.slug}/'
    return HttpResponseRedirect(redirect)
