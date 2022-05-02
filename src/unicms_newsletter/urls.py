from django.urls import include, path, re_path

from cms.api.urls import eb_prefix

from . views import *
from . api.views import (message, message_attachment, message_publication,
                         message_publication_context, message_category,
                         message_webpath, newsletter,)


app_name="unicms_newsletter"


urlpatterns = [
    path('newsletter/subscription/', subscription, name='newsletter_subscription'),
    path('newsletter/unsubscription/', unsubscription, name='newsletter_unsubscription'),
    path('newsletter/subscribtion-confirm/', subscription_confirm, name='newsletter_subscription_confirm'),
    path('newsletter/unsubscribtion-confirm/', unsubscription_confirm, name='newsletter_unsubscription_confirm'),
]

# API

# newsletters
newsletter_prefix = f'{eb_prefix}/newsletters'

urlpatterns += path(f'{newsletter_prefix}/', newsletter.NewsletterList.as_view(), name='newsletters'),
urlpatterns += path(f'{newsletter_prefix}/<int:pk>/', newsletter.NewsletterView.as_view(), name='newsletter'),
urlpatterns += path(f'{newsletter_prefix}/form/', newsletter.NewsletterFormView.as_view(), name='newsletter-form'),
urlpatterns += path(f'{newsletter_prefix}/<int:pk>/logs/', newsletter.NewsletterLogsView.as_view(), name='newsletter-logs'),

# subscriptions
nsub = f'{newsletter_prefix}/<int:newsletter_id>/subscriptions'
urlpatterns += path(f'{nsub}/', newsletter.NewsletterSubscriptionList.as_view(), name='newsletter-subscriptions'),
urlpatterns += path(f'{nsub}/<int:pk>/', newsletter.NewsletterSubscriptionView.as_view(), name='newsletter-subscription'),
urlpatterns += path(f'{nsub}/form/', newsletter.NewsletterSubscriptionFormView.as_view(), name='newsletter-subscription-form'),

# test subscriptions
ntsub = f'{newsletter_prefix}/<int:newsletter_id>/test-subscriptions'
urlpatterns += path(f'{ntsub}/', newsletter.NewsletterTestSubscriptionList.as_view(), name='newsletter-test-subscriptions'),
urlpatterns += path(f'{ntsub}/<int:pk>/', newsletter.NewsletterTestSubscriptionView.as_view(), name='newsletter-test-subscription'),
urlpatterns += path(f'{ntsub}/form/', newsletter.NewsletterTestSubscriptionFormView.as_view(), name='newsletter-test-subscription-form'),

# messages
nmes = f'{newsletter_prefix}/<int:newsletter_id>/messages'
urlpatterns += path(f'{nmes}/', message.MessageList.as_view(), name='newsletter-messages'),
urlpatterns += path(f'{nmes}/<int:pk>/', message.MessageView.as_view(), name='newsletter-message'),
urlpatterns += path(f'{nmes}/form/', message.MessageFormView.as_view(), name='newsletter-message-form'),
urlpatterns += path(f'{nmes}/<int:pk>/sendings/', message.MessageSendingList.as_view(), name='newsletter-message-sendings'),
urlpatterns += path(f'{nmes}/<int:pk>/send/', message.MessageSendView.as_view(), name='newsletter-message-send'),

# message attachments
nmatt = f'{newsletter_prefix}/<int:newsletter_id>/messages/<int:message_id>/attachments'
urlpatterns += path(f'{nmatt}/', message_attachment.MessageAttachmentList.as_view(), name='newsletter-message-attachments'),
urlpatterns += path(f'{nmatt}/<int:pk>/', message_attachment.MessageAttachmentView.as_view(), name='newsletter-message-attachment'),
urlpatterns += path(f'{nmatt}/form/', message_attachment.MessageAttachmentFormView.as_view(), name='newsletter-message-attachment-form'),

# message publications
nmpub = f'{newsletter_prefix}/<int:newsletter_id>/messages/<int:message_id>/publications'
urlpatterns += path(f'{nmpub}/', message_publication.MessagePublicationList.as_view(), name='newsletter-message-publications'),
urlpatterns += path(f'{nmpub}/<int:pk>/', message_publication.MessagePublicationView.as_view(), name='newsletter-message-publication'),
urlpatterns += path(f'{nmpub}/form/', message_publication.MessagePublicationFormView.as_view(), name='newsletter-message-publication-form'),

# message publication contexts
nmctx = f'{newsletter_prefix}/<int:newsletter_id>/messages/<int:message_id>/publication-contexts'
urlpatterns += path(f'{nmctx}/', message_publication_context.MessagePublicationContextList.as_view(), name='newsletter-message-publication-contexts'),
urlpatterns += path(f'{nmctx}/<int:pk>/', message_publication_context.MessagePublicationContextView.as_view(), name='newsletter-message-publication-context'),
urlpatterns += path(f'{nmctx}/form/', message_publication_context.MessagePublicationContextFormView.as_view(), name='newsletter-message-publication-context-form'),

# message categories
nmcat = f'{newsletter_prefix}/<int:newsletter_id>/messages/<int:message_id>/categories'
urlpatterns += path(f'{nmcat}/', message_category.MessagePublicationCategoryList.as_view(), name='newsletter-message-categories'),
urlpatterns += path(f'{nmcat}/<int:pk>/', message_category.MessagePublicationCategoryView.as_view(), name='newsletter-message-category'),
urlpatterns += path(f'{nmcat}/form/', message_category.MessagePublicationCategoryFormView.as_view(), name='newsletter-message-category-form'),

# message webpaths
nmweb = f'{newsletter_prefix}/<int:newsletter_id>/messages/<int:message_id>/webpaths'
urlpatterns += path(f'{nmweb}/', message_webpath.MessageWebpathList.as_view(), name='newsletter-message-webpaths'),
urlpatterns += path(f'{nmweb}/<int:pk>/', message_webpath.MessageWebpathView.as_view(), name='newsletter-message-webpath'),
urlpatterns += path(f'{nmweb}/form/', message_webpath.MessageWebpathFormView.as_view(), name='newsletter-message-webpath-form'),
