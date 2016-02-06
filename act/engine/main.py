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

import collections
import multiprocessing
import random

from oslo_log import log as logging

from act.engine import config
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
        del self.storage[item.id]

    def get_item_types(self):
        item_types = set()
        for item in self.storage.values():
            if item.can_be_used():
                item_types.add(item.item_type)
        return item_types

    def pick_items(self, item_types):
        if not item_types:
            return

        items_by_types = collections.defaultdict(list)
        for item in self.storage.values():
            if item.item_type in item_types and item.can_be_used():
                items_by_types[item.item_type].append(item)

        items = [random.choice(v) for v in items_by_types.values()]
        for item in items:
            item.lock()

        return items

    def __repr__(self):
        return str(self.storage)


class Action(object):
    weight = 0.1
    meta_type = None
    depends_on = set()

    def __init__(self):
        super(Action, self).__init__()

    def get_weight(self):
        return self.weight

    def get_meta_type(self):
        return self.meta_type

    def get_depends_on(self):
        return self.depends_on

    def act(self, items):
        LOG.info('act(%s)', items)

    def get_operation_class(self):
        return Operation


class CreateAction(Action):
    weight = 0.9

    def __init__(self):
        super(CreateAction, self).__init__()

    def get_operation_class(self):
        return CreateOperation


class CreateNet(CreateAction):
    meta_type = 'meta_net'
    depends_on = {'meta_net'}

    def act(self, items):
        LOG.info('Create Net is called! %s', items)
        net = dict(name='foo', id='1234')
        return Item('net', net, ref_count_limit=10)


class DoNothing(Action):

    def act(self, items):
        LOG.info('Do Nothing is called! %s', items)


REGISTRY = [CreateNet(), DoNothing()]


class Operation(object):
    def __init__(self, item, dependencies):
        self.item = item
        self.dependencies = dependencies

    def do(self, world):
        pass


class CreateOperation(Operation):
    def do(self, world):
        LOG.info('Add something to world')
        world.put(self.item, self.dependencies)


class Item(object):
    def __init__(self, item_type, payload, ref_count_limit=1000):
        self.item_type = item_type
        self.payload = payload
        self.id = utils.make_id()
        self.refs = set()
        self.ref_count_limit = ref_count_limit
        self.lock_count = 0

    def __repr__(self):
        return str(dict(id=self.id, item_type=self.item_type,
                        payload=self.payload, ref_count=len(self.refs)))

    def lock(self):
        self.lock_count += 1

    def unlock(self):
        self.lock_count -= 1

    def can_be_used(self):
        return len(self.refs) + self.lock_count < self.ref_count_limit

    def add_ref(self, other_id):
        self.refs.add(other_id)

    def del_ref(self, other_id):
        self.refs.pop(other_id)


class Worker(multiprocessing.Process):

    def __init__(self, task_queue, result_queue):
        multiprocessing.Process.__init__(self)
        self.task_queue = task_queue
        self.result_queue = result_queue

    def run(self):
        proc_name = self.name
        while True:
            task = self.task_queue.get()

            if task is None:
                # Poison pill means shutdown
                LOG.info('%s: Exiting', proc_name)
                self.task_queue.task_done()
                break

            LOG.info('%s executing action %s', proc_name, task)

            action = task.action
            action_result = action.act(task.items)
            operation_class = action.get_operation_class()
            operation = operation_class(item=action_result,
                                        dependencies=task.items)

            LOG.info('%s put operation %s into queue', proc_name, operation)
            self.task_queue.task_done()
            self.result_queue.put(operation)
        return


Task = collections.namedtuple('Task', ['action', 'items'])


def produce_task(world, actions, task_queue):
    available_item_types = world.get_item_types()
    available_actions = [a for a in actions
                         if a.get_depends_on() <= available_item_types]

    action = random.choice(available_actions)
    items = world.pick_items(action.get_depends_on())

    task_queue.put(Task(action=action, items=items))


def handle_operation(op, world):
    LOG.info('Handle: %s', op)
    op.do(world)


def process():
    # Establish communication queues
    task_queue = multiprocessing.JoinableQueue()
    result_queue = multiprocessing.Queue()

    # Start workers
    workers_count = 2  # multiprocessing.cpu_count() * 2
    LOG.info('Creating %d workers' % workers_count)
    workers = [Worker(task_queue, result_queue) for i in range(workers_count)]
    for w in workers:
        w.start()

    default_items = []
    for action_klazz in REGISTRY:
        meta_type = action_klazz.get_meta_type()
        if meta_type:
            item = Item(meta_type, None)
            default_items.append(item)

    world = World()
    for item in default_items:
        world.put(item)

    for i in range(workers_count):
        result_queue.put(Operation(None, None))

    steps = 10

    for i in range(steps):
        operation = result_queue.get()
        handle_operation(operation, world)

        produce_task(world, REGISTRY, task_queue)

    # todo pick remainders from result_queue

    # Add a poison pill for each worker
    for i in range(workers_count):
        task_queue.put(None)

    # Wait for all of the tasks to finish
    task_queue.join()

    LOG.info('World: %s', world)


def main():
    utils.init_config_and_logging(config.MAIN_OPTS)

    process()


if __name__ == "__main__":
    main()