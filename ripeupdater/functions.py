# -*- coding: utf-8 -*-

import json
import os
import smtplib
import socket
from email.message import EmailMessage

from ipaddress import ip_network
from .exceptions import ErrorSmallPrefix, NotRoutedNetwork
from .log_manager import LogManager
from .configuration import *

# Dictionary RIPE Documentaion of response codes for each action
RIPE_DOCU_URLS = {'POST': 'https://github.com/RIPE-NCC/whois/wiki/WHOIS-REST-API-Create',
                  'PUT': 'https://github.com/RIPE-NCC/whois/wiki/WHOIS-REST-API-Update',
                  'DELETE': 'https://github.com/RIPE-NCC/whois/wiki/WHOIS-REST-API-Delete'}

logger = LogManager().logger


def read_json_file(template):
    """
    Reading JSON template file and return dict
    """
    if not os.path.exists(template):
        msg = f'No template file {template}'
        logger.critical(msg)
        raise RuntimeError(msg)

    with open(template, 'r') as f:
        dict = json.load(f)
    return dict


def flatten_ripe_attributes(obj):
    """
    flattens ripe attributes
    """
    ripe_attributes = find('attributes.attribute', obj)
    return {attr.get('name'): attr.get('value') for attr in ripe_attributes}


def format_ripe_object(obj, prefix=''):
    """
    expects a ripe_object dict and return a flat string representation
    """
    string = ''
    if obj:
        for key, value in flatten_ripe_attributes(obj).items():
            string += f'{prefix}{key}:\t\t{value}\n'

    return string


def is_v6(prefix):
    return ip_network(prefix).version == 6


def validate_prefix(prefix):
    """
    validate if prefix is valid to be pushed to RIPE DB
    """
    logger.debug('Processing prefix to formating it to valid RIPE format')
    network = ip_network(prefix)

    if is_v6(prefix):

        # Check if prefix big enough; bigger than defined
        if network.prefixlen > int(SMALLEST_PREFIX_V6):
            raise ErrorSmallPrefix(f'This prefix is too small update only bigger than {SMALLEST_PREFIX_V6}')
            return False

        # Check if private network; no need to continue
        if network.is_loopback or \
                network.is_reserved or \
                network.is_private or \
                network.is_multicast or \
                network.is_link_local or \
                not network.is_global:
            raise NotRoutedNetwork('This is not routed prefix, it will be ignored')
            return False
    else:
        # Check if prefix big enough; bigger than defined
        if network.prefixlen > int(SMALLEST_PREFIX_V4):
            raise ErrorSmallPrefix(f'This prefix is too small update only bigger than {SMALLEST_PREFIX_V4}')

        # Check if private network; no need to continue
        if network.is_loopback or \
                network.is_reserved or \
                network.is_private or \
                network.is_multicast:
            raise NotRoutedNetwork('This is not routed prefix, it will be ignored')
            return False

    return True


def format_cidr(prefix):
    """
    change format of prefix to legacy CIDR notation
    """
    network = ip_network(prefix)

    return f'{network[0]} - {network[-1]}'


def notify(ripe_object, action, prefix, username, response_code, ripe_errors):
    """
    This function uses smtplib and sendmail to send mails to the local MTA
    MTA forward it to your recipient. Added to support alarming,
    when something is not working.
    """
    # Read hostname and IP Address to send out within mail
    hostname = socket.gethostname()
    try:
        ipaddr = socket.gethostbyname(hostname)
    except socket.gaierror as err:
        ipaddr = 'unknown'
    # Building mail content
    msg = EmailMessage()
    ripe_errors = '\n'.join(ripe_errors)
    status = 'succeeded' if response_code == 200 else 'failed'
    text = f"""{action} inetnum {prefix} has {status}:
{ripe_errors}
----------------
{ripe_object}
Result: {status}
Action: {action}
Response code: {str(response_code)}
Response codes doc: {RIPE_DOCU_URLS[action]}
Triggered by: {username}
FQDN: {hostname}
RIPE-Service source IP: {ipaddr}
----------------
\nFor more informations check logs
\nYour awesome RIPE-Service!"""

    msg.set_content(text)
    msg['Subject'] = f'{action} {prefix} has {status}'
    msg['From'] = SENDER_MAIL
    msg['To'] = RECIPIENT_MAIL

    logger.debug(msg)

    if MAIL_REPORT == 'yes':
        try:
            logger.debug(f'opening SMTP connection to {SMTP}')
            with smtplib.SMTP(SMTP) as server:
                if SMTP_STARTTLS == 'yes':
                    server.starttls()
                server.send_message(msg)
        except (ConnectionRefusedError, socket.timeout, OSError, smtplib.SMTPServerDisconnected) as err:
            msg = f'unable to connect to SMTP server: {SMTP} - {err}'
            logger.critical(msg)
            raise RuntimeError(msg)


def find(path, obj):
    """
    find an element in a dictionary using a path
    path: 'elem1.elem2.elem3'
    obj: {'elem1': {'elem2': {'elem3': 'foo'}}}
    """
    for elem in path.split('.'):
        obj = obj.get(elem)
        if obj is None:
            break

    return obj
