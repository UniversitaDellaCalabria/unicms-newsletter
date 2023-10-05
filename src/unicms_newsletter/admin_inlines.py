from django.contrib import admin

from . models import *


class NewsletterTestSubscriptionAdminInline(admin.TabularInline):
    model = NewsletterTestSubscription
    extra = 0
    classes = ['collapse']
    list_display = ('first_name', 'last_name', 'email', 'is_active')
    search_fields = ('first_name', 'last_name', 'email')


class NewsletterSubscriptionAdminInline(admin.TabularInline):
    model = NewsletterSubscription
    extra = 0
    classes = ['collapse']
    list_display = ('first_name', 'last_name', 'email', 'is_active')
    search_fields = ('first_name', 'last_name', 'email')


class MessageAdminInline(admin.TabularInline):
    model = Message
    extra = 0
    classes = ['collapse']
    list_display = ('name', 'is_active')
    search_fields = ('name')
    list_filter = ('created', 'modified', 'is_active')
    readonly_fields = ('created_by', 'modified_by')


class MessageCategoryAdminInline(admin.TabularInline):
    model = MessagePublicationCategory
    extra = 0
    # classes = ['collapse']
    list_display = ('name', 'category', 'order', 'is_active')
    search_fields = ('name')
    list_filter = ('created', 'modified', 'is_active')
    readonly_fields = ('created_by', 'modified_by')
    # raw_id_fields = ('category',)


class MessageWebpathAdminInline(admin.TabularInline):
    model = MessageWebpath
    extra = 0
    # classes = ['collapse']
    readonly_fields = ('created_by', 'modified_by')
    raw_id_fields = ('webpath',)


class MessagePublicationAdminInline(admin.TabularInline):
    model = MessagePublication
    extra = 0
    # classes = ['collapse']
    readonly_fields = ('created_by', 'modified_by')
    raw_id_fields = ('publication',)


class MessagePublicationContextAdminInline(admin.TabularInline):
    model = MessagePublicationContext
    extra = 0
    # classes = ['collapse']
    readonly_fields = ('created_by', 'modified_by')
    raw_id_fields = ('publication',)


class MessageCalendarContextAdminInline(admin.TabularInline):
    model = MessageCalendarContext
    extra = 0
    # classes = ['collapse']
    readonly_fields = ('created_by', 'modified_by')
    raw_id_fields = ('calendar_context',)


class MessageAttachmentAdminInline(admin.TabularInline):
    model = MessageAttachment
    extra = 0
    # classes = ['collapse']
    readonly_fields = ('created_by', 'modified_by')


class MessageSendingAdminInline(admin.TabularInline):
    model = MessageSending
    extra = 0
    classes = ['collapse']
    readonly_fields = ('date', 'html_file', 'recipients')

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
