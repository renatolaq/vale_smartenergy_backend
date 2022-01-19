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

class IAMAuthentication(BearerTokenAuthentication):
    def authenticate(self, request):
        """
        WARNING: this class only works with NetIQ Access Manager (NAM) IAM infrastructure.
        Since NAM does not publish the tokeninfo endpoint in the OpenID Connect metadata,
        the URL is hardcoded below.
        We extend drf-oidc-auth's BearerTokenAuthentication class to test the tokeninfo endpoint before
        retrieving userinfo. This allows us to support client_credentials tokens that do not have
        an associated user, by returning a syntetic user object in these cases.
        """
        logger = HandlerLog()
        bearer_token = self.get_bearer_token(request)
        if bearer_token is None:
            return None

        try:
            tokeninfo = self.get_tokeninfo(bearer_token)
            logger.debug("User ID from token = {0}".format(tokeninfo.get('user_id')))
            logger.debug("{0} {1} {2}".format(tokeninfo.get('user_id'), OIDC_AUTH["OIDC_AUDIENCES"], tokeninfo.get('user_id') in OIDC_AUTH["OIDC_AUDIENCES"]))
            if (tokeninfo.get('expires_in') > 0 and tokeninfo.get('audience') in OIDC_AUTH["OIDC_AUDIENCES"] and tokeninfo.get('user_id') in OIDC_AUTH["OIDC_AUDIENCES"]):
                # Received a client credential, userinfo does not work, create a syntetic user dict
                userinfo = {
                    'sub': tokeninfo.get('user_id'),
                    'cn': tokeninfo.get('user_id'),
                    'UserFullName': tokeninfo.get('user_id'),
                    'mail': "inexistent@domain.com",
                    'groupMembership': [
                        'cn=Admin_EN1,ou=SmartEnergy,ou=Groups,o=vale',
                        'cn=Admin_EPME,ou=SmartEnergy,ou=Groups,o=vale'
                    ]
                }
            else:
               userinfo = self.get_userinfo(bearer_token)
        except HTTPError:
            msg = _('Invalid Authorization header. Unable to verify bearer token')
            raise AuthenticationFailed(msg)

        user = api_settings.OIDC_RESOLVE_USER_FUNCTION(request, userinfo)

        return user, userinfo
    
    @cache(ttl=api_settings.OIDC_BEARER_TOKEN_EXPIRATION_TIME)
    def get_tokeninfo(self, token):
        response = requests.get(self.oidc_config['issuer'] + '/tokeninfo',
                                headers={'Authorization': 'Bearer {0}'.format(token.decode('ascii'))})
        response.raise_for_status()
        return response.json()
