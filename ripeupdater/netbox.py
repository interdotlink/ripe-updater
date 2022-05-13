# -*- coding: utf-8 -*-

import os

import pynetbox

from iso3166 import countries_by_alpha2, countries_by_name
from .exceptions import MissingDataFromNetbox
from .functions import read_json_file
from .log_manager import LogManager
from .configuration import *

# Name of Lir Org mapping template
LIR_ORG = 'lir_org.json'


class FetchData:
    def __init__(self):
        self.logger = LogManager().logger
        self.nb = pynetbox.api(NETBOX_URL, token=NETBOX_TOKEN)

    def authorize_delete_overlapped_candidate(self, overlapped_candidate):
        """
        if overlapped_candidated is not a prefix nor an aggregate in netbox
        return True to indicate this candidate should be deleted from RIPE DB
        """
        is_prefix = bool(self.nb.ipam.prefixes.get(prefix=str(overlapped_candidate)))
        is_aggregate = bool(self.nb.ipam.aggregates.get(prefix=str(overlapped_candidate)))
        self.logger.debug(f'Searched inside netbox for {overlapped_candidate=}, result: \
                          {is_prefix=} {is_aggregate=}')

        # Return Ture is the overlapped_object is neither aggregate nor prefix
        if is_aggregate or is_prefix:
            self.logger.warning(f'Overlapped_candidate {overlapped_candidate} found in NetBox \
                    {is_prefix=} {is_aggregate=}')
            return False
        else:
            self.logger.info('Overlapped object is neither aggregate nor prefix, \
                        authorized to delete it from RIPE-DB')
            return True

    def org(self, prefix):
        """
        lookup lir in parent aggregate for prefix and return matching RIPE org
        """
        template = f'{TEMPLATES_DIR}/{LIR_ORG}'
        dict_template = read_json_file(template)
        dict_template = dict_template['templates']['lir_org'].items()

        aggregate = self.nb.ipam.aggregates.get(q=prefix)
        netbox_lir = aggregate.custom_fields['lir']
        # be compatible with older netbox api
        if type(netbox_lir) is dict:
            netbox_lir = netbox_lir['label']
        netbox_lir = netbox_lir.lower()

        self.logger.info('Defining the suitable RIPE Org attribute')
        for lir, org in dict_template:
            if netbox_lir == lir:
                return org

        return None

    def country(self, site_slug):
        """
        This methode get for a prefix's country in ISO3166-II format
        ISO3166-II is expected from RIPE database
        """
        site = self.nb.dcim.sites.get(slug=site_slug)
        region = self.nb.dcim.regions.get(slug=site.region.slug)

        self.logger.info('Finding the suitable ISO country name, which RIPE accepts')
        while region:
            country = region.slug.upper()
            self.logger.debug(f'testing region {country}')
            if country in countries_by_name:
                country_alpha2 = countries_by_name[country].alpha2
                return country_alpha2
            
            region = region.parent

        return None


class ObjectBuilder:
    """
    This class describs methodes to return catchable data from Netbox webhook
    """
    def __init__(self, webhook):
        self.logger = LogManager().logger
        self.webhook = webhook
        self.logger.info('Parsing incoming prefix from Netbox')
        fetch_data = FetchData()
        self.country_netbox = fetch_data.country
        self.org_netbox = fetch_data.org

    def prefix(self):
        """
        returns prefix as string
        """
        data = self.webhook

        try:
            prefix = data['data']['prefix']

        except TypeError:
            msg = 'No selected prefix in Netbox'
            self.logger.error(msg)
            raise MissingDataFromNetbox(msg)

        self.logger.info(f'Prefix: {str(prefix)}')
        return prefix

    def username(self):
        """
        returns webhook trigger (username) as string
        """
        data = self.webhook

        try:
            username = data['username']

        except TypeError:
            msg = 'No given user in Netbox webhook, RIPE_Service expects a username'
            self.logger.warning(msg)
            username = 'None'

        self.logger.info(f'User: {str(username)}')
        return username

    def netbox_template(self):
        """
        Returns netbox_template as string
        """
        data = self.webhook

        custom_fields = data['data']['custom_fields']
        ripe_report = self.ripe_report()
        ripe_template = custom_fields.get('ripe_template')
        # be compatible with older netbox api
        if type(ripe_template) is dict:
            ripe_template = ripe_template['label']

        if not ripe_report:
            return None

        try:
            netbox_template = ripe_template.upper()
        except TypeError:
            msg = 'No selected ripe_template in Netbox'
            self.logger.error(msg)
            raise MissingDataFromNetbox(msg)

        netbox_template = str(netbox_template)
        self.logger.info('netbox_template: ' + netbox_template)
        return netbox_template

    def ripe_report(self):
        """
        Returns ripe_report as bool
        """
        data = self.webhook

        custom_fields = data['data']['custom_fields']
        ripe_report = custom_fields.get('ripe_report', False)
        self.logger.info(f'Report to RIPE is set: {ripe_report=}')
        if ripe_report is True:
            return ripe_report
        else:
            return False

    def country(self):
        """
        Returns country as string
        """
        data = self.webhook

        try:
            site_slug = data['data']['site']['slug']
            country = self.country_netbox(site_slug)
        except TypeError:
            default_country = DEFAULT_COUNTRY.upper()
            if countries_by_alpha2[default_country]:
                country = default_country
            else:
                self.logger.error('Default country must be in iso alpha2 format')

        self.logger.info(f'Country: {str(country)}')
        return country

    def org(self):
        """
        returns RIPE org as string
        """
        prefix = self.prefix()
        org = self.org_netbox(prefix)
        self.logger.info(f'Org: {str(org)}')
        return org
