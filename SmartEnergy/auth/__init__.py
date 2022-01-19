from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission, ContentType
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied
import SmartEnergy.auth.permissions as permissions
import SmartEnergy.auth.groups as groups
import SmartEnergy.auth.modules as modules
import SmartEnergy.auth.companies as companies

_iambaseou = ',ou=SmartEnergy,ou=Groups,o=vale'
_iamcompanybaseou = ',ou=Companies' + _iambaseou

_user_group_map = {}
_user_company_map = {}
_user_company_list_map = {}
_user_isadmin_map = {}

def get_user(request, id_token):
    User = get_user_model()
    try:
        user = User.objects.get(username=id_token.get('sub'))
    except User.DoesNotExist:
        if id_token.get('sub') is not None:
            user = User.objects.create_user(username=id_token.get('sub'), email=id_token.get('mail'))
        else:
            msg = 'Invalid Authorization header. User not found.'
            raise AuthenticationFailed(msg)
    # Rebuild list of groups and companies user belongs to from list passed by IAM
    ug = []
    cg = []
    cl = []
    isadmin = False
    grouplist = id_token.get('groupMembership')
    if (grouplist is not None):
        for g in grouplist:
            try:
                if g.endswith(_iambaseou):
                    perm = g.split(',')[0][3:]
                    if g.endswith(_iamcompanybaseou):
                        temp = perm.split('_')
                        company = temp[0]
                        access = temp[1]
                        cg.append(company + '_' + access)
                        ug.append(groups.company + '_' + access)
                        cl.append(company)
                    else:
                        ug.append(perm)
                        if (perm[0:5] == 'Admin'):
                            isadmin = True
            except KeyError:
                continue
    _user_group_map[user.username] = ug
    _user_company_map[user.username] = cg
    _user_company_list_map[user.username] = cl
    _user_isadmin_map[user.username] = isadmin
    return user

def check_permission(group, permissions):
    def decorator(drf_custom_method):
        def _decorator(self, *args, **kwargs):
            try:
                user = self.request.user
            except AttributeError:
                user = self.user
            if user.is_authenticated:
                if user.username in _user_group_map:
                    for permission in permissions:
                        if (group+'_'+permission) in _user_group_map[user.username]:
                            return drf_custom_method(self, *args, **kwargs)
                raise PermissionDenied()
            else:
                raise AuthenticationFailed()
        return _decorator
    return decorator

def has_permission(user, group, permissions):
    try:
        for permission in permissions:
            if (group+'_'+permission) in _user_group_map[user.username]:
                return True
    except KeyError:
        pass
    return False

def check_module(module, permissions):
    def decorator(drf_custom_method):
        def _decorator(self, *args, **kwargs):
            try:
                user = self.request.user
            except AttributeError:
                user = self.user
            if user.is_authenticated:
                if user.username in _user_group_map:
                    for group in module:
                        for permission in permissions:
                            if (group+'_'+permission) in _user_group_map[user.username]:
                                return drf_custom_method(self, *args, **kwargs)
                raise PermissionDenied()
            else:
                raise AuthenticationFailed()
        return _decorator
    return decorator

def has_company_permission(user, company, permissions):
    try:
        for permission in permissions:
            if (company+'_'+permission) in _user_company_map[user.username]:
                return True
    except KeyError:
        pass
    return False

def is_administrator(user):
    return _user_isadmin_map[user.username]

def get_user_companies(user):
    return _user_company_list_map[user.username]