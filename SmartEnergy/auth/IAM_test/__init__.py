from django.utils.translation import ugettext as _
import requests
from requests import request
from requests.exceptions import HTTPError
from rest_framework.exceptions import AuthenticationFailed
from oidc_auth.authentication import BearerTokenAuthentication
from oidc_auth.settings import api_settings
from oidc_auth.util import cache
from SmartEnergy.settings import OIDC_AUTH
from SmartEnergy.handler_logging import HandlerLog
from SmartEnergy.auth import groups, permissions


class IAMTestAuthentication(BearerTokenAuthentication):
    def authenticate(self, request):
        """
        WARNING: this class only works with NetIQ Access Manager (NAM) IAM infrastructure.
        Since NAM does not publish the tokeninfo endpoint in the OpenID Connect metadata,
        the URL is hardcoded below.
        We extend drf-oidc-auth's BearerTokenAuthentication class to test the tokeninfo endpoint before
        retrieving userinfo. This allows us to support client_credentials tokens that do not have
        an associated user, by returning a syntetic user object in these cases.
        """
        userinfo = {
            'sub': "test_user",
            'cn': "test_user",
            'mail': "test_user@vale.com",
            'groupMembership': [
                "cn=Admin_APN1,ou=SmartEnergy,ou=Groups,o=vale",
                "cn=Admin_APN2,ou=SmartEnergy,ou=Groups,o=vale",
                "cn=Admin_APN3,ou=SmartEnergy,ou=Groups,o=vale",
                "cn=Admin_EN1,ou=SmartEnergy,ou=Groups,o=vale",
                "cn=Admin_EN2,ou=SmartEnergy,ou=Groups,o=vale",
                "cn=Admin_EPME,ou=SmartEnergy,ou=Groups,o=vale"
            ],
            'UserFullName': "test_user"
        }
        user = api_settings.OIDC_RESOLVE_USER_FUNCTION(request, userinfo)
        return user, userinfo

    def get_bearer_token(self, request):
        return "TOKEN"
