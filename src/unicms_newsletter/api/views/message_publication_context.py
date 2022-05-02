import logging

from django.contrib.contenttypes.models import ContentType
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.decorators import method_decorator

# from cms.contexts.decorators import detect_language

from rest_framework import generics
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
# from ... utils import calendar_context_base_filter


logger = logging.getLogger(__name__)


class MessagePublicationContextList(UniCMSListCreateAPIView):
    """
    """
    description = ""
    search_fields = ['publication__publication__title']
    serializer_class = MessagePublicationContextSerializer

    def get_queryset(self):
        """
        """
        newsletter_id = self.kwargs.get('newsletter_id')
        message_id = self.kwargs.get('message_id')
        if newsletter_id and message_id:
            return MessagePublicationContext.objects.filter(message__newsletter__pk=newsletter_id,
                                                            message__pk=message_id)
        return MessagePublicationContext.objects.none()  # pragma: no cover

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            # get newsletter
            message = serializer.validated_data.get('message')
            newsletter = message.newsletter
            # check permissions on newsletter
            permission = check_user_permission_on_object(request.user,
                                                         newsletter)
            if not permission['granted']:
                raise LoggedPermissionDenied(classname=self.__class__.__name__,
                                             resource=request.method)

            return super().post(request, *args, **kwargs)


class MessagePublicationContextView(UniCMSCachedRetrieveUpdateDestroyAPIView):
    """
    """
    description = ""
    permission_classes = [IsAdminUser]
    serializer_class = MessagePublicationContextSerializer

    def get_queryset(self):
        """
        """
        newsletter_id = self.kwargs['newsletter_id']
        message_id = self.kwargs['message_id']
        pubctx_id = self.kwargs['pk']
        message_ctxs = MessagePublicationContext.objects.filter(message__newsletter__pk=newsletter_id,
                                                                message__pk=message_id,
                                                                pk=pubctx_id)
        return message_ctxs

    def patch(self, request, *args, **kwargs):
        item = self.get_queryset().first()
        if not item:
            raise Http404
        # get newsletter
        permission = check_user_permission_on_object(request.user,
                                                     item.message.newsletter)
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
                                                     item.message.newsletter)
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
                                                     item.message.newsletter)
        if not permission['granted']:
            raise LoggedPermissionDenied(classname=self.__class__.__name__,
                                         resource=request.method)
        return super().delete(request, *args, **kwargs)


class MessagePublicationContextFormView(APIView):

    def get(self, *args, **kwargs):
        form = MessagePublicationContextForm(message_id=kwargs.get('message_id'))
        form_fields = UniCMSFormSerializer.serialize(form)
        return Response(form_fields)
