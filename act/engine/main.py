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

import collections
import random
import time

from oslo_log import log as logging

from act.engine import actions
from act.engine import item as item_pkg


LOG = logging.getLogger(__name__)

OPERATION_ACT = 'act'
OPERATION_RESPONSE = 'response'


class CreateNet(actions.CreateAction):
    meta_type = 'meta_net'
    depends_on = {'meta_net'}

    def act(self, items):
        LOG.info('Create Net is called! %s', items)
        net = dict(name='foo', id='1234')
        time.sleep(random.random())
        return item_pkg.Item('net', net, ref_count_limit=10)


class DeleteNet(actions.DeleteAction):
    depends_on = {'net'}

    def act(self, items):
        assert len(items) == 1
        LOG.info('Delete net is called! %s', items)


class DoNothing(actions.IdempotantAction):

    def act(self, items):
        LOG.info('Do Nothing is called! %s', items)


REGISTRY = [CreateNet(), DeleteNet(), DoNothing()]


def work(task):
    LOG.info('Executing action %s', task)

    action = task.action
    action_result = action.act(task.items)
    operation_class = action.get_operation_class()
    operation = operation_class(item=action_result, dependencies=task.items)

    LOG.info('Operation %s', operation)
    return operation


Task = collections.namedtuple('Task', ['action', 'items'])
NoOpTask = Task(action=None, items=None)
StopTask = None
