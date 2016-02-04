# Copyright (c) 2016 OpenStack Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import copy

from oslo_config import cfg
from oslo_config import types
import yaml

from act.engine import utils


SCENARIOS = 'act/scenarios/'


class Yaml(types.String):

    def __call__(self, value):
        value = str(value)
        try:
            value = yaml.safe_load(value)
        except Exception:
            raise ValueError('YAML value is expected, but got: %s' % value)
        return value

    def __repr__(self):
        return "YAML data"


COMMON_OPTS = [
]

OPENSTACK_OPTS = [
    cfg.StrOpt('os-auth-url', metavar='<auth-url>',
               default=utils.env('OS_AUTH_URL'),
               sample_default='',
               help='Authentication URL, defaults to env[OS_AUTH_URL].'),
    cfg.StrOpt('os-tenant-name', metavar='<auth-tenant-name>',
               default=utils.env('OS_TENANT_NAME'),
               sample_default='',
               help='Authentication tenant name, defaults to '
                    'env[OS_TENANT_NAME].'),
    cfg.StrOpt('os-username', metavar='<auth-username>',
               default=utils.env('OS_USERNAME'),
               sample_default='',
               help='Authentication username, defaults to env[OS_USERNAME].'),
    cfg.StrOpt('os-password', metavar='<auth-password>',
               default=utils.env('OS_PASSWORD'),
               sample_default='',
               help='Authentication password, defaults to env[OS_PASSWORD].'),
    cfg.StrOpt('os-cacert', metavar='<auth-cacert>',
               default=utils.env('OS_CACERT'),
               sample_default='',
               help='Location of CA Certificate, defaults to env[OS_CACERT].'),
    cfg.BoolOpt('os-insecure',
                default=(utils.env('OS_INSECURE') or False),
                help='When using SSL in connections to the registry server, '
                     'do not require validation via a certifying authority, '
                     'defaults to env[OS_INSECURE].'),
    cfg.StrOpt('os-region-name', metavar='<auth-region-name>',
               default=utils.env('OS_REGION_NAME') or 'RegionOne',
               help='Authentication region name, defaults to '
                    'env[OS_REGION_NAME].'),

    cfg.StrOpt('external-net',
               default=utils.env('ACT_EXTERNAL_NET'),
               help='Name or ID of external network, defaults to '
                    'env[ACT_EXTERNAL_NET]. If no value provided then '
                    'Act picks any of available external networks.'),

    cfg.StrOpt('image-name',
               default=utils.env('ACT_IMAGE') or 'act-image',
               help='Name of image to use. The default is created by '
                    'act-image-builder.'),
    cfg.StrOpt('flavor-name',
               default=utils.env('ACT_FLAVOR') or 'act-flavor',
               help='Name of image flavor. The default is created by '
                    'act-image-builder.'),
]

SCENARIO_OPTS = [
    cfg.StrOpt('scenario',
               default=utils.env('ACT_SCENARIO') or 'boom',
               help=utils.make_help_options(
                   'Scenario to play. Can be a file name or one of aliases: '
                   '%s. Defaults to env[ACT_SCENARIO].', SCENARIOS,
                   type_filter=lambda x: x.endswith('.yaml'))),
]

MAIN_OPTS = COMMON_OPTS + OPENSTACK_OPTS + SCENARIO_OPTS


def list_opts():
    all_opts = (COMMON_OPTS + OPENSTACK_OPTS + SCENARIO_OPTS)
    yield (None, copy.deepcopy(all_opts))
