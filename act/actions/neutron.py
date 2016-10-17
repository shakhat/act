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

import random
import time

from oslo_log import log as logging

from act.engine import actions
from act.engine import item


LOG = logging.getLogger(__name__)


class InitNeutronTypes(actions.BatchCreateAction):
    depends_on = {'root'}
    limit = 1

    def __init__(self):
        super(InitNeutronTypes, self).__init__()

    def act(self, items):
        LOG.info('Initialize Neutron meta-classes')
        return (
            item.Item('meta_network'),
            item.Item('meta_external_network'),
            item.Item('meta_subnet'),
            item.Item('meta_router'),
            item.Item('meta_router_interface'),
            item.Item('meta_port'),
        )


class DiscoverExternalNetworks(actions.BatchCreateAction):
    depends_on = {'meta_external_network'}
    limit = 1

    def act(self, items):
        LOG.info('Discover external network')
        ext_net = dict(name='ext_net', id='9999')
        return [item.Item('external_network', ext_net, read_only=True)]


class CreateNetwork(actions.CreateAction):
    depends_on = {'meta_network'}

    def act(self, items):
        LOG.info('Create Network is called! %s', items)
        net = dict(name='foo', id='1234')
        time.sleep(random.random())
        return item.Item('network', net, use_limit=10)


class DeleteNetwork(actions.DeleteAction):
    depends_on = {'network'}

    def act(self, items):
        assert len(items) == 1
        LOG.info('Delete network is called! %s', items)


class CreateSubnet(actions.CreateAction):
    depends_on = {'network', 'meta_subnet'}

    def act(self, items):
        LOG.info('Create Subnet is called! %s', items)
        subnet = dict(name='foo', id='1234')
        time.sleep(random.random())
        return item.Item('subnet', subnet, use_limit=10)


class DeleteSubnet(actions.DeleteAction):
    depends_on = {'subnet'}

    def act(self, items):
        assert len(items) == 1
        LOG.info('Delete subnet is called! %s', items)


class CreateRouter(actions.CreateAction):
    depends_on = {'meta_router'}

    def act(self, items):
        LOG.info('Create Router is called! %s', items)
        router = dict(name='foo', id='1234')
        time.sleep(random.random())
        return item.Item('router', router, use_limit=10)


class DeleteRouter(actions.DeleteAction):
    depends_on = {'router'}

    def act(self, items):
        assert len(items) == 1
        LOG.info('Delete router is called! %s', items)


class CreateRouterInterface(actions.CreateAction):
    depends_on = {'meta_router_interface', 'subnet', 'router'}

    def act(self, items):
        LOG.info('Create RouterInterface is called! %s', items)
        router_interface = dict(name='foo', id='1234')
        time.sleep(random.random())
        return item.Item('router_interface', router_interface,
                         use_limit=10)


class DeleteRouterInterface(actions.DeleteAction):
    depends_on = {'router_interface'}

    def act(self, items):
        assert len(items) == 1
        LOG.info('Delete router interface is called! %s', items)


class CreatePort(actions.CreateAction):
    depends_on = {'meta_port', 'network', 'subnet'}

    def act(self, items):
        LOG.info('Create Port is called! %s', items)
        port = dict(name='foo', id='1234')
        time.sleep(random.random())
        return item.Item('port', port, use_limit=10)


class DeletePort(actions.DeleteAction):
    depends_on = {'port'}

    def act(self, items):
        assert len(items) == 1
        LOG.info('Delete port is called! %s', items)
