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
import rq

from act.engine import consts
from act.engine import item as item_pkg
from act.engine import registry
from act.engine import utils
from act.engine import world as world_pkg

LOG = logging.getLogger(__name__)


Task = collections.namedtuple('Task', ['action', 'items'])
NoOpTask = Task(action=None, items=None)


def produce_task(world, actions):

    available_actions = {}
    for action in actions:
        item_types = action.get_depends_on()
        world_items = world.filter_items(item_types)
        filtered_items = list(action.filter_items(world_items))

        if not filtered_items:
            continue

        LOG.info('Action: %s, item-types: %s, filtered_items: %s', action,
                 item_types, filtered_items)

        # check that filtered_items contain items of *all* item_types
        filtered_item_types = set(i.item_type for i in filtered_items)
        if item_types and filtered_item_types != item_types:
            continue

        available_actions[action] = filtered_items

    if available_actions:
        chosen_action = utils.weighted_random_choice(available_actions.keys())
        available_items = available_actions[chosen_action]

        # pick one random item per type
        items_per_type = collections.defaultdict(list)
        for item in available_items:
            items_per_type[item.item_type].append(item)

        chosen_items = [random.choice(v) for v in items_per_type.values()]

        task = Task(action=chosen_action, items=chosen_items)
    else:
        # nothing to do
        task = NoOpTask

    LOG.info('Produced task: %s', task)

    return task


def handle_operation(op, world):
    # handles a specific operation on the world
    LOG.info('Handle: %s', op)
    op.do(world)


def work(task):
    # does real action inside worker processes
    LOG.info('Executing action %s', task)

    action = task.action
    action_result = action.act(task.items)
    operation_class = action.get_operation_class()
    operation = operation_class(item=action_result, dependencies=task.items)

    LOG.info('Operation %s', operation)
    return operation


def process():
    # initialize the world
    default_items = []
    for action in registry.get_actions():
        meta_type = action.get_meta_type()
        if meta_type:
            item = item_pkg.Item(meta_type, None)
            default_items.append(item)

    world = world_pkg.World()
    for item in default_items:
        world.put(item)

    # initial execution tasks
    steps = 10
    seed = 2
    async_results = []
    task_q = rq.Queue(consts.TASK_QUEUE_NAME)
    failed_q = rq.Queue(consts.FAILURE_QUEUE_NAME)
    failed_q.empty()

    LOG.info('Seeding initial items: %s', seed)

    for x in range(seed):
        next_task = produce_task(world, registry.get_actions())
        async_results.append(task_q.enqueue(work, next_task))

    LOG.info('Starting the work, steps: %s', steps)

    proceed = True
    counter = 0
    failures = 0

    while proceed:
        LOG.info('Work queue: %s', len(async_results))
        proceed = len(async_results) == 0

        nx = []
        for x in range(len(async_results)):
            operation = async_results[x].return_value

            if operation is None:
                proceed = True
                nx.append(async_results[x])
            else:
                handle_operation(operation, world)
                counter += 1
                if counter < steps:
                    next_task = produce_task(world, registry.get_actions())
                    nx.append(task_q.enqueue(work, next_task))
                    proceed = True

        async_results = nx

        if len(failed_q) > failures:
            failures = len(failed_q)
            LOG.info('Failures: %s', failures)

        time.sleep(0.5)

    LOG.info('World: %s', world)
