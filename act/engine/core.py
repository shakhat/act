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
from oslo_utils import timeutils
import rq

from act.engine import consts
from act.engine import item as item_pkg
from act.engine import metrics
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


def do_action(task):
    # does real action inside worker processes
    LOG.info('Executing action %s', task)

    action = task.action
    action_result = action.act(task.items)
    operation_class = action.get_operation_class()
    operation = operation_class(item=action_result, dependencies=task.items)

    LOG.info('Operation %s', operation)
    return operation


def process(scenario, interval):
    # the entry-point to engine
    registry.init()
    metrics.clear()

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

    # play!
    play = scenario['play']

    # add tear down
    play.append(dict(concurrency=0, duration=1000))

    task_results = []
    task_queue = rq.Queue(consts.TASK_QUEUE_NAME)
    failed_queue = rq.Queue(consts.FAILURE_QUEUE_NAME)
    failed_queue.empty()
    metrics.set_metric('failures', 0, mood=metrics.MOOD_HAPPY)

    failures = 0
    counter = 0

    for stage in play:
        duration = stage['duration']
        concurrency = stage['concurrency']

        watch = timeutils.StopWatch(duration=duration)
        watch.start()

        while not watch.expired():

            pending = []
            for task_result in task_results:
                operation = task_result.return_value

                if operation is None:
                    pending.append(task_result)
                else:
                    handle_operation(operation, world)

                    counter += 1
                    metrics.set_metric('operation', counter)

            addition = concurrency - len(pending)
            if addition > 0:  # need to add more tasks
                for i in range(addition):
                    next_task = produce_task(world, registry.get_actions())
                    pending.append(task_queue.enqueue(do_action, next_task))

            task_results = pending

            if len(failed_queue) > failures:
                failures = len(failed_queue)
                metrics.set_metric('failures', failures, mood=metrics.MOOD_SAD)

            metrics.set_metric('backlog', len(task_results))

            if concurrency == 0 and len(task_results) == 0:
                break  # tear down finished

            time.sleep(interval)

    LOG.info('World: %s', world)
