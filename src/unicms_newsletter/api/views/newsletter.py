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


class NewsletterList(UniCMSListCreateAPIView):
    """
    """
    description = ""
    search_fields = ['name', 'description']
    permission_classes = [NewsletterGetCreatePermissions]
    serializer_class = NewsletterSerializer
    queryset = Newsletter.objects.all()


class NewsletterView(UniCMSCachedRetrieveUpdateDestroyAPIView):
    """
    """
    description = ""
    permission_classes = [IsAdminUser]
    serializer_class = NewsletterSerializer

    def get_queryset(self):
        """
        """
        newsletter_id = self.kwargs['pk']
        newsletters = Newsletter.objects.filter(pk=newsletter_id)
        return newsletters

    def patch(self, request, *args, **kwargs):
        item = self.get_queryset().first()
        if not item:
            raise Http404
        permission = check_user_permission_on_object(request.user,
                                                     item)
        if not permission['granted']:
            raise LoggedPermissionDenied(classname=self.__class__.__name__,
                                         resource=request.method)
        return super().patch(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        item = self.get_queryset().first()
        if not item:
            raise Http404
        permission = check_user_permission_on_object(request.user,
                                                     item)
        if not permission['granted']:
            raise LoggedPermissionDenied(classname=self.__class__.__name__,
                                         resource=request.method)
        return super().put(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        item = self.get_queryset().first()
        if not item:
            raise Http404
        permission = check_user_permission_on_object(request.user,
                                                     item, 'delete')
        if not permission['granted']:
            raise LoggedPermissionDenied(classname=self.__class__.__name__,
                                         resource=request.method)
        return super().delete(request, *args, **kwargs)


class NewsletterSubscriptionList(UniCMSListCreateAPIView):
    """
    """
    description = ""
    search_fields = ['email', 'last_name']
    filterset_fields = ['is_active', 'email', 'last_name', 'html',
                        'date_unsubscription', 'date_subscription']
    serializer_class = NewsletterSubscriptionSerializer

    def get_queryset(self):
        """
        """
        newsletter_id = self.kwargs.get('newsletter_id')
        if newsletter_id:
            return NewsletterSubscription.objects.filter(newsletter__pk=newsletter_id)
        return NewsletterSubscription.objects.none()  # pragma: no cover

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


class NewsletterSubscriptionView(UniCMSCachedRetrieveUpdateDestroyAPIView):
    """
    """
    description = ""
    permission_classes = [IsAdminUser]
    serializer_class = NewsletterSubscriptionSerializer

    def get_queryset(self):
        """
        """
        newsletter_id = self.kwargs['newsletter_id']
        subscription_id = self.kwargs['pk']
        subscriptions = NewsletterSubscription.objects.filter(newsletter__pk=newsletter_id,
                                                              pk=subscription_id)
        return subscriptions

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


class NewsletterSubscriptionFormView(APIView):

    def get(self, *args, **kwargs):
        form = NewsletterSubscriptionForm(newsletter_id=kwargs.get('newsletter_id'))
        form_fields = UniCMSFormSerializer.serialize(form)
        return Response(form_fields)

class NewsletterTestSubscriptionFormView(APIView):

    def get(self, *args, **kwargs):
        form = NewsletterTestSubscriptionForm(newsletter_id=kwargs.get('newsletter_id'))
        form_fields = UniCMSFormSerializer.serialize(form)
        return Response(form_fields)


class NewsletterTestSubscriptionList(NewsletterSubscriptionList):
    """
    """
    filterset_fields = ['email', 'last_name', 'html']
    serializer_class = NewsletterTestSubscriptionSerializer

    def get_queryset(self):
        """
        """
        newsletter_id = self.kwargs.get('newsletter_id')
        if newsletter_id:
            return NewsletterTestSubscription.objects.filter(newsletter__pk=newsletter_id)
        return NewsletterTestSubscription.objects.none()  # pragma: no cover


class NewsletterTestSubscriptionView(NewsletterSubscriptionView):
    """
    """
    serializer_class = NewsletterTestSubscriptionSerializer

    def get_queryset(self):
        newsletter_id = self.kwargs['newsletter_id']
        subscription_id = self.kwargs['pk']
        subscriptions = NewsletterTestSubscription.objects.filter(newsletter__pk=newsletter_id,
                                                                  pk=subscription_id)
        return subscriptions


class NewsletterFormView(APIView):

    def get(self, *args, **kwargs):
        form = NewsletterForm()
        form_fields = UniCMSFormSerializer.serialize(form)
        return Response(form_fields)


class NewsletterLogsSchema(AutoSchema):
    def get_operation_id(self, path, method):# pragma: no cover
        return 'listNewsletterLogs'


class NewsletterLogsView(ObjectLogEntriesList):

    schema = NewsletterLogsSchema()

    def get_queryset(self, **kwargs):
        """
        """
        object_id = self.kwargs['pk']
        item = get_object_or_404(Newsletter, pk=object_id)
        content_type_id = ContentType.objects.get_for_model(item).pk
        return super().get_queryset(object_id, content_type_id)
