import logging

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _

# from cms.contexts.decorators import detect_language

from rest_framework import generics
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.schemas.openapi import AutoSchema
from rest_framework.views import APIView

from cms.api.exceptions import LoggedPermissionDenied
from cms.api.serializers import UniCMSFormSerializer
from cms.api.utils import check_user_permission_on_object
from cms.api.views.generics import UniCMSCachedRetrieveUpdateDestroyAPIView, UniCMSListCreateAPIView, UniCMSListSelectOptionsAPIView, UniCmsApiPagination
from cms.api.views.logs import ObjectLogEntriesList

from .. permissions import NewsletterGetCreatePermissions
from ... forms import *
from ... models import *
from ... serializers import *
from ... settings import NEWSLETTER_MAX_ITEMS_FOR_MANUAL_SENDING


logger = logging.getLogger(__name__)

NEWSLETTER_MAX_ITEMS_FOR_MANUAL_SENDING = getattr(settings,'NEWSLETTER_MAX_ITEMS_FOR_MANUAL_SENDING',
                                                  NEWSLETTER_MAX_ITEMS_FOR_MANUAL_SENDING)


class MessageList(UniCMSListCreateAPIView):
    """
    """
    description = ""
    search_fields = ['name']
    serializer_class = MessageSerializer

    def get_queryset(self):
        """
        """
        newsletter_id = self.kwargs.get('newsletter_id')
        if newsletter_id:
            return Message.objects.filter(newsletter__pk=newsletter_id)
        return Message.objects.none()  # pragma: no cover

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            # get newsletter
            newsletter = serializer.validated_data.get('newsletter')
            # check permissions on newsletter
            permission = check_user_permission_on_object(request.user,
                                                         newsletter)
            if not permission['granted']:
                raise LoggedPermissionDenied(classname=self.__class__.__name__,
                                             resource=request.method)
            return super().post(request, *args, **kwargs)


class MessageView(UniCMSCachedRetrieveUpdateDestroyAPIView):
    """
    """
    description = ""
    permission_classes = [IsAdminUser]
    serializer_class = MessageSerializer

    def get_queryset(self):
        """
        """
        newsletter_id = self.kwargs['newsletter_id']
        message_id = self.kwargs['pk']
        messages = Message.objects.filter(newsletter__pk=newsletter_id,
                                          pk=message_id)
        return messages

    def patch(self, request, *args, **kwargs):
        item = self.get_queryset().first()
        if not item:
            raise Http404
        # get newsletter
        permission = check_user_permission_on_object(request.user,
                                                     item.newsletter)
        if not permission['granted']:
            raise LoggedPermissionDenied(classname=self.__class__.__name__,
                                         resource=request.method)
        return super().patch(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        item = self.get_queryset().first()
        if not item:
            raise Http404
        # get newsletter
        permission = check_user_permission_on_object(request.user,
                                                     item.newsletter)
        if not permission['granted']:
            raise LoggedPermissionDenied(classname=self.__class__.__name__,
                                         resource=request.method)
        return super().put(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        item = self.get_queryset().first()
        if not item:
            raise Http404
        # get newsletter
        permission = check_user_permission_on_object(request.user,
                                                     item.newsletter)
        if not permission['granted']:
            raise LoggedPermissionDenied(classname=self.__class__.__name__,
                                         resource=request.method)
        return super().delete(request, *args, **kwargs)


class MessageFormView(APIView):

    def get(self, *args, **kwargs):
        form = MessageForm(newsletter_id=kwargs.get('newsletter_id'))
        form_fields = UniCMSFormSerializer.serialize(form)
        return Response(form_fields)


class MessageSendingList(UniCMSListCreateAPIView):
    """
    """
    description = ""
    search_fields = []
    filterset_fields = []
    serializer_class = MessageSendingSerializer
    http_method_names = ['get', 'head']

    def get_queryset(self):
        """
        """
        newsletter_id = self.kwargs.get('newsletter_id')
        message_id = self.kwargs.get('pk')
        if newsletter_id and message_id:
            return MessageSending.objects.filter(message__newsletter__pk=newsletter_id,
                                                 message__pk=message_id)
        return MessageSending.objects.none()  # pragma: no cover


class EditorialBoardMessageSendTestSchema(AutoSchema):
    def get_operation_id(self, path, method):# pragma: no cover
        return 'sendEditorialBoardMessageTest'


class MessageSendView(APIView):
    """
    """
    description = ""
    permission_classes = [IsAdminUser]
    # serializer_class = MessageSerializer
    schema = EditorialBoardMessageSendTestSchema()

    def get_queryset(self):
        """
        """
        newsletter_id = self.kwargs['newsletter_id']
        message_id = self.kwargs['pk']
        messages = Message.objects.filter(newsletter__pk=newsletter_id,
                                          pk=message_id)
        return messages

    def post(self, request, *args, **kwargs):
        item = self.get_queryset().first()
        if not item: raise Http404
        # get newsletter
        permission = check_user_permission_on_object(request.user,
                                                     item.newsletter)
        if not permission['granted']:
            raise LoggedPermissionDenied(classname=self.__class__.__name__,
                                         resource=request.method)
        test = request.data.get('test', None)
        if test is None:
            raise ValidationError(_("'test' (true/false) param must be passed"))

        try:
            subscribers = item.newsletter.get_valid_subscribers(test=test)
            if len(subscribers) <= NEWSLETTER_MAX_ITEMS_FOR_MANUAL_SENDING:
                result = item.send(test=test)
                message = _("Test message sent") if test else _("Message sent")
            else:
                item.queued = True
                item.save()
                message = _("Test message queued for the next submission") \
                          if test \
                          else _("Message queued for the next submission")
        except Exception as e:
            raise APIException(detail=e)

        return Response(message)
