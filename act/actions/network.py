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


class CreateNetwork(actions.CreateAction):
    meta_type = 'meta_net'
    depends_on = {'meta_net'}

    def act(self, items):
        LOG.info('Create Network is called! %s', items)
        net = dict(name='foo', id='1234')
        time.sleep(random.random())
        return item.Item('net', net, use_limit=10)


class DeleteNetwork(actions.DeleteAction):
    depends_on = {'net'}

    def act(self, items):
        assert len(items) == 1
        LOG.info('Delete network is called! %s', items)


class CreateSubnet(actions.CreateAction):
    meta_type = 'meta_subnet'
    depends_on = {'net', 'meta_subnet'}

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
    meta_type = 'meta_router'
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
    meta_type = 'meta_router_interface'
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
    meta_type = 'meta_port'
    depends_on = {'meta_port', 'net', 'subnet'}

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
