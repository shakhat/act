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

from act.engine import utils


LOG = logging.getLogger(__name__)

OPERATION_ACT = 'act'
OPERATION_RESPONSE = 'response'


class World(object):
    def __init__(self):
        self.storage = {}

    def put(self, item, dependencies=None):
        self.storage[item.id] = item

        if dependencies:
            for dep in dependencies:
                # dependencies are copies of storage objects!
                real_dep = self.storage[dep.id]
                real_dep.add_ref(item.id)
                real_dep.unlock()

    def pop(self, item):
        for ref_id in self.storage[item.id].refs:
            self.storage[ref_id].del_ref(item.id)

        del self.storage[item.id]

    def filter_items(self, item_types):
        for item in self.storage.values():
            if not item_types or item.item_type in item_types:
                yield item

    def __repr__(self):
        return str(self.storage)


class Action(object):
    weight = 0.1
    meta_type = None
    depends_on = None

    def __init__(self):
        super(Action, self).__init__()

    def get_weight(self):
        return self.weight

    def get_meta_type(self):
        return self.meta_type

    def get_depends_on(self):
        return self.depends_on

    def filter_items(self, items):
        pass

    def act(self, items):
        LOG.info('act(%s)', items)

    def get_operation_class(self):
        return Operation


class CreateAction(Action):
    weight = 0.9

    def __init__(self):
        super(CreateAction, self).__init__()

    def filter_items(self, items):
        for item in items:
            if item.can_be_used():
                yield item

    def get_operation_class(self):
        return CreateOperation


class DeleteAction(Action):
    weight = 0.1

    def filter_items(self, items):
        for item in items:
            if not item.has_dependants() and not item.is_locked():
                yield item

    def get_operation_class(self):
        return DeleteOperation


class IdempotantAction(Action):
    def filter_items(self, items):
        for item in items:
            yield item


class IdempotantBlockingAction(Action):
    def filter_items(self, items):
        for item in items:
            if not item.is_locked():
                yield item


class CreateNet(CreateAction):
    meta_type = 'meta_net'
    depends_on = {'meta_net'}

    def act(self, items):
        LOG.info('Create Net is called! %s', items)
        net = dict(name='foo', id='1234')
        time.sleep(random.random())
        return Item('net', net, ref_count_limit=10)


class DeleteNet(DeleteAction):
    depends_on = {'net'}

    def act(self, items):
        assert len(items) == 1
        LOG.info('Delete net is called! %s', items)


class DoNothing(IdempotantAction):

    def act(self, items):
        LOG.info('Do Nothing is called! %s', items)


REGISTRY = [CreateNet(), DeleteNet(), DoNothing()]


class Operation(object):
    def __init__(self, item, dependencies):
        self.item = item
        self.dependencies = dependencies

    def do(self, world):
        LOG.info('Doing nothing')


class CreateOperation(Operation):
    def do(self, world):
        LOG.info('Add to the world: %s', self.item)
        world.put(self.item, self.dependencies)


class DeleteOperation(Operation):
    def do(self, world):
        LOG.info('Delete in the world: %s', self.dependencies[0])
        world.pop(self.dependencies[0])


class Item(object):
    def __init__(self, item_type, payload, ref_count_limit=1000):
        self.item_type = item_type
        self.payload = payload
        self.id = utils.make_id()  # unique id
        self.refs = set()  # items that depend on this one
        self.ref_count_limit = ref_count_limit  # max number of dependants
        self.lock_count = 0  # number of locks taken by operations

    def __repr__(self):
        return str(dict(id=self.id, item_type=self.item_type,
                        payload=self.payload, ref_count=len(self.refs)))

    def lock(self):
        self.lock_count += 1

    def unlock(self):
        self.lock_count -= 1

    def add_ref(self, other_id):
        self.refs.add(other_id)

    def del_ref(self, other_id):
        self.refs.pop(other_id)

    def has_dependants(self):
        return len(self.refs) > 0

    def is_locked(self):
        return self.lock_count > 0

    def can_be_used(self):
        # True if it's possible to add more dependants to this item
        return len(self.refs) + self.lock_count < self.ref_count_limit


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
