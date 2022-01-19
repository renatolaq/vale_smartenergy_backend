import logging
from datetime import datetime, timezone


class HandlerLog:
    logger = logging.getLogger('django')

    def debug(self, msg):
        self.logger.debug('[DEBUG] :: '+ datetime.now(timezone.utc).strftime("%d-%m-%Y %H:%M:%S")  + ' :: ' + msg)

    def info(self, msg):
        self.logger.info('[INFO] :: '+ datetime.now(timezone.utc).strftime("%d-%m-%Y %H:%M:%S")  + ' :: ' + msg)
    
    def error(self, msg):
        self.logger.error('[ERROR] :: '+ datetime.now(timezone.utc).strftime("%d-%m-%Y %H:%M:%S")  + ' :: ' + msg)

    def warning(self, msg):
        self.logger.warning('[WARNING] :: '+ datetime.now(timezone.utc).strftime("%d-%m-%Y %H:%M:%S")  + ' :: ' + msg)
