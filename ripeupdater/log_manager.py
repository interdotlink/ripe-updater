# -*- coding: utf-8 -*-

import os
import logging
from flask import has_request_context, request
from .configuration import *

loggers = {}


class RequestFormatter(logging.Formatter):
    def format(self, record):
        if has_request_context():
            record.url = request.url
            record.remote_addr = request.remote_addr
        else:
            record.url = None
            record.remote_addr = None

        return super().format(record)


class LogManager:
    """
    setup loggig
    """
    def __init__(self):
        """
        setup logging
        """
        global loggers

        loglevel = logging.DEBUG if DEBUG == 'yes' else logging.INFO

        if loggers.get('logger'):
            self.logger = loggers.get('logger')
        else:
            self.logger = logging.getLogger('logger')
            formatter = RequestFormatter(
                '[%(asctime)s] [%(process)d] %(remote_addr)s requested %(url)s %(levelname)s in %(module)s: %(message)s'
            )
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.logger.setLevel(loglevel)
            self.logger.addHandler(console_handler)
            loggers['logger'] = self.logger
