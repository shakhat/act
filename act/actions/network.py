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
        return item.Item('net', net, ref_count_limit=10)


class DeleteNetwork(actions.DeleteAction):
    depends_on = {'net'}

    def act(self, items):
        assert len(items) == 1
        LOG.info('Delete network is called! %s', items)
