"""
Django settings for sge project.
Generated by 'django-admin startproject' using Django 2.2.4.
For more information on this file, see
https://docs.djangoproject.com/en/2.2/topics/settings/
For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.2/ref/settings/
"""

import os

from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

KV_HOST = os.environ.get('KV_NAME')
if KV_HOST is not None:
    KV_HOST = "https://" + KV_HOST + ".vault.azure.net/"
AZURE_CLIENT_ID = os.environ.get('AZURE_CLIENT_ID')
AZURE_CLIENT_SECRET = os.environ.get('AZURE_CLIENT_SECRET')
AZURE_TENANT_ID = os.environ.get('AZURE_TENANT_ID')
CCEE_INTEGRATION_API_URL = None
PME_APP_URL = None
PME_APP_HOST = None
APPINSIGHTS_INSTRUMENTATION_KEY = None
DB_NAME = None
DB_USER = None
DB_PASSWORD = None
DB_HOST = None
DB_PORT = None
DB_DRIVER = None
DB_TEST_NAME = None
DB_TEST_USER = None
DB_TEST_PASSWORD = None
DB_TEST_HOST = None
DB_TEST_PORT = None
IAM_BASE_URL = None
IAM_CLIENT_ID = None
EMAIL_HOST = None
EMAIL_PORT = None
EMAIL_SENDER = None

if KV_HOST is not None and \
    AZURE_CLIENT_ID is not None and \
    AZURE_CLIENT_SECRET is not None and \
    AZURE_TENANT_ID is not None:
        credential = DefaultAzureCredential()
        secret_client = SecretClient(vault_url=KV_HOST, credential=credential)
        CCEE_INTEGRATION_API_URL = secret_client.get_secret('CCEE-INTEGRATION-API-URL').value
        PME_APP_URL = secret_client.get_secret('PME-APP-URL').value
        PME_APP_HOST = secret_client.get_secret('PME-APP-HOST').value
        APPINSIGHTS_INSTRUMENTATION_KEY = secret_client.get_secret('APPINSIGHTS-INSTRUMENTATION-KEY').value
        DB_NAME = secret_client.get_secret('DB-NAME').value
        DB_USER = secret_client.get_secret('DB-USER').value
        DB_PASSWORD = secret_client.get_secret('DB-PASSWORD').value
        DB_HOST = secret_client.get_secret('DB-HOST').value
        DB_PORT = secret_client.get_secret('DB-PORT').value
        DB_DRIVER = secret_client.get_secret('DB-DRIVER').value
        DB_TEST_NAME = secret_client.get_secret('DB-TEST-NAME').value
        DB_TEST_USER = secret_client.get_secret('DB-TEST-USER').value
        DB_TEST_PASSWORD = secret_client.get_secret('DB-TEST-PASSWORD').value
        DB_TEST_HOST = secret_client.get_secret('DB-TEST-HOST').value
        DB_TEST_PORT = secret_client.get_secret('DB-TEST-PORT').value
        IAM_BASE_URL = secret_client.get_secret('IAM-BASE-URL').value
        IAM_CLIENT_ID = secret_client.get_secret('IAM-CLIENT-ID').value
        EMAIL_HOST = secret_client.get_secret('EMAIL-HOST').value
        EMAIL_PORT = secret_client.get_secret('EMAIL-PORT').value
        EMAIL_SENDER = secret_client.get_secret('EMAIL-SENDER').value
else:
    CCEE_INTEGRATION_API_URL = os.environ.get('CCEE_INTEGRATION_API_URL')
    PME_APP_URL = os.environ.get('PME_APP_URL')
    PME_APP_HOST = os.environ.get('PME_APP_HOST')
    APPINSIGHTS_INSTRUMENTATION_KEY = os.environ.get('REACT_APP_APPINSIGHTS_INSTRUMENTATION_KEY')
    DB_NAME = os.environ.get('DB_NAME')
    DB_USER = os.environ.get('DB_USER')
    DB_PASSWORD = os.environ.get('DB_PASSWORD')
    DB_HOST = os.environ.get('DB_HOST')
    DB_PORT = os.environ.get('DB_PORT')
    DB_DRIVER = os.environ.get('DB_DRIVER')
    DB_TEST_NAME = os.environ.get('DB_TEST_NAME')
    DB_TEST_USER = os.environ.get('DB_TEST_USER')
    DB_TEST_PASSWORD = os.environ.get('DB_TEST_PASSWORD')
    DB_TEST_HOST = os.environ.get('DB_TEST_HOST')
    DB_TEST_PORT = os.environ.get('DB_TEST_PORT')
    IAM_BASE_URL = os.environ.get('IAM_BASE_URL')
    IAM_CLIENT_ID = os.environ.get('IAM_CLIENT_ID')
    EMAIL_HOST = os.environ.get('EMAIL_HOST')
    EMAIL_PORT = os.environ.get('EMAIL_PORT')
    EMAIL_SENDER = os.environ.get('EMAIL_SENDER')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '6$bh4u_p7yc&%=%uq$9j$t#h&-90saubg62dff1q%bo)_)0+hf'

DEBUG = True

ALLOWED_HOSTS = ['*']

CORS_ORIGIN_ALLOW_ALL = True
ROOT_URLCONF = 'SmartEnergy.urls'
WSGI_APPLICATION = 'SmartEnergy.wsgi.application'

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, str('static'))

MEDIA_URL = '/uploads/'
MEDIA_ROOT = os.path.join(BASE_DIR, str('uploads'))

# Application definition
INSTALLED_APPS = [
    'django_filters',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_swagger',
    'corsheaders',
    'core',
    'company',
    'gauge_point',
    'balance_report_market_settlement',
    'consumption_metering_reports',
    'energy_composition',
    'agents',
    'profiles',
    'asset_items',
    'organization',
    'assets',
    'energy_contract',
    'cliq_contract',
    'transfer_contract_priority',
    'global_variables',
    'statistical_indexes',
    'manual_import',
    'usage_contract',
    'budget',
    'plan_monitoring',
    'contract_allocation_parameters',
    'contract_allocation_report',
    'occurrence_record',
    'contract_dispatch',
    'notifications'
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.locale.LocaleMiddleware',
]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, str("templates"))],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.i18n',
            ],
        },
    },
]

_smartenergyappikey = APPINSIGHTS_INSTRUMENTATION_KEY

if _smartenergyappikey is not None:
    MIDDLEWARE.append('opencensus.ext.django.middleware.OpencensusMiddleware')
    OPENCENSUS = {
        'TRACE': {
            'SAMPLER': 'opencensus.trace.samplers.ProbabilitySampler(rate=1)',
            'EXPORTER': '''opencensus.ext.azure.trace_exporter.AzureExporter(
                connection_string='InstrumentationKey='''+_smartenergyappikey+'\')',
        }
    }
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'verbose': {
                'format' : "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
                'datefmt' : "%d/%b/%Y %H:%M:%S"
            }
        },
        'handlers': {
            'azure': {
                'level': 'DEBUG',
                'class': 'opencensus.ext.azure.log_exporter.AzureLogHandler',
                'instrumentation_key': _smartenergyappikey,
            },
            'console': {
                'level': 'INFO',
                'class': 'logging.StreamHandler',
            },
        },
        'loggers': {
            'django': {
                'handlers': ['azure', 'console'],
                'level': 'INFO',
                'propagate': True,
            },
        },
    }
else:
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'verbose': {
                'format' : "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
                'datefmt' : "%d/%b/%Y %H:%M:%S"
            }
        },
        'handlers': {
            'console': {
                'level': 'INFO',
                'class': 'logging.StreamHandler',
            },
        },
        'loggers': {
            'django': {
                'handlers': ['console'],
                'level': 'INFO',
                'propagate': True,
            },
        },
    }

WSGI_APPLICATION = 'SmartEnergy.wsgi.application'

# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases

print('DATABASE NAME: ' + DB_NAME)
DATABASES = {
    'default': {
        'ENGINE': 'sql_server.pyodbc',
        'NAME': DB_NAME,
        'USER': DB_USER,
        'PASSWORD': DB_PASSWORD,
        'HOST': DB_HOST,
        'PORT': DB_PORT,
        'OPTIONS': {
            'driver': DB_DRIVER or 'ODBC Driver 17 for SQL Server'
        },
        # only for test
        'TEST': {
            'ENGINE': 'sql_server.pyodbc',
            'NAME': DB_TEST_NAME,
            'USER': DB_TEST_USER,
            'PASSWORD': DB_TEST_PASSWORD,
            'HOST': DB_TEST_HOST,
            'PORT': DB_TEST_PORT,
            'OPTIONS': {
                'driver': DB_DRIVER or 'ODBC Driver 17 for SQL Server'
            },
        },
    },
}

REST_FRAMEWORK = {
    # Use Django's standard `django.contrib.auth` permissions,
    # or allow read-only access for unauthenticated users.
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated', # Enable OIDC Auth
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        # Add support for drf-oidc-auth module
        'SmartEnergy.auth.IAM.IAMAuthentication' # Enable OIDC Auth
    ],
    'DEFAULT_SCHEMA_CLASS': 'rest_framework.schemas.coreapi.AutoSchema',
    'TEST_REQUEST_DEFAULT_FORMAT': 'json',
    'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend'],
}

OIDC_AUTH = {
    # Specify OpenID Connect endpoint. Configuration will be
    # automatically done based on the discovery document found
    # at <endpoint>/.well-known/openid-configuration
    # IAM Dev
    #'OIDC_ENDPOINT': 'https://ids-dev.valeglobal.net/nidp/oauth/nam',
    # IAM QA
    #'OIDC_ENDPOINT': 'https://ids-qa.valeglobal.net/nidp/oauth/nam',
    'OIDC_ENDPOINT': IAM_BASE_URL + '/nidp/oauth/nam',

    # Accepted audiences the ID Tokens can be issued to
    # IAM Dev
    #'OIDC_AUDIENCES': ('ad441ce4-eb7e-4634-8eca-2c84ec40ed46',),
    # IAM QA
    #'OIDC_AUDIENCES': ('56fe47ce-0423-4bf1-8778-5b4904770579',),
    'OIDC_AUDIENCES': (IAM_CLIENT_ID,),

    # (Optional) Function that resolves id_token into user.
    # This function receives a request and an id_token dict and expects to
    # return a User object. The default implementation tries to find the user
    # based on username (natural key) taken from the 'sub'-claim of the
    # id_token.
    'OIDC_RESOLVE_USER_FUNCTION': 'SmartEnergy.auth.get_user',

    # (Optional) Number of seconds in the past valid tokens can be 
    # issued (default 600)
    'OIDC_LEEWAY': 60*60,

    # (Optional) Time before signing keys will be refreshed (default 24 hrs)
    'OIDC_JWKS_EXPIRATION_TIME': 24*60*60,

    # (Optional) Time before bearer token validity is verified again (default 10 minutes)
    'OIDC_BEARER_TOKEN_EXPIRATION_TIME': 10*60,

    # (Optional) Token prefix in JWT authorization header (default 'JWT')
    'JWT_AUTH_HEADER_PREFIX': 'JWT',

    # (Optional) Token prefix in Bearer authorization header (default 'Bearer')
    'BEARER_AUTH_HEADER_PREFIX': 'Bearer',

    # (Optional) Which Django cache to use
    'OIDC_CACHE_NAME': 'default',

    # (Optional) A cache key prefix when storing and retrieving cached values
    'OIDC_CACHE_PREFIX': 'oidc_auth.',
}

# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

# AUTH_PASSWORD_VALIDATORS = [
#     {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator', },
#     {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', },
#     {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator', },
#     {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator', },
# ]

# Internationalization
# https://docs.djangoproject.com/en/2.2/topics/i18n/
ugettext = lambda s: s
LANGUAGES = (
    ('en-us', ugettext('English')),
    ('pt-br', ugettext('Portuguese')),
)

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/

DEFAULT_CHARSET = 'utf-8'
