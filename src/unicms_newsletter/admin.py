from django.contrib import admin

from cms.contexts.admin import AbstractCreatedModifiedBy
from cms.publications.models import PublicationContext

from . admin_inlines import *
from . admin_custom import AbstractPreviewableAdmin
from . forms import MessageForm
from . models import *


@admin.register(Newsletter)
class NewsletterAdmin(AbstractCreatedModifiedBy):
    list_display = ('name', 'site', 'is_active')
    search_fields = ('name', 'description')
    list_filter = ('site', 'created', 'modified')
    inlines = (NewsletterTestSubscriptionAdminInline,
               NewsletterSubscriptionAdminInline)
    readonly_fields = ('created_by', 'modified_by')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Message)
class MessageAdmin(AbstractPreviewableAdmin):
    model = Message
    form = MessageForm
    inlines = (MessageWebpathAdminInline,
               MessageCategoryAdminInline,
               MessagePublicationAdminInline,
               MessagePublicationContextAdminInline,
               MessageAttachmentAdminInline,
               MessageSendingAdminInline
               )
    list_display = ('name', 'newsletter', 'is_active')
    raw_id_fields = ('banner',)
    search_fields = ('name',)
    list_filter = ('newsletter__name', 'created', 'modified', 'is_active')
    readonly_fields = ('created_by', 'modified_by', 'sending')

    class Media:
        js = ("js/ckeditor5/ckeditor.js",
              "js/unicms_newsletter_ckeditor_init.js",
        )


@admin.register(PublicationContext)
class MessagePublicationAdmin(AbstractCreatedModifiedBy):
    model = PublicationContext
    list_display = ('publication', 'webpath', 'is_active', 'date_start', 'date_end',)
    search_fields = ('publication__name', 'publication__title', 'webpath__fullpath')
    list_filter = ('webpath__site',)
