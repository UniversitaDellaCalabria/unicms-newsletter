from cms.api.permissions import UNICMSUserGetCreatePermissions


class NewsletterGetCreatePermissions(UNICMSUserGetCreatePermissions):
    """
    """

    def has_permission(self, request, view):
        return super().has_permission(request, view, 'unicms_newsletter', 'newsletter')


class MessageGetCreatePermissions(UNICMSUserGetCreatePermissions):
    """
    """

    def has_permission(self, request, view):
        return super().has_permission(request, view, 'unicms_newsletter', 'message')
