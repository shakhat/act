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


class InitNovaTypes(actions.BatchCreateAction):
    depends_on = {'root'}
    limit = 1

    def act(self, items):
        LOG.info('Initialize Nova meta-classes')
        return (
            item.Item('meta_flavor'),
            item.Item('meta_server'),
        )


class DiscoverFlavors(actions.BatchCreateAction):
    depends_on = {'meta_flavor'}
    limit = 1

    def act(self, items):
        LOG.info('Discover flavors')
        flavor = dict(name='m1.micro', id='9999')
        return [item.Item('flavor', flavor, read_only=True)]


class CreateServer(actions.CreateAction):
    depends_on = {'meta_server', 'image', 'flavor', 'port'}

    def act(self, items):
        LOG.info('Create Server is called! %s', items)
        server = dict(name='foo', id='1234')
        time.sleep(random.random())
        return item.Item('server', server, use_limit=10)


class DeleteServer(actions.DeleteAction):
    depends_on = {'server'}

    def act(self, items):
        assert len(items) == 1
        LOG.info('Delete server is called! %s', items)


