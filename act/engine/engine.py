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

from oslo_config import cfg
from oslo_log import log as logging
import rq

from act.engine import config
from act.engine import consts
from act.engine import main
from act.engine import utils

LOG = logging.getLogger(__name__)


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

        task = main.Task(action=chosen_action, items=chosen_items)
    else:
        # nothing to do
        task = main.NoOpTask

    LOG.info('Produced task: %s', task)

    return task


def handle_operation(op, world):
    LOG.info('Handle: %s', op)
    op.do(world)


def process():
    # initialize the world
    default_items = []
    for action_klazz in main.REGISTRY:
        meta_type = action_klazz.get_meta_type()
        if meta_type:
            item = main.Item(meta_type, None)
            default_items.append(item)

    world = main.World()
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
        next_task = produce_task(world, main.REGISTRY)
        async_results.append(task_q.enqueue(main.work, next_task))

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
                    next_task = produce_task(world, main.REGISTRY)
                    nx.append(task_q.enqueue(main.work, next_task))
                    proceed = True

        async_results = nx

        if len(failed_q) > failures:
            failures = len(failed_q)
            LOG.info('Failures: %s', failures)

        time.sleep(0.5)

    LOG.info('World: %s', world)


def run():
    utils.init_config_and_logging(config.ENGINE_OPTS)

    redis_connection = utils.make_redis_connection(host=cfg.CONF.redis_host,
                                                   port=cfg.CONF.redis_port)
    with rq.Connection(redis_connection):
        LOG.info('Connected to Redis')
        process()


if __name__ == '__main__':
    run()
