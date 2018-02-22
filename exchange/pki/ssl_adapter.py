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

import re
# We need import ssl to fail if it can't be imported.
# urllib3.create_urllib3_context() will create a context without support for
# PKI private key password otherwise.
import ssl
import traceback
import logging

from ssl import Purpose, SSLError
from requests.adapters import HTTPAdapter
from requests import Session, RequestException
from urllib3.util.ssl_ import (create_urllib3_context,
                               resolve_ssl_version,
                               resolve_cert_reqs)
from urllib3.util.retry import Retry
# noinspection PyCompatibility
from urlparse import urlparse, parse_qsl
from urllib import urlencode

from .utils import hostname_port, requests_base_url, normalize_hostname
from .models import HostnamePortSslConfig, SslConfig


logger = logging.getLogger(__name__)


class SslContextAdapter(HTTPAdapter):
    """
    A requests TransportAdapter that enables manipulation of its SSL context.

    For some defaults, see `import ssl; dir(ssl)` for what your Python's ssl
    module supports via the dynamically loaded symbols from OpenSSL.

    :param context_create_options: ssl.context creation options, accepts any:
        (defaults shown are supplied by urllib3, when adapter value is None)
        ssl_version=ssl.PROTOCOL_SSLv23
          accepts: None or a PROTOCOL_* enum loaded from OpenSSL
        cert_reqs=ssl.CERT_REQUIRED
          accepts: None or one of CERT_NONE, CERT_OPTIONAL, CERT_REQUIRED
        options=ssl.OP_NO_SSLv2 | ssl.OP_NO_SSLv3 | ssl.OP_NO_COMPRESSION
          accepts: None or ssl.OP_* client-side enums loaded from OpenSSL
        ciphers=urllib3.util.ssl_.DEFAULT_CIPHERS
          accepts: None or string of OpenSSL ciphers
          see: https://wiki.openssl.org/index.php/Manual:Ciphers(1)
               and (https://www.openssl.org/docs/man1.0.2/apps/ciphers.html
               or https://www.openssl.org/docs/man1.1.0/apps/ciphers.html)

    :param context_options: ssl.context options, accepts any:
        cafile=None
          accepts: None or path to contatenated PEM file of CAs
        certfile=None
          accepts: None or path to PEM file of client cert (with no key)
        keyfile=None
          accepts: None or path to PEM file of client cert key (path required
                   if certfile path defined)
        password=None
          accepts: None or password string

    :param adapter_options: HTTPAdapter options defaults, accepts any:
        https_retries=3
          accepts: None, int >= 0 or False
          (0 does not retry; False does the same, but skips rasising)
        https_redirects=3
          accepts: None, int >= 0 or False
          (0 does not redirect; False does the same, but skips rasising)
    """
    def __init__(self, context_create_options, context_options,
                 adapter_options, *args, **kwargs):
        self._ctx_create_opts = context_create_options
        self._ctx_opts = context_options
        self._adptr_opts = adapter_options

        # set up adapter options
        _retries = self._adptr_opts.get('retries', None)
        _redirects = self._adptr_opts.get('redirects', None)
        if _retries is not None:  # needs int; redirects can be None
            kwargs['max_retries'] = Retry(
                total=_retries,
                redirect=_redirects,
                backoff_factor=0.9,
                status_forcelist=[502, 503, 504],
                method_whitelist={'HEAD', 'TRACE', 'GET', 'PUT',
                                  'POST', 'OPTIONS', 'DELETE'},
            )

        super(SslContextAdapter, self).__init__(*args, **kwargs)

    @staticmethod
    def _normalize_hostname(url):
        """
        Replace url with same URL, but with lowercased hostname
        :param url: A URL
        :rtype: basestring
        """
        parts = urlparse(url)
        return re.sub(parts.hostname, parts.hostname, url, count=1, flags=re.I)

    def context_options(self):
        return self._ctx_create_opts, self._ctx_opts, self._adptr_opts

    def _update_context(self, context):
        """
        :type context: ssl.SSLContext
        """
        cafile = self._ctx_opts.get('cafile', None)
        if cafile:
            context.load_verify_locations(cafile=cafile)
        else:
            # TODO: Will loaded defaults be overridden later by socket wrap?
            context.load_default_certs(purpose=Purpose.SERVER_AUTH)

        certfile = self._ctx_opts.get('certfile', None)
        keyfile = self._ctx_opts.get('keyfile', None)
        password = self._ctx_opts.get('password', None)
        supports_password = True
        if certfile and keyfile:
            # if password:  # for debugging
            #     print("password = {0}".format(password))
            try:
                context.load_cert_chain(certfile=certfile,
                                        keyfile=keyfile,
                                        password=password)
            except SSLError as e:
                msg = ('Could not use client cert, key or password: {0}'
                       .format(e.strerror))
                raise SSLError(msg)
            except TypeError:
                # urllib3.create_urllib3_context() (as of v1.22) and older ssl
                # modules do not support setting a private key password.
                # However, we can't use inspect to test for the kwarg, because
                # load_cert_chain is a built-in method bound to OpenSSL lib.
                # See try below
                supports_password = False

            if not supports_password and password is not None:
                raise SSLError('Private key password defined, but underlying '
                               'SSL context does not support setting it')

            if not supports_password:
                try:
                    # See try above, for why we are trying again
                    context.load_cert_chain(certfile=certfile,
                                            keyfile=keyfile)
                except SSLError as e:
                    msg = ('Could not use client cert or key: {0}'
                           .format(e.strerror))
                    raise SSLError(msg)

    def init_poolmanager(self, *args, **kwargs):
        context = create_urllib3_context(**self._ctx_create_opts)
        self._update_context(context)
        kwargs['ssl_context'] = context
        return super(SslContextAdapter, self).init_poolmanager(*args,
                                                               **kwargs)

    def proxy_manager_for(self, *args, **kwargs):
        context = create_urllib3_context(**self._ctx_create_opts)
        self._update_context(context)
        kwargs['ssl_context'] = context
        return super(SslContextAdapter, self).proxy_manager_for(*args,
                                                                **kwargs)

    # **kwargs doesn't work here; requests' send() calls 'proxies' positionally
    def get_connection(self, url, proxies=None):
        url = self._normalize_hostname(url)
        return super(SslContextAdapter, self).get_connection(url,
                                                             proxies=proxies)

    def request_url(self, request, proxies):
        request.url = self._normalize_hostname(request.url)
        return super(SslContextAdapter, self).request_url(request, proxies)

    def send(self, request, **kwargs):
        request.url = self._normalize_hostname(request.url)
        return super(SslContextAdapter, self).send(request, **kwargs)


def ssl_config_to_context_opts(config):
    if isinstance(config, SslConfig):
        ssl_config = config.to_ssl_config()
    else:
        ssl_config = config

    if not isinstance(ssl_config, dict):
        raise TypeError("SSL config not defined as dictionary")
    if 'name' not in ssl_config:
        raise KeyError("SSL config does not have a name property")

    # SslContextAdapter context_create_options
    ctx_c_opts = dict()
    ctx_c_opts['ssl_version'] = \
        resolve_ssl_version(ssl_config.get('ssl_version', None))
    ctx_c_opts['cert_reqs'] = \
        resolve_cert_reqs(ssl_config.get('ssl_verify_mode', None))
    ssl_opts = ssl_config.get('ssl_options', None)
    opts = 0
    if ssl_opts and isinstance(ssl_opts, list):
        # ssl OP_* enums are dynamically loaded from OpenSSL, so verify
        # they are present in ssl module before bitwise appending them
        op_opts = [o for o in dir(ssl) if o.startswith('OP_')]
        for opt in ssl_opts:
            if opt in op_opts:
                opts |= getattr(ssl, opt)
            else:
                # TODO: Log (don't raise) unresolvable options, for admin
                pass
    ctx_c_opts['options'] = opts if opts else None
    ctx_c_opts['ciphers'] = ssl_config.get('ssl_ciphers', None)

    # SslContextAdapter context_options
    ctx_opts = dict()
    ctx_opts['cafile'] = ssl_config.get('ca_custom_certs', None)
    ctx_opts['certfile'] = ssl_config.get('client_cert', None)
    ctx_opts['keyfile'] = ssl_config.get('client_key', None)
    # coerce password to str or pyOpenSSL complains
    pw = ssl_config.get('client_key_pass', None)
    ctx_opts['password'] = str(pw) if pw else None
    # print('password: {0}'.format(ctx_opts['password']))

    # SslContextAdapter adapter_options
    def _redo_value(value):
        if value is None:
            return None
        if value == 'False':
            return False
        if int(value) in range(11):
            return int(value)
        return None
    adptr_opts = dict()
    adptr_opts['retries'] = _redo_value(
        ssl_config.get('https_retries', None))
    adptr_opts['redirects'] = _redo_value(
        ssl_config.get('https_redirects', None))

    return ctx_c_opts, ctx_opts, adptr_opts


def get_ssl_context_opts(url):
    """
    :param url: URL or base URL, e.g. https://mydomain:8000
    :type url: basestring
    :return: tuple of dicts that matches input for SslContextAdapter
    """

    ssl_default_config = SslConfig.objects.get_create_default()
    ssl_config = ssl_default_config
    """:type: dict"""

    host_port = hostname_port(url)  # MUST to be lowercase

    try:
        host_port_map = HostnamePortSslConfig.objects.get(
            hostname_port=host_port)
        logger.debug("Found Hostname:Port record get for: {0}"
                     .format(host_port))
        config = host_port_map.ssl_config

        if config and isinstance(config, SslConfig):
            logger.debug("Found SslConfig related record: {0}"
                         .format(config.to_ssl_config()
                                 .get('name', '(name missing)')))
            ssl_config = config
        else:
            logger.debug("Missing SslConfig related record, "
                         "reverting to default")
            host_port_map.ssl_config = ssl_default_config
            host_port_map.save()
    except HostnamePortSslConfig.DoesNotExist:
        logger.debug("Hostname:Port record not found for: {0}"
                     .format(host_port))
        logger.debug("Hostname:Port objects:\n{0}"
                     .format(HostnamePortSslConfig.objects.all()))
        # TODO: Log for admin; communicate to user?
        # TODO: Should routed URL be rewritten back to original URL,
        #       i.e. no /pki path prefix?
        #       If logic flow gets here, record should exist. Maybe have a
        #       Default exposed in widget and revert to it?
        pass
    except HostnamePortSslConfig.MultipleObjectsReturned:
        # Shouldn't happen...
        pass

    return ssl_config_to_context_opts(ssl_config)


def https_request(url, data=None, method='GET', headers=None,
                  access_token=None):
    if headers is None:
        headers = {}

    # IMPORTANT: base_url is (scheme://hostname:port), not full url.
    # Note: urllib3 (as of 1.22) seems to care about case when matching the
    # hostname to the peer server's SSL cert, in contrast to the spec, which
    # says such matches should be case-insensitive (this is a bug):
    #   https://tools.ietf.org/html/rfc5280#section-4.2.1.6
    #   https://tools.ietf.org/html/rfc6125 <-- best practices
    # normalize_hostname() handles this bug
    base_url = requests_base_url(normalize_hostname(url))
    http_client = Session()  # type: requests.Session
    http_client.mount(base_url,
                      SslContextAdapter(*get_ssl_context_opts(base_url)))

    req_method = getattr(http_client, method.lower())

    if access_token:
        headers['Authorization'] = "Bearer {}".format(access_token)
        parsed_url = urlparse(url)
        params = parse_qsl(parsed_url.query.strip())
        # Don't add access token to params; prefer header fields
        # TODO: Should we add a call param option to enable/disable?
        # params.append(('access_token', access_token))
        params = urlencode(params)
        url = "{proto}://{address}{path}?{params}"\
              .format(proto=parsed_url.scheme, address=parsed_url.netloc,
                      path=parsed_url.path, params=params)

    # TODO: [FIXME] Temp workaround for decompression error in arcrest pkg,
    #       in arcrest.web._base._chunk()
    headers['Accept-Encoding'] = ''

    resp = None
    # TODO: Do we need GeoFence stuff here, like in geonode/security/models.py?
    #       See: geonode.security.models.http_request() response handling
    try:
        resp = req_method(url, headers=headers, data=data)
    except RequestException:
        logger.debug(traceback.format_exc())

    return resp
