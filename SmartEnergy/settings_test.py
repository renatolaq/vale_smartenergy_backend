from .settings import *

REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES'] = ['SmartEnergy.auth.IAM_test.IAMTestAuthentication']

MIGRATION_MODULES = {}
for module in INSTALLED_APPS:
    MIGRATION_MODULES[module] = None