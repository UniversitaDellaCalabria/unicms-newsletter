from django.urls import include, path, re_path

from . views import *


app_name="unicms_newsletter"


urlpatterns = [
    path('newsletter/subscription/', subscription, name='newsletter_subscription'),
    path('newsletter/unsubscription/', unsubscription, name='newsletter_unsubscription'),
    path('newsletter/subscribtion-confirm/', subscription_confirm, name='newsletter_subscription_confirm'),
    path('newsletter/unsubscribtion-confirm/', unsubscription_confirm, name='newsletter_unsubscription_confirm'),
]
