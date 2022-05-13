# -*- coding: utf-8 -*-

import os

import requests
import json

from difflib import ndiff
from ipaddress import (ip_network, ip_address, summarize_address_range)
from .exceptions import (BadRequest, ConfigError, RipeDBError)
from .functions import (validate_prefix, is_v6, notify, read_json_file, format_ripe_object, find,
                                    format_cidr)
from .log_manager import LogManager
from .netbox import FetchData
from .configuration import *

# Inetnum defines how Inetnum (IPv4) object look likes in the RIPE-DB
INETNUM = 'inetnum'
# Status of each object (IPv4), which has to be setten by the outgoing object query
STATUS_INETNUM = 'ASSIGNED PA'
# Inet6num defines how Inet6num (IPv6) object look likes in the RIPE-DB
INET6NUM = 'inet6num'
# Status of each object (IPv6), which has to be setten by the outgoing object query
STATUS_INET6NUM = 'ASSIGNED'
# Which headers must be used by each query to RIPE
RIPE_HEADERS = {'Content-Type': 'application/json',
                'Accept': 'application/json; charset=utf-8'}
RIPE_PARAMS = {'password': RIPE_MNT_PASSWORD}

# The main templates file
TEMPLATES = 'templates.json'


class RipeObjectManager():
    def __init__(self, netbox_object, backup):
        logmgr = LogManager()
        self.backup = backup
        self.logger = logmgr.logger
        self.prefix = netbox_object.prefix()

        validate_prefix(self.prefix)

        if is_v6(self.prefix):
            self.objecttype = INET6NUM
            self.status = STATUS_INET6NUM
        else:
            self.objecttype = INETNUM
            self.status = STATUS_INETNUM

        databases = {
                'RIPE': 'https://rest.db.ripe.net/ripe',
                'TEST': 'https://rest-test.db.ripe.net/test',
                }
        searchurls = {
                'RIPE': 'https://rest.db.ripe.net/search',
                'TEST': 'https://rest-test.db.ripe.net/search',
                }

        self.baseurl = databases.get(RIPE_DB)

        if not self.baseurl:
            raise ConfigError('Please set RIPE_DB to RIPE or TEST')

        self.url = f'{self.baseurl}/{self.objecttype}'
        self.searchurl = searchurls.get(RIPE_DB)
        self.username = netbox_object.username()
        self.org = netbox_object.org()
        self.netbox_template = netbox_object.netbox_template()
        self.country = netbox_object.country()

        # always create a backup
        self.backup_ripe_object()

    def get_old_object(self):
        """
        get old object from RIPE DB and returns it as json
        """
        self.logger.info(f'Getting old ripe object {self.prefix}')
        response = requests.get(f'{self.url}/{self.prefix}?unfiltered', headers=RIPE_HEADERS)

        # return object if found
        if response.ok:
            self.logger.info(f'Getting old object has succeeded Return Code: {response.status_code}')
            return response.json()

        # return None if object is not found
        elif response.status_code == 404:
            self.logger.info(f'Object is not existing in RIPE-DB Return Code: {response.status_code}')
            return None

        else:
            self.logger.error(f'Could not query old object, something went wrong! Return Code {response.status_code}')
            # This raise is important to prevent the application from going further
            raise BadRequest('Bad request, something went wrong!')

    def backup_ripe_object(self):
        """
        save json string of an ripe object
        """
        filename = f"prefix_{self.prefix.replace('/', '_')}.json"

        ripe_object = self.get_old_object()
        if ripe_object:
            self.logger.info(f'saving ripe object {filename}')
            self.backup.put(filename, json.dumps(ripe_object))

    def read_local_template(self):
        netbox_template = self.netbox_template
        file = f'{TEMPLATES_DIR}/{TEMPLATES}'
        self.logger.info(f'Reading {netbox_template} in templates file: {file}')
        templates = read_json_file(file)
        selected_template = templates['templates'][netbox_template]
        return selected_template

    def read_master_template(self):
        inherit = self.read_local_template()['inherit']
        file = f'{TEMPLATES_DIR}/{inherit}'
        self.logger.info(f'Reading template file: {file}')
        master_attributes = read_json_file(file)
        master_attributes = master_attributes['attributes']
        return master_attributes

    def overlapped_with(self):
        """
        Checks if there is overlapping and return a candidate, it there is not it returns False
        the overlapped object must be network prefix
        """
        params = {
            'source': RIPE_DB,
            'type-filter': self.objecttype,
            'flags': 'no-referenced',
            'query-string': self.prefix
        }
        request = requests.get(self.searchurl, params=params, headers=RIPE_HEADERS)

        # found matching entry in RIPE DB, this could be the prefix itself or an overlapping prefix
        if request.status_code == 200:
            overlap = request.json()['objects']['object'][0]['primary-key']['attribute'][0]['value']
            if is_v6(self.prefix):
                prefix = ip_network(overlap)
            else:
                cidr = overlap.split(' - ')
                prefix = next(summarize_address_range(ip_address(cidr[0]), ip_address(cidr[1])))

            if prefix != ip_network(self.prefix):
                self.logger.info(f'May overlapped with: {prefix}')
                return prefix

            return False

        # if no prefix is found there is no overlapping prefix
        if request.status_code == 404:
            self.logger.info(f'No overlapping prefix for {self.prefix} found')
            return False

        # something went wrong
        raise RipeDBError(f'Could not query RIPE DB for {self.prefix}: {request}')

    def generate_object(self):
        """
        generates the new object for RIPE DB based on selected template
        """
        # Defining list to gather attributes to prioritize the master_fields
        templates_fields = []
        # Defining list to gather attributes to prioritize the dynamic generated attributes
        master_fields = []
        # Defining list to gather all attributes together
        all_fields = []

        # List of attributes in template
        template_attributes = self.read_local_template()['attributes']
        # List of attributes in master template
        master_attributes = self.read_master_template()

        # Parsing template attributes to check which ones have a value
        for t_attribute in template_attributes:
            for t_name, t_value in t_attribute.items():
                if t_value:
                    if t_name != 'org':
                        templates_fields.append({t_name: t_value})
                    else:
                        self.org = t_value
                    for m_attribute in master_attributes:
                        for m_name, m_value in m_attribute.items():
                            if m_value:
                                master_fields.append({m_name: m_value})
                                if m_name in t_attribute.keys() and m_name != 'descr':
                                    if m_name in t_attribute.keys() and m_name != 'country':
                                        master_fields.remove({m_name: m_value})
                                if m_name == 'org':
                                    self.org = m_value
                                    master_fields.remove({m_name: m_value})

        # List of dynamic generated attributes from prefix, This list is to guarantee the sequence
        dynamic_attributes = [{self.objecttype: self.prefix if is_v6(self.prefix) else format_cidr(self.prefix)},
                              {'netname': self.netbox_template},
                              {'org': self.org},
                              {'country': self.country}]

        # Gathering all templates in one list all_fields
        all_fields.extend(dynamic_attributes)
        all_fields.extend(templates_fields)
        all_fields.extend(master_fields)

        # List for sorted fields, will be used to insert fields in specific sequence inside it
        sorted_fields = []
        i_descr = 0  # Helps to sort one and many descr fields
        i_country = 0  # Helps to sort one and many country fields

        for item in all_fields:
            for key in item.keys():
                if RIPE_DB == 'TEST':
                    # patch attributes, that don't exist in TEST DB
                    if key == 'org':
                        item[key] = RIPE_TEST_ORG
                    if key in ['mnt-by', 'mnt-ref', 'mnt-lower', 'mnt-domains', 'mnt-routes', 'mnt-irt']:
                        item[key] = RIPE_TEST_MNT
                    if key in ['admin-c', 'tech-c', 'abuse-c']:
                        item[key] = RIPE_TEST_PERSON
                    if key == 'source':
                        item[key] = RIPE_DB
                    if key == 'status':
                        # override status, as parent objects with mnt-lower may not be present in TEST-DB
                        item[key] = RIPE_TEST_STATUS_V6 if is_v6(self.prefix) else RIPE_TEST_STATUS_V4
                    self.status = RIPE_TEST_STATUS_V6 if is_v6(self.prefix) else RIPE_TEST_STATUS_V4

                if key == 'descr':
                    # Sort descr fields up second place. Counting from 0
                    sorted_fields.insert(i_descr + 2, item)
                    i_descr += 1
                elif key == 'country':
                    # Sort country fields up fourth place. Counting from 0
                    if i_descr != 0:
                        sorted_fields.insert(i_country + i_descr + 4, item)
                        i_country += 1
                    else:
                        sorted_fields.insert(i_country + i_descr + 4, item)
                        i_country += 1
                else:
                    sorted_fields.append(item)

                # This condition make it possible to overwrite status field
                if key == 'status':
                    status_overwritted = sorted_fields.pop(all_fields.index(item))
                else:
                    status_overwritted = False

        if status_overwritted:
            sorted_fields.insert(len(all_fields)-1, item)
        else:
            sorted_fields.insert(len(all_fields)-1, {'status': self.status})

        obj = {
                'objects': {
                    'object': [{
                        'source': {'id': RIPE_DB},
                        'attributes': {
                            'attribute': [{'name': k, 'value': v} for a in sorted_fields for k, v in a.items() if v]
                        }
                    }]
                }
            }

        self.logger.debug(f'{obj=}')

        return obj

    def post_object(self, new_object):
        # Create object
        self.logger.info(f'CREATE {self.url}')
        request = requests.post(self.url, json=new_object, headers=RIPE_HEADERS, params=RIPE_PARAMS)

        ripe_object, ripe_errors = self.handle_request(request)

        if request.ok:
            notify(format_ripe_object(ripe_object, '+ '), request.request.method, self.prefix, self.username,
                   request.status_code, ripe_errors)

            return
        elif request.status_code == 400:
            overlapped = self.overlapped_with()
            if overlapped:
                netbox = FetchData()
                authorize = netbox.authorize_delete_overlapped_candidate(overlapped)
                if authorize:
                    # Saving old prefix to push after delete
                    cache_prefix = self.prefix

                    self.prefix = overlapped
                    self.delete_object()

                    self.prefix = cache_prefix
                    post = requests.post(self.url, json=new_object, headers=RIPE_HEADERS, params=RIPE_PARAMS)
                    ripe_object, ripe_errors = self.handle_request(post)

                    if post.ok:
                        msg = f'I had to delete overlapped: {overlapped}'
                        ripe_errors = [msg]
                        self.logger.info(msg)
                        notify(format_ripe_object(ripe_object, '+ '), post.request.method, self.prefix, self.username,
                               post.status_code, ripe_errors)

                        return
                else:
                    ripe_errors.append(f'Overlap found for {self.prefix}: {overlapped}')

        notify(format_ripe_object(ripe_object, '+ '), request.request.method, self.prefix, self.username,
               request.status_code, ripe_errors)

        msg = f'Could not create prefix {self.prefix}'
        self.logger.error(msg)
        raise BadRequest(msg)

    def put_object(self, old_object, new_object):
        # Update object
        self.logger.info(f'CREATE {self.url}')
        request = requests.put(f'{self.url}/{self.prefix if is_v6(self.prefix) else format_cidr(self.prefix)}',
                               json=new_object, headers=RIPE_HEADERS, params=RIPE_PARAMS)

        ripe_object, ripe_errors = self.handle_request(request)

        diff = ndiff(format_ripe_object(old_object['objects']['object'][0]).splitlines(keepends=True),
                     format_ripe_object(ripe_object).splitlines(keepends=True))

        if not request.ok:
            msg = f'UPDATE for {self.prefix} failed: {request=} {ripe_errors=}'
            self.logger.error(msg)
            raise BadRequest(msg)

        notify(''.join(diff), request.request.method, self.prefix, self.username,
               request.status_code, ripe_errors)

    def push_object(self):
        """
        entry point if report_ripe is set to true
        determines if post (create) or put (update) should be executed
        """
        old_object = self.get_old_object()
        new_object = self.generate_object()
        self.logger.debug(f'{old_object=}')
        self.logger.debug(f'{new_object=}')

        # if old object exists run update, otherwise create
        if old_object:
            self.put_object(old_object, new_object)
        else:
            self.post_object(new_object)

    def delete_object(self):
        """
        delete object from RIPE DB
        """
        self.logger.info(f'DELETE {self.url}')
        request = requests.delete(f'{self.url}/{self.prefix}', headers=RIPE_HEADERS, params=RIPE_PARAMS)

        ripe_object, ripe_errors = self.handle_request(request)

        if not request.ok:
            msg = f'DELETE for {self.prefix} failed: {request=} {ripe_errors=}'
            self.logger.error(msg)

            # if object is already delete, ok else raise exception
            if request.status_code != 404:
                raise BadRequest(msg)

        notify(format_ripe_object(ripe_object, '-'), request.request.method, self.prefix, self.username,
               request.status_code, ripe_errors)

    def handle_request(self, request):
        self.logger.debug(request)
        response = request.json()
        self.logger.debug(response)

        ripe_objects = find('objects.object', response)
        self.logger.debug(f'{ripe_objects=}')
        ripe_errormessages = find('errormessages.errormessage', response)
        self.logger.debug(f'{ripe_errormessages=}')

        ripe_object = {}
        ripe_errors = []

        if ripe_objects:
            ripe_object = ripe_objects[0]

        if ripe_errormessages:
            ripe_errors = [msg.get('text') for msg in ripe_errormessages]

        if request.ok:
            self.logger.info(f'{request.request.method} {self.prefix} succeeded')
        else:
            self.logger.error(f'{request.request.method} {self.prefix} failed')

        return ripe_object, ripe_errors
