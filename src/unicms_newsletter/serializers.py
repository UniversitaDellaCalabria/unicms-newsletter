from django.urls import reverse
from django.utils import timezone

from cms.api.serializers import UniCMSContentTypeClass, UniCMSCreateUpdateSerializer
from cms.contexts.serializers import WebPathSerializer
from cms.medias.serializers import MediaSerializer
from cms.publications.serializers import (CategorySerializer,
                                          PublicationSerializer,
                                          PublicationContextSerializer,
                                          WebPathForeignKey)

from rest_framework import serializers

from . models import *
from . settings import *


class NewsletterSerializer(UniCMSCreateUpdateSerializer,
                           UniCMSContentTypeClass):

    class Meta:
        model = Newsletter
        fields = '__all__'
        read_only_fields = ('created_by', 'modified_by')


class NewsletterForeignKey(serializers.PrimaryKeyRelatedField):
    def get_queryset(self):
        request = self.context.get('request', None)
        if request:
            newsletter_id = self.context['request'].parser_context['kwargs']['newsletter_id']
            return Newsletter.objects.filter(pk=newsletter_id)
        return None # pragma: no cover


class NewsletterSubscriptionSerializer(UniCMSCreateUpdateSerializer,
                                       UniCMSContentTypeClass):

    newsletter = NewsletterForeignKey()
    class Meta:
        model = NewsletterSubscription
        fields = '__all__'
        read_only_fields = ('created_by', 'modified_by')


class NewsletterTestSubscriptionSerializer(UniCMSCreateUpdateSerializer,
                                           UniCMSContentTypeClass):

    class Meta:
        model = NewsletterTestSubscription
        fields = '__all__'
        read_only_fields = ('created_by', 'modified_by')


class MessageSerializer(UniCMSCreateUpdateSerializer,
                        UniCMSContentTypeClass):

    def to_internal_value(self, data):
        if data.get('date_start') == '':
            data['date_start'] = None
        if data.get('date_end') == '':
            data['date_end'] = None
        return super().to_internal_value(data)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.banner:
            banner = MediaSerializer(instance.banner)
            data['banner'] = banner.data
        data['preview'] = f'/{settings.CMS_PATH_PREFIX}{CMS_NEWSLETTER_VIEW_PREFIX_PATH}/{instance.newsletter.slug}/{CMS_NEWSLETTER_MESSAGE_SUB_PATH}/{instance.pk}/'
        return data

    class Meta:
        model = Message
        fields = '__all__'
        read_only_fields = ('created_by', 'modified_by')


class MessageAttachmentSerializer(UniCMSCreateUpdateSerializer,
                                  UniCMSContentTypeClass):

    class Meta:
        model = MessageAttachment
        fields = '__all__'
        read_only_fields = ('created_by', 'modified_by')


class MessagePublicationSerializer(UniCMSCreateUpdateSerializer,
                                  UniCMSContentTypeClass):

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.publication:
            publication = PublicationSerializer(instance.publication)
            data['publication_data'] = publication.data
        return data

    class Meta:
        model = MessagePublication
        fields = '__all__'
        read_only_fields = ('created_by', 'modified_by')


class MessagePublicationContextSerializer(UniCMSCreateUpdateSerializer,
                                          UniCMSContentTypeClass):

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.publication:
            # publication = PublicationContextSerializer(instance.publication)
            data['publication_data'] = instance.publication.__str__()
        return data

    class Meta:
        model = MessagePublicationContext
        fields = '__all__'
        read_only_fields = ('created_by', 'modified_by')


class MessageCategorySerializer(UniCMSCreateUpdateSerializer,
                                UniCMSContentTypeClass):

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.category:
            category = CategorySerializer(instance.category)
            data['category_data'] = category.data
        return data

    class Meta:
        model = MessagePublicationCategory
        fields = '__all__'
        read_only_fields = ('created_by', 'modified_by')


class MessageWebpathSerializer(UniCMSCreateUpdateSerializer,
                               UniCMSContentTypeClass):

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.webpath:
            data['webpath_data'] = instance.webpath.__str__()
        return data

    class Meta:
        model = MessageWebpath
        fields = '__all__'
        read_only_fields = ('created_by', 'modified_by')


class MessageSendingSerializer(UniCMSCreateUpdateSerializer,
                               UniCMSContentTypeClass):

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['message_name'] = instance.message.name
        data['html_file'] = instance.view_html()
        return data

    class Meta:
        model = MessageSending
        fields = '__all__'
        # read_only_fields = ('__all__')
