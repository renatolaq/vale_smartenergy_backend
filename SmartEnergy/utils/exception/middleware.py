from opencensus.trace import config_integration
from opencensus.ext.azure.log_exporter import AzureLogHandler
from SmartEnergy.settings import _smartenergyappikey
from datetime import datetime, timezone
import logging

class AppInsightsExceptionMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

        config_integration.trace_integrations(['logging'])
        self.azure_logger = logging.getLogger(__name__)
        handler = AzureLogHandler(connection_string='InstrumentationKey='+ _smartenergyappikey)
        handler.setFormatter(logging.Formatter('[EXCEPTION] :: '+ datetime.now(timezone.utc).strftime("%d-%m-%Y %H:%M:%S")  + ' :: %(message)s'))
        self.azure_logger.addHandler(handler)

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        print(repr(exception))
        self.azure_logger.exception(exception)
        return None
