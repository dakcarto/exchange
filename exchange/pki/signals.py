# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2018 Boundless Spatial
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################

import logging

from requests.exceptions import InvalidSchema
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .ssl_adapter import https_client, SslContextAdapter, get_ssl_context_opts

logger = logging.getLogger(__name__)


# noinspection PyUnusedLocal
@receiver(post_save, sender='pki.HostnamePortSslConfig',
          dispatch_uid='pki_signals_post_save')
def add_update_adapter(sender, instance, created, raw,
                       using, update_fields, **kwargs):
    """
    Respond to HostnamePortSslConfig edits and update https_client cache
    """
    hostname_port = instance.hostname_port
    if not hostname_port:
        logger.error('No hostname:port saved with mapping model, '
                     'can\'t update SSL cache.')
        return

    ssl_config = instance.ssl_config
    if not ssl_config:
        logger.error('No SSL config saved with mapping model, '
                     'updating SSL cache not attempted.')
        return

    # Seed https_client (requests.Session) mounted adapters.
    # The mount() call wraps a dictionary[key] = value assignment, so works
    # for either creation or update.
    base_url = 'https://' + hostname_port.lower()
    try:
        _https_adapter = https_client.get_adapter(base_url)
        _https_adapter.close()  # clean up session pool manager
        # del https_client.adapters[base_url]
        act = 'update'
    except InvalidSchema:
        act = 'add'
        pass

    https_client.mount(base_url,
                       SslContextAdapter(*get_ssl_context_opts(base_url)))
    logger.debug('Signaled session adapter {0} for {1}'.format(act, base_url))


# noinspection PyUnusedLocal
@receiver(post_delete, sender='pki.HostnamePortSslConfig',
          dispatch_uid='pki_signals_post_delete')
def remove_adapter(sender, instance, using, **kwargs):
    """
    Respond to HostnamePortSslConfig deletions and update https_client cache
    """
    hostname_port = instance.hostname_port
    if not hostname_port:
        logger.error('Tried empty hostname:port removal from mapping model, '
                     'removal from SSL cache not attempted.')
        return

    # Remove any matching https_client (requests.Session) mounted adapter
    base_url = 'https://' + hostname_port.lower()
    try:
        _https_adapter = https_client.get_adapter(base_url)
        _https_adapter.close()  # clean up session pool manager
        del https_client.adapters[base_url]
        logger.debug(
            'Signaled session adapter clear for {0}'.format(base_url))
    except InvalidSchema:
        pass
