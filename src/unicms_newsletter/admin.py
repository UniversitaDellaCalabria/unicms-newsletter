from django.contrib import admin

from cms.contexts.admin import AbstractCreatedModifiedBy
from cms.publications.models import PublicationContext

from . admin_inlines import *
from . models import *


@admin.register(Newsletter)
class NewsletterAdmin(AbstractCreatedModifiedBy):
    list_display = ('name', 'site', 'is_active')
    search_fields = ('name', 'description')
    list_filter = ('site', 'created', 'modified')
    inlines = (NewsletterSubscriptionAdminInline,)
    readonly_fields = ('created_by', 'modified_by')


@admin.register(Message)
class MessageAdmin(AbstractCreatedModifiedBy):
    model = Message
    inlines = (MessageWebpathAdminInline,
               MessageCategoryAdminInline,
               MessagePublicationAdminInline,
               MessageAttachmentAdminInline,
               MessageSendingAdminInline
               )
    list_display = ('name', 'newsletter', 'is_active')
    search_fields = ('name',)
    list_filter = ('newsletter__name', 'created', 'modified', 'is_active')
    readonly_fields = ('created_by', 'modified_by')


@admin.register(PublicationContext)
class MessagePublicationAdmin(AbstractCreatedModifiedBy):
    model = PublicationContext
    list_display = ('publication', 'webpath', 'is_active', 'date_start', 'date_end',)
    search_fields = ('publication__name', 'publication__title', 'webpath__fullpath')
    list_filter = ('webpath__site',)
